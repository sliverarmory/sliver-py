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
import functools
import logging
from contextlib import suppress
from typing import Any

import grpc

from . import models
from ._protocols import PbWithRequestProp
from ._rpc import PydanticSliverRPCStub
from .interactive import BaseInteractiveCommands
from .models import ProtobufModel, protobuf_to_pydantic


class BaseBeacon:
    def __init__(
        self,
        beacon: models.clientpb.Beacon,
        channel: grpc.aio.Channel,
        timeout: int = 60,
    ):
        """Base class for Beacon classes.

        :param beacon: Pydantic beacon model. A raw protobuf message is accepted
            during the v0.1 transition.
        :type beacon: models.clientpb.Beacon
        :param channel: A gRPC channel.
        :type channel: grpc.aio.Channel
        :param timeout: Seconds to wait for timeout, defaults to TIMEOUT
        :type timeout: int, optional
        """
        self._log = logging.getLogger(self.__class__.__name__)
        self._channel = channel
        self._beacon = protobuf_to_pydantic(beacon)
        self._stub = PydanticSliverRPCStub(channel)
        self.timeout = timeout
        self.beacon_tasks: dict[
            str, tuple[asyncio.Future[Any], type[ProtobufModel] | None]
        ] = {}
        self._taskresult_ready = asyncio.Event()
        self._taskresult_error: Exception | None = None
        self._closed = False
        self._taskresult_watcher = asyncio.get_event_loop().create_task(
            self.taskresult_events()
        )

    async def close(self) -> None:
        """Stop watching for beacon task results and cancel pending commands."""

        if self._closed:
            return
        self._closed = True
        for task_future, _ in self.beacon_tasks.values():
            task_future.cancel()
        self.beacon_tasks.clear()

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

    def _request(self, pb: PbWithRequestProp) -> PbWithRequestProp:
        """Attach this beacon's routing metadata to a command request.

        ``pb`` is any Pydantic command model with a ``request`` field.
        """
        pb.request = models.commonpb.Request(  # type: ignore[attr-defined]
            beacon_id=self._beacon.id,
            timeout=self.timeout - 1,
            async_=True,
        )
        return pb

    async def taskresult_events(self):
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
                task_future: asyncio.Future[Any] | None = None
                try:
                    beacon_task_class = models.clientpb.BeaconTask.__protobuf_class__
                    if beacon_task_class is None:
                        raise TypeError("BeaconTask model has no protobuf class")
                    beacon_task_proto = beacon_task_class()
                    beacon_task_proto.ParseFromString(event.data)
                    beacon_task = models.clientpb.BeaconTask.from_protobuf(
                        beacon_task_proto
                    )
                    task_id = beacon_task.id
                    if task_id not in self.beacon_tasks:
                        continue
                    task_content = await self._stub.GetBeaconTaskContent(
                        models.clientpb.BeaconTask(id=task_id)
                    )
                    task_future, model_type = self.beacon_tasks[task_id]
                    if model_type is not None:
                        result_class = model_type.__protobuf_class__
                        if result_class is None:
                            raise TypeError(
                                f"{model_type.__name__} has no protobuf class"
                            )
                        result_proto = result_class()
                        result_proto.ParseFromString(task_content.response)
                        result = model_type.from_protobuf(result_proto)
                    else:
                        result = None
                    self.beacon_tasks.pop(task_id, None)
                    task_future.set_result(result)
                except Exception as err:
                    if task_id is not None:
                        pending = self.beacon_tasks.pop(task_id, None)
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
                for task_future, _ in self.beacon_tasks.values():
                    if not task_future.done():
                        task_future.set_exception(stopped)
                self.beacon_tasks.clear()


def beacon_taskresult(model_type: type[ProtobufModel] | None):
    """
    Wraps a class method to return a future that resolves when the
    beacon task result is available.
    """

    def func(method):
        @functools.wraps(method)
        async def wrapper(self, *args, **kwargs):
            await self._wait_for_taskresult_watcher()
            task_response = await method(self, *args, **kwargs)
            if task_response.response is None or not task_response.response.task_id:
                raise RuntimeError("beacon command did not return a task ID")
            task_id = task_response.response.task_id
            task_future = asyncio.get_running_loop().create_future()
            self.beacon_tasks[task_id] = (
                task_future,
                model_type,
            )
            return await task_future

        return wrapper

    return func


class InteractiveBeacon(BaseBeacon, BaseInteractiveCommands):
    """Wrap all commands that can be executed against a beacon mode implant"""

    async def interactive_session(self):
        pass

    # ----------------  Wrapped super() commands ----------------

    @beacon_taskresult(models.sliverpb.Ping)
    async def ping(self, *args, **kwargs) -> models.sliverpb.Ping:
        return await super().ping(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Ps)
    async def ps(self, *args, **kwargs) -> models.sliverpb.Ps:
        return await super().ps(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Terminate)
    async def terminate(self, *args, **kwargs) -> models.sliverpb.Terminate:
        return await super().terminate(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Ifconfig)
    async def ifconfig(self, *args, **kwargs) -> models.sliverpb.Ifconfig:
        return await super().ifconfig(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Netstat)
    async def netstat(self, *args, **kwargs) -> models.sliverpb.Netstat:
        return await super().netstat(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Ls)
    async def ls(self, *args, **kwargs) -> models.sliverpb.Ls:
        return await super().ls(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Pwd)
    async def cd(self, *args, **kwargs) -> models.sliverpb.Pwd:
        return await super().cd(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Pwd)
    async def pwd(self, *args, **kwargs) -> models.sliverpb.Pwd:
        return await super().pwd(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Rm)
    async def rm(self, *args, **kwargs) -> models.sliverpb.Rm:
        return await super().rm(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Mkdir)
    async def mkdir(self, *args, **kwargs) -> models.sliverpb.Mkdir:
        return await super().mkdir(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Download)
    async def download(self, *args, **kwargs) -> models.sliverpb.Download:
        return await super().download(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Upload)
    async def upload(self, *args, **kwargs) -> models.sliverpb.Upload:
        return await super().upload(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.ProcessDump)
    async def process_dump(self, *args, **kwargs) -> models.sliverpb.ProcessDump:
        return await super().process_dump(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.RunAs)
    async def run_as(self, *args, **kwargs) -> models.sliverpb.RunAs:
        return await super().run_as(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Impersonate)
    async def impersonate(self, *args, **kwargs) -> models.sliverpb.Impersonate:
        return await super().impersonate(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.RevToSelf)
    async def revert_to_self(self, *args, **kwargs) -> models.sliverpb.RevToSelf:
        return await super().revert_to_self(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.GetSystem)
    async def get_system(self, *args, **kwargs) -> models.sliverpb.GetSystem:
        return await super().get_system(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Task)
    async def execute_shellcode(self, *args, **kwargs) -> models.sliverpb.Task:
        return await super().execute_shellcode(*args, **kwargs)

    @beacon_taskresult(None)
    async def msf(self, *args, **kwargs) -> None:
        return await super().msf(*args, **kwargs)

    @beacon_taskresult(None)
    async def msf_remote(self, *args, **kwargs) -> None:
        return await super().msf_remote(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.ExecuteAssembly)
    async def execute_assembly(
        self, *args, **kwargs
    ) -> models.sliverpb.ExecuteAssembly:
        return await super().execute_assembly(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Migrate)
    async def migrate(self, *args, **kwargs) -> models.sliverpb.Migrate:
        return await super().migrate(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Execute)
    async def execute(self, *args, **kwargs) -> models.sliverpb.Execute:
        return await super().execute(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Sideload)
    async def sideload(self, *args, **kwargs) -> models.sliverpb.Sideload:
        return await super().sideload(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.SpawnDll)
    async def spawn_dll(self, *args, **kwargs) -> models.sliverpb.SpawnDll:
        return await super().spawn_dll(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.ListExtensions)
    async def list_extensions(self, *args, **kwargs) -> models.sliverpb.ListExtensions:
        return await super().list_extensions(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.RegisterExtension)
    async def register_extension(
        self, *args, **kwargs
    ) -> models.sliverpb.RegisterExtension:
        return await super().register_extension(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.CallExtension)
    async def call_extension(self, *args, **kwargs) -> models.sliverpb.CallExtension:
        return await super().call_extension(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.Screenshot)
    async def screenshot(self, *args, **kwargs) -> models.sliverpb.Screenshot:
        return await super().screenshot(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.MakeToken)
    async def make_token(self, *args, **kwargs) -> models.sliverpb.MakeToken:
        return await super().make_token(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.EnvInfo)
    async def get_env(self, *args, **kwargs) -> models.sliverpb.EnvInfo:
        return await super().get_env(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.SetEnv)
    async def set_env(self, *args, **kwargs) -> models.sliverpb.SetEnv:
        return await super().set_env(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.UnsetEnv)
    async def unset_env(self, *args, **kwargs) -> models.sliverpb.UnsetEnv:
        return await super().unset_env(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.RegistryRead)
    async def registry_read(self, *args, **kwargs) -> models.sliverpb.RegistryRead:
        return await super().registry_read(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.RegistryWrite)
    async def registry_write(self, *args, **kwargs) -> models.sliverpb.RegistryWrite:
        return await super().registry_write(*args, **kwargs)

    @beacon_taskresult(models.sliverpb.RegistryCreateKey)
    async def registry_create_key(
        self, *args, **kwargs
    ) -> models.sliverpb.RegistryCreateKey:
        return await super().registry_create_key(*args, **kwargs)
