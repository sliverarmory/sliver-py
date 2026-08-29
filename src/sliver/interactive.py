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

from . import models
from ._protocols import InteractiveObject
from .enums import GOOS, LogonType, RegistryHive


class BaseInteractiveCommands:
    async def ping(self: InteractiveObject, nonce: int = 0) -> models.sliverpb.Ping:
        """Send a round trip message to the implant (does NOT use ICMP)

        :param nonce: Optional value echoed by the implant, defaults to 0
        :type nonce: int, optional
        :return: Pydantic ping model
        :rtype: models.sliverpb.Ping
        """
        return await self._execute(
            "Ping",
            self._request(models.sliverpb.Ping(nonce=nonce)),
            models.sliverpb.Ping,
        )

    async def ps(
        self: InteractiveObject, full_info: bool = False
    ) -> models.sliverpb.Ps:
        """List the processes of the remote system

        :param full_info: Include full process metadata, defaults to False
        :type full_info: bool, optional
        :return: Pydantic process-list model
        :rtype: models.sliverpb.Ps
        """
        ps = models.sliverpb.PsReq(full_info=full_info)
        return await self._execute("Ps", self._request(ps), models.sliverpb.Ps)

    async def terminate(
        self: InteractiveObject, pid: int, force: bool = False
    ) -> models.sliverpb.Terminate:
        """Terminate a remote process

        :param pid: The process ID to terminate.
        :type pid: int
        :param force: Force termination of the process, defaults to False
        :type force: bool, optional
        :return: Pydantic terminate model
        :rtype: models.sliverpb.Terminate
        """
        terminator = models.sliverpb.TerminateReq(pid=pid, force=force)
        return await self._execute(
            "Terminate", self._request(terminator), models.sliverpb.Terminate
        )

    async def ifconfig(self: InteractiveObject) -> models.sliverpb.Ifconfig:
        """Get network interface configuration information about the remote system

        :return: Pydantic interface-configuration model
        :rtype: models.sliverpb.Ifconfig
        """
        return await self._execute(
            "Ifconfig",
            self._request(models.sliverpb.IfconfigReq()),
            models.sliverpb.Ifconfig,
        )

    async def netstat(
        self: InteractiveObject,
        tcp: bool,
        udp: bool,
        ipv4: bool,
        ipv6: bool,
        listening: bool = True,
    ) -> models.sliverpb.Netstat:
        """Get information about network connections on the remote system.

        :param tcp: Get TCP information
        :type tcp: bool
        :param udp: Get UDP information
        :type udp: bool
        :param ipv4: Get IPv4 connection information
        :type ipv4: bool
        :param ipv6: Get IPv6 connection information
        :type ipv6: bool
        :param listening: Get listening connection information, defaults to True
        :type listening: bool, optional
        :return: Pydantic network-connection model
        :rtype: models.sliverpb.Netstat
        """
        net = models.sliverpb.NetstatReq(
            tcp=tcp, udp=udp, ip4=ipv4, ip6=ipv6, listening=listening
        )
        return await self._execute(
            "Netstat", self._request(net), models.sliverpb.Netstat
        )

    async def ls(self: InteractiveObject, remote_path: str = ".") -> models.sliverpb.Ls:
        """Get a directory listing from the remote system

        :param remote_path: Remote path
        :type remote_path: str
        :return: Pydantic directory-listing model
        :rtype: models.sliverpb.Ls
        """
        ls = models.sliverpb.LsReq(path=remote_path)
        return await self._execute("Ls", self._request(ls), models.sliverpb.Ls)

    async def cd(self: InteractiveObject, remote_path: str) -> models.sliverpb.Pwd:
        """Change the current working directory of the implant

        :param remote_path: Remote path
        :type remote_path: str
        :return: Pydantic working-directory model
        :rtype: models.sliverpb.Pwd
        """
        cd = models.sliverpb.CdReq(path=remote_path)
        return await self._execute("Cd", self._request(cd), models.sliverpb.Pwd)

    async def pwd(self: InteractiveObject) -> models.sliverpb.Pwd:
        """Get the implant's current working directory

        :return: Pydantic working-directory model
        :rtype: models.sliverpb.Pwd
        """
        pwd = models.sliverpb.PwdReq()
        return await self._execute("Pwd", self._request(pwd), models.sliverpb.Pwd)

    async def mv(
        self: InteractiveObject, source: str, destination: str
    ) -> models.sliverpb.Mv:
        """Move or rename a remote file.

        :param source: Existing remote path
        :type source: str
        :param destination: New remote path
        :type destination: str
        :return: Pydantic move-result model
        :rtype: models.sliverpb.Mv
        """
        move = models.sliverpb.MvReq(src=source, dst=destination)
        return await self._execute("Mv", self._request(move), models.sliverpb.Mv)

    async def cp(
        self: InteractiveObject, source: str, destination: str
    ) -> models.sliverpb.Cp:
        """Copy a remote file.

        :param source: Existing remote path
        :type source: str
        :param destination: New remote path
        :type destination: str
        :return: Pydantic copy-result model
        :rtype: models.sliverpb.Cp
        """
        copy = models.sliverpb.CpReq(src=source, dst=destination)
        return await self._execute("Cp", self._request(copy), models.sliverpb.Cp)

    async def rm(
        self: InteractiveObject,
        remote_path: str,
        recursive: bool = False,
        force: bool = False,
    ) -> models.sliverpb.Rm:
        """Remove a directory or file(s)

        :param remote_path: Remote path
        :type remote_path: str
        :param recursive: Recursively remove file(s), defaults to False
        :type recursive: bool, optional
        :param force: Forcefully remove the file(s), defaults to False
        :type force: bool, optional
        :return: Pydantic removal-result model
        :rtype: models.sliverpb.Rm
        """
        rm = models.sliverpb.RmReq(path=remote_path, recursive=recursive, force=force)
        return await self._execute("Rm", self._request(rm), models.sliverpb.Rm)

    async def mkdir(self: InteractiveObject, remote_path: str) -> models.sliverpb.Mkdir:
        """Make a directory on the remote file system

        :param remote_path: Directory to create
        :type remote_path: str
        :return: Pydantic directory-creation model
        :rtype: models.sliverpb.Mkdir
        """
        make = models.sliverpb.MkdirReq(path=remote_path)
        return await self._execute("Mkdir", self._request(make), models.sliverpb.Mkdir)

    async def download(
        self: InteractiveObject, remote_path: str, recurse: bool = False
    ) -> models.sliverpb.Download:
        """Download a file or directory from the remote file system

        :param remote_path: File to download
        :type remote_path: str
        :param recurse: Download all files in a directory
        :type recurse: bool
        :return: Pydantic download model
        :rtype: models.sliverpb.Download
        """
        download = models.sliverpb.DownloadReq(path=remote_path, recurse=recurse)
        return await self._execute(
            "Download", self._request(download), models.sliverpb.Download
        )

    async def upload(
        self: InteractiveObject,
        remote_path: str,
        data: bytes,
        is_ioc: bool = False,
    ) -> models.sliverpb.Upload:
        """Write data to specified path on remote file system

        :param remote_path: Remote path
        :type remote_path: str
        :param data: Data to write
        :type data: bytes
        :param is_ioc: Data is an indicator of compromise, defaults to False
        :type is_ioc: bool, optional
        :return: Pydantic upload model
        :rtype: models.sliverpb.Upload
        """
        upload = models.sliverpb.UploadReq(path=remote_path, data=data, is_ioc=is_ioc)
        return await self._execute(
            "Upload", self._request(upload), models.sliverpb.Upload
        )

    async def grep(
        self: InteractiveObject,
        search_pattern: str,
        remote_path: str,
        *,
        recursive: bool = False,
        lines_before: int = 0,
        lines_after: int = 0,
    ) -> models.sliverpb.Grep:
        """Search remote files for a regular expression.

        :param search_pattern: Go-compatible regular expression to search for
        :type search_pattern: str
        :param remote_path: Remote file or directory to search
        :type remote_path: str
        :param recursive: Search directories recursively, defaults to False
        :type recursive: bool, optional
        :param lines_before: Context lines before each match, defaults to 0
        :type lines_before: int, optional
        :param lines_after: Context lines after each match, defaults to 0
        :type lines_after: int, optional
        :return: Pydantic search-result model
        :rtype: models.sliverpb.Grep
        """
        grep = models.sliverpb.GrepReq(
            search_pattern=search_pattern,
            path=remote_path,
            recursive=recursive,
            lines_before=lines_before,
            lines_after=lines_after,
        )
        return await self._execute("Grep", self._request(grep), models.sliverpb.Grep)

    async def chtimes(
        self: InteractiveObject,
        remote_path: str,
        accessed_at: int,
        modified_at: int,
    ) -> models.sliverpb.Chtimes:
        """Change a remote file's access and modification times.

        :param remote_path: Remote file or directory
        :type remote_path: str
        :param accessed_at: Last-access time as Unix seconds
        :type accessed_at: int
        :param modified_at: Last-modified time as Unix seconds
        :type modified_at: int
        :return: Pydantic timestamp-update model
        :rtype: models.sliverpb.Chtimes
        """
        times = models.sliverpb.ChtimesReq(
            path=remote_path,
            a_time=accessed_at,
            m_time=modified_at,
        )
        return await self._execute(
            "Chtimes", self._request(times), models.sliverpb.Chtimes
        )

    async def mount(self: InteractiveObject) -> models.sliverpb.Mount:
        """Get information about mounted remote filesystems.

        :return: Pydantic mounted-filesystem inventory
        :rtype: models.sliverpb.Mount
        """
        return await self._execute(
            "Mount",
            self._request(models.sliverpb.MountReq()),
            models.sliverpb.Mount,
        )

    async def procdump(
        self: InteractiveObject, pid: int
    ) -> models.sliverpb.ProcessDump:
        """Dump a remote process' memory.

        :param pid: PID of the process to dump
        :type pid: int
        :return: Pydantic process-dump model
        :rtype: models.sliverpb.ProcessDump
        """
        procdump = models.sliverpb.ProcessDumpReq(pid=pid)
        return await self._execute(
            "ProcessDump", self._request(procdump), models.sliverpb.ProcessDump
        )

    async def process_dump(
        self: BaseInteractiveCommands, pid: int
    ) -> models.sliverpb.ProcessDump:
        """Compatibility alias for :meth:`procdump`."""

        return await self.procdump(pid)

    async def runas(
        self: InteractiveObject,
        username: str,
        process_name: str,
        args: str = "",
        *,
        domain: str = "",
        password: str = "",
        show_window: bool = False,
        net_only: bool = False,
    ) -> models.sliverpb.RunAs:
        """Run a command as another user, matching Sliver's ``runas`` command.

        :param username: User to run process as
        :type username: str
        :param process_name: Process to execute
        :type process_name: str
        :param args: Arguments to process
        :type args: str
        :param domain: Domain of the user
        :type domain: str
        :param password: Password of the user
        :type password: str
        :param show_window: Show the new process window
        :type show_window: bool
        :param net_only: Use the credentials for network access only
        :type net_only: bool
        :return: Pydantic run-as result model
        :rtype: models.sliverpb.RunAs
        """
        run_as = models.sliverpb.RunAsReq(
            username=username,
            process_name=process_name,
            args=args,
            domain=domain,
            password=password,
            hide_window=not show_window,
            net_only=net_only,
        )
        return await self._execute(
            "RunAs", self._request(run_as), models.sliverpb.RunAs
        )

    async def run_as(
        self: BaseInteractiveCommands,
        username: str,
        process_name: str,
        args: str,
    ) -> models.sliverpb.RunAs:
        """Compatibility alias for :meth:`runas`."""

        # The historical method omitted HideWindow, whose wire default is
        # false. Preserve that behavior while the command-shaped ``runas``
        # method follows Sliver's hidden-window default.
        return await self.runas(
            username,
            process_name,
            args,
            show_window=True,
        )

    async def impersonate(
        self: InteractiveObject, username: str
    ) -> models.sliverpb.Impersonate:
        """Impersonate a user using tokens (Windows only)

        :param username: User to impersonate
        :type username: str
        :return: Pydantic impersonation-result model
        :rtype: models.sliverpb.Impersonate
        """
        impersonate = models.sliverpb.ImpersonateReq(username=username)
        return await self._execute(
            "Impersonate", self._request(impersonate), models.sliverpb.Impersonate
        )

    async def rev2self(self: InteractiveObject) -> models.sliverpb.RevToSelf:
        """Revert to self from impersonation context

        :return: Pydantic revert-result model
        :rtype: models.sliverpb.RevToSelf
        """
        return await self._execute(
            "RevToSelf",
            self._request(models.sliverpb.RevToSelfReq()),
            models.sliverpb.RevToSelf,
        )

    async def revert_to_self(
        self: BaseInteractiveCommands,
    ) -> models.sliverpb.RevToSelf:
        """Compatibility alias for :meth:`rev2self`."""

        return await self.rev2self()

    async def get_system(
        self: InteractiveObject,
        hosting_process: str,
        config: models.clientpb.ImplantConfig,
    ) -> models.sliverpb.GetSystem:
        """Attempt to get SYSTEM (Windows only)

        :param hosting_process: Hosting process to attempt gaining privileges
        :type hosting_process: str
        :param config: Implant configuration to be injected into the hosting process
        :type config: models.clientpb.ImplantConfig
        :return: Pydantic privilege-escalation result model
        :rtype: models.sliverpb.GetSystem
        """
        system = models.clientpb.GetSystemReq(
            hosting_process=hosting_process,
            config=config,
        )
        return await self._execute(
            "GetSystem", self._request(system), models.sliverpb.GetSystem
        )

    async def execute_shellcode(
        self: InteractiveObject,
        data: bytes,
        rwx: bool,
        pid: int,
        encoder: str = "",
    ) -> models.sliverpb.Task:
        """Execute shellcode in-memory

        :param data: Shellcode buffer
        :type data: bytes
        :param rwx: Enable/disable RWX pages
        :type rwx: bool
        :param pid: Process ID to inject shellcode into
        :type pid: int
        :param encoder: Encoder ('', 'gzip'), defaults to ''
        :type encoder: str, optional
        :return: Pydantic task model
        :rtype: models.sliverpb.Task
        """
        task = models.sliverpb.TaskReq(
            encoder=encoder, data=data, rwx_pages=rwx, pid=pid
        )
        return await self._execute("Task", self._request(task), models.sliverpb.Task)

    async def msf(
        self: InteractiveObject,
        payload: str,
        lhost: str,
        lport: int,
        encoder: str,
        iterations: int,
    ) -> models.sliverpb.Task:
        """Generate and execute a Metasploit payload on the remote system.

        The server must be configured with Metasploit.

        :param payload: Payload to generate
        :type payload: str
        :param lhost: Metasploit LHOST parameter
        :type lhost: str
        :param lport: Metasploit LPORT parameter
        :type lport: int
        :param encoder: Metasploit encoder
        :type encoder: str
        :param iterations: Iterations for Metasploit encoder
        :type iterations: int
        """
        msf = models.clientpb.MSFReq(
            payload=payload,
            l_host=lhost,
            l_port=lport,
            encoder=encoder,
            iterations=iterations,
        )
        return await self._execute("Msf", self._request(msf), models.sliverpb.Task)

    async def msf_inject(
        self: InteractiveObject,
        payload: str,
        lhost: str,
        lport: int,
        encoder: str,
        iterations: int,
        pid: int,
    ) -> models.sliverpb.Task:
        """Generate and execute a Metasploit payload in a remote process.

        The server must be configured with Metasploit.

        :param payload: Payload to generate
        :type payload: str
        :param lhost: Metasploit LHOST parameter
        :type lhost: str
        :param lport: Metasploit LPORT parameter
        :type lport: int
        :param encoder: Metasploit encoder
        :type encoder: str
        :param iterations: Iterations for Metasploit encoder
        :type iterations: int
        :param pid: Process ID to inject the payload into
        :type pid: int
        """
        msf = models.clientpb.MSFRemoteReq(
            payload=payload,
            l_host=lhost,
            l_port=lport,
            encoder=encoder,
            iterations=iterations,
            pid=pid,
        )
        return await self._execute(
            "MsfRemote", self._request(msf), models.sliverpb.Task
        )

    async def msf_remote(
        self: BaseInteractiveCommands,
        payload: str,
        lhost: str,
        lport: int,
        encoder: str,
        iterations: int,
        pid: int,
    ) -> models.sliverpb.Task:
        """Compatibility alias for :meth:`msf_inject`."""

        return await self.msf_inject(
            payload,
            lhost,
            lport,
            encoder,
            iterations,
            pid,
        )

    async def execute_assembly(
        self: InteractiveObject,
        assembly: bytes,
        arguments: list[str],
        process: str,
        is_dll: bool,
        arch: str,
        class_name: str,
        method: str,
        app_domain: str,
    ) -> models.sliverpb.ExecuteAssembly:
        """Execute a .NET assembly in-memory on the remote system

        :param assembly: A buffer of the .NET assembly to execute
        :type assembly: bytes
        :param arguments: Arguments to the .NET assembly
        :type arguments: list[str]
        :param process: Process to execute assembly
        :type process: str
        :param is_dll: Is assembly a DLL
        :type is_dll: bool
        :param arch: Assembly architecture
        :type arch: str
        :param class_name: Class name of the assembly
        :type class_name: str
        :param method: Method to execute
        :type method: str
        :param app_domain: AppDomain
        :type app_domain: str
        :return: Pydantic assembly-execution result model
        :rtype: models.sliverpb.ExecuteAssembly
        """
        asm = models.sliverpb.ExecuteAssemblyReq(
            assembly=assembly,
            arguments=arguments,
            process=process,
            is_dll=is_dll,
            arch=arch,
            class_name=class_name,
            method=method,
            app_domain=app_domain,
        )
        return await self._execute(
            "ExecuteAssembly",
            self._request(asm),
            models.sliverpb.ExecuteAssembly,
        )

    async def migrate(
        self: InteractiveObject, pid: int, config: models.clientpb.ImplantConfig
    ) -> models.sliverpb.Migrate:
        """Migrate implant to another process

        :param pid: Process ID to inject implant into
        :type pid: int
        :param config: Implant configuration to inject into the remote process
        :type config: models.clientpb.ImplantConfig
        :return: Pydantic migration-result model
        :rtype: models.sliverpb.Migrate
        """
        migrate = models.clientpb.MigrateReq(pid=pid, config=config)
        return await self._execute(
            "Migrate", self._request(migrate), models.sliverpb.Migrate
        )

    async def execute(
        self: InteractiveObject,
        exe: str,
        args: list[str] | None = None,
        output: bool = True,
        *,
        background: bool = False,
        stdout: str = "",
        stderr: str = "",
        env: dict[str, str] | None = None,
        env_inheritance: bool = False,
    ) -> models.sliverpb.Execute:
        """Execute a command/subprocess on the remote system

        :param exe: Command/subprocess to execute
        :type exe: str
        :param args: Arguments to the command/subprocess
        :type args: List[str]
        :param output: Enable capturing command/subprocess stdout
        :type output: bool
        :param background: Track the process in the background, defaults to False
        :type background: bool, optional
        :param stdout: Remote path to redirect stdout to, defaults to ""
        :type stdout: str, optional
        :param stderr: Remote path to redirect stderr to, defaults to ""
        :type stderr: str, optional
        :param env: Environment variables for the child process
        :type env: dict[str, str] | None, optional
        :param env_inheritance: Inherit the implant's environment, defaults to False
        :type env_inheritance: bool, optional
        :return: Pydantic execution-result model
        :rtype: models.sliverpb.Execute
        """
        execute_req = models.sliverpb.ExecuteReq(
            path=exe,
            args=args or [],
            output=output,
            background=background,
            stdout=stdout,
            stderr=stderr,
            env=dict(env or {}),
            env_inheritance=env_inheritance,
        )
        return await self._execute(
            "Execute", self._request(execute_req), models.sliverpb.Execute
        )

    async def execute_children(
        self: InteractiveObject,
    ) -> models.sliverpb.ExecuteChildren:
        """List processes tracked by background ``execute`` commands.

        :return: Pydantic tracked-child inventory
        :rtype: models.sliverpb.ExecuteChildren
        """
        return await self._execute(
            "ExecuteChildren",
            self._request(models.sliverpb.ExecuteChildrenReq()),
            models.sliverpb.ExecuteChildren,
        )

    async def sideload(
        self: InteractiveObject,
        data: bytes,
        process_name: str,
        arguments: list[str],
        entry_point: str,
        kill: bool,
    ) -> models.sliverpb.Sideload:
        """Sideload a shared library using the platform's in-memory loader.

        :param data: Shared library raw bytes
        :type data: bytes
        :param process_name: Process name to sideload library into
        :type process_name: str
        :param arguments: Arguments to the shared library
        :type arguments: list[str]
        :param entry_point: Entrypoint of the shared library
        :type entry_point: str
        :param kill: Kill normal execution after sideloading the shared library
        :type kill: bool
        :return: Pydantic sideload-result model
        :rtype: models.sliverpb.Sideload
        """
        side = models.sliverpb.SideloadReq(
            data=data,
            process_name=process_name,
            args=arguments,
            entry_point=entry_point,
            kill=kill,
        )
        return await self._execute(
            "Sideload", self._request(side), models.sliverpb.Sideload
        )

    async def spawndll(
        self: InteractiveObject,
        data: bytes,
        *,
        process_name: str = r"c:\windows\system32\notepad.exe",
        arguments: list[str] | None = None,
        entry_point: str = "ReflectiveLoader",
        keep_alive: bool = False,
        parent_pid: int = 0,
        process_arguments: list[str] | None = None,
    ) -> models.sliverpb.SpawnDll:
        """Spawn a DLL from memory, matching Sliver's ``spawndll`` command.

        :param data: DLL raw bytes
        :type data: bytes
        :param process_name: Process name to spawn DLL into
        :type process_name: str
        :param arguments: Arguments to the DLL
        :type arguments: list[str]
        :param entry_point: Entrypoint of the DLL
        :type entry_point: str
        :param keep_alive: Keep the hosting process alive after execution
        :type keep_alive: bool
        :param parent_pid: Optional parent process ID for the host process
        :type parent_pid: int
        :param process_arguments: Arguments passed to the hosting process
        :type process_arguments: list[str]
        :return: Pydantic DLL-execution result model
        :rtype: models.sliverpb.SpawnDll
        """
        spawn = models.sliverpb.InvokeSpawnDllReq(
            data=data,
            process_name=process_name,
            args=arguments or [],
            entry_point=entry_point,
            kill=not keep_alive,
            p_pid=parent_pid,
            process_args=process_arguments or [],
        )
        return await self._execute(
            "SpawnDll", self._request(spawn), models.sliverpb.SpawnDll
        )

    async def spawn_dll(
        self: BaseInteractiveCommands,
        data: bytes,
        process_name: str,
        arguments: list[str],
        entry_point: str,
        kill: bool,
    ) -> models.sliverpb.SpawnDll:
        """Compatibility alias for :meth:`spawndll`."""

        return await self.spawndll(
            data,
            process_name=process_name,
            arguments=arguments,
            entry_point=entry_point,
            keep_alive=not kill,
        )

    async def list_extensions(
        self: InteractiveObject,
    ) -> models.sliverpb.ListExtensions:
        """List extensions

        :return: Pydantic extension-list model
        :rtype: models.sliverpb.ListExtensions
        """
        listex = models.sliverpb.ListExtensionsReq()
        return await self._execute(
            "ListExtensions",
            self._request(listex),
            models.sliverpb.ListExtensions,
        )

    async def register_extension(
        self: InteractiveObject,
        name: str,
        data: bytes,
        goos: GOOS | str,
        init: str,
    ) -> models.sliverpb.RegisterExtension:
        """Call an extension

        :param name: Extension name
        :type name: str
        :param data: Extension binary data
        :type data: bytes
        :param goos: OS
        :type goos: GOOS | str
        :param init: Init entrypoint to run
        :type init: str
        :return: Pydantic extension-registration result model
        :rtype: models.sliverpb.RegisterExtension
        """
        regext = models.sliverpb.RegisterExtensionReq(
            name=name,
            data=data,
            os=str(goos),
            init=init,
        )
        return await self._execute(
            "RegisterExtension",
            self._request(regext),
            models.sliverpb.RegisterExtension,
        )

    async def call_extension(
        self: InteractiveObject,
        name: str,
        export: str,
        ext_args: bytes,
    ) -> models.sliverpb.CallExtension:
        """Call an extension

        :param name: Extension name
        :type name: str
        :param export: Extension entrypoint
        :type export: str
        :param ext_args: Extension argument buffer
        :type ext_args: bytes
        :return: Pydantic extension-result model
        :rtype: models.sliverpb.CallExtension
        """
        callex = models.sliverpb.CallExtensionReq(
            name=name,
            export=export,
            args=ext_args,
        )
        return await self._execute(
            "CallExtension",
            self._request(callex),
            models.sliverpb.CallExtension,
        )

    async def wasm_ls(
        self: InteractiveObject,
    ) -> models.sliverpb.ListWasmExtensions:
        """List registered Wasm extensions, matching Sliver's ``wasm ls`` command.

        :return: Pydantic Wasm-extension inventory
        :rtype: models.sliverpb.ListWasmExtensions
        """
        return await self._execute(
            "ListWasmExtensions",
            self._request(models.sliverpb.ListWasmExtensionsReq()),
            models.sliverpb.ListWasmExtensions,
        )

    async def wasm_list(
        self: BaseInteractiveCommands,
    ) -> models.sliverpb.ListWasmExtensions:
        """Compatibility alias for :meth:`wasm_ls`."""

        return await self.wasm_ls()

    async def screenshot(self: InteractiveObject) -> models.sliverpb.Screenshot:
        """Take a screenshot of the remote system, screenshot data is PNG formatted

        :return: Pydantic screenshot model
        :rtype: models.sliverpb.Screenshot
        """
        return await self._execute(
            "Screenshot",
            self._request(models.sliverpb.ScreenshotReq()),
            models.sliverpb.Screenshot,
        )

    async def make_token(
        self: InteractiveObject,
        username: str,
        password: str,
        domain: str = ".",
        *,
        logon_type: LogonType = LogonType.NEW_CREDENTIALS,
    ) -> models.sliverpb.MakeToken:
        """Make a Windows user token from a valid login (Windows only)

        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        :param domain: Domain
        :type domain: str
        :param logon_type: Windows logon type, defaults to new credentials
        :type logon_type: LogonType
        :return: Pydantic token-creation result model
        :rtype: models.sliverpb.MakeToken
        """
        make = models.sliverpb.MakeTokenReq(
            username=username,
            password=password,
            domain=domain,
            logon_type=int(logon_type),
        )
        return await self._execute(
            "MakeToken", self._request(make), models.sliverpb.MakeToken
        )

    async def env(self: InteractiveObject, name: str = "") -> models.sliverpb.EnvInfo:
        """Get an environment variable

        :param name: Name of the variable
        :type name: str
        :return: Pydantic environment-variable model
        :rtype: models.sliverpb.EnvInfo
        """
        env = models.sliverpb.EnvReq(name=name)
        return await self._execute(
            "GetEnv", self._request(env), models.sliverpb.EnvInfo
        )

    async def get_env(
        self: BaseInteractiveCommands, name: str
    ) -> models.sliverpb.EnvInfo:
        """Compatibility alias for :meth:`env`."""

        return await self.env(name)

    async def set_env(
        self: InteractiveObject, key: str, value: str
    ) -> models.sliverpb.SetEnv:
        """Set an environment variable

        :param key: Name of the environment variable
        :type key: str
        :param value: Value of the environment variable
        :type value: str
        :return: Pydantic environment-update result model
        :rtype: models.sliverpb.SetEnv
        """
        env_var = models.commonpb.EnvVar(key=key, value=value)
        env_req = models.sliverpb.SetEnvReq(variable=env_var)
        return await self._execute(
            "SetEnv", self._request(env_req), models.sliverpb.SetEnv
        )

    async def env_set(
        self: BaseInteractiveCommands, key: str, value: str
    ) -> models.sliverpb.SetEnv:
        """Set a variable, matching Sliver's ``env set`` command."""

        return await self.set_env(key, value)

    async def unset_env(self: InteractiveObject, key: str) -> models.sliverpb.UnsetEnv:
        """Unset an environment variable

        :param key: Name of the environment variable
        :type key: str
        :return: Pydantic environment-update result model
        :rtype: models.sliverpb.UnsetEnv
        """
        env = models.sliverpb.UnsetEnvReq(name=key)
        return await self._execute(
            "UnsetEnv", self._request(env), models.sliverpb.UnsetEnv
        )

    async def env_unset(
        self: BaseInteractiveCommands, key: str
    ) -> models.sliverpb.UnsetEnv:
        """Unset a variable, matching Sliver's ``env unset`` command."""

        return await self.unset_env(key)

    async def registry_read(
        self: InteractiveObject,
        hive: RegistryHive | str,
        reg_path: str,
        key: str,
        hostname: str,
    ) -> models.sliverpb.RegistryRead:
        """Read a value from the remote system's registry (Windows only)

        :param hive: Registry hive to read value from
        :type hive: RegistryHive | str
        :param reg_path: Path to registry key to read
        :type reg_path: str
        :param key: Key name to read
        :type key: str
        :param hostname: Hostname
        :type hostname: str
        :return: Pydantic registry-read result model
        :rtype: models.sliverpb.RegistryRead
        """
        reg = models.sliverpb.RegistryReadReq(
            hive=str(hive), path=reg_path, key=key, hostname=hostname
        )
        return await self._execute(
            "RegistryRead", self._request(reg), models.sliverpb.RegistryRead
        )

    async def registry_write(
        self: InteractiveObject,
        hive: RegistryHive | str,
        reg_path: str,
        key: str,
        hostname: str,
        string_value: str,
        byte_value: bytes,
        dword_value: int,
        qword_value: int,
        reg_type: models.sliverpb.RegistryType,
    ) -> models.sliverpb.RegistryWrite:
        """Write a value to the remote system's registry (Windows only)

        :param hive: Registry hive to write the key/value to
        :type hive: RegistryHive | str
        :param reg_path: Registry path to write to
        :type reg_path: str
        :param key: Registry key to write to
        :type key: str
        :param hostname: Hostname
        :type hostname: str
        :param string_value: String value to write (ignored for non-string key)
        :type string_value: str
        :param byte_value: Byte value to write (ignored for non-byte key)
        :type byte_value: bytes
        :param dword_value: DWORD value to write (ignored for non-DWORD key)
        :type dword_value: int
        :param qword_value: QWORD value to write (ignored for non-QWORD key)
        :type qword_value: int
        :param reg_type: Type of registry key to write
        :type reg_type: models.sliverpb.RegistryType
        :return: Pydantic registry-write result model
        :rtype: models.sliverpb.RegistryWrite
        """
        reg = models.sliverpb.RegistryWriteReq(
            hive=str(hive),
            path=reg_path,
            key=key,
            hostname=hostname,
            string_value=string_value,
            byte_value=byte_value,
            d_word_value=dword_value,
            q_word_value=qword_value,
            type=int(reg_type),
        )

        return await self._execute(
            "RegistryWrite", self._request(reg), models.sliverpb.RegistryWrite
        )

    async def registry_create(
        self: BaseInteractiveCommands,
        path: str,
        *,
        hive: RegistryHive | str = RegistryHive.CURRENT_USER,
        hostname: str = "",
    ) -> models.sliverpb.RegistryCreateKey:
        """Create a key, matching Sliver's ``registry create`` command.

        :param hive: Registry hive to create key in
        :type hive: RegistryHive | str
        :param path: Full registry path including the key to create
        :type path: str
        :param hostname: Hostname
        :type hostname: str
        :return: Pydantic registry-create result model
        :rtype: models.sliverpb.RegistryCreateKey
        """
        normalized = path.strip().replace("/", "\\")
        reg_path, separator, key = normalized.rpartition("\\")
        if not separator or not reg_path or not key:
            raise ValueError("path must include a parent path and key name")
        return await self.registry_create_key(hive, reg_path, key, hostname)

    async def registry_create_key(
        self: BaseInteractiveCommands,
        hive: RegistryHive | str,
        reg_path: str,
        key: str,
        hostname: str,
    ) -> models.sliverpb.RegistryCreateKey:
        """Create a registry key using the historical split-path arguments."""

        reg = models.sliverpb.RegistryCreateKeyReq(
            hive=str(hive), path=reg_path, key=key, hostname=hostname
        )
        return await self._execute(
            "RegistryCreateKey",
            self._request(reg),
            models.sliverpb.RegistryCreateKey,
        )
