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
from contextlib import suppress
from typing import TypeVar

import grpc

from . import models
from ._protocols import RequestRoutedModel
from ._rpc import PydanticSliverRPCStub
from .interactive import BaseInteractiveCommands
from .models import ProtobufModel, _model_from_bytes

_RequestT = TypeVar("_RequestT", bound=RequestRoutedModel)
_ResultT = TypeVar("_ResultT", bound=ProtobufModel)


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
        self._beacon_tasks: dict[
            str, tuple[asyncio.Future[ProtobufModel], type[ProtobufModel]]
        ] = {}
        self._taskresult_ready = asyncio.Event()
        self._taskresult_error: Exception | None = None
        self._closed = False
        self._taskresult_watcher = asyncio.get_event_loop().create_task(
            self._taskresult_events()
        )

    async def close(self) -> None:
        """Stop watching for beacon task results and cancel pending commands."""

        if self._closed:
            return
        self._closed = True
        for task_future, _ in self._beacon_tasks.values():
            task_future.cancel()
        self._beacon_tasks.clear()

        if not self._taskresult_watcher.done():
            self._taskresult_watcher.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await self._taskresult_watcher

    async def _wait_for_taskresult_watcher(self) -> None:
        """Wait until the result stream is subscribed before queueing a task."""

        if self._closed:
            raise RuntimeError("beacon interaction is closed")
        await self._taskresult_ready.wait()
        if self._taskresult_watcher.done():
            raise RuntimeError("beacon task-result watcher is not running") from (
                self._taskresult_error
            )

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
            timeout=self.timeout - 1,
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

        await self._wait_for_taskresult_watcher()
        if not isinstance(request, ProtobufModel):
            raise TypeError("interactive requests must be Pydantic models")
        task_response = await getattr(self._stub, rpc_name)(
            request, timeout=self.timeout
        )
        response = getattr(task_response, "response", None)
        if not isinstance(response, models.commonpb.Response) or not response.task_id:
            raise RuntimeError("beacon command did not return a task ID")

        task_future: asyncio.Future[ProtobufModel] = (
            asyncio.get_running_loop().create_future()
        )
        self._beacon_tasks[response.task_id] = (task_future, result_type)
        result = await task_future
        if not isinstance(result, result_type):
            raise TypeError(
                f"{rpc_name} returned {type(result).__name__}, "
                f"expected {result_type.__name__}"
            )
        return result

    async def _taskresult_events(self) -> None:
        """
        Monitor task events for results, resolve futures for any results
        we get back.
        """
        try:
            events = self._stub.Events(models.commonpb.Empty())
            self._taskresult_ready.set()
            async for event in events:
                if event.event_type != "beacon-taskresult":
                    continue
                task_id: str | None = None
                task_future: asyncio.Future[ProtobufModel] | None = None
                try:
                    beacon_task = _model_from_bytes(
                        models.clientpb.BeaconTask, event.data
                    )
                    task_id = beacon_task.id
                    if task_id not in self._beacon_tasks:
                        continue
                    task_content = await self._stub.GetBeaconTaskContent(
                        models.clientpb.BeaconTask(id=task_id)
                    )
                    task_future, model_type = self._beacon_tasks[task_id]
                    result = _model_from_bytes(model_type, task_content.response)
                    self._beacon_tasks.pop(task_id, None)
                    if not task_future.done():
                        task_future.set_result(result)
                except Exception as err:
                    if task_id is not None:
                        pending = self._beacon_tasks.pop(task_id, None)
                        if task_future is None and pending is not None:
                            task_future = pending[0]
                    if task_future is not None and not task_future.done():
                        task_future.set_exception(err)
                    self._log.exception(err)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            self._taskresult_error = err
            self._log.exception(err)
        finally:
            self._taskresult_ready.set()
            if not self._closed:
                stopped = RuntimeError("beacon task-result watcher stopped")
                for task_future, _ in self._beacon_tasks.values():
                    if not task_future.done():
                        task_future.set_exception(stopped)
                self._beacon_tasks.clear()


class InteractiveBeacon(BaseBeacon, BaseInteractiveCommands):
    """Commands executed asynchronously against a beacon-mode implant.

    Shared command methods and their explicit Pydantic/base-type signatures are
    inherited from :class:`BaseInteractiveCommands`. :class:`BaseBeacon`
    supplies beacon-specific task dispatch and result decoding.
    """
