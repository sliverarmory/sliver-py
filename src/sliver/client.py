"""
Sliver Implant Framework
Copyright (C) 2021  Bishop Fox

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
import os
from collections.abc import AsyncGenerator, Collection
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import timedelta

import grpc

from . import models
from ._duration import duration_nanoseconds, request_timeout_nanoseconds
from ._rpc import PydanticSliverRPCStub
from .beacon import InteractiveBeacon, _ClientEventBroker
from .config import OperatorConfig, SliverClientConfig
from .domain import GeneratedImplant, ImplantSpec, Inventory
from .enums import EventType
from .errors import (
    CleanupError,
    NotConnectedError,
    ResourceNotFoundError,
    SliverTimeoutError,
)
from .session import InteractiveSession

KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TIMEOUT = 60


def _normalize_event_types(
    event_types: EventType | str | Collection[EventType | str] | None,
) -> list[str] | None:
    if event_types is None:
        return None
    if isinstance(event_types, str):
        return [str(event_types)]
    return [str(event_type) for event_type in event_types]


def _duration_nanoseconds(value: timedelta | int, *, name: str) -> int:
    """Compatibility wrapper for the shared Sliver-duration converter."""

    return duration_nanoseconds(value, name=name)


class BaseClient:
    # 2GB triggers an overflow error in the gRPC library so we do 2GB-1
    MAX_MESSAGE_LENGTH = (2 * GB) - 1

    KEEP_ALIVE_TIMEOUT = 10000
    CERT_COMMON_NAME = "multiplayer"

    def __init__(self, config: SliverClientConfig) -> None:
        if not isinstance(config, SliverClientConfig):
            raise TypeError("config must be a SliverClientConfig Pydantic model")
        self.config = config
        self._channel: grpc.aio.Channel | None = None
        self._stub: PydanticSliverRPCStub | None = None
        self._event_broker: _ClientEventBroker | None = None
        self._lifecycle_lock = asyncio.Lock()
        self._log = logging.getLogger(self.__class__.__name__)

    def is_connected(self) -> bool:
        return self._channel is not None

    async def __aenter__(self) -> BaseClient:
        """Connect the client and return it as an owned async resource."""

        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Close the client regardless of how its context exits."""

        await self.close()

    async def connect(self, timeout: int = TIMEOUT) -> models.clientpb.Version:
        """Establish a connection to the Sliver server."""

        raise NotImplementedError

    async def close(self) -> None:
        """Close the active gRPC channel.

        Calling ``close`` more than once is safe. A closed client may be
        connected again with :meth:`SliverClient.connect`.
        """

        async with self._lifecycle_lock:
            await self._close_unlocked()

    async def _close_unlocked(self) -> None:
        """Close owned resources while the lifecycle lock is held."""

        broker = self._event_broker
        self._event_broker = None
        if broker is not None:
            await broker.close()

        channel = self._channel
        self._channel = None
        self._stub = None
        if channel is not None:
            await channel.close()

    async def aclose(self) -> None:
        """Alias for :meth:`close` following asynchronous resource conventions."""

        await self.close()

    @property
    def target(self) -> str:
        return f"{self.config.lhost}:{self.config.lport}"

    @property
    def credentials(self) -> grpc.ChannelCredentials:
        return grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(
                root_certificates=self.config.ca_certificate.encode(),
                private_key=self.config.private_key.encode(),
                certificate_chain=self.config.certificate.encode(),
            ),
            grpc.access_token_call_credentials(
                access_token=self.config.token,
            ),
        )

    @property
    def options(self) -> list[tuple[str, int | str]]:
        return [
            ("grpc.keepalive_timeout_ms", self.KEEP_ALIVE_TIMEOUT),
            ("grpc.ssl_target_name_override", self.CERT_COMMON_NAME),
            ("grpc.max_send_message_length", self.MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", self.MAX_MESSAGE_LENGTH),
        ]

    @property
    def rpc(self) -> PydanticSliverRPCStub:
        """Typed Pydantic access to every Sliver RPC.

        Requests accept descriptor-generated Pydantic models and responses are
        converted back to Pydantic models. The stub is available only while the
        client is connected.
        """
        if self._stub is None:
            raise NotConnectedError()
        return self._stub

    @property
    def pydantic_stub(self) -> PydanticSliverRPCStub:
        """Compatibility alias for :attr:`rpc`."""

        return self.rpc


class SliverClient(BaseClient):
    """Asyncio client implementation"""

    beacon_event_types = frozenset({EventType.BEACON_REGISTERED})
    session_event_types = frozenset(
        {EventType.SESSION_CONNECTED, EventType.SESSION_DISCONNECTED}
    )
    job_event_types = frozenset({EventType.JOB_STARTED, EventType.JOB_STOPPED})
    canary_event_types = frozenset({EventType.CANARY})

    @classmethod
    def from_config_file(
        cls,
        filepath: os.PathLike[str] | str | None = None,
    ) -> SliverClient:
        """Construct a client from an explicit, environment, or default config."""

        return cls(SliverClientConfig.from_file(filepath))

    async def __aenter__(self) -> SliverClient:
        """Connect and preserve the concrete client type in async contexts."""

        await self.connect()
        return self

    async def connect(self, timeout: int = TIMEOUT) -> models.clientpb.Version:
        """Establish a connection to the Sliver server

        :return: Pydantic model containing the server's version information
        :rtype: models.clientpb.Version
        """
        async with self._lifecycle_lock:
            if self.is_connected():
                try:
                    return await self.version(timeout=timeout)
                except BaseException:
                    await self._close_unlocked()
                    raise

            self._channel = grpc.aio.secure_channel(
                target=self.target,
                credentials=self.credentials,
                options=self.options,
            )
            self._stub = PydanticSliverRPCStub(self._channel)
            self._event_broker = _ClientEventBroker(self._stub)
            try:
                return await self.version(timeout=timeout)
            except BaseException:
                await self._close_unlocked()
                raise

    async def interact_session(
        self, session_id: str, timeout: int = TIMEOUT
    ) -> InteractiveSession | None:
        """Interact with a session, returns an :class:`InteractiveSession`

        :param session_id: Session ID
        :type session_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :return: An interactive session
        :rtype: Optional[InteractiveSession]
        """
        session = await self.session_by_id(session_id, timeout)
        if session:
            if self._channel is None:
                raise NotConnectedError()
            return InteractiveSession(session, self._channel, timeout)

    async def interact_beacon(
        self, beacon_id: str, timeout: int = TIMEOUT
    ) -> InteractiveBeacon | None:
        """Interact with a beacon, returns an :class:`InteractiveBeacon`

        :param beacon_id: Beacon ID
        :type beacon_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :return: An interactive beacon
        :rtype: InteractiveBeacon | None
        """
        beacon = await self.beacon_by_id(beacon_id, timeout)
        if beacon:
            if self._channel is None:
                raise NotConnectedError()
            interactive = InteractiveBeacon(beacon, self._channel, timeout)
            if self._event_broker is None:
                self._event_broker = _ClientEventBroker(self.pydantic_stub)
            interactive._attach_event_broker(self._event_broker)
            return interactive

    async def use_session(
        self, session_id: str, timeout: int = TIMEOUT
    ) -> InteractiveSession:
        """Select a session for interaction, matching ``use sessions``."""

        interaction = await self.interact_session(session_id, timeout=timeout)
        if interaction is None:
            raise ResourceNotFoundError("session", session_id)
        return interaction

    async def use_beacon(
        self, beacon_id: str, timeout: int = TIMEOUT
    ) -> InteractiveBeacon:
        """Select a beacon for interaction, matching ``use beacons``."""

        interaction = await self.interact_beacon(beacon_id, timeout=timeout)
        if interaction is None:
            raise ResourceNotFoundError("beacon", beacon_id)
        return interaction

    async def use(
        self,
        target: models.clientpb.Session | models.clientpb.Beacon,
        timeout: int = TIMEOUT,
    ) -> InteractiveSession | InteractiveBeacon:
        """Select a detached session or beacon model for interaction."""

        if isinstance(target, models.clientpb.Session):
            return await self.use_session(target.id, timeout=timeout)
        if isinstance(target, models.clientpb.Beacon):
            return await self.use_beacon(target.id, timeout=timeout)
        raise TypeError("target must be a Pydantic Session or Beacon model")

    async def session_by_id(
        self, session_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Session | None:
        """Get the session information from a session ID

        :param session_id: Session ID
        :type session_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :return: Matching Pydantic session model, if present
        :rtype: Optional[models.clientpb.Session]
        """
        sessions = await self.sessions(timeout)
        for session in sessions:
            if session.id == session_id:
                return session

    async def beacon_by_id(
        self, beacon_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Beacon | None:
        """Get the beacon information from a beacon ID

        :param beacon_id: Beacon ID
        :type beacon_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :return: Matching Pydantic beacon model, if present
        :rtype: Optional[models.clientpb.Beacon]
        """
        beacons = await self.beacons(timeout)
        for beacon in beacons:
            if beacon.id == beacon_id:
                return beacon

    async def find_session(
        self, session_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Session | None:
        """Return a session by ID, or ``None`` when it is absent."""

        return await self.session_by_id(session_id, timeout=timeout)

    async def get_session(
        self, session_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Session:
        """Return a session by ID or raise :class:`ResourceNotFoundError`."""

        session = await self.find_session(session_id, timeout=timeout)
        if session is None:
            raise ResourceNotFoundError("session", session_id)
        return session

    async def find_beacon(
        self, beacon_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Beacon | None:
        """Return a beacon by ID, or ``None`` when it is absent."""

        return await self.beacon_by_id(beacon_id, timeout=timeout)

    async def get_beacon(
        self, beacon_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Beacon:
        """Return a beacon by ID or raise :class:`ResourceNotFoundError`."""

        beacon = await self.find_beacon(beacon_id, timeout=timeout)
        if beacon is None:
            raise ResourceNotFoundError("beacon", beacon_id)
        return beacon

    async def events(
        self,
        event_types: EventType | str | Collection[EventType | str] | None = None,
    ) -> AsyncGenerator[models.clientpb.Event, None]:
        """Iterate all events or only the selected typed event names.

        :yield: A stream of events
        :rtype: models.clientpb.Event
        """
        if self._event_broker is None:
            self._event_broker = _ClientEventBroker(self.rpc)
        filters = _normalize_event_types(event_types)
        async for event in self._event_broker.subscribe(filters):
            yield event

    async def on(
        self, event_types: EventType | str | Collection[EventType | str]
    ) -> AsyncGenerator[models.clientpb.Event, None]:
        """Compatibility alias for filtered :meth:`events` iteration.

        :param event_types: An event type or list of event types
        :type event_types: Union[str, List[str]]
        :yield: A stream of events of the given type(s)
        :rtype: models.clientpb.Event
        """
        async for event in self.events(event_types):
            yield event

    async def collect_events(
        self,
        *event_types: EventType | str,
        limit: int = 1,
        timeout: float | None = None,
    ) -> list[models.clientpb.Event]:
        """Collect a bounded set of events and close the subscription."""

        if limit < 1:
            raise ValueError("limit must be at least 1")

        async def collect() -> list[models.clientpb.Event]:
            collected: list[models.clientpb.Event] = []
            filters: Collection[EventType | str] | None = event_types or None
            stream = self.events(filters)
            try:
                async for event in stream:
                    collected.append(event)
                    if len(collected) == limit:
                        break
            finally:
                await stream.aclose()
            return collected

        if timeout is None:
            return await collect()
        try:
            return await asyncio.wait_for(collect(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise SliverTimeoutError("collect events", timeout) from exc

    async def version(self, timeout: int = TIMEOUT) -> models.clientpb.Version:
        """Get server version information

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic server-version model
        :rtype: models.clientpb.Version
        """
        return await self.pydantic_stub.GetVersion(
            models.commonpb.Empty(), timeout=timeout
        )

    async def operators(self, timeout: int = TIMEOUT) -> list[models.clientpb.Operator]:
        """Get a list of operators and their online status

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic operator models
        :rtype: list[models.clientpb.Operator]
        """
        operators = await self.pydantic_stub.GetOperators(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(operators.operators)

    async def inventory(self, timeout: int = TIMEOUT) -> Inventory:
        """Collect the common Sliver server resources concurrently."""

        version, sessions, beacons, jobs, operators = await asyncio.gather(
            self.version(timeout=timeout),
            self.sessions(timeout=timeout),
            self.beacons(timeout=timeout),
            self.jobs(timeout=timeout),
            self.operators(timeout=timeout),
        )
        return Inventory(
            version=version,
            sessions=sessions,
            beacons=beacons,
            jobs=jobs,
            operators=operators,
        )

    async def sessions(self, timeout: int = TIMEOUT) -> list[models.clientpb.Session]:
        """Get a list of active sessions

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic session models
        :rtype: list[models.clientpb.Session]
        """
        sessions: models.clientpb.Sessions = await self.pydantic_stub.GetSessions(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(sessions.sessions)

    async def rename_session(
        self, session_id: str, name: str, timeout: int = TIMEOUT
    ) -> None:
        """Rename a session

        :param session_id: Session ID to update
        :type session_id: str
        :param name: Rename session to this value
        :type name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: None
        :rtype: None
        """
        rename_req = models.clientpb.RenameReq(session_id=session_id, name=name)
        await self.pydantic_stub.Rename(rename_req, timeout=timeout)

    async def kill_session(
        self,
        session_id: str,
        force: bool = False,
        timeout: int = TIMEOUT,
    ) -> None:
        """Kill a session

        :param session_id: Session ID to kill
        :type session_id: str
        :param force: Force kill the session, defaults to False
        :type force: bool, optional
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        request = models.commonpb.Request(
            session_id=session_id,
            timeout=request_timeout_nanoseconds(timeout),
        )
        kill_req = models.sliverpb.KillReq(force=force, request=request)
        await self.pydantic_stub.Kill(kill_req, timeout=timeout)

    async def beacons(self, timeout: int = TIMEOUT) -> list[models.clientpb.Beacon]:
        """Get a list of active beacons

        :param timeout: gRPC timeout, defaults to 60 seconds
        :rtype: list[models.clientpb.Beacon]
        """
        beacons: models.clientpb.Beacons = await self.pydantic_stub.GetBeacons(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(beacons.beacons)

    async def rename_beacon(
        self, beacon_id: str, name: str, timeout: int = TIMEOUT
    ) -> None:
        """Rename a beacon

        :param beacon_id: Beacon ID to update
        :type beacon_id: str
        :param name: Rename beacon to this value
        :type name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: None
        :rtype: None
        """
        rename_req = models.clientpb.RenameReq(beacon_id=beacon_id, name=name)
        await self.pydantic_stub.Rename(rename_req, timeout=timeout)

    async def kill_beacon(
        self,
        beacon_id: str,
        force: bool = False,
        timeout: int = TIMEOUT,
    ) -> None:
        """Queue a command that terminates a beacon implant process.

        :param beacon_id: Beacon ID to kill
        :type beacon_id: str
        :param force: Force kill the beacon, defaults to False
        :type force: bool, optional
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        request = models.commonpb.Request(
            beacon_id=beacon_id,
            timeout=request_timeout_nanoseconds(timeout),
        )
        kill_req = models.sliverpb.KillReq(force=force, request=request)
        await self.pydantic_stub.Kill(kill_req, timeout=timeout)

    async def rm_beacon(self, beacon_id: str, timeout: int = TIMEOUT) -> None:
        """Remove a beacon record from the server without killing its process.

        :param beacon_id: Beacon ID to remove
        :type beacon_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        beacon_rm = models.clientpb.Beacon(id=beacon_id)
        await self.pydantic_stub.RmBeacon(beacon_rm, timeout=timeout)

    async def beacons_rm(self, beacon_id: str, timeout: int = TIMEOUT) -> None:
        """Remove a beacon record, matching Sliver's ``beacons rm`` path."""

        await self.rm_beacon(beacon_id, timeout=timeout)

    async def beacon_tasks(
        self, beacon_id: str, timeout: int = TIMEOUT
    ) -> list[models.clientpb.BeaconTask]:
        """Get a list of tasks for a beacon

        :param beacon_id: Beacon ID to get tasks for
        :type beacon_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic beacon-task models
        :rtype: list[models.clientpb.BeaconTask]
        """
        beacon = models.clientpb.Beacon(id=beacon_id)
        tasks = await self.pydantic_stub.GetBeaconTasks(beacon, timeout=timeout)
        return list(tasks.tasks)

    async def beacon_task_content(
        self, task_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.BeaconTask:
        """Get the stored request and response content for a beacon task

        :param task_id: Task ID to get content for
        :type task_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic beacon-task model
        :rtype: models.clientpb.BeaconTask
        """
        task_req = models.clientpb.BeaconTask(id=task_id)
        task = await self.pydantic_stub.GetBeaconTaskContent(task_req, timeout=timeout)
        return task

    async def tasks(
        self, beacon_id: str, timeout: int = TIMEOUT
    ) -> list[models.clientpb.BeaconTask]:
        """List a beacon's tasks, matching Sliver's ``tasks`` command."""

        return await self.beacon_tasks(beacon_id, timeout=timeout)

    async def tasks_fetch(
        self, task_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.BeaconTask:
        """Fetch stored task content, matching Sliver's ``tasks fetch``."""

        return await self.fetch_task(task_id, timeout=timeout)

    async def fetch_task(
        self, task_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.BeaconTask:
        """Fetch stored task content, matching ``tasks fetch``."""

        return await self.beacon_task_content(task_id, timeout=timeout)

    async def cancel_task(
        self, task_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.BeaconTask:
        """Cancel a pending beacon task, matching ``tasks cancel``."""

        return await self.rpc.cancel_beacon_task(
            models.clientpb.BeaconTask(id=task_id),
            timeout=timeout,
        )

    async def tasks_cancel(
        self, task_id: str, timeout: int = TIMEOUT
    ) -> models.clientpb.BeaconTask:
        """Cancel a pending task, matching Sliver's ``tasks cancel``."""

        return await self.cancel_task(task_id, timeout=timeout)

    async def jobs(self, timeout: int = TIMEOUT) -> list[models.clientpb.Job]:
        """Get a list of active jobs

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic job models
        :rtype: list[models.clientpb.Job]
        """
        jobs: models.clientpb.Jobs = await self.pydantic_stub.GetJobs(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(jobs.active)

    async def job_by_id(
        self, job_id: int, timeout: int = TIMEOUT
    ) -> models.clientpb.Job | None:
        """Get job by id

        :param job_id: Numeric job ID
        :type job_id: int
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Matching Pydantic job model, if present
        :rtype: Optional[models.clientpb.Job]
        """
        for job in await self.jobs(timeout=timeout):
            if job.id == job_id:
                return job

    async def job_by_port(
        self, job_port: int, timeout: int = TIMEOUT
    ) -> models.clientpb.Job | None:
        """Get job by port

        :param job_port: Listener port to match
        :type job_port: int
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Matching Pydantic job model, if present
        :rtype: Optional[models.clientpb.Job]
        """
        for job in await self.jobs(timeout=timeout):
            if job.port == job_port:
                return job

    async def find_job(
        self, job_id: int, timeout: int = TIMEOUT
    ) -> models.clientpb.Job | None:
        """Return a job by ID, or ``None`` when it is absent."""

        return await self.job_by_id(job_id, timeout=timeout)

    async def get_job(
        self, job_id: int, timeout: int = TIMEOUT
    ) -> models.clientpb.Job:
        """Return a job by ID or raise :class:`ResourceNotFoundError`."""

        job = await self.find_job(job_id, timeout=timeout)
        if job is None:
            raise ResourceNotFoundError("job", job_id)
        return job

    async def kill_job(
        self, job_id: int, timeout: int = TIMEOUT
    ) -> models.clientpb.KillJob:
        """Kill a job

        :param job_id: Numeric job ID to kill
        :type job_id: int
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic job-termination model
        :rtype: models.clientpb.KillJob
        """
        kill_req = models.clientpb.KillJobReq(id=job_id)
        return await self.pydantic_stub.KillJob(kill_req, timeout=timeout)

    async def mtls(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8888,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start an mTLS listener, matching Sliver's ``mtls`` command."""

        return await self.start_mtls_listener(host=host, port=port, timeout=timeout)

    async def wg(
        self,
        *,
        tun_ip: str | None = None,
        host: str = "0.0.0.0",
        port: int = 53,
        n_port: int = 8888,
        key_port: int = 1337,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start a WireGuard listener, matching Sliver's ``wg`` command."""

        return await self.start_wg_listener(
            tun_ip=tun_ip,
            host=host,
            port=port,
            n_port=n_port,
            key_port=key_port,
            timeout=timeout,
        )

    async def dns(
        self,
        domains: list[str],
        *,
        host: str = "0.0.0.0",
        port: int = 53,
        canaries: bool = True,
        enforce_otp: bool = True,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start a DNS listener, matching Sliver's ``dns`` command."""

        return await self.start_dns_listener(
            domains,
            host=host,
            port=port,
            canaries=canaries,
            enforce_otp=enforce_otp,
            timeout=timeout,
        )

    async def http(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 80,
        website: str = "",
        domain: str = "",
        enforce_otp: bool = True,
        long_poll_timeout: timedelta | int = timedelta(seconds=1),
        long_poll_jitter: timedelta | int = timedelta(seconds=2),
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start an HTTP listener, matching Sliver's ``http`` command."""

        return await self.start_http_listener(
            host=host,
            port=port,
            website=website,
            domain=domain,
            enforce_otp=enforce_otp,
            long_poll_timeout=long_poll_timeout,
            long_poll_jitter=long_poll_jitter,
            timeout=timeout,
        )

    async def https(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 443,
        website: str = "",
        domain: str = "",
        cert: bytes = b"",
        key: bytes = b"",
        acme: bool = False,
        enforce_otp: bool = True,
        randomize_jarm: bool = True,
        long_poll_timeout: timedelta | int = timedelta(seconds=1),
        long_poll_jitter: timedelta | int = timedelta(seconds=2),
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start an HTTPS listener, matching Sliver's ``https`` command."""

        return await self.start_https_listener(
            host=host,
            port=port,
            website=website,
            domain=domain,
            cert=cert,
            key=key,
            acme=acme,
            enforce_otp=enforce_otp,
            randomize_jarm=randomize_jarm,
            long_poll_timeout=long_poll_timeout,
            long_poll_jitter=long_poll_jitter,
            timeout=timeout,
        )

    def temporary_mtls(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8888,
        timeout: int = TIMEOUT,
    ) -> AbstractAsyncContextManager[models.clientpb.ListenerJob]:
        """Own an mTLS listener for the duration of an async context."""

        @asynccontextmanager
        async def manage() -> AsyncGenerator[models.clientpb.ListenerJob, None]:
            listener = await self.mtls(host=host, port=port, timeout=timeout)
            try:
                yield listener
            finally:
                try:
                    stopped = await self.kill_job(listener.job_id, timeout=timeout)
                    if not stopped.success or stopped.id != listener.job_id:
                        raise RuntimeError(
                            f"Sliver did not stop listener job {listener.job_id}"
                        )
                except Exception as failure:
                    raise CleanupError(
                        "temporary mTLS listener", [failure]
                    ) from failure

        return manage()

    async def start_mtls_listener(
        self,
        host: str = "0.0.0.0",
        port: int = 8888,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start a mutual TLS (mTLS) C2 listener

        :param host: Host interface to bind; an empty string binds all interfaces
        :type host: str
        :param port: TCP port number to start listener on
        :type port: int
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic listener-job model
        :rtype: models.clientpb.ListenerJob
        """
        mtls_req = models.clientpb.MTLSListenerReq(host=host, port=port)
        return await self.pydantic_stub.StartMTLSListener(mtls_req, timeout=timeout)

    async def start_wg_listener(
        self,
        tun_ip: str | None = None,
        host: str = "0.0.0.0",
        port: int = 53,
        n_port: int = 8888,
        key_port: int = 1337,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start a WireGuard (wg) C2 listener

        :param tun_ip: Virtual TUN IP listen address
        :type tun_ip: str
        :type host: str
        :param port: TCP port number to start listener on
        :param port: UDP port to start listener on
        :type port: int
        :param n_port: Virtual TUN port number
        :type n_port: int
        :param key_port: Virtual TUN port number for key exchanges
        :type key_port: int
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic listener-job model
        :rtype: models.clientpb.ListenerJob
        """
        if tun_ip is None:
            uniq_ip = await self.generate_wg_ip(timeout=timeout)
            tun_ip = uniq_ip.ip

        wg_req = models.clientpb.WGListenerReq(
            tun_ip=tun_ip,
            host=host,
            port=port,
            n_port=n_port,
            key_port=key_port,
        )
        return await self.pydantic_stub.StartWGListener(wg_req, timeout=timeout)

    async def start_dns_listener(
        self,
        domains: list[str],
        host: str = "0.0.0.0",
        port: int = 53,
        canaries: bool = True,
        enforce_otp: bool = True,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start a DNS C2 listener

        :param domains: C2 domains to listen for
        :type domains: List[str]
        :param canaries: Enable/disable DNS canaries
        :type canaries: bool
        :param host: Host interface to bind; an empty string binds all interfaces
        :type host: str
        :param port: TCP port number to start listener on
        :type port: int
        :param enforce_otp: Enforce OTP auth for DNS C2, defaults to True
        :type enforce_otp: bool, optional
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic listener-job model
        :rtype: models.clientpb.ListenerJob
        """
        if not domains:
            raise ValueError("domains must contain at least one DNS name")
        normalized_domains: list[str] = []
        for domain in domains:
            normalized = domain.strip()
            if not normalized:
                raise ValueError("domains cannot contain an empty DNS name")
            normalized_domains.append(
                normalized if normalized.endswith(".") else f"{normalized}."
            )

        dns_req = models.clientpb.DNSListenerReq(
            domains=normalized_domains,
            canaries=canaries,
            host=host,
            port=port,
            enforce_otp=enforce_otp,
        )
        return await self.pydantic_stub.StartDNSListener(dns_req, timeout=timeout)

    async def start_http_listener(
        self,
        host: str = "0.0.0.0",
        port: int = 80,
        website: str = "",
        domain: str = "",
        enforce_otp: bool = True,
        long_poll_timeout: timedelta | int = timedelta(seconds=1),
        long_poll_jitter: timedelta | int = timedelta(seconds=2),
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start an HTTP C2 listener


        :param host: Host interface to bind; an empty string binds all interfaces
        :type host: str
        :param port: TCP port number to start listener on
        :type port: int
        :param website: Name of the "website" to host on listener
        :type website: str
        :param domain: Domain name for HTTP server (one domain per listener)
        :type domain: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Listener job metadata
        :rtype: models.clientpb.ListenerJob
        """
        http_req = models.clientpb.HTTPListenerReq(
            domain=domain,
            host=host,
            port=port,
            secure=False,
            website=website,
            enforce_otp=enforce_otp,
            long_poll_timeout=_duration_nanoseconds(
                long_poll_timeout, name="long_poll_timeout"
            ),
            long_poll_jitter=_duration_nanoseconds(
                long_poll_jitter, name="long_poll_jitter"
            ),
        )
        return await self.pydantic_stub.StartHTTPListener(http_req, timeout=timeout)

    async def start_https_listener(
        self,
        host: str = "0.0.0.0",
        port: int = 443,
        website: str = "",
        domain: str = "",
        cert: bytes = b"",
        key: bytes = b"",
        acme: bool = False,
        enforce_otp: bool = True,
        randomize_jarm: bool = True,
        long_poll_timeout: timedelta | int = timedelta(seconds=1),
        long_poll_jitter: timedelta | int = timedelta(seconds=2),
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ListenerJob:
        """Start an HTTPS C2 listener

        :param domain: Domain name for HTTPS server (one domain per listener)
        :type domain: str
        :param host: Host interface to bind; an empty string binds all interfaces
        :type host: str
        :param port: TCP port number to start listener on
        :type port: int
        :param website: Name of the "website" to host on listener
        :type website: str
        :param cert: TLS certificate (leave blank to generate self-signed certificate)
        :type cert: bytes
        :param key: TLS private key (leave blank to generate self-signed certificate)
        :type key: bytes
        :param acme: Automatically provision a TLS certificate using ACME
        :type acme: bool
        :param enforce_otp: Enforce OTP auth for HTTPS C2, defaults to True
        :type enforce_otp: bool, optional
        :param randomize_jarm: Randomize JARM fingerprint for HTTPS C2, defaults to True
        :type randomize_jarm: bool, optional
        :param long_poll_timeout: Long poll timeout for HTTPS C2, defaults to 1
        :type long_poll_timeout: int, optional
        :param long_poll_jitter: Long poll jitter for HTTPS C2, defaults to 2
        :type long_poll_jitter: int, optional
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Listener job metadata
        :rtype: models.clientpb.ListenerJob
        """
        https_req = models.clientpb.HTTPListenerReq(
            domain=domain,
            host=host,
            port=port,
            secure=True,
            website=website,
            cert=cert,
            key=key,
            acme=acme,
            enforce_otp=enforce_otp,
            long_poll_timeout=_duration_nanoseconds(
                long_poll_timeout, name="long_poll_timeout"
            ),
            long_poll_jitter=_duration_nanoseconds(
                long_poll_jitter, name="long_poll_jitter"
            ),
            randomize_jarm=randomize_jarm,
        )
        return await self.pydantic_stub.StartHTTPSListener(https_req, timeout=timeout)

    async def start_tcp_stager_listener(
        self,
        host: str,
        port: int,
        data: bytes,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.StagerListener:
        """Start a TCP stager listener

        :param host: Host interface to bind; an empty string binds all interfaces
        :type host: str
        :param port: TCP port number to start listener on
        :type port: int
        :param data: Binary data of stage to host on listener
        :type data: bytes
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic stager-listener model
        :rtype: models.clientpb.StagerListener

        The current Sliver schema only exposes a TCP stager-listener RPC.
        The HTTP, HTTPS, and Metasploit staging RPCs found in older Sliver
        releases no longer exist, so this client does not emulate them.
        """
        stage_req = models.clientpb.StagerListenerReq(
            protocol=models.clientpb.StageProtocol.TCP,
            host=host,
            port=port,
            data=data,
        )
        return await self.pydantic_stub.StartTCPStagerListener(
            stage_req, timeout=timeout
        )

    async def stage_listener(
        self,
        host: str,
        port: int,
        data: bytes,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.StagerListener:
        """Start a TCP stage listener, matching Sliver's ``stage-listener``."""

        return await self.start_tcp_stager_listener(
            host,
            port,
            data,
            timeout=timeout,
        )

    async def generate_implant(
        self, config: models.clientpb.ImplantConfig, timeout: int = 360
    ) -> models.clientpb.Generate:
        """Generate a new implant using a given configuration

        :param config: Pydantic implant-configuration model
        :type config: models.clientpb.ImplantConfig
        :param timeout: gRPC timeout, defaults to 360
        :type timeout: int, optional
        :return: Pydantic model containing the generated implant
        :rtype: models.clientpb.Generate
        """
        req = models.clientpb.GenerateReq(config=config)
        return await self.pydantic_stub.Generate(req, timeout=timeout)

    async def generate(
        self,
        spec: ImplantSpec,
        *,
        name: str = "",
        timeout: int = 360,
        base_config: models.clientpb.ImplantConfig | None = None,
    ) -> GeneratedImplant:
        """Generate an implant from a concise, validated specification."""

        if not isinstance(spec, ImplantSpec):
            raise TypeError("spec must be an ImplantSpec Pydantic model")
        generated = await self.rpc.generate(
            spec.to_generate_request(name=name, base=base_config),
            timeout=timeout,
        )
        return GeneratedImplant.from_generate(generated)

    async def generate_stage(
        self,
        request: models.clientpb.GenerateStageReq,
        timeout: int = 360,
    ) -> models.clientpb.Generate:
        """Generate a stage from a saved implant profile.

        ``request`` is the Pydantic model generated from Sliver's current
        ``GenerateStageReq`` descriptor. It supports the profile and optional
        implant name, AES or RC4 encryption settings, size prefixing, and
        compression settings defined by the server schema. Set ``compress``
        for the current server; the descriptor's legacy ``compress_f`` field
        is retained upstream but is not consumed by the stage generator.

        :param request: Stage-generation settings
        :type request: models.clientpb.GenerateStageReq
        :param timeout: gRPC timeout, defaults to 360 seconds
        :type timeout: int, optional
        :return: Pydantic model containing the generated stage
        :rtype: models.clientpb.Generate
        """
        return await self.pydantic_stub.GenerateStage(request, timeout=timeout)

    async def profiles_stage(
        self,
        request: models.clientpb.GenerateStageReq,
        timeout: int = 360,
    ) -> GeneratedImplant:
        """Generate a stage, matching Sliver's ``profiles stage`` command."""

        generated = await self.generate_stage(request, timeout=timeout)
        return GeneratedImplant.from_generate(generated)

    async def regenerate_implant(
        self, implant_name: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Generate:
        """Regenerate an implant binary given the implants "name"

        :param implant_name: The name of the implant to regenerate
        :type implant_name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic model containing the regenerated implant
        :rtype: models.clientpb.Generate
        """
        regenerate = models.clientpb.RegenerateReq(implant_name=implant_name)
        return await self.pydantic_stub.Regenerate(regenerate, timeout=timeout)

    async def regenerate(
        self, implant_name: str, timeout: int = TIMEOUT
    ) -> GeneratedImplant:
        """Regenerate a stored implant, matching Sliver's ``regenerate`` command."""

        generated = await self.regenerate_implant(implant_name, timeout=timeout)
        return GeneratedImplant.from_generate(generated)

    async def implant_builds(
        self, timeout: int = TIMEOUT
    ) -> dict[str, models.clientpb.ImplantConfig]:
        """Get information about historical implant builds

        :return: Map from implant names to their configurations
        :rtype: dict[str, models.clientpb.ImplantConfig]
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        builds: models.clientpb.ImplantBuilds = await self.pydantic_stub.ImplantBuilds(
            models.commonpb.Empty(), timeout=timeout
        )
        return dict(builds.configs)

    async def implants(
        self, timeout: int = TIMEOUT
    ) -> dict[str, models.clientpb.ImplantConfig]:
        """List stored builds, matching Sliver's ``implants`` command."""

        return await self.implant_builds(timeout=timeout)

    async def delete_implant_build(
        self, implant_name: str, timeout: int = TIMEOUT
    ) -> None:
        """Delete a historical implant build from the server by name

        :param implant_name: The name of the implant build to delete
        :type implant_name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        delete = models.clientpb.DeleteReq(name=implant_name)
        await self.pydantic_stub.DeleteImplantBuild(delete, timeout=timeout)

    async def rm_implant(
        self, implant_name: str, timeout: int = TIMEOUT
    ) -> None:
        """Remove a stored build, matching Sliver's ``implants rm`` command."""

        await self.delete_implant_build(implant_name, timeout=timeout)

    async def implants_rm(
        self, implant_name: str, timeout: int = TIMEOUT
    ) -> None:
        """Remove a stored build, matching Sliver's ``implants rm`` path."""

        await self.rm_implant(implant_name, timeout=timeout)

    async def canaries(self, timeout: int = TIMEOUT) -> list[models.clientpb.DNSCanary]:
        """Get canaries generated during implant builds and their metadata.

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic DNS-canary models
        :rtype: list[models.clientpb.DNSCanary]
        """
        canaries = await self.pydantic_stub.Canaries(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(canaries.canaries)

    async def generate_wg_client_config(
        self, timeout: int = TIMEOUT
    ) -> models.clientpb.WGClientConfig:
        """Generate a new WireGuard client configuration files

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic WireGuard-client configuration model
        :rtype: models.clientpb.WGClientConfig
        """
        return await self.pydantic_stub.GenerateWGClientConfig(
            models.commonpb.Empty(), timeout=timeout
        )

    async def wg_config(
        self, timeout: int = TIMEOUT
    ) -> models.clientpb.WGClientConfig:
        """Generate a WireGuard client config, matching ``wg-config``."""

        return await self.generate_wg_client_config(timeout=timeout)

    async def generate_wg_ip(
        self, timeout: int = TIMEOUT
    ) -> models.clientpb.UniqueWGIP:
        """Generate a unique IP address for use with WireGuard

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic unique WireGuard IP model
        :rtype: models.clientpb.UniqueWGIP
        """
        return await self.pydantic_stub.GenerateUniqueIP(
            models.commonpb.Empty(), timeout=timeout
        )

    async def implant_profiles(
        self, timeout: int = TIMEOUT
    ) -> list[models.clientpb.ImplantProfile]:
        """Get a list of all implant configuration profiles on the server

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic implant-profile models
        :rtype: list[models.clientpb.ImplantProfile]
        """
        profiles = await self.pydantic_stub.ImplantProfiles(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(profiles.profiles)

    async def profiles(
        self, timeout: int = TIMEOUT
    ) -> list[models.clientpb.ImplantProfile]:
        """List implant profiles, matching Sliver's ``profiles`` command."""

        return await self.implant_profiles(timeout=timeout)

    async def profiles_generate(
        self,
        profile_name: str,
        *,
        name: str = "",
        timeout: int = 360,
    ) -> GeneratedImplant:
        """Generate an implant, matching Sliver's ``profiles generate`` command."""

        profile = next(
            (
                profile
                for profile in await self.profiles(timeout=timeout)
                if profile.name == profile_name
            ),
            None,
        )
        if profile is None:
            raise ResourceNotFoundError("implant profile", profile_name)
        if profile.config is None:
            raise ValueError(f"implant profile {profile_name!r} has no configuration")
        generated = await self.rpc.generate(
            models.clientpb.GenerateReq(
                config=profile.config.model_copy(deep=True),
                name=name,
            ),
            timeout=timeout,
        )
        return GeneratedImplant.from_generate(generated)

    async def delete_implant_profile(
        self, profile_name: str, timeout: int = TIMEOUT
    ) -> None:
        """Delete an implant configuration profile by name

        :param profile_name: Name of the profile to delete
        :type profile_name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        delete = models.clientpb.DeleteReq(name=profile_name)
        await self.pydantic_stub.DeleteImplantProfile(delete, timeout=timeout)

    async def rm_profile(
        self, profile_name: str, timeout: int = TIMEOUT
    ) -> None:
        """Remove an implant profile, matching ``profiles rm``."""

        await self.delete_implant_profile(profile_name, timeout=timeout)

    async def profiles_rm(
        self, profile_name: str, timeout: int = TIMEOUT
    ) -> None:
        """Remove a profile, matching Sliver's ``profiles rm`` path."""

        await self.rm_profile(profile_name, timeout=timeout)

    async def save_implant_profile(
        self,
        profile: models.clientpb.ImplantProfile,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ImplantProfile:
        """Save an implant configuration profile to the server

        :param profile: An implant configuration profile model
        :type profile: models.clientpb.ImplantProfile
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic implant-profile model
        :rtype: models.clientpb.ImplantProfile
        """
        return await self.pydantic_stub.SaveImplantProfile(profile, timeout=timeout)

    async def new_profile(
        self,
        profile: models.clientpb.ImplantProfile,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ImplantProfile:
        """Save an implant profile, matching ``profiles new``."""

        return await self.save_implant_profile(profile, timeout=timeout)

    async def profiles_new(
        self,
        profile: models.clientpb.ImplantProfile,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ImplantProfile:
        """Save a profile, matching Sliver's ``profiles new`` path."""

        return await self.new_profile(profile, timeout=timeout)

    async def shellcode(
        self,
        data: bytes,
        function_name: str,
        arguments: str = "",
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ShellcodeRDI:
        """Generate Donut shellcode

        :param data: The DLL file to wrap in a shellcode loader
        :type data: bytes
        :param function_name: Function to call on the DLL
        :type function_name: str
        :param arguments: Arguments to the function called
        :type arguments: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic Shellcode RDI result model
        :rtype: models.clientpb.ShellcodeRDI
        """
        shell_req = models.clientpb.ShellcodeRDIReq(
            data=data, function_name=function_name, arguments=arguments
        )
        return await self.pydantic_stub.ShellcodeRDI(shell_req, timeout=timeout)

    async def shellcode_rdi(
        self,
        data: bytes,
        function_name: str,
        *,
        arguments: str = "",
        timeout: int = TIMEOUT,
    ) -> models.clientpb.ShellcodeRDI:
        """Generate shellcode from a DLL without colliding with implant commands."""

        return await self.shellcode(
            data,
            function_name,
            arguments=arguments,
            timeout=timeout,
        )

    async def websites(self, timeout: int = TIMEOUT) -> list[models.clientpb.Website]:
        """Get a list of websites

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic website models
        :rtype: list[models.clientpb.Website]
        """
        websites = await self.pydantic_stub.Websites(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(websites.websites)

    async def website(
        self, name: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Website:
        """Compatibility spelling for :meth:`show_website`."""

        return await self.pydantic_stub.Website(
            models.clientpb.Website(name=name), timeout=timeout
        )

    async def show_website(
        self, name: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Website:
        """Show a website and its content, matching ``websites show``."""

        return await self.website(name, timeout=timeout)

    async def websites_show(
        self, name: str, timeout: int = TIMEOUT
    ) -> models.clientpb.Website:
        """Show a website, matching Sliver's ``websites show`` path."""

        return await self.show_website(name, timeout=timeout)

    async def update_website(
        self,
        website: models.clientpb.Website,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.Website:
        """Synchronize an existing website with a Pydantic website model.

        Sliver does not expose a whole-website update RPC. This helper uses the
        current content RPCs to remove paths absent from ``website.contents``
        and then upsert every desired path. The operations are sequential and
        are therefore not atomic on the server.

        Map keys are the canonical web paths. A content model may leave its
        own ``path`` empty, in which case the corresponding map key is used;
        a non-empty mismatched path is rejected. Content is always rebound to
        the fetched website ID so stale model IDs cannot update another site.

        :param website: Desired Pydantic website model
        :type website: models.clientpb.Website
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: The synchronized Pydantic website model from the server
        :rtype: models.clientpb.Website
        """
        if not isinstance(website, models.clientpb.Website):
            raise TypeError("website must be a models.clientpb.Website Pydantic model")
        if not website.name:
            raise ValueError("website.name must not be empty")

        current = await self.website(website.name, timeout=timeout)
        if website.id and current.id and website.id != current.id:
            raise ValueError(
                f"website ID {website.id!r} does not match the server's "
                f"ID {current.id!r} for {website.name!r}"
            )

        desired_contents: dict[str, models.clientpb.WebContent] = {}
        for path, content in website.contents.items():
            if content.path and content.path != path:
                raise ValueError(
                    f"website content path {content.path!r} does not match "
                    f"its map key {path!r}"
                )
            desired_contents[path] = content.model_copy(
                update={"path": path, "website_id": current.id}
            )

        removed_paths = sorted(set(current.contents) - set(desired_contents))
        if removed_paths:
            current = await self.pydantic_stub.WebsiteRemoveContent(
                models.clientpb.WebsiteRemoveContent(
                    name=website.name,
                    paths=removed_paths,
                ),
                timeout=timeout,
            )

        if not desired_contents:
            return current

        return await self.pydantic_stub.WebsiteUpdateContent(
            models.clientpb.WebsiteAddContent(
                name=website.name,
                contents=desired_contents,
            ),
            timeout=timeout,
        )

    async def remove_website(self, name: str, timeout: int = TIMEOUT) -> None:
        """Compatibility spelling for :meth:`rm_website`.

        :param name: The name of the website to remove
        :type name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        website = models.clientpb.Website(name=name)
        await self.pydantic_stub.WebsiteRemove(website, timeout=timeout)

    async def rm_website(self, name: str, timeout: int = TIMEOUT) -> None:
        """Remove a website and its content, matching ``websites rm``."""

        await self.remove_website(name, timeout=timeout)

    async def websites_rm(self, name: str, timeout: int = TIMEOUT) -> None:
        """Remove a website, matching Sliver's ``websites rm`` path."""

        await self.rm_website(name, timeout=timeout)

    async def add_website_content(
        self,
        name: str,
        web_path: str,
        content_type: str,
        content: bytes,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.Website:
        """Add content to a specific website

        :param name: Name of the website to add the content to
        :type name: str
        :param web_path: Bind content to web path
        :type web_path: str
        :param content_type: Specify the Content-type response HTTP header
        :type content_type: str
        :param content: The raw response content
        :type content: bytes
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic website model
        :rtype: models.clientpb.Website
        """
        web = models.clientpb.WebContent(
            path=web_path,
            content_type=content_type,
            content=content,
            size=len(content),
        )

        web_add = models.clientpb.WebsiteAddContent(name=name, contents={web_path: web})
        return await self.pydantic_stub.WebsiteAddContent(web_add, timeout=timeout)

    async def update_website_content(
        self,
        name: str,
        web_path: str,
        content_type: str,
        content: bytes,
        timeout: int = TIMEOUT,
    ) -> models.clientpb.Website:
        """Update content on a specific website / web path

        :param name: Name of the website to add the content to
        :type name: str
        :param web_path: Bind content to web path
        :type web_path: str
        :param content_type: Specify the Content-type response HTTP header
        :type content_type: str
        :param content: The raw response content
        :type content: bytes
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic website model
        :rtype: models.clientpb.Website
        """
        web = models.clientpb.WebContent(
            path=web_path,
            content_type=content_type,
            content=content,
            size=len(content),
        )

        web_update = models.clientpb.WebsiteAddContent(
            name=name, contents={web_path: web}
        )
        return await self.pydantic_stub.WebsiteUpdateContent(
            web_update, timeout=timeout
        )

    async def remove_website_content(
        self, name: str, paths: list[str], timeout: int = TIMEOUT
    ) -> models.clientpb.Website:
        """Compatibility spelling for :meth:`rm_website_content`.

        :param name: The name of the website from which to remove the content
        :type name: str
        :param paths: A list of paths to content that should be removed from the website
        :type paths: List[str]
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic website model
        :rtype: models.clientpb.Website
        """
        web = models.clientpb.WebsiteRemoveContent(name=name, paths=paths)
        return await self.pydantic_stub.WebsiteRemoveContent(web, timeout=timeout)

    async def rm_website_content(
        self, name: str, paths: list[str], timeout: int = TIMEOUT
    ) -> models.clientpb.Website:
        """Remove content paths, matching ``websites rm-content``."""

        return await self.remove_website_content(name, paths, timeout=timeout)

    async def websites_rm_content(
        self, name: str, paths: list[str], timeout: int = TIMEOUT
    ) -> models.clientpb.Website:
        """Remove paths, matching Sliver's ``websites rm-content`` path."""

        return await self.rm_website_content(name, paths, timeout=timeout)


class Client(SliverClient):
    """Preferred concise name for the asynchronous Sliver client."""

    @classmethod
    def from_config_file(
        cls,
        filepath: os.PathLike[str] | str | None = None,
    ) -> Client:
        """Construct a client from an explicit, environment, or default config."""

        return cls(OperatorConfig.from_file(filepath))

    async def __aenter__(self) -> Client:
        """Connect and preserve :class:`Client` in async contexts."""

        await self.connect()
        return self
