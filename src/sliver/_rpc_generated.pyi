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

    get_version: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Version]
    GetVersion: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Version]
    client_log: StreamUnaryMultiCallable[clientpb.ClientLogData, commonpb.Empty]
    ClientLog: StreamUnaryMultiCallable[clientpb.ClientLogData, commonpb.Empty]
    get_operators: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Operators]
    GetOperators: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Operators]
    kill: UnaryUnaryMultiCallable[sliverpb.KillReq, commonpb.Empty]
    Kill: UnaryUnaryMultiCallable[sliverpb.KillReq, commonpb.Empty]
    reconfigure: UnaryUnaryMultiCallable[sliverpb.ReconfigureReq, sliverpb.Reconfigure]
    Reconfigure: UnaryUnaryMultiCallable[sliverpb.ReconfigureReq, sliverpb.Reconfigure]
    rename: UnaryUnaryMultiCallable[clientpb.RenameReq, commonpb.Empty]
    Rename: UnaryUnaryMultiCallable[clientpb.RenameReq, commonpb.Empty]
    get_sessions: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Sessions]
    GetSessions: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Sessions]
    monitor_start: UnaryUnaryMultiCallable[commonpb.Empty, commonpb.Response]
    MonitorStart: UnaryUnaryMultiCallable[commonpb.Empty, commonpb.Response]
    monitor_stop: UnaryUnaryMultiCallable[commonpb.Empty, commonpb.Empty]
    MonitorStop: UnaryUnaryMultiCallable[commonpb.Empty, commonpb.Empty]
    monitor_list_config: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.MonitoringProviders
    ]
    MonitorListConfig: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.MonitoringProviders
    ]
    monitor_add_config: UnaryUnaryMultiCallable[
        clientpb.MonitoringProvider, commonpb.Response
    ]
    MonitorAddConfig: UnaryUnaryMultiCallable[
        clientpb.MonitoringProvider, commonpb.Response
    ]
    monitor_del_config: UnaryUnaryMultiCallable[
        clientpb.MonitoringProvider, commonpb.Response
    ]
    MonitorDelConfig: UnaryUnaryMultiCallable[
        clientpb.MonitoringProvider, commonpb.Response
    ]
    get_ai_providers: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.AIProviderConfigs
    ]
    GetAIProviders: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AIProviderConfigs]
    get_ai_conversations: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.AIConversations
    ]
    GetAIConversations: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.AIConversations
    ]
    get_ai_conversation: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, clientpb.AIConversation
    ]
    GetAIConversation: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, clientpb.AIConversation
    ]
    save_ai_conversation: UnaryUnaryMultiCallable[
        clientpb.AIConversation, clientpb.AIConversation
    ]
    SaveAIConversation: UnaryUnaryMultiCallable[
        clientpb.AIConversation, clientpb.AIConversation
    ]
    delete_ai_conversation: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, commonpb.Empty
    ]
    DeleteAIConversation: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, commonpb.Empty
    ]
    get_ai_conversation_messages: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, clientpb.AIConversationMessages
    ]
    GetAIConversationMessages: UnaryUnaryMultiCallable[
        clientpb.AIConversationReq, clientpb.AIConversationMessages
    ]
    save_ai_conversation_message: UnaryUnaryMultiCallable[
        clientpb.AIConversationMessage, clientpb.AIConversationMessage
    ]
    SaveAIConversationMessage: UnaryUnaryMultiCallable[
        clientpb.AIConversationMessage, clientpb.AIConversationMessage
    ]
    start_mtls_listener: UnaryUnaryMultiCallable[
        clientpb.MTLSListenerReq, clientpb.ListenerJob
    ]
    StartMTLSListener: UnaryUnaryMultiCallable[
        clientpb.MTLSListenerReq, clientpb.ListenerJob
    ]
    start_wg_listener: UnaryUnaryMultiCallable[
        clientpb.WGListenerReq, clientpb.ListenerJob
    ]
    StartWGListener: UnaryUnaryMultiCallable[
        clientpb.WGListenerReq, clientpb.ListenerJob
    ]
    start_dns_listener: UnaryUnaryMultiCallable[
        clientpb.DNSListenerReq, clientpb.ListenerJob
    ]
    StartDNSListener: UnaryUnaryMultiCallable[
        clientpb.DNSListenerReq, clientpb.ListenerJob
    ]
    start_https_listener: UnaryUnaryMultiCallable[
        clientpb.HTTPListenerReq, clientpb.ListenerJob
    ]
    StartHTTPSListener: UnaryUnaryMultiCallable[
        clientpb.HTTPListenerReq, clientpb.ListenerJob
    ]
    start_http_listener: UnaryUnaryMultiCallable[
        clientpb.HTTPListenerReq, clientpb.ListenerJob
    ]
    StartHTTPListener: UnaryUnaryMultiCallable[
        clientpb.HTTPListenerReq, clientpb.ListenerJob
    ]
    get_beacons: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Beacons]
    GetBeacons: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Beacons]
    get_beacon: UnaryUnaryMultiCallable[clientpb.Beacon, clientpb.Beacon]
    GetBeacon: UnaryUnaryMultiCallable[clientpb.Beacon, clientpb.Beacon]
    rm_beacon: UnaryUnaryMultiCallable[clientpb.Beacon, commonpb.Empty]
    RmBeacon: UnaryUnaryMultiCallable[clientpb.Beacon, commonpb.Empty]
    get_beacon_tasks: UnaryUnaryMultiCallable[clientpb.Beacon, clientpb.BeaconTasks]
    GetBeaconTasks: UnaryUnaryMultiCallable[clientpb.Beacon, clientpb.BeaconTasks]
    get_beacon_task_content: UnaryUnaryMultiCallable[
        clientpb.BeaconTask, clientpb.BeaconTask
    ]
    GetBeaconTaskContent: UnaryUnaryMultiCallable[
        clientpb.BeaconTask, clientpb.BeaconTask
    ]
    cancel_beacon_task: UnaryUnaryMultiCallable[
        clientpb.BeaconTask, clientpb.BeaconTask
    ]
    CancelBeaconTask: UnaryUnaryMultiCallable[clientpb.BeaconTask, clientpb.BeaconTask]
    update_beacon_integrity_information: UnaryUnaryMultiCallable[
        clientpb.BeaconIntegrity, commonpb.Empty
    ]
    UpdateBeaconIntegrityInformation: UnaryUnaryMultiCallable[
        clientpb.BeaconIntegrity, commonpb.Empty
    ]
    get_jobs: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Jobs]
    GetJobs: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Jobs]
    kill_job: UnaryUnaryMultiCallable[clientpb.KillJobReq, clientpb.KillJob]
    KillJob: UnaryUnaryMultiCallable[clientpb.KillJobReq, clientpb.KillJob]
    restart_jobs: UnaryUnaryMultiCallable[clientpb.RestartJobReq, commonpb.Empty]
    RestartJobs: UnaryUnaryMultiCallable[clientpb.RestartJobReq, commonpb.Empty]
    start_tcp_stager_listener: UnaryUnaryMultiCallable[
        clientpb.StagerListenerReq, clientpb.StagerListener
    ]
    StartTCPStagerListener: UnaryUnaryMultiCallable[
        clientpb.StagerListenerReq, clientpb.StagerListener
    ]
    loot_add: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    LootAdd: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    loot_rm: UnaryUnaryMultiCallable[clientpb.Loot, commonpb.Empty]
    LootRm: UnaryUnaryMultiCallable[clientpb.Loot, commonpb.Empty]
    loot_update: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    LootUpdate: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    loot_content: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    LootContent: UnaryUnaryMultiCallable[clientpb.Loot, clientpb.Loot]
    loot_all: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AllLoot]
    LootAll: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AllLoot]
    creds: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Credentials]
    Creds: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Credentials]
    creds_add: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    CredsAdd: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    creds_rm: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    CredsRm: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    creds_update: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    CredsUpdate: UnaryUnaryMultiCallable[clientpb.Credentials, commonpb.Empty]
    get_cred_by_id: UnaryUnaryMultiCallable[clientpb.Credential, clientpb.Credential]
    GetCredByID: UnaryUnaryMultiCallable[clientpb.Credential, clientpb.Credential]
    get_creds_by_hash_type: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credentials
    ]
    GetCredsByHashType: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credentials
    ]
    get_plaintext_creds_by_hash_type: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credentials
    ]
    GetPlaintextCredsByHashType: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credentials
    ]
    creds_sniff_hash_type: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credential
    ]
    CredsSniffHashType: UnaryUnaryMultiCallable[
        clientpb.Credential, clientpb.Credential
    ]
    hosts: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AllHosts]
    Hosts: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.AllHosts]
    host: UnaryUnaryMultiCallable[clientpb.Host, clientpb.Host]
    Host: UnaryUnaryMultiCallable[clientpb.Host, clientpb.Host]
    host_rm: UnaryUnaryMultiCallable[clientpb.Host, commonpb.Empty]
    HostRm: UnaryUnaryMultiCallable[clientpb.Host, commonpb.Empty]
    host_ioc_rm: UnaryUnaryMultiCallable[clientpb.IOC, commonpb.Empty]
    HostIOCRm: UnaryUnaryMultiCallable[clientpb.IOC, commonpb.Empty]
    generate: UnaryUnaryMultiCallable[clientpb.GenerateReq, clientpb.Generate]
    Generate: UnaryUnaryMultiCallable[clientpb.GenerateReq, clientpb.Generate]
    generate_spoof_metadata: UnaryUnaryMultiCallable[
        clientpb.GenerateSpoofMetadataReq, commonpb.Empty
    ]
    GenerateSpoofMetadata: UnaryUnaryMultiCallable[
        clientpb.GenerateSpoofMetadataReq, commonpb.Empty
    ]
    generate_external: UnaryUnaryMultiCallable[
        clientpb.ExternalGenerateReq, clientpb.ExternalImplantConfig
    ]
    GenerateExternal: UnaryUnaryMultiCallable[
        clientpb.ExternalGenerateReq, clientpb.ExternalImplantConfig
    ]
    generate_external_save_build: UnaryUnaryMultiCallable[
        clientpb.ExternalImplantBinary, commonpb.Empty
    ]
    GenerateExternalSaveBuild: UnaryUnaryMultiCallable[
        clientpb.ExternalImplantBinary, commonpb.Empty
    ]
    generate_external_get_build_config: UnaryUnaryMultiCallable[
        clientpb.ImplantBuild, clientpb.ExternalImplantConfig
    ]
    GenerateExternalGetBuildConfig: UnaryUnaryMultiCallable[
        clientpb.ImplantBuild, clientpb.ExternalImplantConfig
    ]
    generate_stage: UnaryUnaryMultiCallable[
        clientpb.GenerateStageReq, clientpb.Generate
    ]
    GenerateStage: UnaryUnaryMultiCallable[clientpb.GenerateStageReq, clientpb.Generate]
    stage_implant_build: UnaryUnaryMultiCallable[
        clientpb.ImplantStageReq, commonpb.Empty
    ]
    StageImplantBuild: UnaryUnaryMultiCallable[clientpb.ImplantStageReq, commonpb.Empty]
    get_httpc2_profiles: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.HTTPC2Configs]
    GetHTTPC2Profiles: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.HTTPC2Configs]
    get_httpc2_profile_by_name: UnaryUnaryMultiCallable[
        clientpb.C2ProfileReq, clientpb.HTTPC2Config
    ]
    GetHTTPC2ProfileByName: UnaryUnaryMultiCallable[
        clientpb.C2ProfileReq, clientpb.HTTPC2Config
    ]
    save_httpc2_profile: UnaryUnaryMultiCallable[
        clientpb.HTTPC2ConfigReq, commonpb.Empty
    ]
    SaveHTTPC2Profile: UnaryUnaryMultiCallable[clientpb.HTTPC2ConfigReq, commonpb.Empty]
    builder_register: UnaryStreamMultiCallable[clientpb.Builder, clientpb.Event]
    BuilderRegister: UnaryStreamMultiCallable[clientpb.Builder, clientpb.Event]
    builder_trigger: UnaryUnaryMultiCallable[clientpb.Event, commonpb.Empty]
    BuilderTrigger: UnaryUnaryMultiCallable[clientpb.Event, commonpb.Empty]
    builders: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Builders]
    Builders: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Builders]
    get_certificate_info: UnaryUnaryMultiCallable[
        clientpb.CertificatesReq, clientpb.CertificateInfo
    ]
    GetCertificateInfo: UnaryUnaryMultiCallable[
        clientpb.CertificatesReq, clientpb.CertificateInfo
    ]
    get_certificate_authority_info: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.CertificateAuthorityInfo
    ]
    GetCertificateAuthorityInfo: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.CertificateAuthorityInfo
    ]
    crack: UnaryUnaryMultiCallable[clientpb.CrackCommand, clientpb.CrackResponse]
    Crack: UnaryUnaryMultiCallable[clientpb.CrackCommand, clientpb.CrackResponse]
    crackstation_register: UnaryStreamMultiCallable[
        clientpb.Crackstation, clientpb.Event
    ]
    CrackstationRegister: UnaryStreamMultiCallable[
        clientpb.Crackstation, clientpb.Event
    ]
    crackstation_trigger: UnaryUnaryMultiCallable[clientpb.Event, commonpb.Empty]
    CrackstationTrigger: UnaryUnaryMultiCallable[clientpb.Event, commonpb.Empty]
    crackstation_benchmark: UnaryUnaryMultiCallable[
        clientpb.CrackBenchmark, commonpb.Empty
    ]
    CrackstationBenchmark: UnaryUnaryMultiCallable[
        clientpb.CrackBenchmark, commonpb.Empty
    ]
    crackstations: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Crackstations]
    Crackstations: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Crackstations]
    crack_task_by_id: UnaryUnaryMultiCallable[clientpb.CrackTask, clientpb.CrackTask]
    CrackTaskByID: UnaryUnaryMultiCallable[clientpb.CrackTask, clientpb.CrackTask]
    crack_task_update: UnaryUnaryMultiCallable[clientpb.CrackTask, commonpb.Empty]
    CrackTaskUpdate: UnaryUnaryMultiCallable[clientpb.CrackTask, commonpb.Empty]
    crack_files_list: UnaryUnaryMultiCallable[clientpb.CrackFile, clientpb.CrackFiles]
    CrackFilesList: UnaryUnaryMultiCallable[clientpb.CrackFile, clientpb.CrackFiles]
    crack_file_create: UnaryUnaryMultiCallable[clientpb.CrackFile, clientpb.CrackFile]
    CrackFileCreate: UnaryUnaryMultiCallable[clientpb.CrackFile, clientpb.CrackFile]
    crack_file_chunk_upload: UnaryUnaryMultiCallable[
        clientpb.CrackFileChunk, commonpb.Empty
    ]
    CrackFileChunkUpload: UnaryUnaryMultiCallable[
        clientpb.CrackFileChunk, commonpb.Empty
    ]
    crack_file_chunk_download: UnaryUnaryMultiCallable[
        clientpb.CrackFileChunk, clientpb.CrackFileChunk
    ]
    CrackFileChunkDownload: UnaryUnaryMultiCallable[
        clientpb.CrackFileChunk, clientpb.CrackFileChunk
    ]
    crack_file_complete: UnaryUnaryMultiCallable[clientpb.CrackFile, commonpb.Empty]
    CrackFileComplete: UnaryUnaryMultiCallable[clientpb.CrackFile, commonpb.Empty]
    crack_file_delete: UnaryUnaryMultiCallable[clientpb.CrackFile, commonpb.Empty]
    CrackFileDelete: UnaryUnaryMultiCallable[clientpb.CrackFile, commonpb.Empty]
    regenerate: UnaryUnaryMultiCallable[clientpb.RegenerateReq, clientpb.Generate]
    Regenerate: UnaryUnaryMultiCallable[clientpb.RegenerateReq, clientpb.Generate]
    implant_builds: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.ImplantBuilds]
    ImplantBuilds: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.ImplantBuilds]
    delete_implant_build: UnaryUnaryMultiCallable[clientpb.DeleteReq, commonpb.Empty]
    DeleteImplantBuild: UnaryUnaryMultiCallable[clientpb.DeleteReq, commonpb.Empty]
    canaries: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Canaries]
    Canaries: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Canaries]
    generate_wg_client_config: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.WGClientConfig
    ]
    GenerateWGClientConfig: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.WGClientConfig
    ]
    generate_unique_ip: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.UniqueWGIP]
    GenerateUniqueIP: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.UniqueWGIP]
    implant_profiles: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.ImplantProfiles]
    ImplantProfiles: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.ImplantProfiles]
    delete_implant_profile: UnaryUnaryMultiCallable[clientpb.DeleteReq, commonpb.Empty]
    DeleteImplantProfile: UnaryUnaryMultiCallable[clientpb.DeleteReq, commonpb.Empty]
    save_implant_profile: UnaryUnaryMultiCallable[
        clientpb.ImplantProfile, clientpb.ImplantProfile
    ]
    SaveImplantProfile: UnaryUnaryMultiCallable[
        clientpb.ImplantProfile, clientpb.ImplantProfile
    ]
    shellcode_rdi: UnaryUnaryMultiCallable[
        clientpb.ShellcodeRDIReq, clientpb.ShellcodeRDI
    ]
    ShellcodeRDI: UnaryUnaryMultiCallable[
        clientpb.ShellcodeRDIReq, clientpb.ShellcodeRDI
    ]
    get_compiler: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Compiler]
    GetCompiler: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Compiler]
    shellcode_encoder: UnaryUnaryMultiCallable[
        clientpb.ShellcodeEncodeReq, clientpb.ShellcodeEncode
    ]
    ShellcodeEncoder: UnaryUnaryMultiCallable[
        clientpb.ShellcodeEncodeReq, clientpb.ShellcodeEncode
    ]
    shellcode_encoder_map: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.ShellcodeEncoderMap
    ]
    ShellcodeEncoderMap: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.ShellcodeEncoderMap
    ]
    traffic_encoder_map: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.TrafficEncoderMap
    ]
    TrafficEncoderMap: UnaryUnaryMultiCallable[
        commonpb.Empty, clientpb.TrafficEncoderMap
    ]
    traffic_encoder_add: UnaryUnaryMultiCallable[
        clientpb.TrafficEncoder, clientpb.TrafficEncoderTests
    ]
    TrafficEncoderAdd: UnaryUnaryMultiCallable[
        clientpb.TrafficEncoder, clientpb.TrafficEncoderTests
    ]
    traffic_encoder_rm: UnaryUnaryMultiCallable[clientpb.TrafficEncoder, commonpb.Empty]
    TrafficEncoderRm: UnaryUnaryMultiCallable[clientpb.TrafficEncoder, commonpb.Empty]
    websites: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Websites]
    Websites: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.Websites]
    website: UnaryUnaryMultiCallable[clientpb.Website, clientpb.Website]
    Website: UnaryUnaryMultiCallable[clientpb.Website, clientpb.Website]
    website_remove: UnaryUnaryMultiCallable[clientpb.Website, commonpb.Empty]
    WebsiteRemove: UnaryUnaryMultiCallable[clientpb.Website, commonpb.Empty]
    website_add_content: UnaryUnaryMultiCallable[
        clientpb.WebsiteAddContent, clientpb.Website
    ]
    WebsiteAddContent: UnaryUnaryMultiCallable[
        clientpb.WebsiteAddContent, clientpb.Website
    ]
    website_update_content: UnaryUnaryMultiCallable[
        clientpb.WebsiteAddContent, clientpb.Website
    ]
    WebsiteUpdateContent: UnaryUnaryMultiCallable[
        clientpb.WebsiteAddContent, clientpb.Website
    ]
    website_remove_content: UnaryUnaryMultiCallable[
        clientpb.WebsiteRemoveContent, clientpb.Website
    ]
    WebsiteRemoveContent: UnaryUnaryMultiCallable[
        clientpb.WebsiteRemoveContent, clientpb.Website
    ]
    ping: UnaryUnaryMultiCallable[sliverpb.Ping, sliverpb.Ping]
    Ping: UnaryUnaryMultiCallable[sliverpb.Ping, sliverpb.Ping]
    ps: UnaryUnaryMultiCallable[sliverpb.PsReq, sliverpb.Ps]
    Ps: UnaryUnaryMultiCallable[sliverpb.PsReq, sliverpb.Ps]
    terminate: UnaryUnaryMultiCallable[sliverpb.TerminateReq, sliverpb.Terminate]
    Terminate: UnaryUnaryMultiCallable[sliverpb.TerminateReq, sliverpb.Terminate]
    ifconfig: UnaryUnaryMultiCallable[sliverpb.IfconfigReq, sliverpb.Ifconfig]
    Ifconfig: UnaryUnaryMultiCallable[sliverpb.IfconfigReq, sliverpb.Ifconfig]
    netstat: UnaryUnaryMultiCallable[sliverpb.NetstatReq, sliverpb.Netstat]
    Netstat: UnaryUnaryMultiCallable[sliverpb.NetstatReq, sliverpb.Netstat]
    ls: UnaryUnaryMultiCallable[sliverpb.LsReq, sliverpb.Ls]
    Ls: UnaryUnaryMultiCallable[sliverpb.LsReq, sliverpb.Ls]
    cd: UnaryUnaryMultiCallable[sliverpb.CdReq, sliverpb.Pwd]
    Cd: UnaryUnaryMultiCallable[sliverpb.CdReq, sliverpb.Pwd]
    pwd: UnaryUnaryMultiCallable[sliverpb.PwdReq, sliverpb.Pwd]
    Pwd: UnaryUnaryMultiCallable[sliverpb.PwdReq, sliverpb.Pwd]
    mv: UnaryUnaryMultiCallable[sliverpb.MvReq, sliverpb.Mv]
    Mv: UnaryUnaryMultiCallable[sliverpb.MvReq, sliverpb.Mv]
    cp: UnaryUnaryMultiCallable[sliverpb.CpReq, sliverpb.Cp]
    Cp: UnaryUnaryMultiCallable[sliverpb.CpReq, sliverpb.Cp]
    rm: UnaryUnaryMultiCallable[sliverpb.RmReq, sliverpb.Rm]
    Rm: UnaryUnaryMultiCallable[sliverpb.RmReq, sliverpb.Rm]
    mkdir: UnaryUnaryMultiCallable[sliverpb.MkdirReq, sliverpb.Mkdir]
    Mkdir: UnaryUnaryMultiCallable[sliverpb.MkdirReq, sliverpb.Mkdir]
    download: UnaryUnaryMultiCallable[sliverpb.DownloadReq, sliverpb.Download]
    Download: UnaryUnaryMultiCallable[sliverpb.DownloadReq, sliverpb.Download]
    upload: UnaryUnaryMultiCallable[sliverpb.UploadReq, sliverpb.Upload]
    Upload: UnaryUnaryMultiCallable[sliverpb.UploadReq, sliverpb.Upload]
    grep: UnaryUnaryMultiCallable[sliverpb.GrepReq, sliverpb.Grep]
    Grep: UnaryUnaryMultiCallable[sliverpb.GrepReq, sliverpb.Grep]
    chmod: UnaryUnaryMultiCallable[sliverpb.ChmodReq, sliverpb.Chmod]
    Chmod: UnaryUnaryMultiCallable[sliverpb.ChmodReq, sliverpb.Chmod]
    chown: UnaryUnaryMultiCallable[sliverpb.ChownReq, sliverpb.Chown]
    Chown: UnaryUnaryMultiCallable[sliverpb.ChownReq, sliverpb.Chown]
    chtimes: UnaryUnaryMultiCallable[sliverpb.ChtimesReq, sliverpb.Chtimes]
    Chtimes: UnaryUnaryMultiCallable[sliverpb.ChtimesReq, sliverpb.Chtimes]
    memfiles_list: UnaryUnaryMultiCallable[sliverpb.MemfilesListReq, sliverpb.Ls]
    MemfilesList: UnaryUnaryMultiCallable[sliverpb.MemfilesListReq, sliverpb.Ls]
    memfiles_add: UnaryUnaryMultiCallable[sliverpb.MemfilesAddReq, sliverpb.MemfilesAdd]
    MemfilesAdd: UnaryUnaryMultiCallable[sliverpb.MemfilesAddReq, sliverpb.MemfilesAdd]
    memfiles_rm: UnaryUnaryMultiCallable[sliverpb.MemfilesRmReq, sliverpb.MemfilesRm]
    MemfilesRm: UnaryUnaryMultiCallable[sliverpb.MemfilesRmReq, sliverpb.MemfilesRm]
    mount: UnaryUnaryMultiCallable[sliverpb.MountReq, sliverpb.Mount]
    Mount: UnaryUnaryMultiCallable[sliverpb.MountReq, sliverpb.Mount]
    process_dump: UnaryUnaryMultiCallable[sliverpb.ProcessDumpReq, sliverpb.ProcessDump]
    ProcessDump: UnaryUnaryMultiCallable[sliverpb.ProcessDumpReq, sliverpb.ProcessDump]
    run_as: UnaryUnaryMultiCallable[sliverpb.RunAsReq, sliverpb.RunAs]
    RunAs: UnaryUnaryMultiCallable[sliverpb.RunAsReq, sliverpb.RunAs]
    impersonate: UnaryUnaryMultiCallable[sliverpb.ImpersonateReq, sliverpb.Impersonate]
    Impersonate: UnaryUnaryMultiCallable[sliverpb.ImpersonateReq, sliverpb.Impersonate]
    rev_to_self: UnaryUnaryMultiCallable[sliverpb.RevToSelfReq, sliverpb.RevToSelf]
    RevToSelf: UnaryUnaryMultiCallable[sliverpb.RevToSelfReq, sliverpb.RevToSelf]
    get_system: UnaryUnaryMultiCallable[clientpb.GetSystemReq, sliverpb.GetSystem]
    GetSystem: UnaryUnaryMultiCallable[clientpb.GetSystemReq, sliverpb.GetSystem]
    task: UnaryUnaryMultiCallable[sliverpb.TaskReq, sliverpb.Task]
    Task: UnaryUnaryMultiCallable[sliverpb.TaskReq, sliverpb.Task]
    msf: UnaryUnaryMultiCallable[clientpb.MSFReq, sliverpb.Task]
    Msf: UnaryUnaryMultiCallable[clientpb.MSFReq, sliverpb.Task]
    msf_remote: UnaryUnaryMultiCallable[clientpb.MSFRemoteReq, sliverpb.Task]
    MsfRemote: UnaryUnaryMultiCallable[clientpb.MSFRemoteReq, sliverpb.Task]
    execute_assembly: UnaryUnaryMultiCallable[
        sliverpb.ExecuteAssemblyReq, sliverpb.ExecuteAssembly
    ]
    ExecuteAssembly: UnaryUnaryMultiCallable[
        sliverpb.ExecuteAssemblyReq, sliverpb.ExecuteAssembly
    ]
    migrate: UnaryUnaryMultiCallable[clientpb.MigrateReq, sliverpb.Migrate]
    Migrate: UnaryUnaryMultiCallable[clientpb.MigrateReq, sliverpb.Migrate]
    execute: UnaryUnaryMultiCallable[sliverpb.ExecuteReq, sliverpb.Execute]
    Execute: UnaryUnaryMultiCallable[sliverpb.ExecuteReq, sliverpb.Execute]
    execute_windows: UnaryUnaryMultiCallable[
        sliverpb.ExecuteWindowsReq, sliverpb.Execute
    ]
    ExecuteWindows: UnaryUnaryMultiCallable[
        sliverpb.ExecuteWindowsReq, sliverpb.Execute
    ]
    execute_children: UnaryUnaryMultiCallable[
        sliverpb.ExecuteChildrenReq, sliverpb.ExecuteChildren
    ]
    ExecuteChildren: UnaryUnaryMultiCallable[
        sliverpb.ExecuteChildrenReq, sliverpb.ExecuteChildren
    ]
    sideload: UnaryUnaryMultiCallable[sliverpb.SideloadReq, sliverpb.Sideload]
    Sideload: UnaryUnaryMultiCallable[sliverpb.SideloadReq, sliverpb.Sideload]
    spawn_dll: UnaryUnaryMultiCallable[sliverpb.InvokeSpawnDllReq, sliverpb.SpawnDll]
    SpawnDll: UnaryUnaryMultiCallable[sliverpb.InvokeSpawnDllReq, sliverpb.SpawnDll]
    screenshot: UnaryUnaryMultiCallable[sliverpb.ScreenshotReq, sliverpb.Screenshot]
    Screenshot: UnaryUnaryMultiCallable[sliverpb.ScreenshotReq, sliverpb.Screenshot]
    current_token_owner: UnaryUnaryMultiCallable[
        sliverpb.CurrentTokenOwnerReq, sliverpb.CurrentTokenOwner
    ]
    CurrentTokenOwner: UnaryUnaryMultiCallable[
        sliverpb.CurrentTokenOwnerReq, sliverpb.CurrentTokenOwner
    ]
    services: UnaryUnaryMultiCallable[sliverpb.ServicesReq, sliverpb.Services]
    Services: UnaryUnaryMultiCallable[sliverpb.ServicesReq, sliverpb.Services]
    service_detail: UnaryUnaryMultiCallable[
        sliverpb.ServiceDetailReq, sliverpb.ServiceDetail
    ]
    ServiceDetail: UnaryUnaryMultiCallable[
        sliverpb.ServiceDetailReq, sliverpb.ServiceDetail
    ]
    start_service_by_name: UnaryUnaryMultiCallable[
        sliverpb.StartServiceByNameReq, sliverpb.ServiceInfo
    ]
    StartServiceByName: UnaryUnaryMultiCallable[
        sliverpb.StartServiceByNameReq, sliverpb.ServiceInfo
    ]
    pivot_start_listener: UnaryUnaryMultiCallable[
        sliverpb.PivotStartListenerReq, sliverpb.PivotListener
    ]
    PivotStartListener: UnaryUnaryMultiCallable[
        sliverpb.PivotStartListenerReq, sliverpb.PivotListener
    ]
    pivot_stop_listener: UnaryUnaryMultiCallable[
        sliverpb.PivotStopListenerReq, commonpb.Empty
    ]
    PivotStopListener: UnaryUnaryMultiCallable[
        sliverpb.PivotStopListenerReq, commonpb.Empty
    ]
    pivot_session_listeners: UnaryUnaryMultiCallable[
        sliverpb.PivotListenersReq, sliverpb.PivotListeners
    ]
    PivotSessionListeners: UnaryUnaryMultiCallable[
        sliverpb.PivotListenersReq, sliverpb.PivotListeners
    ]
    pivot_graph: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.PivotGraph]
    PivotGraph: UnaryUnaryMultiCallable[commonpb.Empty, clientpb.PivotGraph]
    start_service: UnaryUnaryMultiCallable[
        sliverpb.StartServiceReq, sliverpb.ServiceInfo
    ]
    StartService: UnaryUnaryMultiCallable[
        sliverpb.StartServiceReq, sliverpb.ServiceInfo
    ]
    stop_service: UnaryUnaryMultiCallable[sliverpb.StopServiceReq, sliverpb.ServiceInfo]
    StopService: UnaryUnaryMultiCallable[sliverpb.StopServiceReq, sliverpb.ServiceInfo]
    remove_service: UnaryUnaryMultiCallable[
        sliverpb.RemoveServiceReq, sliverpb.ServiceInfo
    ]
    RemoveService: UnaryUnaryMultiCallable[
        sliverpb.RemoveServiceReq, sliverpb.ServiceInfo
    ]
    make_token: UnaryUnaryMultiCallable[sliverpb.MakeTokenReq, sliverpb.MakeToken]
    MakeToken: UnaryUnaryMultiCallable[sliverpb.MakeTokenReq, sliverpb.MakeToken]
    get_env: UnaryUnaryMultiCallable[sliverpb.EnvReq, sliverpb.EnvInfo]
    GetEnv: UnaryUnaryMultiCallable[sliverpb.EnvReq, sliverpb.EnvInfo]
    set_env: UnaryUnaryMultiCallable[sliverpb.SetEnvReq, sliverpb.SetEnv]
    SetEnv: UnaryUnaryMultiCallable[sliverpb.SetEnvReq, sliverpb.SetEnv]
    unset_env: UnaryUnaryMultiCallable[sliverpb.UnsetEnvReq, sliverpb.UnsetEnv]
    UnsetEnv: UnaryUnaryMultiCallable[sliverpb.UnsetEnvReq, sliverpb.UnsetEnv]
    backdoor: UnaryUnaryMultiCallable[clientpb.BackdoorReq, clientpb.Backdoor]
    Backdoor: UnaryUnaryMultiCallable[clientpb.BackdoorReq, clientpb.Backdoor]
    registry_read: UnaryUnaryMultiCallable[
        sliverpb.RegistryReadReq, sliverpb.RegistryRead
    ]
    RegistryRead: UnaryUnaryMultiCallable[
        sliverpb.RegistryReadReq, sliverpb.RegistryRead
    ]
    registry_write: UnaryUnaryMultiCallable[
        sliverpb.RegistryWriteReq, sliverpb.RegistryWrite
    ]
    RegistryWrite: UnaryUnaryMultiCallable[
        sliverpb.RegistryWriteReq, sliverpb.RegistryWrite
    ]
    registry_create_key: UnaryUnaryMultiCallable[
        sliverpb.RegistryCreateKeyReq, sliverpb.RegistryCreateKey
    ]
    RegistryCreateKey: UnaryUnaryMultiCallable[
        sliverpb.RegistryCreateKeyReq, sliverpb.RegistryCreateKey
    ]
    registry_delete_key: UnaryUnaryMultiCallable[
        sliverpb.RegistryDeleteKeyReq, sliverpb.RegistryDeleteKey
    ]
    RegistryDeleteKey: UnaryUnaryMultiCallable[
        sliverpb.RegistryDeleteKeyReq, sliverpb.RegistryDeleteKey
    ]
    registry_list_sub_keys: UnaryUnaryMultiCallable[
        sliverpb.RegistrySubKeyListReq, sliverpb.RegistrySubKeyList
    ]
    RegistryListSubKeys: UnaryUnaryMultiCallable[
        sliverpb.RegistrySubKeyListReq, sliverpb.RegistrySubKeyList
    ]
    registry_list_values: UnaryUnaryMultiCallable[
        sliverpb.RegistryListValuesReq, sliverpb.RegistryValuesList
    ]
    RegistryListValues: UnaryUnaryMultiCallable[
        sliverpb.RegistryListValuesReq, sliverpb.RegistryValuesList
    ]
    registry_read_hive: UnaryUnaryMultiCallable[
        sliverpb.RegistryReadHiveReq, sliverpb.RegistryReadHive
    ]
    RegistryReadHive: UnaryUnaryMultiCallable[
        sliverpb.RegistryReadHiveReq, sliverpb.RegistryReadHive
    ]
    run_ssh_command: UnaryUnaryMultiCallable[
        sliverpb.SSHCommandReq, sliverpb.SSHCommand
    ]
    RunSSHCommand: UnaryUnaryMultiCallable[sliverpb.SSHCommandReq, sliverpb.SSHCommand]
    hijack_dll: UnaryUnaryMultiCallable[clientpb.DllHijackReq, clientpb.DllHijack]
    HijackDLL: UnaryUnaryMultiCallable[clientpb.DllHijackReq, clientpb.DllHijack]
    get_privs: UnaryUnaryMultiCallable[sliverpb.GetPrivsReq, sliverpb.GetPrivs]
    GetPrivs: UnaryUnaryMultiCallable[sliverpb.GetPrivsReq, sliverpb.GetPrivs]
    start_rport_fwd_listener: UnaryUnaryMultiCallable[
        sliverpb.RportFwdStartListenerReq, sliverpb.RportFwdListener
    ]
    StartRportFwdListener: UnaryUnaryMultiCallable[
        sliverpb.RportFwdStartListenerReq, sliverpb.RportFwdListener
    ]
    get_rport_fwd_listeners: UnaryUnaryMultiCallable[
        sliverpb.RportFwdListenersReq, sliverpb.RportFwdListeners
    ]
    GetRportFwdListeners: UnaryUnaryMultiCallable[
        sliverpb.RportFwdListenersReq, sliverpb.RportFwdListeners
    ]
    stop_rport_fwd_listener: UnaryUnaryMultiCallable[
        sliverpb.RportFwdStopListenerReq, sliverpb.RportFwdListener
    ]
    StopRportFwdListener: UnaryUnaryMultiCallable[
        sliverpb.RportFwdStopListenerReq, sliverpb.RportFwdListener
    ]
    open_session: UnaryUnaryMultiCallable[sliverpb.OpenSession, sliverpb.OpenSession]
    OpenSession: UnaryUnaryMultiCallable[sliverpb.OpenSession, sliverpb.OpenSession]
    close_session: UnaryUnaryMultiCallable[sliverpb.CloseSession, commonpb.Empty]
    CloseSession: UnaryUnaryMultiCallable[sliverpb.CloseSession, commonpb.Empty]
    register_extension: UnaryUnaryMultiCallable[
        sliverpb.RegisterExtensionReq, sliverpb.RegisterExtension
    ]
    RegisterExtension: UnaryUnaryMultiCallable[
        sliverpb.RegisterExtensionReq, sliverpb.RegisterExtension
    ]
    call_extension: UnaryUnaryMultiCallable[
        sliverpb.CallExtensionReq, sliverpb.CallExtension
    ]
    CallExtension: UnaryUnaryMultiCallable[
        sliverpb.CallExtensionReq, sliverpb.CallExtension
    ]
    list_extensions: UnaryUnaryMultiCallable[
        sliverpb.ListExtensionsReq, sliverpb.ListExtensions
    ]
    ListExtensions: UnaryUnaryMultiCallable[
        sliverpb.ListExtensionsReq, sliverpb.ListExtensions
    ]
    register_wasm_extension: UnaryUnaryMultiCallable[
        sliverpb.RegisterWasmExtensionReq, sliverpb.RegisterWasmExtension
    ]
    RegisterWasmExtension: UnaryUnaryMultiCallable[
        sliverpb.RegisterWasmExtensionReq, sliverpb.RegisterWasmExtension
    ]
    list_wasm_extensions: UnaryUnaryMultiCallable[
        sliverpb.ListWasmExtensionsReq, sliverpb.ListWasmExtensions
    ]
    ListWasmExtensions: UnaryUnaryMultiCallable[
        sliverpb.ListWasmExtensionsReq, sliverpb.ListWasmExtensions
    ]
    exec_wasm_extension: UnaryUnaryMultiCallable[
        sliverpb.ExecWasmExtensionReq, sliverpb.ExecWasmExtension
    ]
    ExecWasmExtension: UnaryUnaryMultiCallable[
        sliverpb.ExecWasmExtensionReq, sliverpb.ExecWasmExtension
    ]
    wg_start_port_forward: UnaryUnaryMultiCallable[
        sliverpb.WGPortForwardStartReq, sliverpb.WGPortForward
    ]
    WGStartPortForward: UnaryUnaryMultiCallable[
        sliverpb.WGPortForwardStartReq, sliverpb.WGPortForward
    ]
    wg_stop_port_forward: UnaryUnaryMultiCallable[
        sliverpb.WGPortForwardStopReq, sliverpb.WGPortForward
    ]
    WGStopPortForward: UnaryUnaryMultiCallable[
        sliverpb.WGPortForwardStopReq, sliverpb.WGPortForward
    ]
    wg_start_socks: UnaryUnaryMultiCallable[sliverpb.WGSocksStartReq, sliverpb.WGSocks]
    WGStartSocks: UnaryUnaryMultiCallable[sliverpb.WGSocksStartReq, sliverpb.WGSocks]
    wg_stop_socks: UnaryUnaryMultiCallable[sliverpb.WGSocksStopReq, sliverpb.WGSocks]
    WGStopSocks: UnaryUnaryMultiCallable[sliverpb.WGSocksStopReq, sliverpb.WGSocks]
    wg_list_forwarders: UnaryUnaryMultiCallable[
        sliverpb.WGTCPForwardersReq, sliverpb.WGTCPForwarders
    ]
    WGListForwarders: UnaryUnaryMultiCallable[
        sliverpb.WGTCPForwardersReq, sliverpb.WGTCPForwarders
    ]
    wg_list_socks_servers: UnaryUnaryMultiCallable[
        sliverpb.WGSocksServersReq, sliverpb.WGSocksServers
    ]
    WGListSocksServers: UnaryUnaryMultiCallable[
        sliverpb.WGSocksServersReq, sliverpb.WGSocksServers
    ]
    shell: UnaryUnaryMultiCallable[sliverpb.ShellReq, sliverpb.Shell]
    Shell: UnaryUnaryMultiCallable[sliverpb.ShellReq, sliverpb.Shell]
    shell_resize: UnaryUnaryMultiCallable[sliverpb.ShellResizeReq, commonpb.Empty]
    ShellResize: UnaryUnaryMultiCallable[sliverpb.ShellResizeReq, commonpb.Empty]
    portfwd: UnaryUnaryMultiCallable[sliverpb.PortfwdReq, sliverpb.Portfwd]
    Portfwd: UnaryUnaryMultiCallable[sliverpb.PortfwdReq, sliverpb.Portfwd]
    create_socks: UnaryUnaryMultiCallable[sliverpb.Socks, sliverpb.Socks]
    CreateSocks: UnaryUnaryMultiCallable[sliverpb.Socks, sliverpb.Socks]
    close_socks: UnaryUnaryMultiCallable[sliverpb.Socks, commonpb.Empty]
    CloseSocks: UnaryUnaryMultiCallable[sliverpb.Socks, commonpb.Empty]
    socks_proxy: StreamStreamMultiCallable[sliverpb.SocksData, sliverpb.SocksData]
    SocksProxy: StreamStreamMultiCallable[sliverpb.SocksData, sliverpb.SocksData]
    create_tunnel: UnaryUnaryMultiCallable[sliverpb.Tunnel, sliverpb.Tunnel]
    CreateTunnel: UnaryUnaryMultiCallable[sliverpb.Tunnel, sliverpb.Tunnel]
    close_tunnel: UnaryUnaryMultiCallable[sliverpb.Tunnel, commonpb.Empty]
    CloseTunnel: UnaryUnaryMultiCallable[sliverpb.Tunnel, commonpb.Empty]
    tunnel_data: StreamStreamMultiCallable[sliverpb.TunnelData, sliverpb.TunnelData]
    TunnelData: StreamStreamMultiCallable[sliverpb.TunnelData, sliverpb.TunnelData]
    events: UnaryStreamMultiCallable[commonpb.Empty, clientpb.Event]
    Events: UnaryStreamMultiCallable[commonpb.Empty, clientpb.Event]

    def _initialize_rpc_methods(self, raw: object) -> None: ...

RPC_METHOD_COUNT: int
