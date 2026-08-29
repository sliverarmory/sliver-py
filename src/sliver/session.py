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

from typing import TypeVar

import grpc

from . import models
from ._duration import request_timeout_nanoseconds
from ._protocols import RequestRoutedModel
from ._rpc import PydanticSliverRPCStub
from .errors import raise_for_command_error
from .interactive import BaseInteractiveCommands
from .models import ProtobufModel

_RequestT = TypeVar("_RequestT", bound=RequestRoutedModel)
_ResultT = TypeVar("_ResultT", bound=ProtobufModel)


class BaseSession:
    """Base class for Session objects.

    :param session: Pydantic session model.
    :type session: models.clientpb.Session
    :param channel: A gRPC channel.
    :type channel: grpc.Channel
    :param timeout: Timeout in seconds
    :type timeout: int, optional
    """

    def __init__(
        self,
        session: models.clientpb.Session,
        channel: grpc.aio.Channel,
        timeout: int = 60,
    ) -> None:
        if not isinstance(session, models.clientpb.Session):
            raise TypeError(
                "session must be a models.clientpb.Session Pydantic model"
            )
        self._channel = channel
        self._session = session.model_copy(deep=True)
        self._stub = PydanticSliverRPCStub(channel)
        self.timeout = timeout

    def _request(self, model: _RequestT) -> _RequestT:
        """Attach this session's routing metadata to a command request.

        ``model`` is any Pydantic command model with a ``request`` field.
        """
        model.request = models.commonpb.Request(
            session_id=self._session.id,
            timeout=request_timeout_nanoseconds(self.timeout),
        )
        return model

    async def _execute(
        self,
        rpc_name: str,
        request: RequestRoutedModel,
        result_type: type[_ResultT],
    ) -> _ResultT:
        """Execute a session command and validate its Pydantic result."""

        if not isinstance(request, ProtobufModel):
            raise TypeError("interactive requests must be Pydantic models")
        result = await getattr(self._stub, rpc_name)(request, timeout=self.timeout)
        if not isinstance(result, result_type):
            raise TypeError(
                f"{rpc_name} returned {type(result).__name__}, "
                f"expected {result_type.__name__}"
            )
        return raise_for_command_error(
            result,
            operation=rpc_name,
            target_id=self.session_id,
        )

    @property
    def session(self) -> models.clientpb.Session:
        """A copy of the complete Pydantic session model."""

        return self._session.model_copy(deep=True)

    @property
    def session_id(self) -> str:
        """Session ID"""
        return self._session.id

    @property
    def name(self) -> str:
        """Session name"""
        return self._session.name

    @property
    def hostname(self) -> str:
        """Hostname"""
        return self._session.hostname

    @property
    def uuid(self) -> str:
        """Session UUID"""
        return self._session.uuid

    @property
    def username(self) -> str:
        """Username"""
        return self._session.username

    @property
    def uid(self) -> str:
        """User ID"""
        return self._session.uid

    @property
    def gid(self) -> str:
        """Group ID"""
        return self._session.gid

    @property
    def os(self) -> str:
        """Operating system"""
        return self._session.os

    @property
    def arch(self) -> str:
        """Architecture"""
        return self._session.arch

    @property
    def transport(self) -> str:
        """Transport Method"""
        return self._session.transport

    @property
    def remote_address(self) -> str:
        """Remote address"""
        return self._session.remote_address

    @property
    def pid(self) -> int:
        """Process ID"""
        return self._session.pid

    @property
    def filename(self) -> str:
        """Implant filename"""
        return self._session.filename

    @property
    def last_checkin(self) -> int:
        """Last check in"""
        return self._session.last_checkin

    @property
    def active_c2(self) -> str:
        """Active C2"""
        return self._session.active_c2

    @property
    def version(self) -> str:
        """Version"""
        return self._session.version

    @property
    def is_dead(self) -> bool:
        """Is dead"""
        return self._session.is_dead

    @property
    def reconnect_interval(self) -> int:
        """Reconnect interval"""
        return self._session.reconnect_interval

    @property
    def proxy_url(self) -> str:
        """Proxy URL"""

        return self._session.proxy_url


class InteractiveSession(BaseSession, BaseInteractiveCommands):
    """Session only commands"""

    async def getsystem(
        self,
        hosting_process: str,
        config: models.clientpb.ImplantConfig,
    ) -> models.sliverpb.GetSystem:
        """Attempt to get SYSTEM, matching Sliver's session-only command."""

        return await self.get_system(hosting_process, config)

    async def extensions_list(self) -> models.sliverpb.ListExtensions:
        """List loaded extensions, matching Sliver's session-only command."""

        return await self.list_extensions()

    async def pivots(self) -> list[models.sliverpb.PivotListener]:
        """List C2 pivots

        :return: Pydantic pivot-listener models
        :rtype: list[models.sliverpb.PivotListener]
        """
        pivots = await self._stub.PivotSessionListeners(
            self._request(models.sliverpb.PivotListenersReq()), timeout=self.timeout
        )
        return list(pivots.listeners)

    async def pivot_listeners(self) -> list[models.sliverpb.PivotListener]:
        """Compatibility alias for :meth:`pivots`."""

        return await self.pivots()

    async def start_service(
        self, name: str, description: str, exe: str, hostname: str, arguments: str
    ) -> models.sliverpb.ServiceInfo:
        """Create and start a Windows service (Windows only)

        :param name: Name of the service
        :type name: str
        :param description: Service description
        :type description: str
        :param exe: Path to the service .exe file
        :type exe: str
        :param hostname: Hostname
        :type hostname: str
        :param arguments: Arguments to start the service with
        :type arguments: str
        :return: Pydantic service-information model
        :rtype: models.sliverpb.ServiceInfo
        """
        svc = models.sliverpb.StartServiceReq(
            service_name=name,
            service_description=description,
            bin_path=exe,
            hostname=hostname,
            arguments=arguments,
        )
        return await self._stub.StartService(self._request(svc), timeout=self.timeout)

    async def stop_service(
        self, name: str, hostname: str
    ) -> models.sliverpb.ServiceInfo:
        """Stop a Windows service (Windows only)

        :param name: Name of the servie
        :type name: str
        :param hostname: Hostname
        :type hostname: str
        :return: Pydantic service-information model
        :rtype: models.sliverpb.ServiceInfo
        """
        svc = models.sliverpb.StopServiceReq(
            service_info=models.sliverpb.ServiceInfoReq(
                service_name=name, hostname=hostname
            )
        )
        return await self._stub.StopService(self._request(svc), timeout=self.timeout)

    async def services_start(
        self,
        name: str,
        *,
        hostname: str = "localhost",
    ) -> models.sliverpb.ServiceInfo:
        """Start an existing service, matching Sliver's ``services start``."""

        request = models.sliverpb.StartServiceByNameReq(
            service_info=models.sliverpb.ServiceInfoReq(
                service_name=name,
                hostname=hostname,
            )
        )
        result = await self._stub.StartServiceByName(
            self._request(request),
            timeout=self.timeout,
        )
        return raise_for_command_error(
            result,
            operation="StartServiceByName",
            target_id=self.session_id,
        )

    async def services_stop(
        self,
        name: str,
        *,
        hostname: str = "localhost",
    ) -> models.sliverpb.ServiceInfo:
        """Stop a service, matching Sliver's ``services stop`` command."""

        result = await self.stop_service(name, hostname)
        return raise_for_command_error(
            result,
            operation="StopService",
            target_id=self.session_id,
        )

    async def remove_service(
        self, name: str, hostname: str
    ) -> models.sliverpb.ServiceInfo:
        """Remove a Windows service (Windows only)

        :param name: Name of the service
        :type name: str
        :param hostname: Hostname
        :type hostname: str
        :return: Pydantic service-information model
        :rtype: models.sliverpb.ServiceInfo
        """
        svc = models.sliverpb.RemoveServiceReq(
            service_info=models.sliverpb.ServiceInfoReq(
                service_name=name, hostname=hostname
            )
        )
        return await self._stub.RemoveService(self._request(svc), timeout=self.timeout)

    async def backdoor(
        self, remote_path: str, profile_name: str
    ) -> models.clientpb.Backdoor:
        """Inject a Sliver payload into a remote executable's code cave.

        :param remote_path: Remote path to an executable to backdoor
        :type remote_path: str
        :param profile_name: Implant profile name to inject into the binary
        :type profile_name: str
        :return: Pydantic backdoor-result model
        :rtype: models.clientpb.Backdoor
        """
        backdoor = models.clientpb.BackdoorReq(
            file_path=remote_path, profile_name=profile_name
        )
        return await self._stub.Backdoor(self._request(backdoor), timeout=self.timeout)
