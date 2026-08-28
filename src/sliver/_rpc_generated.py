"""Generated Pydantic RPC declarations. Do not edit manually."""

from __future__ import annotations

from ._pb.rpcpb.services_pb2_grpc import (
    SliverRPCStub as _WireSliverRPCStub,
)
from ._rpc_base import (
    StreamStreamMultiCallable,
    StreamUnaryMultiCallable,
    UnaryStreamMultiCallable,
    UnaryUnaryMultiCallable,
)
from .models import clientpb, commonpb, sliverpb


class GeneratedPydanticSliverRPCStub:
    """Concrete Pydantic method declarations generated from SliverRPC."""

    GetVersion: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Version]
    ClientLog: StreamUnaryMultiCallable[clientpb.ClientLogData, commonpb.Empty]
    GetOperators: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Operators]
    Kill: UnaryUnaryMultiCallable[sliverpb.KillReq, commonpb.Empty]
    Reconfigure: UnaryUnaryMultiCallable[sliverpb.ReconfigureReq, sliverpb.Reconfigure]
    Rename: UnaryUnaryMultiCallable[clientpb.RenameReq, commonpb.Empty]
    GetSessions: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Sessions]
    MonitorStart: UnaryUnaryMultiCallable[commonpb.Empty, commonpb.Response]
    MonitorStop: UnaryUnaryMultiCallable[commonpb.Empty, commonpb.Empty]
    MonitorListConfig: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.MonitoringProviders
    ]
    MonitorAddConfig: UnaryUnaryMultiCallable[
        clientpb.MonitoringProvider, commonpb.Response
    ]
    MonitorDelConfig: UnaryUnaryMultiCallable[
        clientpb.MonitoringProvider, commonpb.Response
    ]
    GetAIProviders: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AIProviderConfigs]
    GetAIConversations: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.AIConversations
    ]
    GetAIConversation: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, clientpb.AIConversation
    ]
    SaveAIConversation: UnaryUnaryMultiCallable[
        clientpb.AIConversation, clientpb.AIConversation
    ]
    DeleteAIConversation: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, commonpb.Empty
    ]
    GetAIConversationMessages: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, clientpb.AIConversationMessages
    ]
    SaveAIConversationMessage: UnaryUnaryMultiCallable[
        clientpb.AIConversationMessage, clientpb.AIConversationMessage
    ]
    StartMTLSListener: UnaryUnaryMultiCallable[
        clientpb.MTLSListenerReq, clientpb.ListenerJob
    ]
    StartWGListener: UnaryUnaryMultiCallable[
        clientpb.WGListenerReq, clientpb.ListenerJob
    ]
    StartDNSListener: UnaryUnaryMultiCallable[
        clientpb.DNSListenerReq, clientpb.ListenerJob
    ]
    StartHTTPSListener: UnaryUnaryMultiCallable[
        clientpb.HTTPListenerReq, clientpb.ListenerJob
    ]
    StartHTTPListener: UnaryUnaryMultiCallable[
        clientpb.HTTPListenerReq, clientpb.ListenerJob
    ]
    GetBeacons: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Beacons]
    GetBeacon: UnaryUnaryMultiCallable[clientpb.Beacon, clientpb.Beacon]
    RmBeacon: UnaryUnaryMultiCallable[clientpb.Beacon, commonpb.Empty]
    GetBeaconTasks: UnaryUnaryMultiCallable[clientpb.Beacon, clientpb.BeaconTasks]
    GetBeaconTaskContent: UnaryUnaryMultiCallable[
        clientpb.BeaconTask, clientpb.BeaconTask
    ]
    CancelBeaconTask: UnaryUnaryMultiCallable[clientpb.BeaconTask, clientpb.BeaconTask]
    UpdateBeaconIntegrityInformation: UnaryUnaryMultiCallable[
        clientpb.BeaconIntegrity, commonpb.Empty
    ]
    GetJobs: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Jobs]
    KillJob: UnaryUnaryMultiCallable[clientpb.KillJobReq, clientpb.KillJob]
    RestartJobs: UnaryUnaryMultiCallable[clientpb.RestartJobReq, commonpb.Empty]
    StartTCPStagerListener: UnaryUnaryMultiCallable[
        clientpb.StagerListenerReq, clientpb.StagerListener
    ]
    LootAdd: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    LootRm: UnaryUnaryMultiCallable[clientpb.Loot, commonpb.Empty]
    LootUpdate: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    LootContent: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    LootAll: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AllLoot]
    Creds: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Credentials]
    CredsAdd: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    CredsRm: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    CredsUpdate: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    GetCredByID: UnaryUnaryMultiCallable[clientpb.Credential, clientpb.Credential]
    GetCredsByHashType: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credentials
    ]
    GetPlaintextCredsByHashType: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credentials
    ]
    CredsSniffHashType: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credential
    ]
    Hosts: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AllHosts]
    Host: UnaryUnaryMultiCallable[clientpb.Host, clientpb.Host]
    HostRm: UnaryUnaryMultiCallable[clientpb.Host, commonpb.Empty]
    HostIOCRm: UnaryUnaryMultiCallable[clientpb.IOC, commonpb.Empty]
    Generate: UnaryUnaryMultiCallable[clientpb.GenerateReq, clientpb.Generate]
    GenerateSpoofMetadata: UnaryUnaryMultiCallable[
        clientpb.GenerateSpoofMetadataReq, commonpb.Empty
    ]
    GenerateExternal: UnaryUnaryMultiCallable[
        clientpb.ExternalGenerateReq, clientpb.ExternalImplantConfig
    ]
    GenerateExternalSaveBuild: UnaryUnaryMultiCallable[
        clientpb.ExternalImplantBinary, commonpb.Empty
    ]
    GenerateExternalGetBuildConfig: UnaryUnaryMultiCallable[
        clientpb.ImplantBuild, clientpb.ExternalImplantConfig
    ]
    GenerateStage: UnaryUnaryMultiCallable[clientpb.GenerateStageReq, clientpb.Generate]
    StageImplantBuild: UnaryUnaryMultiCallable[clientpb.ImplantStageReq, commonpb.Empty]
    GetHTTPC2Profiles: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.HTTPC2Configs]
    GetHTTPC2ProfileByName: UnaryUnaryMultiCallable[
        clientpb.C2ProfileReq, clientpb.HTTPC2Config
    ]
    SaveHTTPC2Profile: UnaryUnaryMultiCallable[clientpb.HTTPC2ConfigReq, commonpb.Empty]
    BuilderRegister: UnaryStreamMultiCallable[clientpb.Builder, clientpb.Event]
    BuilderTrigger: UnaryUnaryMultiCallable[clientpb.Event, commonpb.Empty]
    Builders: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Builders]
    GetCertificateInfo: UnaryUnaryMultiCallable[
        clientpb.CertificatesReq, clientpb.CertificateInfo
    ]
    GetCertificateAuthorityInfo: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.CertificateAuthorityInfo
    ]
    Crack: UnaryUnaryMultiCallable[clientpb.CrackCommand, clientpb.CrackResponse]
    CrackstationRegister: UnaryStreamMultiCallable[
        clientpb.Crackstation, clientpb.Event
    ]
    CrackstationTrigger: UnaryUnaryMultiCallable[clientpb.Event, commonpb.Empty]
    CrackstationBenchmark: UnaryUnaryMultiCallable[
        clientpb.CrackBenchmark, commonpb.Empty
    ]
    Crackstations: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Crackstations]
    CrackTaskByID: UnaryUnaryMultiCallable[clientpb.CrackTask, clientpb.CrackTask]
    CrackTaskUpdate: UnaryUnaryMultiCallable[clientpb.CrackTask, commonpb.Empty]
    CrackFilesList: UnaryUnaryMultiCallable[clientpb.CrackFile, clientpb.CrackFiles]
    CrackFileCreate: UnaryUnaryMultiCallable[clientpb.CrackFile, clientpb.CrackFile]
    CrackFileChunkUpload: UnaryUnaryMultiCallable[
        clientpb.CrackFileChunk, commonpb.Empty
    ]
    CrackFileChunkDownload: UnaryUnaryMultiCallable[
        clientpb.CrackFileChunk, clientpb.CrackFileChunk
    ]
    CrackFileComplete: UnaryUnaryMultiCallable[clientpb.CrackFile, commonpb.Empty]
    CrackFileDelete: UnaryUnaryMultiCallable[clientpb.CrackFile, commonpb.Empty]
    Regenerate: UnaryUnaryMultiCallable[clientpb.RegenerateReq, clientpb.Generate]
    ImplantBuilds: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.ImplantBuilds]
    DeleteImplantBuild: UnaryUnaryMultiCallable[clientpb.DeleteReq, commonpb.Empty]
    Canaries: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Canaries]
    GenerateWGClientConfig: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.WGClientConfig
    ]
    GenerateUniqueIP: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.UniqueWGIP]
    ImplantProfiles: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.ImplantProfiles]
    DeleteImplantProfile: UnaryUnaryMultiCallable[clientpb.DeleteReq, commonpb.Empty]
    SaveImplantProfile: UnaryUnaryMultiCallable[
        clientpb.ImplantProfile, clientpb.ImplantProfile
    ]
    ShellcodeRDI: UnaryUnaryMultiCallable[
        clientpb.ShellcodeRDIReq, clientpb.ShellcodeRDI
    ]
    GetCompiler: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Compiler]
    ShellcodeEncoder: UnaryUnaryMultiCallable[
        clientpb.ShellcodeEncodeReq, clientpb.ShellcodeEncode
    ]
    ShellcodeEncoderMap: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.ShellcodeEncoderMap
    ]
    TrafficEncoderMap: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.TrafficEncoderMap
    ]
    TrafficEncoderAdd: UnaryUnaryMultiCallable[
        clientpb.TrafficEncoder, clientpb.TrafficEncoderTests
    ]
    TrafficEncoderRm: UnaryUnaryMultiCallable[clientpb.TrafficEncoder, commonpb.Empty]
    Websites: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Websites]
    Website: UnaryUnaryMultiCallable[clientpb.Website, clientpb.Website]
    WebsiteRemove: UnaryUnaryMultiCallable[clientpb.Website, commonpb.Empty]
    WebsiteAddContent: UnaryUnaryMultiCallable[
        clientpb.WebsiteAddContent, clientpb.Website
    ]
    WebsiteUpdateContent: UnaryUnaryMultiCallable[
        clientpb.WebsiteAddContent, clientpb.Website
    ]
    WebsiteRemoveContent: UnaryUnaryMultiCallable[
        clientpb.WebsiteRemoveContent, clientpb.Website
    ]
    Ping: UnaryUnaryMultiCallable[sliverpb.Ping, sliverpb.Ping]
    Ps: UnaryUnaryMultiCallable[sliverpb.PsReq, sliverpb.Ps]
    Terminate: UnaryUnaryMultiCallable[sliverpb.TerminateReq, sliverpb.Terminate]
    Ifconfig: UnaryUnaryMultiCallable[sliverpb.IfconfigReq, sliverpb.Ifconfig]
    Netstat: UnaryUnaryMultiCallable[sliverpb.NetstatReq, sliverpb.Netstat]
    Ls: UnaryUnaryMultiCallable[sliverpb.LsReq, sliverpb.Ls]
    Cd: UnaryUnaryMultiCallable[sliverpb.CdReq, sliverpb.Pwd]
    Pwd: UnaryUnaryMultiCallable[sliverpb.PwdReq, sliverpb.Pwd]
    Mv: UnaryUnaryMultiCallable[sliverpb.MvReq, sliverpb.Mv]
    Cp: UnaryUnaryMultiCallable[sliverpb.CpReq, sliverpb.Cp]
    Rm: UnaryUnaryMultiCallable[sliverpb.RmReq, sliverpb.Rm]
    Mkdir: UnaryUnaryMultiCallable[sliverpb.MkdirReq, sliverpb.Mkdir]
    Download: UnaryUnaryMultiCallable[sliverpb.DownloadReq, sliverpb.Download]
    Upload: UnaryUnaryMultiCallable[sliverpb.UploadReq, sliverpb.Upload]
    Grep: UnaryUnaryMultiCallable[sliverpb.GrepReq, sliverpb.Grep]
    Chmod: UnaryUnaryMultiCallable[sliverpb.ChmodReq, sliverpb.Chmod]
    Chown: UnaryUnaryMultiCallable[sliverpb.ChownReq, sliverpb.Chown]
    Chtimes: UnaryUnaryMultiCallable[sliverpb.ChtimesReq, sliverpb.Chtimes]
    MemfilesList: UnaryUnaryMultiCallable[sliverpb.MemfilesListReq, sliverpb.Ls]
    MemfilesAdd: UnaryUnaryMultiCallable[sliverpb.MemfilesAddReq, sliverpb.MemfilesAdd]
    MemfilesRm: UnaryUnaryMultiCallable[sliverpb.MemfilesRmReq, sliverpb.MemfilesRm]
    Mount: UnaryUnaryMultiCallable[sliverpb.MountReq, sliverpb.Mount]
    ProcessDump: UnaryUnaryMultiCallable[sliverpb.ProcessDumpReq, sliverpb.ProcessDump]
    RunAs: UnaryUnaryMultiCallable[sliverpb.RunAsReq, sliverpb.RunAs]
    Impersonate: UnaryUnaryMultiCallable[sliverpb.ImpersonateReq, sliverpb.Impersonate]
    RevToSelf: UnaryUnaryMultiCallable[sliverpb.RevToSelfReq, sliverpb.RevToSelf]
    GetSystem: UnaryUnaryMultiCallable[clientpb.GetSystemReq, sliverpb.GetSystem]
    Task: UnaryUnaryMultiCallable[sliverpb.TaskReq, sliverpb.Task]
    Msf: UnaryUnaryMultiCallable[clientpb.MSFReq, sliverpb.Task]
    MsfRemote: UnaryUnaryMultiCallable[clientpb.MSFRemoteReq, sliverpb.Task]
    ExecuteAssembly: UnaryUnaryMultiCallable[
        sliverpb.ExecuteAssemblyReq, sliverpb.ExecuteAssembly
    ]
    Migrate: UnaryUnaryMultiCallable[clientpb.MigrateReq, sliverpb.Migrate]
    Execute: UnaryUnaryMultiCallable[sliverpb.ExecuteReq, sliverpb.Execute]
    ExecuteWindows: UnaryUnaryMultiCallable[
        sliverpb.ExecuteWindowsReq, sliverpb.Execute
    ]
    ExecuteChildren: UnaryUnaryMultiCallable[
        sliverpb.ExecuteChildrenReq, sliverpb.ExecuteChildren
    ]
    Sideload: UnaryUnaryMultiCallable[sliverpb.SideloadReq, sliverpb.Sideload]
    SpawnDll: UnaryUnaryMultiCallable[sliverpb.InvokeSpawnDllReq, sliverpb.SpawnDll]
    Screenshot: UnaryUnaryMultiCallable[sliverpb.ScreenshotReq, sliverpb.Screenshot]
    CurrentTokenOwner: UnaryUnaryMultiCallable[
        sliverpb.CurrentTokenOwnerReq, sliverpb.CurrentTokenOwner
    ]
    Services: UnaryUnaryMultiCallable[sliverpb.ServicesReq, sliverpb.Services]
    ServiceDetail: UnaryUnaryMultiCallable[
        sliverpb.ServiceDetailReq, sliverpb.ServiceDetail
    ]
    StartServiceByName: UnaryUnaryMultiCallable[
        sliverpb.StartServiceByNameReq, sliverpb.ServiceInfo
    ]
    PivotStartListener: UnaryUnaryMultiCallable[
        sliverpb.PivotStartListenerReq, sliverpb.PivotListener
    ]
    PivotStopListener: UnaryUnaryMultiCallable[
        sliverpb.PivotStopListenerReq, commonpb.Empty
    ]
    PivotSessionListeners: UnaryUnaryMultiCallable[
        sliverpb.PivotListenersReq, sliverpb.PivotListeners
    ]
    PivotGraph: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.PivotGraph]
    StartService: UnaryUnaryMultiCallable[
        sliverpb.StartServiceReq, sliverpb.ServiceInfo
    ]
    StopService: UnaryUnaryMultiCallable[sliverpb.StopServiceReq, sliverpb.ServiceInfo]
    RemoveService: UnaryUnaryMultiCallable[
        sliverpb.RemoveServiceReq, sliverpb.ServiceInfo
    ]
    MakeToken: UnaryUnaryMultiCallable[sliverpb.MakeTokenReq, sliverpb.MakeToken]
    GetEnv: UnaryUnaryMultiCallable[sliverpb.EnvReq, sliverpb.EnvInfo]
    SetEnv: UnaryUnaryMultiCallable[sliverpb.SetEnvReq, sliverpb.SetEnv]
    UnsetEnv: UnaryUnaryMultiCallable[sliverpb.UnsetEnvReq, sliverpb.UnsetEnv]
    Backdoor: UnaryUnaryMultiCallable[clientpb.BackdoorReq, clientpb.Backdoor]
    RegistryRead: UnaryUnaryMultiCallable[
        sliverpb.RegistryReadReq, sliverpb.RegistryRead
    ]
    RegistryWrite: UnaryUnaryMultiCallable[
        sliverpb.RegistryWriteReq, sliverpb.RegistryWrite
    ]
    RegistryCreateKey: UnaryUnaryMultiCallable[
        sliverpb.RegistryCreateKeyReq, sliverpb.RegistryCreateKey
    ]
    RegistryDeleteKey: UnaryUnaryMultiCallable[
        sliverpb.RegistryDeleteKeyReq, sliverpb.RegistryDeleteKey
    ]
    RegistryListSubKeys: UnaryUnaryMultiCallable[
        sliverpb.RegistrySubKeyListReq, sliverpb.RegistrySubKeyList
    ]
    RegistryListValues: UnaryUnaryMultiCallable[
        sliverpb.RegistryListValuesReq, sliverpb.RegistryValuesList
    ]
    RegistryReadHive: UnaryUnaryMultiCallable[
        sliverpb.RegistryReadHiveReq, sliverpb.RegistryReadHive
    ]
    RunSSHCommand: UnaryUnaryMultiCallable[sliverpb.SSHCommandReq, sliverpb.SSHCommand]
    HijackDLL: UnaryUnaryMultiCallable[clientpb.DllHijackReq, clientpb.DllHijack]
    GetPrivs: UnaryUnaryMultiCallable[sliverpb.GetPrivsReq, sliverpb.GetPrivs]
    StartRportFwdListener: UnaryUnaryMultiCallable[
        sliverpb.RportFwdStartListenerReq, sliverpb.RportFwdListener
    ]
    GetRportFwdListeners: UnaryUnaryMultiCallable[
        sliverpb.RportFwdListenersReq, sliverpb.RportFwdListeners
    ]
    StopRportFwdListener: UnaryUnaryMultiCallable[
        sliverpb.RportFwdStopListenerReq, sliverpb.RportFwdListener
    ]
    OpenSession: UnaryUnaryMultiCallable[sliverpb.OpenSession, sliverpb.OpenSession]
    CloseSession: UnaryUnaryMultiCallable[sliverpb.CloseSession, commonpb.Empty]
    RegisterExtension: UnaryUnaryMultiCallable[
        sliverpb.RegisterExtensionReq, sliverpb.RegisterExtension
    ]
    CallExtension: UnaryUnaryMultiCallable[
        sliverpb.CallExtensionReq, sliverpb.CallExtension
    ]
    ListExtensions: UnaryUnaryMultiCallable[
        sliverpb.ListExtensionsReq, sliverpb.ListExtensions
    ]
    RegisterWasmExtension: UnaryUnaryMultiCallable[
        sliverpb.RegisterWasmExtensionReq, sliverpb.RegisterWasmExtension
    ]
    ListWasmExtensions: UnaryUnaryMultiCallable[
        sliverpb.ListWasmExtensionsReq, sliverpb.ListWasmExtensions
    ]
    ExecWasmExtension: UnaryUnaryMultiCallable[
        sliverpb.ExecWasmExtensionReq, sliverpb.ExecWasmExtension
    ]
    WGStartPortForward: UnaryUnaryMultiCallable[
        sliverpb.WGPortForwardStartReq, sliverpb.WGPortForward
    ]
    WGStopPortForward: UnaryUnaryMultiCallable[
        sliverpb.WGPortForwardStopReq, sliverpb.WGPortForward
    ]
    WGStartSocks: UnaryUnaryMultiCallable[sliverpb.WGSocksStartReq, sliverpb.WGSocks]
    WGStopSocks: UnaryUnaryMultiCallable[sliverpb.WGSocksStopReq, sliverpb.WGSocks]
    WGListForwarders: UnaryUnaryMultiCallable[
        sliverpb.WGTCPForwardersReq, sliverpb.WGTCPForwarders
    ]
    WGListSocksServers: UnaryUnaryMultiCallable[
        sliverpb.WGSocksServersReq, sliverpb.WGSocksServers
    ]
    Shell: UnaryUnaryMultiCallable[sliverpb.ShellReq, sliverpb.Shell]
    ShellResize: UnaryUnaryMultiCallable[sliverpb.ShellResizeReq, commonpb.Empty]
    Portfwd: UnaryUnaryMultiCallable[sliverpb.PortfwdReq, sliverpb.Portfwd]
    CreateSocks: UnaryUnaryMultiCallable[sliverpb.Socks, sliverpb.Socks]
    CloseSocks: UnaryUnaryMultiCallable[sliverpb.Socks, commonpb.Empty]
    SocksProxy: StreamStreamMultiCallable[sliverpb.SocksData, sliverpb.SocksData]
    CreateTunnel: UnaryUnaryMultiCallable[sliverpb.Tunnel, sliverpb.Tunnel]
    CloseTunnel: UnaryUnaryMultiCallable[sliverpb.Tunnel, commonpb.Empty]
    TunnelData: StreamStreamMultiCallable[sliverpb.TunnelData, sliverpb.TunnelData]
    Events: UnaryStreamMultiCallable[commonpb.Empty, clientpb.Event]

    def _initialize_rpc_methods(self, raw: _WireSliverRPCStub) -> None:
        self.GetVersion = UnaryUnaryMultiCallable(
            raw.GetVersion,
            commonpb.Empty,
            clientpb.Version,
        )
        self.ClientLog = StreamUnaryMultiCallable(
            raw.ClientLog,
            clientpb.ClientLogData,
            commonpb.Empty,
        )
        self.GetOperators = UnaryUnaryMultiCallable(
            raw.GetOperators,
            commonpb.Empty,
            clientpb.Operators,
        )
        self.Kill = UnaryUnaryMultiCallable(
            raw.Kill,
            sliverpb.KillReq,
            commonpb.Empty,
        )
        self.Reconfigure = UnaryUnaryMultiCallable(
            raw.Reconfigure,
            sliverpb.ReconfigureReq,
            sliverpb.Reconfigure,
        )
        self.Rename = UnaryUnaryMultiCallable(
            raw.Rename,
            clientpb.RenameReq,
            commonpb.Empty,
        )
        self.GetSessions = UnaryUnaryMultiCallable(
            raw.GetSessions,
            commonpb.Empty,
            clientpb.Sessions,
        )
        self.MonitorStart = UnaryUnaryMultiCallable(
            raw.MonitorStart,
            commonpb.Empty,
            commonpb.Response,
        )
        self.MonitorStop = UnaryUnaryMultiCallable(
            raw.MonitorStop,
            commonpb.Empty,
            commonpb.Empty,
        )
        self.MonitorListConfig = UnaryUnaryMultiCallable(
            raw.MonitorListConfig,
            commonpb.Empty,
            clientpb.MonitoringProviders,
        )
        self.MonitorAddConfig = UnaryUnaryMultiCallable(
            raw.MonitorAddConfig,
            clientpb.MonitoringProvider,
            commonpb.Response,
        )
        self.MonitorDelConfig = UnaryUnaryMultiCallable(
            raw.MonitorDelConfig,
            clientpb.MonitoringProvider,
            commonpb.Response,
        )
        self.GetAIProviders = UnaryUnaryMultiCallable(
            raw.GetAIProviders,
            commonpb.Empty,
            clientpb.AIProviderConfigs,
        )
        self.GetAIConversations = UnaryUnaryMultiCallable(
            raw.GetAIConversations,
            commonpb.Empty,
            clientpb.AIConversations,
        )
        self.GetAIConversation = UnaryUnaryMultiCallable(
            raw.GetAIConversation,
            clientpb.AIConversationReq,
            clientpb.AIConversation,
        )
        self.SaveAIConversation = UnaryUnaryMultiCallable(
            raw.SaveAIConversation,
            clientpb.AIConversation,
            clientpb.AIConversation,
        )
        self.DeleteAIConversation = UnaryUnaryMultiCallable(
            raw.DeleteAIConversation,
            clientpb.AIConversationReq,
            commonpb.Empty,
        )
        self.GetAIConversationMessages = UnaryUnaryMultiCallable(
            raw.GetAIConversationMessages,
            clientpb.AIConversationReq,
            clientpb.AIConversationMessages,
        )
        self.SaveAIConversationMessage = UnaryUnaryMultiCallable(
            raw.SaveAIConversationMessage,
            clientpb.AIConversationMessage,
            clientpb.AIConversationMessage,
        )
        self.StartMTLSListener = UnaryUnaryMultiCallable(
            raw.StartMTLSListener,
            clientpb.MTLSListenerReq,
            clientpb.ListenerJob,
        )
        self.StartWGListener = UnaryUnaryMultiCallable(
            raw.StartWGListener,
            clientpb.WGListenerReq,
            clientpb.ListenerJob,
        )
        self.StartDNSListener = UnaryUnaryMultiCallable(
            raw.StartDNSListener,
            clientpb.DNSListenerReq,
            clientpb.ListenerJob,
        )
        self.StartHTTPSListener = UnaryUnaryMultiCallable(
            raw.StartHTTPSListener,
            clientpb.HTTPListenerReq,
            clientpb.ListenerJob,
        )
        self.StartHTTPListener = UnaryUnaryMultiCallable(
            raw.StartHTTPListener,
            clientpb.HTTPListenerReq,
            clientpb.ListenerJob,
        )
        self.GetBeacons = UnaryUnaryMultiCallable(
            raw.GetBeacons,
            commonpb.Empty,
            clientpb.Beacons,
        )
        self.GetBeacon = UnaryUnaryMultiCallable(
            raw.GetBeacon,
            clientpb.Beacon,
            clientpb.Beacon,
        )
        self.RmBeacon = UnaryUnaryMultiCallable(
            raw.RmBeacon,
            clientpb.Beacon,
            commonpb.Empty,
        )
        self.GetBeaconTasks = UnaryUnaryMultiCallable(
            raw.GetBeaconTasks,
            clientpb.Beacon,
            clientpb.BeaconTasks,
        )
        self.GetBeaconTaskContent = UnaryUnaryMultiCallable(
            raw.GetBeaconTaskContent,
            clientpb.BeaconTask,
            clientpb.BeaconTask,
        )
        self.CancelBeaconTask = UnaryUnaryMultiCallable(
            raw.CancelBeaconTask,
            clientpb.BeaconTask,
            clientpb.BeaconTask,
        )
        self.UpdateBeaconIntegrityInformation = UnaryUnaryMultiCallable(
            raw.UpdateBeaconIntegrityInformation,
            clientpb.BeaconIntegrity,
            commonpb.Empty,
        )
        self.GetJobs = UnaryUnaryMultiCallable(
            raw.GetJobs,
            commonpb.Empty,
            clientpb.Jobs,
        )
        self.KillJob = UnaryUnaryMultiCallable(
            raw.KillJob,
            clientpb.KillJobReq,
            clientpb.KillJob,
        )
        self.RestartJobs = UnaryUnaryMultiCallable(
            raw.RestartJobs,
            clientpb.RestartJobReq,
            commonpb.Empty,
        )
        self.StartTCPStagerListener = UnaryUnaryMultiCallable(
            raw.StartTCPStagerListener,
            clientpb.StagerListenerReq,
            clientpb.StagerListener,
        )
        self.LootAdd = UnaryUnaryMultiCallable(
            raw.LootAdd,
            clientpb.Loot,
            clientpb.Loot,
        )
        self.LootRm = UnaryUnaryMultiCallable(
            raw.LootRm,
            clientpb.Loot,
            commonpb.Empty,
        )
        self.LootUpdate = UnaryUnaryMultiCallable(
            raw.LootUpdate,
            clientpb.Loot,
            clientpb.Loot,
        )
        self.LootContent = UnaryUnaryMultiCallable(
            raw.LootContent,
            clientpb.Loot,
            clientpb.Loot,
        )
        self.LootAll = UnaryUnaryMultiCallable(
            raw.LootAll,
            commonpb.Empty,
            clientpb.AllLoot,
        )
        self.Creds = UnaryUnaryMultiCallable(
            raw.Creds,
            commonpb.Empty,
            clientpb.Credentials,
        )
        self.CredsAdd = UnaryUnaryMultiCallable(
            raw.CredsAdd,
            clientpb.Credentials,
            commonpb.Empty,
        )
        self.CredsRm = UnaryUnaryMultiCallable(
            raw.CredsRm,
            clientpb.Credentials,
            commonpb.Empty,
        )
        self.CredsUpdate = UnaryUnaryMultiCallable(
            raw.CredsUpdate,
            clientpb.Credentials,
            commonpb.Empty,
        )
        self.GetCredByID = UnaryUnaryMultiCallable(
            raw.GetCredByID,
            clientpb.Credential,
            clientpb.Credential,
        )
        self.GetCredsByHashType = UnaryUnaryMultiCallable(
            raw.GetCredsByHashType,
            clientpb.Credential,
            clientpb.Credentials,
        )
        self.GetPlaintextCredsByHashType = UnaryUnaryMultiCallable(
            raw.GetPlaintextCredsByHashType,
            clientpb.Credential,
            clientpb.Credentials,
        )
        self.CredsSniffHashType = UnaryUnaryMultiCallable(
            raw.CredsSniffHashType,
            clientpb.Credential,
            clientpb.Credential,
        )
        self.Hosts = UnaryUnaryMultiCallable(
            raw.Hosts,
            commonpb.Empty,
            clientpb.AllHosts,
        )
        self.Host = UnaryUnaryMultiCallable(
            raw.Host,
            clientpb.Host,
            clientpb.Host,
        )
        self.HostRm = UnaryUnaryMultiCallable(
            raw.HostRm,
            clientpb.Host,
            commonpb.Empty,
        )
        self.HostIOCRm = UnaryUnaryMultiCallable(
            raw.HostIOCRm,
            clientpb.IOC,
            commonpb.Empty,
        )
        self.Generate = UnaryUnaryMultiCallable(
            raw.Generate,
            clientpb.GenerateReq,
            clientpb.Generate,
        )
        self.GenerateSpoofMetadata = UnaryUnaryMultiCallable(
            raw.GenerateSpoofMetadata,
            clientpb.GenerateSpoofMetadataReq,
            commonpb.Empty,
        )
        self.GenerateExternal = UnaryUnaryMultiCallable(
            raw.GenerateExternal,
            clientpb.ExternalGenerateReq,
            clientpb.ExternalImplantConfig,
        )
        self.GenerateExternalSaveBuild = UnaryUnaryMultiCallable(
            raw.GenerateExternalSaveBuild,
            clientpb.ExternalImplantBinary,
            commonpb.Empty,
        )
        self.GenerateExternalGetBuildConfig = UnaryUnaryMultiCallable(
            raw.GenerateExternalGetBuildConfig,
            clientpb.ImplantBuild,
            clientpb.ExternalImplantConfig,
        )
        self.GenerateStage = UnaryUnaryMultiCallable(
            raw.GenerateStage,
            clientpb.GenerateStageReq,
            clientpb.Generate,
        )
        self.StageImplantBuild = UnaryUnaryMultiCallable(
            raw.StageImplantBuild,
            clientpb.ImplantStageReq,
            commonpb.Empty,
        )
        self.GetHTTPC2Profiles = UnaryUnaryMultiCallable(
            raw.GetHTTPC2Profiles,
            commonpb.Empty,
            clientpb.HTTPC2Configs,
        )
        self.GetHTTPC2ProfileByName = UnaryUnaryMultiCallable(
            raw.GetHTTPC2ProfileByName,
            clientpb.C2ProfileReq,
            clientpb.HTTPC2Config,
        )
        self.SaveHTTPC2Profile = UnaryUnaryMultiCallable(
            raw.SaveHTTPC2Profile,
            clientpb.HTTPC2ConfigReq,
            commonpb.Empty,
        )
        self.BuilderRegister = UnaryStreamMultiCallable(
            raw.BuilderRegister,
            clientpb.Builder,
            clientpb.Event,
        )
        self.BuilderTrigger = UnaryUnaryMultiCallable(
            raw.BuilderTrigger,
            clientpb.Event,
            commonpb.Empty,
        )
        self.Builders = UnaryUnaryMultiCallable(
            raw.Builders,
            commonpb.Empty,
            clientpb.Builders,
        )
        self.GetCertificateInfo = UnaryUnaryMultiCallable(
            raw.GetCertificateInfo,
            clientpb.CertificatesReq,
            clientpb.CertificateInfo,
        )
        self.GetCertificateAuthorityInfo = UnaryUnaryMultiCallable(
            raw.GetCertificateAuthorityInfo,
            commonpb.Empty,
            clientpb.CertificateAuthorityInfo,
        )
        self.Crack = UnaryUnaryMultiCallable(
            raw.Crack,
            clientpb.CrackCommand,
            clientpb.CrackResponse,
        )
        self.CrackstationRegister = UnaryStreamMultiCallable(
            raw.CrackstationRegister,
            clientpb.Crackstation,
            clientpb.Event,
        )
        self.CrackstationTrigger = UnaryUnaryMultiCallable(
            raw.CrackstationTrigger,
            clientpb.Event,
            commonpb.Empty,
        )
        self.CrackstationBenchmark = UnaryUnaryMultiCallable(
            raw.CrackstationBenchmark,
            clientpb.CrackBenchmark,
            commonpb.Empty,
        )
        self.Crackstations = UnaryUnaryMultiCallable(
            raw.Crackstations,
            commonpb.Empty,
            clientpb.Crackstations,
        )
        self.CrackTaskByID = UnaryUnaryMultiCallable(
            raw.CrackTaskByID,
            clientpb.CrackTask,
            clientpb.CrackTask,
        )
        self.CrackTaskUpdate = UnaryUnaryMultiCallable(
            raw.CrackTaskUpdate,
            clientpb.CrackTask,
            commonpb.Empty,
        )
        self.CrackFilesList = UnaryUnaryMultiCallable(
            raw.CrackFilesList,
            clientpb.CrackFile,
            clientpb.CrackFiles,
        )
        self.CrackFileCreate = UnaryUnaryMultiCallable(
            raw.CrackFileCreate,
            clientpb.CrackFile,
            clientpb.CrackFile,
        )
        self.CrackFileChunkUpload = UnaryUnaryMultiCallable(
            raw.CrackFileChunkUpload,
            clientpb.CrackFileChunk,
            commonpb.Empty,
        )
        self.CrackFileChunkDownload = UnaryUnaryMultiCallable(
            raw.CrackFileChunkDownload,
            clientpb.CrackFileChunk,
            clientpb.CrackFileChunk,
        )
        self.CrackFileComplete = UnaryUnaryMultiCallable(
            raw.CrackFileComplete,
            clientpb.CrackFile,
            commonpb.Empty,
        )
        self.CrackFileDelete = UnaryUnaryMultiCallable(
            raw.CrackFileDelete,
            clientpb.CrackFile,
            commonpb.Empty,
        )
        self.Regenerate = UnaryUnaryMultiCallable(
            raw.Regenerate,
            clientpb.RegenerateReq,
            clientpb.Generate,
        )
        self.ImplantBuilds = UnaryUnaryMultiCallable(
            raw.ImplantBuilds,
            commonpb.Empty,
            clientpb.ImplantBuilds,
        )
        self.DeleteImplantBuild = UnaryUnaryMultiCallable(
            raw.DeleteImplantBuild,
            clientpb.DeleteReq,
            commonpb.Empty,
        )
        self.Canaries = UnaryUnaryMultiCallable(
            raw.Canaries,
            commonpb.Empty,
            clientpb.Canaries,
        )
        self.GenerateWGClientConfig = UnaryUnaryMultiCallable(
            raw.GenerateWGClientConfig,
            commonpb.Empty,
            clientpb.WGClientConfig,
        )
        self.GenerateUniqueIP = UnaryUnaryMultiCallable(
            raw.GenerateUniqueIP,
            commonpb.Empty,
            clientpb.UniqueWGIP,
        )
        self.ImplantProfiles = UnaryUnaryMultiCallable(
            raw.ImplantProfiles,
            commonpb.Empty,
            clientpb.ImplantProfiles,
        )
        self.DeleteImplantProfile = UnaryUnaryMultiCallable(
            raw.DeleteImplantProfile,
            clientpb.DeleteReq,
            commonpb.Empty,
        )
        self.SaveImplantProfile = UnaryUnaryMultiCallable(
            raw.SaveImplantProfile,
            clientpb.ImplantProfile,
            clientpb.ImplantProfile,
        )
        self.ShellcodeRDI = UnaryUnaryMultiCallable(
            raw.ShellcodeRDI,
            clientpb.ShellcodeRDIReq,
            clientpb.ShellcodeRDI,
        )
        self.GetCompiler = UnaryUnaryMultiCallable(
            raw.GetCompiler,
            commonpb.Empty,
            clientpb.Compiler,
        )
        self.ShellcodeEncoder = UnaryUnaryMultiCallable(
            raw.ShellcodeEncoder,
            clientpb.ShellcodeEncodeReq,
            clientpb.ShellcodeEncode,
        )
        self.ShellcodeEncoderMap = UnaryUnaryMultiCallable(
            raw.ShellcodeEncoderMap,
            commonpb.Empty,
            clientpb.ShellcodeEncoderMap,
        )
        self.TrafficEncoderMap = UnaryUnaryMultiCallable(
            raw.TrafficEncoderMap,
            commonpb.Empty,
            clientpb.TrafficEncoderMap,
        )
        self.TrafficEncoderAdd = UnaryUnaryMultiCallable(
            raw.TrafficEncoderAdd,
            clientpb.TrafficEncoder,
            clientpb.TrafficEncoderTests,
        )
        self.TrafficEncoderRm = UnaryUnaryMultiCallable(
            raw.TrafficEncoderRm,
            clientpb.TrafficEncoder,
            commonpb.Empty,
        )
        self.Websites = UnaryUnaryMultiCallable(
            raw.Websites,
            commonpb.Empty,
            clientpb.Websites,
        )
        self.Website = UnaryUnaryMultiCallable(
            raw.Website,
            clientpb.Website,
            clientpb.Website,
        )
        self.WebsiteRemove = UnaryUnaryMultiCallable(
            raw.WebsiteRemove,
            clientpb.Website,
            commonpb.Empty,
        )
        self.WebsiteAddContent = UnaryUnaryMultiCallable(
            raw.WebsiteAddContent,
            clientpb.WebsiteAddContent,
            clientpb.Website,
        )
        self.WebsiteUpdateContent = UnaryUnaryMultiCallable(
            raw.WebsiteUpdateContent,
            clientpb.WebsiteAddContent,
            clientpb.Website,
        )
        self.WebsiteRemoveContent = UnaryUnaryMultiCallable(
            raw.WebsiteRemoveContent,
            clientpb.WebsiteRemoveContent,
            clientpb.Website,
        )
        self.Ping = UnaryUnaryMultiCallable(
            raw.Ping,
            sliverpb.Ping,
            sliverpb.Ping,
        )
        self.Ps = UnaryUnaryMultiCallable(
            raw.Ps,
            sliverpb.PsReq,
            sliverpb.Ps,
        )
        self.Terminate = UnaryUnaryMultiCallable(
            raw.Terminate,
            sliverpb.TerminateReq,
            sliverpb.Terminate,
        )
        self.Ifconfig = UnaryUnaryMultiCallable(
            raw.Ifconfig,
            sliverpb.IfconfigReq,
            sliverpb.Ifconfig,
        )
        self.Netstat = UnaryUnaryMultiCallable(
            raw.Netstat,
            sliverpb.NetstatReq,
            sliverpb.Netstat,
        )
        self.Ls = UnaryUnaryMultiCallable(
            raw.Ls,
            sliverpb.LsReq,
            sliverpb.Ls,
        )
        self.Cd = UnaryUnaryMultiCallable(
            raw.Cd,
            sliverpb.CdReq,
            sliverpb.Pwd,
        )
        self.Pwd = UnaryUnaryMultiCallable(
            raw.Pwd,
            sliverpb.PwdReq,
            sliverpb.Pwd,
        )
        self.Mv = UnaryUnaryMultiCallable(
            raw.Mv,
            sliverpb.MvReq,
            sliverpb.Mv,
        )
        self.Cp = UnaryUnaryMultiCallable(
            raw.Cp,
            sliverpb.CpReq,
            sliverpb.Cp,
        )
        self.Rm = UnaryUnaryMultiCallable(
            raw.Rm,
            sliverpb.RmReq,
            sliverpb.Rm,
        )
        self.Mkdir = UnaryUnaryMultiCallable(
            raw.Mkdir,
            sliverpb.MkdirReq,
            sliverpb.Mkdir,
        )
        self.Download = UnaryUnaryMultiCallable(
            raw.Download,
            sliverpb.DownloadReq,
            sliverpb.Download,
        )
        self.Upload = UnaryUnaryMultiCallable(
            raw.Upload,
            sliverpb.UploadReq,
            sliverpb.Upload,
        )
        self.Grep = UnaryUnaryMultiCallable(
            raw.Grep,
            sliverpb.GrepReq,
            sliverpb.Grep,
        )
        self.Chmod = UnaryUnaryMultiCallable(
            raw.Chmod,
            sliverpb.ChmodReq,
            sliverpb.Chmod,
        )
        self.Chown = UnaryUnaryMultiCallable(
            raw.Chown,
            sliverpb.ChownReq,
            sliverpb.Chown,
        )
        self.Chtimes = UnaryUnaryMultiCallable(
            raw.Chtimes,
            sliverpb.ChtimesReq,
            sliverpb.Chtimes,
        )
        self.MemfilesList = UnaryUnaryMultiCallable(
            raw.MemfilesList,
            sliverpb.MemfilesListReq,
            sliverpb.Ls,
        )
        self.MemfilesAdd = UnaryUnaryMultiCallable(
            raw.MemfilesAdd,
            sliverpb.MemfilesAddReq,
            sliverpb.MemfilesAdd,
        )
        self.MemfilesRm = UnaryUnaryMultiCallable(
            raw.MemfilesRm,
            sliverpb.MemfilesRmReq,
            sliverpb.MemfilesRm,
        )
        self.Mount = UnaryUnaryMultiCallable(
            raw.Mount,
            sliverpb.MountReq,
            sliverpb.Mount,
        )
        self.ProcessDump = UnaryUnaryMultiCallable(
            raw.ProcessDump,
            sliverpb.ProcessDumpReq,
            sliverpb.ProcessDump,
        )
        self.RunAs = UnaryUnaryMultiCallable(
            raw.RunAs,
            sliverpb.RunAsReq,
            sliverpb.RunAs,
        )
        self.Impersonate = UnaryUnaryMultiCallable(
            raw.Impersonate,
            sliverpb.ImpersonateReq,
            sliverpb.Impersonate,
        )
        self.RevToSelf = UnaryUnaryMultiCallable(
            raw.RevToSelf,
            sliverpb.RevToSelfReq,
            sliverpb.RevToSelf,
        )
        self.GetSystem = UnaryUnaryMultiCallable(
            raw.GetSystem,
            clientpb.GetSystemReq,
            sliverpb.GetSystem,
        )
        self.Task = UnaryUnaryMultiCallable(
            raw.Task,
            sliverpb.TaskReq,
            sliverpb.Task,
        )
        self.Msf = UnaryUnaryMultiCallable(
            raw.Msf,
            clientpb.MSFReq,
            sliverpb.Task,
        )
        self.MsfRemote = UnaryUnaryMultiCallable(
            raw.MsfRemote,
            clientpb.MSFRemoteReq,
            sliverpb.Task,
        )
        self.ExecuteAssembly = UnaryUnaryMultiCallable(
            raw.ExecuteAssembly,
            sliverpb.ExecuteAssemblyReq,
            sliverpb.ExecuteAssembly,
        )
        self.Migrate = UnaryUnaryMultiCallable(
            raw.Migrate,
            clientpb.MigrateReq,
            sliverpb.Migrate,
        )
        self.Execute = UnaryUnaryMultiCallable(
            raw.Execute,
            sliverpb.ExecuteReq,
            sliverpb.Execute,
        )
        self.ExecuteWindows = UnaryUnaryMultiCallable(
            raw.ExecuteWindows,
            sliverpb.ExecuteWindowsReq,
            sliverpb.Execute,
        )
        self.ExecuteChildren = UnaryUnaryMultiCallable(
            raw.ExecuteChildren,
            sliverpb.ExecuteChildrenReq,
            sliverpb.ExecuteChildren,
        )
        self.Sideload = UnaryUnaryMultiCallable(
            raw.Sideload,
            sliverpb.SideloadReq,
            sliverpb.Sideload,
        )
        self.SpawnDll = UnaryUnaryMultiCallable(
            raw.SpawnDll,
            sliverpb.InvokeSpawnDllReq,
            sliverpb.SpawnDll,
        )
        self.Screenshot = UnaryUnaryMultiCallable(
            raw.Screenshot,
            sliverpb.ScreenshotReq,
            sliverpb.Screenshot,
        )
        self.CurrentTokenOwner = UnaryUnaryMultiCallable(
            raw.CurrentTokenOwner,
            sliverpb.CurrentTokenOwnerReq,
            sliverpb.CurrentTokenOwner,
        )
        self.Services = UnaryUnaryMultiCallable(
            raw.Services,
            sliverpb.ServicesReq,
            sliverpb.Services,
        )
        self.ServiceDetail = UnaryUnaryMultiCallable(
            raw.ServiceDetail,
            sliverpb.ServiceDetailReq,
            sliverpb.ServiceDetail,
        )
        self.StartServiceByName = UnaryUnaryMultiCallable(
            raw.StartServiceByName,
            sliverpb.StartServiceByNameReq,
            sliverpb.ServiceInfo,
        )
        self.PivotStartListener = UnaryUnaryMultiCallable(
            raw.PivotStartListener,
            sliverpb.PivotStartListenerReq,
            sliverpb.PivotListener,
        )
        self.PivotStopListener = UnaryUnaryMultiCallable(
            raw.PivotStopListener,
            sliverpb.PivotStopListenerReq,
            commonpb.Empty,
        )
        self.PivotSessionListeners = UnaryUnaryMultiCallable(
            raw.PivotSessionListeners,
            sliverpb.PivotListenersReq,
            sliverpb.PivotListeners,
        )
        self.PivotGraph = UnaryUnaryMultiCallable(
            raw.PivotGraph,
            commonpb.Empty,
            clientpb.PivotGraph,
        )
        self.StartService = UnaryUnaryMultiCallable(
            raw.StartService,
            sliverpb.StartServiceReq,
            sliverpb.ServiceInfo,
        )
        self.StopService = UnaryUnaryMultiCallable(
            raw.StopService,
            sliverpb.StopServiceReq,
            sliverpb.ServiceInfo,
        )
        self.RemoveService = UnaryUnaryMultiCallable(
            raw.RemoveService,
            sliverpb.RemoveServiceReq,
            sliverpb.ServiceInfo,
        )
        self.MakeToken = UnaryUnaryMultiCallable(
            raw.MakeToken,
            sliverpb.MakeTokenReq,
            sliverpb.MakeToken,
        )
        self.GetEnv = UnaryUnaryMultiCallable(
            raw.GetEnv,
            sliverpb.EnvReq,
            sliverpb.EnvInfo,
        )
        self.SetEnv = UnaryUnaryMultiCallable(
            raw.SetEnv,
            sliverpb.SetEnvReq,
            sliverpb.SetEnv,
        )
        self.UnsetEnv = UnaryUnaryMultiCallable(
            raw.UnsetEnv,
            sliverpb.UnsetEnvReq,
            sliverpb.UnsetEnv,
        )
        self.Backdoor = UnaryUnaryMultiCallable(
            raw.Backdoor,
            clientpb.BackdoorReq,
            clientpb.Backdoor,
        )
        self.RegistryRead = UnaryUnaryMultiCallable(
            raw.RegistryRead,
            sliverpb.RegistryReadReq,
            sliverpb.RegistryRead,
        )
        self.RegistryWrite = UnaryUnaryMultiCallable(
            raw.RegistryWrite,
            sliverpb.RegistryWriteReq,
            sliverpb.RegistryWrite,
        )
        self.RegistryCreateKey = UnaryUnaryMultiCallable(
            raw.RegistryCreateKey,
            sliverpb.RegistryCreateKeyReq,
            sliverpb.RegistryCreateKey,
        )
        self.RegistryDeleteKey = UnaryUnaryMultiCallable(
            raw.RegistryDeleteKey,
            sliverpb.RegistryDeleteKeyReq,
            sliverpb.RegistryDeleteKey,
        )
        self.RegistryListSubKeys = UnaryUnaryMultiCallable(
            raw.RegistryListSubKeys,
            sliverpb.RegistrySubKeyListReq,
            sliverpb.RegistrySubKeyList,
        )
        self.RegistryListValues = UnaryUnaryMultiCallable(
            raw.RegistryListValues,
            sliverpb.RegistryListValuesReq,
            sliverpb.RegistryValuesList,
        )
        self.RegistryReadHive = UnaryUnaryMultiCallable(
            raw.RegistryReadHive,
            sliverpb.RegistryReadHiveReq,
            sliverpb.RegistryReadHive,
        )
        self.RunSSHCommand = UnaryUnaryMultiCallable(
            raw.RunSSHCommand,
            sliverpb.SSHCommandReq,
            sliverpb.SSHCommand,
        )
        self.HijackDLL = UnaryUnaryMultiCallable(
            raw.HijackDLL,
            clientpb.DllHijackReq,
            clientpb.DllHijack,
        )
        self.GetPrivs = UnaryUnaryMultiCallable(
            raw.GetPrivs,
            sliverpb.GetPrivsReq,
            sliverpb.GetPrivs,
        )
        self.StartRportFwdListener = UnaryUnaryMultiCallable(
            raw.StartRportFwdListener,
            sliverpb.RportFwdStartListenerReq,
            sliverpb.RportFwdListener,
        )
        self.GetRportFwdListeners = UnaryUnaryMultiCallable(
            raw.GetRportFwdListeners,
            sliverpb.RportFwdListenersReq,
            sliverpb.RportFwdListeners,
        )
        self.StopRportFwdListener = UnaryUnaryMultiCallable(
            raw.StopRportFwdListener,
            sliverpb.RportFwdStopListenerReq,
            sliverpb.RportFwdListener,
        )
        self.OpenSession = UnaryUnaryMultiCallable(
            raw.OpenSession,
            sliverpb.OpenSession,
            sliverpb.OpenSession,
        )
        self.CloseSession = UnaryUnaryMultiCallable(
            raw.CloseSession,
            sliverpb.CloseSession,
            commonpb.Empty,
        )
        self.RegisterExtension = UnaryUnaryMultiCallable(
            raw.RegisterExtension,
            sliverpb.RegisterExtensionReq,
            sliverpb.RegisterExtension,
        )
        self.CallExtension = UnaryUnaryMultiCallable(
            raw.CallExtension,
            sliverpb.CallExtensionReq,
            sliverpb.CallExtension,
        )
        self.ListExtensions = UnaryUnaryMultiCallable(
            raw.ListExtensions,
            sliverpb.ListExtensionsReq,
            sliverpb.ListExtensions,
        )
        self.RegisterWasmExtension = UnaryUnaryMultiCallable(
            raw.RegisterWasmExtension,
            sliverpb.RegisterWasmExtensionReq,
            sliverpb.RegisterWasmExtension,
        )
        self.ListWasmExtensions = UnaryUnaryMultiCallable(
            raw.ListWasmExtensions,
            sliverpb.ListWasmExtensionsReq,
            sliverpb.ListWasmExtensions,
        )
        self.ExecWasmExtension = UnaryUnaryMultiCallable(
            raw.ExecWasmExtension,
            sliverpb.ExecWasmExtensionReq,
            sliverpb.ExecWasmExtension,
        )
        self.WGStartPortForward = UnaryUnaryMultiCallable(
            raw.WGStartPortForward,
            sliverpb.WGPortForwardStartReq,
            sliverpb.WGPortForward,
        )
        self.WGStopPortForward = UnaryUnaryMultiCallable(
            raw.WGStopPortForward,
            sliverpb.WGPortForwardStopReq,
            sliverpb.WGPortForward,
        )
        self.WGStartSocks = UnaryUnaryMultiCallable(
            raw.WGStartSocks,
            sliverpb.WGSocksStartReq,
            sliverpb.WGSocks,
        )
        self.WGStopSocks = UnaryUnaryMultiCallable(
            raw.WGStopSocks,
            sliverpb.WGSocksStopReq,
            sliverpb.WGSocks,
        )
        self.WGListForwarders = UnaryUnaryMultiCallable(
            raw.WGListForwarders,
            sliverpb.WGTCPForwardersReq,
            sliverpb.WGTCPForwarders,
        )
        self.WGListSocksServers = UnaryUnaryMultiCallable(
            raw.WGListSocksServers,
            sliverpb.WGSocksServersReq,
            sliverpb.WGSocksServers,
        )
        self.Shell = UnaryUnaryMultiCallable(
            raw.Shell,
            sliverpb.ShellReq,
            sliverpb.Shell,
        )
        self.ShellResize = UnaryUnaryMultiCallable(
            raw.ShellResize,
            sliverpb.ShellResizeReq,
            commonpb.Empty,
        )
        self.Portfwd = UnaryUnaryMultiCallable(
            raw.Portfwd,
            sliverpb.PortfwdReq,
            sliverpb.Portfwd,
        )
        self.CreateSocks = UnaryUnaryMultiCallable(
            raw.CreateSocks,
            sliverpb.Socks,
            sliverpb.Socks,
        )
        self.CloseSocks = UnaryUnaryMultiCallable(
            raw.CloseSocks,
            sliverpb.Socks,
            commonpb.Empty,
        )
        self.SocksProxy = StreamStreamMultiCallable(
            raw.SocksProxy,
            sliverpb.SocksData,
            sliverpb.SocksData,
        )
        self.CreateTunnel = UnaryUnaryMultiCallable(
            raw.CreateTunnel,
            sliverpb.Tunnel,
            sliverpb.Tunnel,
        )
        self.CloseTunnel = UnaryUnaryMultiCallable(
            raw.CloseTunnel,
            sliverpb.Tunnel,
            commonpb.Empty,
        )
        self.TunnelData = StreamStreamMultiCallable(
            raw.TunnelData,
            sliverpb.TunnelData,
            sliverpb.TunnelData,
        )
        self.Events = UnaryStreamMultiCallable(
            raw.Events,
            commonpb.Empty,
            clientpb.Event,
        )


RPC_METHOD_COUNT = 193
