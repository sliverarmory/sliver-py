"""
Sliver Implant Framework
Copyright (C) 2022  Bishop Fox

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from collections.abc import AsyncGenerator, Collection
from contextlib import suppress
from dataclasses import dataclass
from typing import TypeVar

import grpc

from . import models
from ._duration import request_timeout_nanoseconds
from ._protocols import RequestRoutedModel
from ._rpc import PydanticSliverRPCStub
from .enums import BeaconTaskState, EventType
from .errors import SliverTimeoutError, raise_for_command_error
from .interactive import BaseInteractiveCommands
from .models import ProtobufModel, _model_from_bytes

_RequestT = TypeVar("_RequestT", bound=RequestRoutedModel)
_ResultT = TypeVar("_ResultT", bound=ProtobufModel)


@dataclass(frozen=True)
class _PendingBeaconResult:
    future: asyncio.Future[ProtobufModel]
    result_type: type[ProtobufModel]
    timeout: float | None
    deadline: float | None


class _EventStreamStopped:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error


class _ClientEventBroker:
    """Multiplex one client event stream to task waiters and subscribers."""

    _EVENT_TYPE = EventType.BEACON_TASK_RESULT.value
    _MAX_ORPHANED_RESULTS = 256
    _SUBSCRIBER_QUEUE_SIZE = 256
    _REMOTE_CANCEL_TIMEOUT = 5.0
    _INITIAL_RECONNECT_DELAY = 0.25
    _MAX_RECONNECT_DELAY = 5.0
    _TASK_POLL_INTERVAL = 0.25
    _ACTIVE_TASK_STATES = frozenset(
        {
            "",
            BeaconTaskState.PENDING.value,
            BeaconTaskState.SENT.value,
        }
    )

    def __init__(self, stub: PydanticSliverRPCStub) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._stub = stub
        self._pending: dict[str, _PendingBeaconResult] = {}
        self._orphaned_results: OrderedDict[str, None] = OrderedDict()
        self._resolvers: dict[str, asyncio.Task[None]] = {}
        self._pollers: dict[str, asyncio.Task[None]] = {}
        self._subscribers: dict[
            int,
            tuple[
                asyncio.Queue[models.clientpb.Event | _EventStreamStopped],
                frozenset[str] | None,
            ],
        ] = {}
        self._next_subscriber_id = 0
        self._watcher: asyncio.Task[None] | None = None
        self._ready = asyncio.Event()
        self._start_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        self._watcher_error: Exception | None = None
        self._closed = False

    async def start(self) -> None:
        """Start the shared event subscription once, on first use."""

        if self._closed:
            raise RuntimeError("client event broker is closed")
        async with self._start_lock:
            if self._closed:
                raise RuntimeError("client event broker is closed")
            if self._watcher is None:
                self._watcher = asyncio.create_task(self._event_stream())

        await self._ready.wait()
        if self._closed:
            raise RuntimeError("client event broker is closed")
        watcher = self._watcher
        if watcher is None or watcher.done():
            raise RuntimeError("client event broker is not running") from self._watcher_error

    async def subscribe(
        self, event_types: Collection[str] | None = None
    ) -> AsyncGenerator[models.clientpb.Event, None]:
        """Subscribe to the shared event stream with bounded buffering."""

        filters = frozenset(event_types) if event_types is not None else None
        queue: asyncio.Queue[models.clientpb.Event | _EventStreamStopped] = (
            asyncio.Queue(maxsize=self._SUBSCRIBER_QUEUE_SIZE)
        )
        async with self._state_lock:
            if self._closed:
                raise RuntimeError("client event broker is closed")
            subscriber_id = self._next_subscriber_id
            self._next_subscriber_id += 1
            self._subscribers[subscriber_id] = (queue, filters)

        try:
            try:
                await self.start()
            except RuntimeError:
                if self._closed:
                    return
                raise
            while True:
                item = await queue.get()
                if isinstance(item, _EventStreamStopped):
                    if item.error is not None:
                        raise RuntimeError("client event stream stopped") from item.error
                    return
                yield item
        finally:
            async with self._state_lock:
                self._subscribers.pop(subscriber_id, None)

    async def wait_for_result(
        self,
        task_id: str,
        result_type: type[_ResultT],
        timeout: float | None,
    ) -> _ResultT:
        """Register a task result waiter and decode its Pydantic response."""

        await self.start()
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ProtobufModel] = loop.create_future()
        deadline = None if timeout is None else loop.time() + max(timeout, 0.0)
        pending = _PendingBeaconResult(future, result_type, timeout, deadline)
        resolve_orphan = False
        async with self._state_lock:
            if self._closed:
                raise RuntimeError("beacon task broker is closed")
            if task_id in self._pending:
                raise RuntimeError(f"beacon task {task_id!r} is already pending")
            self._pending[task_id] = pending
            self._pollers[task_id] = asyncio.create_task(
                self._poll_for_result(task_id, pending)
            )
            if task_id in self._orphaned_results:
                self._orphaned_results.pop(task_id)
                resolve_orphan = True

        if resolve_orphan:
            await self._schedule_resolution(task_id)

        try:
            result = await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
        except asyncio.TimeoutError as err:
            await self._release_waiter(task_id, pending, cancel_future=True)
            await self._cancel_remote(task_id, timeout)
            raise SliverTimeoutError(
                operation=f"beacon task {task_id}", timeout=timeout
            ) from err
        except asyncio.CancelledError:
            await self._release_waiter(task_id, pending, cancel_future=True)
            await self._cancel_remote(task_id, timeout)
            raise
        finally:
            await self._release_waiter(task_id, pending)

        if not isinstance(result, result_type):
            raise TypeError(
                f"beacon task returned {type(result).__name__}, "
                f"expected {result_type.__name__}"
            )
        return result

    async def close(self) -> None:
        """Stop the dispatcher and fail all outstanding result waiters."""

        if self._closed:
            return
        self._closed = True
        self._ready.set()

        watcher = self._watcher
        if watcher is not None and not watcher.done():
            watcher.cancel()

        async with self._state_lock:
            resolvers = list(self._resolvers.values())
            self._resolvers.clear()
            pollers = list(self._pollers.values())
            self._pollers.clear()
            pending = list(self._pending.items())
            self._pending.clear()
            self._orphaned_results.clear()
        workers = resolvers + pollers
        for worker in workers:
            worker.cancel()
        stopped = RuntimeError("client event broker is closed")
        for _, waiter in pending:
            if not waiter.future.done():
                waiter.future.set_exception(stopped)
        await asyncio.gather(
            *(
                self._cancel_remote(task_id, waiter.timeout)
                for task_id, waiter in pending
            )
        )

        await self._stop_subscribers()

        if watcher is not None:
            with suppress(asyncio.CancelledError, Exception):
                await watcher
        for worker in workers:
            with suppress(asyncio.CancelledError, Exception):
                await worker

    async def _release_waiter(
        self,
        task_id: str,
        pending: _PendingBeaconResult,
        *,
        cancel_future: bool = False,
    ) -> None:
        workers: list[asyncio.Task[None]] = []
        async with self._state_lock:
            current = self._pending.get(task_id)
            if current is pending:
                self._pending.pop(task_id)
                resolver = self._resolvers.pop(task_id, None)
                poller = self._pollers.pop(task_id, None)
                workers.extend(
                    worker for worker in (resolver, poller) if worker is not None
                )
        if cancel_future and not pending.future.done():
            pending.future.cancel()
        current_task = asyncio.current_task()
        for worker in workers:
            if worker is not current_task:
                worker.cancel()
        for worker in workers:
            if worker is current_task:
                continue
            with suppress(asyncio.CancelledError, Exception):
                await worker

    async def _cancel_remote(self, task_id: str, timeout: float | None) -> None:
        cancel_task = getattr(self._stub, "CancelBeaconTask", None)
        if cancel_task is None:
            return
        cancel_timeout = self._REMOTE_CANCEL_TIMEOUT
        if timeout is not None:
            cancel_timeout = min(cancel_timeout, max(timeout, 0.0))
        try:
            await cancel_task(
                models.clientpb.BeaconTask(id=task_id), timeout=cancel_timeout
            )
        except Exception as err:
            self._log.debug("could not cancel beacon task %s: %s", task_id, err)

    async def _schedule_resolution(self, task_id: str) -> None:
        async with self._state_lock:
            pending = self._pending.get(task_id)
            if (
                pending is None
                or pending.future.done()
                or task_id in self._resolvers
            ):
                return
            resolver = asyncio.create_task(self._resolve(task_id))
            self._resolvers[task_id] = resolver

    async def _resolve(self, task_id: str) -> None:
        pending: _PendingBeaconResult | None = None
        try:
            async with self._state_lock:
                pending = self._pending.get(task_id)
            if pending is None:
                return
            rpc_timeout = self._remaining_timeout(pending.deadline)
            if rpc_timeout is not None and rpc_timeout <= 0:
                return
            task_content = await self._stub.GetBeaconTaskContent(
                models.clientpb.BeaconTask(id=task_id), timeout=rpc_timeout
            )
            result = _model_from_bytes(pending.result_type, task_content.response)
            async with self._state_lock:
                current = self._pending.get(task_id)
                if current is not pending:
                    return
            if not pending.future.done():
                pending.future.set_result(result)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            self._log.debug(
                "could not resolve beacon task %s from its event; polling will "
                "continue: %s",
                task_id,
                err,
            )
        finally:
            async with self._state_lock:
                current_task = asyncio.current_task()
                if self._resolvers.get(task_id) is current_task:
                    self._resolvers.pop(task_id)

    async def _poll_for_result(
        self, task_id: str, pending: _PendingBeaconResult
    ) -> None:
        try:
            while not pending.future.done():
                remaining = self._remaining_timeout(pending.deadline)
                if remaining is not None and remaining <= 0:
                    return
                delay = self._TASK_POLL_INTERVAL
                if remaining is not None:
                    delay = min(delay, remaining)
                await asyncio.sleep(delay)

                async with self._state_lock:
                    if self._pending.get(task_id) is not pending:
                        return
                remaining = self._remaining_timeout(pending.deadline)
                if remaining is not None and remaining <= 0:
                    return
                try:
                    task_content = await self._stub.GetBeaconTaskContent(
                        models.clientpb.BeaconTask(id=task_id), timeout=remaining
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as err:
                    self._log.debug(
                        "could not poll beacon task %s: %s", task_id, err
                    )
                    continue

                state = task_content.state.strip().lower()
                if state == BeaconTaskState.COMPLETED.value:
                    try:
                        result = _model_from_bytes(
                            pending.result_type, task_content.response
                        )
                    except Exception as err:
                        if not pending.future.done():
                            pending.future.set_exception(err)
                    else:
                        if not pending.future.done():
                            pending.future.set_result(result)
                    return
                if state not in self._ACTIVE_TASK_STATES:
                    if not pending.future.done():
                        pending.future.set_exception(
                            RuntimeError(
                                f"beacon task {task_id!r} ended in state {state!r}"
                            )
                        )
                    return
        except asyncio.CancelledError:
            raise
        finally:
            async with self._state_lock:
                current_task = asyncio.current_task()
                if self._pollers.get(task_id) is current_task:
                    self._pollers.pop(task_id)

    @staticmethod
    def _remaining_timeout(deadline: float | None) -> float | None:
        if deadline is None:
            return None
        return max(deadline - asyncio.get_running_loop().time(), 0.0)

    @staticmethod
    def _put_bounded(
        queue: asyncio.Queue[models.clientpb.Event | _EventStreamStopped],
        item: models.clientpb.Event | _EventStreamStopped,
    ) -> None:
        if queue.full():
            queue.get_nowait()
        queue.put_nowait(item)

    async def _publish(self, event: models.clientpb.Event) -> None:
        async with self._state_lock:
            subscribers = list(self._subscribers.values())
        for queue, filters in subscribers:
            if filters is None or event.event_type in filters:
                self._put_bounded(queue, event.model_copy(deep=True))

    async def _stop_subscribers(self, error: Exception | None = None) -> None:
        async with self._state_lock:
            subscribers = list(self._subscribers.values())
            self._subscribers.clear()
        stopped = _EventStreamStopped(error)
        for queue, _ in subscribers:
            while not queue.empty():
                queue.get_nowait()
            self._put_bounded(queue, stopped)

    async def _dispatch(self, event: models.clientpb.Event) -> None:
        await self._publish(event)
        if event.event_type != self._EVENT_TYPE:
            return
        try:
            beacon_task = _model_from_bytes(models.clientpb.BeaconTask, event.data)
        except Exception:
            self._log.exception("could not decode beacon task-result event")
            return
        if not beacon_task.id:
            return

        should_resolve = False
        async with self._state_lock:
            if beacon_task.id in self._pending:
                should_resolve = True
            else:
                self._orphaned_results[beacon_task.id] = None
                self._orphaned_results.move_to_end(beacon_task.id)
                while len(self._orphaned_results) > self._MAX_ORPHANED_RESULTS:
                    self._orphaned_results.popitem(last=False)
        if should_resolve:
            await self._schedule_resolution(beacon_task.id)

    async def _event_stream(self) -> None:
        reconnect_delay = self._INITIAL_RECONNECT_DELAY
        try:
            while not self._closed:
                try:
                    events = self._stub.Events(models.commonpb.Empty())
                    self._ready.set()
                    received_event = False
                    async for event in events:
                        received_event = True
                        reconnect_delay = self._INITIAL_RECONNECT_DELAY
                        await self._dispatch(event)
                    if self._closed:
                        return
                    if received_event:
                        reconnect_delay = self._INITIAL_RECONNECT_DELAY
                    raise RuntimeError("client event stream ended unexpectedly")
                except asyncio.CancelledError:
                    raise
                except Exception as err:
                    self._watcher_error = err
                    self._ready.set()
                    self._log.warning(
                        "client event stream interrupted; reconnecting in %.2fs",
                        reconnect_delay,
                    )
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(
                        reconnect_delay * 2, self._MAX_RECONNECT_DELAY
                    )
        except asyncio.CancelledError:
            raise
        except Exception as err:
            self._watcher_error = err
            self._log.exception("client event broker stopped")
        finally:
            self._ready.set()
            if not self._closed:
                stopped = RuntimeError("client event broker stopped")
                async with self._state_lock:
                    pending = list(self._pending.values())
                    self._pending.clear()
                for waiter in pending:
                    if not waiter.future.done():
                        waiter.future.set_exception(stopped)
                await self._stop_subscribers(stopped)


class BaseBeacon:
    def __init__(
        self,
        beacon: models.clientpb.Beacon,
        channel: grpc.aio.Channel,
        timeout: int = 60,
    ) -> None:
        """Base class for Beacon classes.

        :param beacon: Pydantic beacon model.
        :type beacon: models.clientpb.Beacon
        :param channel: A gRPC channel.
        :type channel: grpc.aio.Channel
        :param timeout: Seconds to wait for timeout, defaults to TIMEOUT
        :type timeout: int, optional
        """
        if not isinstance(beacon, models.clientpb.Beacon):
            raise TypeError("beacon must be a models.clientpb.Beacon Pydantic model")
        self._log = logging.getLogger(self.__class__.__name__)
        self._channel = channel
        self._beacon = beacon.model_copy(deep=True)
        self._stub = PydanticSliverRPCStub(channel)
        self.timeout = timeout
        self._event_broker = _ClientEventBroker(self._stub)
        self._owns_event_broker = True
        self._closed = False

    async def close(self) -> None:
        """Release resources owned by a directly constructed beacon wrapper."""

        if self._closed:
            return
        self._closed = True
        if self._owns_event_broker:
            await self._event_broker.close()

    def _attach_event_broker(self, broker: _ClientEventBroker) -> None:
        """Use the owning client's shared event broker."""

        self._event_broker = broker
        self._owns_event_broker = False

    @property
    def beacon(self) -> models.clientpb.Beacon:
        """A copy of the complete Pydantic beacon model."""

        return self._beacon.model_copy(deep=True)

    @property
    def beacon_id(self) -> str:
        """Beacon ID"""
        return self._beacon.id

    @property
    def name(self) -> str:
        """Beacon name"""
        return self._beacon.name

    @property
    def hostname(self) -> str:
        """Beacon hostname"""
        return self._beacon.hostname

    @property
    def uuid(self) -> str:
        """Beacon UUID"""
        return self._beacon.uuid

    @property
    def username(self) -> str:
        """Username"""
        return self._beacon.username

    @property
    def uid(self) -> str:
        """User ID"""
        return self._beacon.uid

    @property
    def gid(self) -> str:
        """Group ID"""
        return self._beacon.gid

    @property
    def os(self) -> str:
        """Operating system"""
        return self._beacon.os

    @property
    def arch(self) -> str:
        """Architecture"""
        return self._beacon.arch

    @property
    def transport(self) -> str:
        """Transport Method"""
        return self._beacon.transport

    @property
    def remote_address(self) -> str:
        """Remote address"""
        return self._beacon.remote_address

    @property
    def pid(self) -> int:
        """Process ID"""
        return self._beacon.pid

    @property
    def filename(self) -> str:
        """Beacon filename"""
        return self._beacon.filename

    @property
    def last_checkin(self) -> int:
        """Last check in time"""
        return self._beacon.last_checkin

    @property
    def active_c2(self) -> str:
        """Active C2"""
        return self._beacon.active_c2

    @property
    def version(self) -> str:
        """Version"""
        return self._beacon.version

    @property
    def reconnect_interval(self) -> int:
        """Reconnect interval"""
        return self._beacon.reconnect_interval

    def _request(self, model: _RequestT) -> _RequestT:
        """Attach this beacon's routing metadata to a command request.

        ``model`` is any Pydantic command model with a ``request`` field.
        """
        model.request = models.commonpb.Request(
            beacon_id=self._beacon.id,
            timeout=request_timeout_nanoseconds(self.timeout),
            async_=True,
        )
        return model

    async def _execute(
        self,
        rpc_name: str,
        request: RequestRoutedModel,
        result_type: type[_ResultT],
    ) -> _ResultT:
        """Queue a beacon command and await its decoded Pydantic result."""

        if self._closed:
            raise RuntimeError("beacon interaction is closed")
        await self._event_broker.start()
        if not isinstance(request, ProtobufModel):
            raise TypeError("interactive requests must be Pydantic models")
        task_response = await getattr(self._stub, rpc_name)(
            request, timeout=self.timeout
        )
        raise_for_command_error(
            task_response,
            operation=rpc_name,
            target_id=self.beacon_id,
        )
        response = getattr(task_response, "response", None)
        if not isinstance(response, models.commonpb.Response) or not response.task_id:
            raise RuntimeError("beacon command did not return a task ID")

        result = await self._event_broker.wait_for_result(
            response.task_id, result_type, self.timeout
        )
        return raise_for_command_error(
            result, operation=rpc_name, target_id=self.beacon_id
        )


class InteractiveBeacon(BaseBeacon, BaseInteractiveCommands):
    """Commands executed asynchronously against a beacon-mode implant.

    Shared command methods and their explicit Pydantic/base-type signatures are
    inherited from :class:`BaseInteractiveCommands`. :class:`BaseBeacon`
    supplies beacon-specific task dispatch and result decoding.
    """
