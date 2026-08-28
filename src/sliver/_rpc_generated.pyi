"""Generated static Pydantic RPC declarations. Do not edit manually."""

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

    def _initialize_rpc_methods(self, raw: object) -> None: ...

RPC_METHOD_COUNT: int
