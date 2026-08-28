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

import logging
from collections.abc import AsyncGenerator

import grpc

from . import models
from ._rpc import PydanticSliverRPCStub
from .beacon import InteractiveBeacon
from .config import SliverClientConfig
from .models import protobuf_to_pydantic
from .pb.rpcpb.services_pb2_grpc import SliverRPCStub
from .session import InteractiveSession

KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TIMEOUT = 60


class BaseClient:
    # 2GB triggers an overflow error in the gRPC library so we do 2GB-1
    MAX_MESSAGE_LENGTH = (2 * GB) - 1

    KEEP_ALIVE_TIMEOUT = 10000
    CERT_COMMON_NAME = "multiplayer"

    def __init__(self, config: SliverClientConfig):
        self.config = config
        self._channel: grpc.aio.Channel = None  # type: ignore[assignment]
        self._stub: PydanticSliverRPCStub = None  # type: ignore[assignment]
        self._log = logging.getLogger(self.__class__.__name__)

    def is_connected(self) -> bool:
        return self._channel is not None

    async def close(self) -> None:
        """Close the active gRPC channel.

        Calling ``close`` more than once is safe. A closed client may be
        connected again with :meth:`SliverClient.connect`.
        """

        channel = self._channel
        self._channel = None  # type: ignore[assignment]
        self._stub = None  # type: ignore[assignment]
        if channel is not None:
            await channel.close()

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
    def options(self):
        return [
            ("grpc.keepalive_timeout_ms", self.KEEP_ALIVE_TIMEOUT),
            ("grpc.ssl_target_name_override", self.CERT_COMMON_NAME),
            ("grpc.max_send_message_length", self.MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", self.MAX_MESSAGE_LENGTH),
        ]

    @property
    def pydantic_stub(self) -> PydanticSliverRPCStub:
        """Return the model-converting stub for unsupported low-level RPCs.

        Requests accept descriptor-generated Pydantic models and responses are
        converted back to Pydantic models. The stub is available only while the
        client is connected.
        """
        if self._stub is None:
            raise RuntimeError("client is not connected")
        return self._stub

    @property
    def raw_stub(self) -> SliverRPCStub:
        """Return the generated protobuf stub for unsupported low-level RPCs.

        The raw stub does not perform Pydantic conversion and is available only
        while the client is connected.
        """

        return self.pydantic_stub.raw


class SliverClient(BaseClient):
    """Asyncio client implementation"""

    beacon_event_types = ["beacon-registered"]
    session_event_types = ["session-connected", "session-disconnected"]
    job_event_types = ["job-started", "job-stopped"]
    canary_event_types = ["canary"]

    async def connect(self) -> models.clientpb.Version:
        """Establish a connection to the Sliver server

        :return: Pydantic model containing the server's version information
        :rtype: models.clientpb.Version
        """
        self._channel = grpc.aio.secure_channel(
            target=self.target,
            credentials=self.credentials,
            options=self.options,
        )
        self._stub = PydanticSliverRPCStub(self._channel)
        return await self.version()

    async def interact_session(
        self, session_id: str, timeout=TIMEOUT
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
            return InteractiveSession(session, self._channel, timeout)

    async def interact_beacon(
        self, beacon_id: str, timeout=TIMEOUT
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
            return InteractiveBeacon(beacon, self._channel, timeout)

    async def session_by_id(
        self, session_id: str, timeout=TIMEOUT
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
        self, beacon_id: str, timeout=TIMEOUT
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

    async def events(self) -> AsyncGenerator[models.clientpb.Event, None]:
        """All events

        :yield: A stream of events
        :rtype: models.clientpb.Event
        """
        async for event in self._stub.Events(models.commonpb.Empty()):
            yield event

    async def on(
        self, event_types: str | list[str]
    ) -> AsyncGenerator[models.clientpb.Event, None]:
        """Iterate on a specific event or list of events

        :param event_types: An event type or list of event types
        :type event_types: Union[str, List[str]]
        :yield: A stream of events of the given type(s)
        :rtype: models.clientpb.Event
        """
        if isinstance(event_types, str):
            event_types = [event_types]
        async for event in self.events():
            if event.event_type in event_types:
                yield event

    async def version(self, timeout=TIMEOUT) -> models.clientpb.Version:
        """Get server version information

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic server-version model
        :rtype: models.clientpb.Version
        """
        return await self._stub.GetVersion(models.commonpb.Empty(), timeout=timeout)

    async def operators(self, timeout=TIMEOUT) -> list[models.clientpb.Operator]:
        """Get a list of operators and their online status

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic operator models
        :rtype: list[models.clientpb.Operator]
        """
        operators = await self._stub.GetOperators(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(operators.operators)

    async def sessions(self, timeout=TIMEOUT) -> list[models.clientpb.Session]:
        """Get a list of active sessions

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic session models
        :rtype: list[models.clientpb.Session]
        """
        sessions: models.clientpb.Sessions = await self._stub.GetSessions(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(sessions.sessions)

    async def rename_session(self, session_id: str, name: str, timeout=TIMEOUT) -> None:
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
        await self._stub.Rename(rename_req, timeout=timeout)

    async def kill_session(self, session_id: str, force=False, timeout=TIMEOUT) -> None:
        """Kill a session

        :param session_id: Session ID to kill
        :type session_id: str
        :param force: Force kill the session, defaults to False
        :type force: bool, optional
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        request = models.commonpb.Request(session_id=session_id, timeout=timeout)
        kill_req = models.sliverpb.KillReq(force=force, request=request)
        await self._stub.Kill(kill_req, timeout=timeout)

    async def beacons(self, timeout=TIMEOUT) -> list[models.clientpb.Beacon]:
        """Get a list of active beacons

        :param timeout: gRPC timeout, defaults to 60 seconds
        :rtype: list[models.clientpb.Beacon]
        """
        beacons: models.clientpb.Beacons = await self._stub.GetBeacons(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(beacons.beacons)

    async def rename_beacon(self, beacon_id: str, name: str, timeout=TIMEOUT) -> None:
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
        await self._stub.Rename(rename_req, timeout=timeout)

    async def kill_beacon(self, beacon_id: str, timeout=TIMEOUT) -> None:
        """Remove a beacon record from the server.

        This does not terminate a running beacon process.

        :param beacon_id: Beacon ID to remove
        :type beacon_id: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        beacon_rm = models.clientpb.Beacon(id=beacon_id)
        await self._stub.RmBeacon(beacon_rm, timeout=timeout)

    async def beacon_tasks(
        self, beacon_id: str, timeout=TIMEOUT
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
        tasks = await self._stub.GetBeaconTasks(beacon, timeout=timeout)
        return list(tasks.tasks)

    async def beacon_task_content(
        self, task_id: str, timeout=TIMEOUT
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
        task = await self._stub.GetBeaconTaskContent(task_req, timeout=timeout)
        return task

    async def jobs(self, timeout=TIMEOUT) -> list[models.clientpb.Job]:
        """Get a list of active jobs

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic job models
        :rtype: list[models.clientpb.Job]
        """
        jobs: models.clientpb.Jobs = await self._stub.GetJobs(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(jobs.active)

    async def job_by_id(
        self, job_id: int, timeout=TIMEOUT
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
        self, job_port: int, timeout=TIMEOUT
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

    async def kill_job(self, job_id: int, timeout=TIMEOUT) -> models.clientpb.KillJob:
        """Kill a job

        :param job_id: Numeric job ID to kill
        :type job_id: int
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic job-termination model
        :rtype: models.clientpb.KillJob
        """
        kill_req = models.clientpb.KillJobReq(id=job_id)
        return await self._stub.KillJob(kill_req, timeout=timeout)

    async def start_mtls_listener(
        self,
        host: str = "0.0.0.0",
        port: int = 8888,
        timeout=TIMEOUT,
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
        return await self._stub.StartMTLSListener(mtls_req, timeout=timeout)

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
            uniq_ip = await self.generate_wg_ip()
            tun_ip = uniq_ip.ip

        wg_req = models.clientpb.WGListenerReq(
            tun_ip=tun_ip,
            host=host,
            port=port,
            n_port=n_port,
            key_port=key_port,
        )
        return await self._stub.StartWGListener(wg_req, timeout=timeout)

    async def start_dns_listener(
        self,
        domains: list[str],
        host: str = "0.0.0.0",
        port: int = 53,
        canaries: bool = True,
        enforce_otp=True,
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
        # Ensure domains always have a trailing dot
        domains = list(map(lambda d: d + "." if d[-1] != "." else d, domains))

        dns_req = models.clientpb.DNSListenerReq(
            domains=domains,
            canaries=canaries,
            host=host,
            port=port,
            enforce_otp=enforce_otp,
        )
        return await self._stub.StartDNSListener(dns_req, timeout=timeout)

    async def start_http_listener(
        self,
        host: str = "0.0.0.0",
        port: int = 80,
        website: str = "",
        domain: str = "",
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
        )
        return await self._stub.StartHTTPListener(http_req, timeout=timeout)

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
        long_poll_timeout: int = 1,
        long_poll_jitter: int = 2,
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
            long_poll_timeout=long_poll_timeout,
            long_poll_jitter=long_poll_jitter,
            randomize_jarm=randomize_jarm,
        )
        return await self._stub.StartHTTPSListener(https_req, timeout=timeout)

    async def start_tcp_stager_listener(
        self, host: str, port: int, data: bytes, timeout=TIMEOUT
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
        """
        stage_req = models.clientpb.StagerListenerReq(
            protocol=models.clientpb.StageProtocol.TCP,
            host=host,
            port=port,
            data=data,
        )
        return await self._stub.StartTCPStagerListener(stage_req, timeout=timeout)

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
        req = models.clientpb.GenerateReq(config=protobuf_to_pydantic(config))
        return await self._stub.Generate(req, timeout=timeout)

    async def regenerate_implant(
        self, implant_name: str, timeout=TIMEOUT
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
        return await self._stub.Regenerate(regenerate, timeout=timeout)

    async def implant_builds(
        self, timeout=TIMEOUT
    ) -> dict[str, models.clientpb.ImplantConfig]:
        """Get information about historical implant builds

        :return: Map from implant names to their configurations
        :rtype: dict[str, models.clientpb.ImplantConfig]
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        builds: models.clientpb.ImplantBuilds = await self._stub.ImplantBuilds(
            models.commonpb.Empty(), timeout=timeout
        )
        return dict(builds.configs)

    async def delete_implant_build(self, implant_name: str, timeout=TIMEOUT) -> None:
        """Delete a historical implant build from the server by name

        :param implant_name: The name of the implant build to delete
        :type implant_name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        delete = models.clientpb.DeleteReq(name=implant_name)
        await self._stub.DeleteImplantBuild(delete, timeout=timeout)

    async def canaries(self, timeout=TIMEOUT) -> list[models.clientpb.DNSCanary]:
        """Get canaries generated during implant builds and their metadata.

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic DNS-canary models
        :rtype: list[models.clientpb.DNSCanary]
        """
        canaries = await self._stub.Canaries(models.commonpb.Empty(), timeout=timeout)
        return list(canaries.canaries)

    async def generate_wg_client_config(
        self, timeout=TIMEOUT
    ) -> models.clientpb.WGClientConfig:
        """Generate a new WireGuard client configuration files

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic WireGuard-client configuration model
        :rtype: models.clientpb.WGClientConfig
        """
        return await self._stub.GenerateWGClientConfig(
            models.commonpb.Empty(), timeout=timeout
        )

    async def generate_wg_ip(self, timeout=TIMEOUT) -> models.clientpb.UniqueWGIP:
        """Generate a unique IP address for use with WireGuard

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic unique WireGuard IP model
        :rtype: models.clientpb.UniqueWGIP
        """
        return await self._stub.GenerateUniqueIP(
            models.commonpb.Empty(), timeout=timeout
        )

    async def implant_profiles(
        self, timeout=TIMEOUT
    ) -> list[models.clientpb.ImplantProfile]:
        """Get a list of all implant configuration profiles on the server

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic implant-profile models
        :rtype: list[models.clientpb.ImplantProfile]
        """
        profiles = await self._stub.ImplantProfiles(
            models.commonpb.Empty(), timeout=timeout
        )
        return list(profiles.profiles)

    async def delete_implant_profile(self, profile_name, timeout=TIMEOUT) -> None:
        """Delete an implant configuration profile by name

        :param profile_name: Name of the profile to delete
        :type profile_name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        delete = models.clientpb.DeleteReq(name=profile_name)
        await self._stub.DeleteImplantProfile(delete, timeout=timeout)

    async def save_implant_profile(
        self, profile: models.clientpb.ImplantProfile, timeout=TIMEOUT
    ) -> models.clientpb.ImplantProfile:
        """Save an implant configuration profile to the server

        :param profile: An implant configuration profile model
        :type profile: models.clientpb.ImplantProfile
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic implant-profile model
        :rtype: models.clientpb.ImplantProfile
        """
        return await self._stub.SaveImplantProfile(
            protobuf_to_pydantic(profile), timeout=timeout
        )

    async def shellcode(
        self, data: bytes, function_name: str, arguments: str = "", timeout=TIMEOUT
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
        return await self._stub.ShellcodeRDI(shell_req, timeout=timeout)

    async def websites(self, timeout=TIMEOUT) -> list[models.clientpb.Website]:
        """Get a list of websites

        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        :return: Pydantic website models
        :rtype: list[models.clientpb.Website]
        """
        websites = await self._stub.Websites(models.commonpb.Empty(), timeout=timeout)
        return list(websites.websites)

    async def website(self, name: str, timeout=TIMEOUT) -> models.clientpb.Website:
        """Get a website and its content by name."""

        return await self._stub.Website(
            models.clientpb.Website(name=name), timeout=timeout
        )

    async def remove_website(self, name: str, timeout=TIMEOUT) -> None:
        """Remove an entire website and its content

        :param name: The name of the website to remove
        :type name: str
        :param timeout: gRPC timeout, defaults to 60 seconds
        :type timeout: int, optional
        """
        website = models.clientpb.Website(name=name)
        await self._stub.WebsiteRemove(website, timeout=timeout)

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
        return await self._stub.WebsiteAddContent(web_add, timeout=timeout)

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
        return await self._stub.WebsiteUpdateContent(web_update, timeout=timeout)

    async def remove_website_content(
        self, name: str, paths: list[str], timeout=TIMEOUT
    ) -> models.clientpb.Website:
        """Remove content from a specific website

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
        return await self._stub.WebsiteRemoveContent(web, timeout=timeout)
