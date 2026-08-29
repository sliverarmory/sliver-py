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

    def _initialize_rpc_methods(self, raw: _WireSliverRPCStub) -> None:
        self.get_version = UnaryUnaryMultiCallable(
            raw.GetVersion,
            commonpb.Empty,
            clientpb.Version,
            "GetVersion",
        )
        self.GetVersion = self.get_version
        self.client_log = StreamUnaryMultiCallable(
            raw.ClientLog,
            clientpb.ClientLogData,
            commonpb.Empty,
            "ClientLog",
        )
        self.ClientLog = self.client_log
        self.get_operators = UnaryUnaryMultiCallable(
            raw.GetOperators,
            commonpb.Empty,
            clientpb.Operators,
            "GetOperators",
        )
        self.GetOperators = self.get_operators
        self.kill = UnaryUnaryMultiCallable(
            raw.Kill,
            sliverpb.KillReq,
            commonpb.Empty,
            "Kill",
        )
        self.Kill = self.kill
        self.reconfigure = UnaryUnaryMultiCallable(
            raw.Reconfigure,
            sliverpb.ReconfigureReq,
            sliverpb.Reconfigure,
            "Reconfigure",
        )
        self.Reconfigure = self.reconfigure
        self.rename = UnaryUnaryMultiCallable(
            raw.Rename,
            clientpb.RenameReq,
            commonpb.Empty,
            "Rename",
        )
        self.Rename = self.rename
        self.get_sessions = UnaryUnaryMultiCallable(
            raw.GetSessions,
            commonpb.Empty,
            clientpb.Sessions,
            "GetSessions",
        )
        self.GetSessions = self.get_sessions
        self.monitor_start = UnaryUnaryMultiCallable(
            raw.MonitorStart,
            commonpb.Empty,
            commonpb.Response,
            "MonitorStart",
        )
        self.MonitorStart = self.monitor_start
        self.monitor_stop = UnaryUnaryMultiCallable(
            raw.MonitorStop,
            commonpb.Empty,
            commonpb.Empty,
            "MonitorStop",
        )
        self.MonitorStop = self.monitor_stop
        self.monitor_list_config = UnaryUnaryMultiCallable(
            raw.MonitorListConfig,
            commonpb.Empty,
            clientpb.MonitoringProviders,
            "MonitorListConfig",
        )
        self.MonitorListConfig = self.monitor_list_config
        self.monitor_add_config = UnaryUnaryMultiCallable(
            raw.MonitorAddConfig,
            clientpb.MonitoringProvider,
            commonpb.Response,
            "MonitorAddConfig",
        )
        self.MonitorAddConfig = self.monitor_add_config
        self.monitor_del_config = UnaryUnaryMultiCallable(
            raw.MonitorDelConfig,
            clientpb.MonitoringProvider,
            commonpb.Response,
            "MonitorDelConfig",
        )
        self.MonitorDelConfig = self.monitor_del_config
        self.get_ai_providers = UnaryUnaryMultiCallable(
            raw.GetAIProviders,
            commonpb.Empty,
            clientpb.AIProviderConfigs,
            "GetAIProviders",
        )
        self.GetAIProviders = self.get_ai_providers
        self.get_ai_conversations = UnaryUnaryMultiCallable(
            raw.GetAIConversations,
            commonpb.Empty,
            clientpb.AIConversations,
            "GetAIConversations",
        )
        self.GetAIConversations = self.get_ai_conversations
        self.get_ai_conversation = UnaryUnaryMultiCallable(
            raw.GetAIConversation,
            clientpb.AIConversationReq,
            clientpb.AIConversation,
            "GetAIConversation",
        )
        self.GetAIConversation = self.get_ai_conversation
        self.save_ai_conversation = UnaryUnaryMultiCallable(
            raw.SaveAIConversation,
            clientpb.AIConversation,
            clientpb.AIConversation,
            "SaveAIConversation",
        )
        self.SaveAIConversation = self.save_ai_conversation
        self.delete_ai_conversation = UnaryUnaryMultiCallable(
            raw.DeleteAIConversation,
            clientpb.AIConversationReq,
            commonpb.Empty,
            "DeleteAIConversation",
        )
        self.DeleteAIConversation = self.delete_ai_conversation
        self.get_ai_conversation_messages = UnaryUnaryMultiCallable(
            raw.GetAIConversationMessages,
            clientpb.AIConversationReq,
            clientpb.AIConversationMessages,
            "GetAIConversationMessages",
        )
        self.GetAIConversationMessages = self.get_ai_conversation_messages
        self.save_ai_conversation_message = UnaryUnaryMultiCallable(
            raw.SaveAIConversationMessage,
            clientpb.AIConversationMessage,
            clientpb.AIConversationMessage,
            "SaveAIConversationMessage",
        )
        self.SaveAIConversationMessage = self.save_ai_conversation_message
        self.start_mtls_listener = UnaryUnaryMultiCallable(
            raw.StartMTLSListener,
            clientpb.MTLSListenerReq,
            clientpb.ListenerJob,
            "StartMTLSListener",
        )
        self.StartMTLSListener = self.start_mtls_listener
        self.start_wg_listener = UnaryUnaryMultiCallable(
            raw.StartWGListener,
            clientpb.WGListenerReq,
            clientpb.ListenerJob,
            "StartWGListener",
        )
        self.StartWGListener = self.start_wg_listener
        self.start_dns_listener = UnaryUnaryMultiCallable(
            raw.StartDNSListener,
            clientpb.DNSListenerReq,
            clientpb.ListenerJob,
            "StartDNSListener",
        )
        self.StartDNSListener = self.start_dns_listener
        self.start_https_listener = UnaryUnaryMultiCallable(
            raw.StartHTTPSListener,
            clientpb.HTTPListenerReq,
            clientpb.ListenerJob,
            "StartHTTPSListener",
        )
        self.StartHTTPSListener = self.start_https_listener
        self.start_http_listener = UnaryUnaryMultiCallable(
            raw.StartHTTPListener,
            clientpb.HTTPListenerReq,
            clientpb.ListenerJob,
            "StartHTTPListener",
        )
        self.StartHTTPListener = self.start_http_listener
        self.get_beacons = UnaryUnaryMultiCallable(
            raw.GetBeacons,
            commonpb.Empty,
            clientpb.Beacons,
            "GetBeacons",
        )
        self.GetBeacons = self.get_beacons
        self.get_beacon = UnaryUnaryMultiCallable(
            raw.GetBeacon,
            clientpb.Beacon,
            clientpb.Beacon,
            "GetBeacon",
        )
        self.GetBeacon = self.get_beacon
        self.rm_beacon = UnaryUnaryMultiCallable(
            raw.RmBeacon,
            clientpb.Beacon,
            commonpb.Empty,
            "RmBeacon",
        )
        self.RmBeacon = self.rm_beacon
        self.get_beacon_tasks = UnaryUnaryMultiCallable(
            raw.GetBeaconTasks,
            clientpb.Beacon,
            clientpb.BeaconTasks,
            "GetBeaconTasks",
        )
        self.GetBeaconTasks = self.get_beacon_tasks
        self.get_beacon_task_content = UnaryUnaryMultiCallable(
            raw.GetBeaconTaskContent,
            clientpb.BeaconTask,
            clientpb.BeaconTask,
            "GetBeaconTaskContent",
        )
        self.GetBeaconTaskContent = self.get_beacon_task_content
        self.cancel_beacon_task = UnaryUnaryMultiCallable(
            raw.CancelBeaconTask,
            clientpb.BeaconTask,
            clientpb.BeaconTask,
            "CancelBeaconTask",
        )
        self.CancelBeaconTask = self.cancel_beacon_task
        self.update_beacon_integrity_information = UnaryUnaryMultiCallable(
            raw.UpdateBeaconIntegrityInformation,
            clientpb.BeaconIntegrity,
            commonpb.Empty,
            "UpdateBeaconIntegrityInformation",
        )
        self.UpdateBeaconIntegrityInformation = self.update_beacon_integrity_information
        self.get_jobs = UnaryUnaryMultiCallable(
            raw.GetJobs,
            commonpb.Empty,
            clientpb.Jobs,
            "GetJobs",
        )
        self.GetJobs = self.get_jobs
        self.kill_job = UnaryUnaryMultiCallable(
            raw.KillJob,
            clientpb.KillJobReq,
            clientpb.KillJob,
            "KillJob",
        )
        self.KillJob = self.kill_job
        self.restart_jobs = UnaryUnaryMultiCallable(
            raw.RestartJobs,
            clientpb.RestartJobReq,
            commonpb.Empty,
            "RestartJobs",
        )
        self.RestartJobs = self.restart_jobs
        self.start_tcp_stager_listener = UnaryUnaryMultiCallable(
            raw.StartTCPStagerListener,
            clientpb.StagerListenerReq,
            clientpb.StagerListener,
            "StartTCPStagerListener",
        )
        self.StartTCPStagerListener = self.start_tcp_stager_listener
        self.loot_add = UnaryUnaryMultiCallable(
            raw.LootAdd,
            clientpb.Loot,
            clientpb.Loot,
            "LootAdd",
        )
        self.LootAdd = self.loot_add
        self.loot_rm = UnaryUnaryMultiCallable(
            raw.LootRm,
            clientpb.Loot,
            commonpb.Empty,
            "LootRm",
        )
        self.LootRm = self.loot_rm
        self.loot_update = UnaryUnaryMultiCallable(
            raw.LootUpdate,
            clientpb.Loot,
            clientpb.Loot,
            "LootUpdate",
        )
        self.LootUpdate = self.loot_update
        self.loot_content = UnaryUnaryMultiCallable(
            raw.LootContent,
            clientpb.Loot,
            clientpb.Loot,
            "LootContent",
        )
        self.LootContent = self.loot_content
        self.loot_all = UnaryUnaryMultiCallable(
            raw.LootAll,
            commonpb.Empty,
            clientpb.AllLoot,
            "LootAll",
        )
        self.LootAll = self.loot_all
        self.creds = UnaryUnaryMultiCallable(
            raw.Creds,
            commonpb.Empty,
            clientpb.Credentials,
            "Creds",
        )
        self.Creds = self.creds
        self.creds_add = UnaryUnaryMultiCallable(
            raw.CredsAdd,
            clientpb.Credentials,
            commonpb.Empty,
            "CredsAdd",
        )
        self.CredsAdd = self.creds_add
        self.creds_rm = UnaryUnaryMultiCallable(
            raw.CredsRm,
            clientpb.Credentials,
            commonpb.Empty,
            "CredsRm",
        )
        self.CredsRm = self.creds_rm
        self.creds_update = UnaryUnaryMultiCallable(
            raw.CredsUpdate,
            clientpb.Credentials,
            commonpb.Empty,
            "CredsUpdate",
        )
        self.CredsUpdate = self.creds_update
        self.get_cred_by_id = UnaryUnaryMultiCallable(
            raw.GetCredByID,
            clientpb.Credential,
            clientpb.Credential,
            "GetCredByID",
        )
        self.GetCredByID = self.get_cred_by_id
        self.get_creds_by_hash_type = UnaryUnaryMultiCallable(
            raw.GetCredsByHashType,
            clientpb.Credential,
            clientpb.Credentials,
            "GetCredsByHashType",
        )
        self.GetCredsByHashType = self.get_creds_by_hash_type
        self.get_plaintext_creds_by_hash_type = UnaryUnaryMultiCallable(
            raw.GetPlaintextCredsByHashType,
            clientpb.Credential,
            clientpb.Credentials,
            "GetPlaintextCredsByHashType",
        )
        self.GetPlaintextCredsByHashType = self.get_plaintext_creds_by_hash_type
        self.creds_sniff_hash_type = UnaryUnaryMultiCallable(
            raw.CredsSniffHashType,
            clientpb.Credential,
            clientpb.Credential,
            "CredsSniffHashType",
        )
        self.CredsSniffHashType = self.creds_sniff_hash_type
        self.hosts = UnaryUnaryMultiCallable(
            raw.Hosts,
            commonpb.Empty,
            clientpb.AllHosts,
            "Hosts",
        )
        self.Hosts = self.hosts
        self.host = UnaryUnaryMultiCallable(
            raw.Host,
            clientpb.Host,
            clientpb.Host,
            "Host",
        )
        self.Host = self.host
        self.host_rm = UnaryUnaryMultiCallable(
            raw.HostRm,
            clientpb.Host,
            commonpb.Empty,
            "HostRm",
        )
        self.HostRm = self.host_rm
        self.host_ioc_rm = UnaryUnaryMultiCallable(
            raw.HostIOCRm,
            clientpb.IOC,
            commonpb.Empty,
            "HostIOCRm",
        )
        self.HostIOCRm = self.host_ioc_rm
        self.generate = UnaryUnaryMultiCallable(
            raw.Generate,
            clientpb.GenerateReq,
            clientpb.Generate,
            "Generate",
        )
        self.Generate = self.generate
        self.generate_spoof_metadata = UnaryUnaryMultiCallable(
            raw.GenerateSpoofMetadata,
            clientpb.GenerateSpoofMetadataReq,
            commonpb.Empty,
            "GenerateSpoofMetadata",
        )
        self.GenerateSpoofMetadata = self.generate_spoof_metadata
        self.generate_external = UnaryUnaryMultiCallable(
            raw.GenerateExternal,
            clientpb.ExternalGenerateReq,
            clientpb.ExternalImplantConfig,
            "GenerateExternal",
        )
        self.GenerateExternal = self.generate_external
        self.generate_external_save_build = UnaryUnaryMultiCallable(
            raw.GenerateExternalSaveBuild,
            clientpb.ExternalImplantBinary,
            commonpb.Empty,
            "GenerateExternalSaveBuild",
        )
        self.GenerateExternalSaveBuild = self.generate_external_save_build
        self.generate_external_get_build_config = UnaryUnaryMultiCallable(
            raw.GenerateExternalGetBuildConfig,
            clientpb.ImplantBuild,
            clientpb.ExternalImplantConfig,
            "GenerateExternalGetBuildConfig",
        )
        self.GenerateExternalGetBuildConfig = self.generate_external_get_build_config
        self.generate_stage = UnaryUnaryMultiCallable(
            raw.GenerateStage,
            clientpb.GenerateStageReq,
            clientpb.Generate,
            "GenerateStage",
        )
        self.GenerateStage = self.generate_stage
        self.stage_implant_build = UnaryUnaryMultiCallable(
            raw.StageImplantBuild,
            clientpb.ImplantStageReq,
            commonpb.Empty,
            "StageImplantBuild",
        )
        self.StageImplantBuild = self.stage_implant_build
        self.get_httpc2_profiles = UnaryUnaryMultiCallable(
            raw.GetHTTPC2Profiles,
            commonpb.Empty,
            clientpb.HTTPC2Configs,
            "GetHTTPC2Profiles",
        )
        self.GetHTTPC2Profiles = self.get_httpc2_profiles
        self.get_httpc2_profile_by_name = UnaryUnaryMultiCallable(
            raw.GetHTTPC2ProfileByName,
            clientpb.C2ProfileReq,
            clientpb.HTTPC2Config,
            "GetHTTPC2ProfileByName",
        )
        self.GetHTTPC2ProfileByName = self.get_httpc2_profile_by_name
        self.save_httpc2_profile = UnaryUnaryMultiCallable(
            raw.SaveHTTPC2Profile,
            clientpb.HTTPC2ConfigReq,
            commonpb.Empty,
            "SaveHTTPC2Profile",
        )
        self.SaveHTTPC2Profile = self.save_httpc2_profile
        self.builder_register = UnaryStreamMultiCallable(
            raw.BuilderRegister,
            clientpb.Builder,
            clientpb.Event,
            "BuilderRegister",
        )
        self.BuilderRegister = self.builder_register
        self.builder_trigger = UnaryUnaryMultiCallable(
            raw.BuilderTrigger,
            clientpb.Event,
            commonpb.Empty,
            "BuilderTrigger",
        )
        self.BuilderTrigger = self.builder_trigger
        self.builders = UnaryUnaryMultiCallable(
            raw.Builders,
            commonpb.Empty,
            clientpb.Builders,
            "Builders",
        )
        self.Builders = self.builders
        self.get_certificate_info = UnaryUnaryMultiCallable(
            raw.GetCertificateInfo,
            clientpb.CertificatesReq,
            clientpb.CertificateInfo,
            "GetCertificateInfo",
        )
        self.GetCertificateInfo = self.get_certificate_info
        self.get_certificate_authority_info = UnaryUnaryMultiCallable(
            raw.GetCertificateAuthorityInfo,
            commonpb.Empty,
            clientpb.CertificateAuthorityInfo,
            "GetCertificateAuthorityInfo",
        )
        self.GetCertificateAuthorityInfo = self.get_certificate_authority_info
        self.crack = UnaryUnaryMultiCallable(
            raw.Crack,
            clientpb.CrackCommand,
            clientpb.CrackResponse,
            "Crack",
        )
        self.Crack = self.crack
        self.crackstation_register = UnaryStreamMultiCallable(
            raw.CrackstationRegister,
            clientpb.Crackstation,
            clientpb.Event,
            "CrackstationRegister",
        )
        self.CrackstationRegister = self.crackstation_register
        self.crackstation_trigger = UnaryUnaryMultiCallable(
            raw.CrackstationTrigger,
            clientpb.Event,
            commonpb.Empty,
            "CrackstationTrigger",
        )
        self.CrackstationTrigger = self.crackstation_trigger
        self.crackstation_benchmark = UnaryUnaryMultiCallable(
            raw.CrackstationBenchmark,
            clientpb.CrackBenchmark,
            commonpb.Empty,
            "CrackstationBenchmark",
        )
        self.CrackstationBenchmark = self.crackstation_benchmark
        self.crackstations = UnaryUnaryMultiCallable(
            raw.Crackstations,
            commonpb.Empty,
            clientpb.Crackstations,
            "Crackstations",
        )
        self.Crackstations = self.crackstations
        self.crack_task_by_id = UnaryUnaryMultiCallable(
            raw.CrackTaskByID,
            clientpb.CrackTask,
            clientpb.CrackTask,
            "CrackTaskByID",
        )
        self.CrackTaskByID = self.crack_task_by_id
        self.crack_task_update = UnaryUnaryMultiCallable(
            raw.CrackTaskUpdate,
            clientpb.CrackTask,
            commonpb.Empty,
            "CrackTaskUpdate",
        )
        self.CrackTaskUpdate = self.crack_task_update
        self.crack_files_list = UnaryUnaryMultiCallable(
            raw.CrackFilesList,
            clientpb.CrackFile,
            clientpb.CrackFiles,
            "CrackFilesList",
        )
        self.CrackFilesList = self.crack_files_list
        self.crack_file_create = UnaryUnaryMultiCallable(
            raw.CrackFileCreate,
            clientpb.CrackFile,
            clientpb.CrackFile,
            "CrackFileCreate",
        )
        self.CrackFileCreate = self.crack_file_create
        self.crack_file_chunk_upload = UnaryUnaryMultiCallable(
            raw.CrackFileChunkUpload,
            clientpb.CrackFileChunk,
            commonpb.Empty,
            "CrackFileChunkUpload",
        )
        self.CrackFileChunkUpload = self.crack_file_chunk_upload
        self.crack_file_chunk_download = UnaryUnaryMultiCallable(
            raw.CrackFileChunkDownload,
            clientpb.CrackFileChunk,
            clientpb.CrackFileChunk,
            "CrackFileChunkDownload",
        )
        self.CrackFileChunkDownload = self.crack_file_chunk_download
        self.crack_file_complete = UnaryUnaryMultiCallable(
            raw.CrackFileComplete,
            clientpb.CrackFile,
            commonpb.Empty,
            "CrackFileComplete",
        )
        self.CrackFileComplete = self.crack_file_complete
        self.crack_file_delete = UnaryUnaryMultiCallable(
            raw.CrackFileDelete,
            clientpb.CrackFile,
            commonpb.Empty,
            "CrackFileDelete",
        )
        self.CrackFileDelete = self.crack_file_delete
        self.regenerate = UnaryUnaryMultiCallable(
            raw.Regenerate,
            clientpb.RegenerateReq,
            clientpb.Generate,
            "Regenerate",
        )
        self.Regenerate = self.regenerate
        self.implant_builds = UnaryUnaryMultiCallable(
            raw.ImplantBuilds,
            commonpb.Empty,
            clientpb.ImplantBuilds,
            "ImplantBuilds",
        )
        self.ImplantBuilds = self.implant_builds
        self.delete_implant_build = UnaryUnaryMultiCallable(
            raw.DeleteImplantBuild,
            clientpb.DeleteReq,
            commonpb.Empty,
            "DeleteImplantBuild",
        )
        self.DeleteImplantBuild = self.delete_implant_build
        self.canaries = UnaryUnaryMultiCallable(
            raw.Canaries,
            commonpb.Empty,
            clientpb.Canaries,
            "Canaries",
        )
        self.Canaries = self.canaries
        self.generate_wg_client_config = UnaryUnaryMultiCallable(
            raw.GenerateWGClientConfig,
            commonpb.Empty,
            clientpb.WGClientConfig,
            "GenerateWGClientConfig",
        )
        self.GenerateWGClientConfig = self.generate_wg_client_config
        self.generate_unique_ip = UnaryUnaryMultiCallable(
            raw.GenerateUniqueIP,
            commonpb.Empty,
            clientpb.UniqueWGIP,
            "GenerateUniqueIP",
        )
        self.GenerateUniqueIP = self.generate_unique_ip
        self.implant_profiles = UnaryUnaryMultiCallable(
            raw.ImplantProfiles,
            commonpb.Empty,
            clientpb.ImplantProfiles,
            "ImplantProfiles",
        )
        self.ImplantProfiles = self.implant_profiles
        self.delete_implant_profile = UnaryUnaryMultiCallable(
            raw.DeleteImplantProfile,
            clientpb.DeleteReq,
            commonpb.Empty,
            "DeleteImplantProfile",
        )
        self.DeleteImplantProfile = self.delete_implant_profile
        self.save_implant_profile = UnaryUnaryMultiCallable(
            raw.SaveImplantProfile,
            clientpb.ImplantProfile,
            clientpb.ImplantProfile,
            "SaveImplantProfile",
        )
        self.SaveImplantProfile = self.save_implant_profile
        self.shellcode_rdi = UnaryUnaryMultiCallable(
            raw.ShellcodeRDI,
            clientpb.ShellcodeRDIReq,
            clientpb.ShellcodeRDI,
            "ShellcodeRDI",
        )
        self.ShellcodeRDI = self.shellcode_rdi
        self.get_compiler = UnaryUnaryMultiCallable(
            raw.GetCompiler,
            commonpb.Empty,
            clientpb.Compiler,
            "GetCompiler",
        )
        self.GetCompiler = self.get_compiler
        self.shellcode_encoder = UnaryUnaryMultiCallable(
            raw.ShellcodeEncoder,
            clientpb.ShellcodeEncodeReq,
            clientpb.ShellcodeEncode,
            "ShellcodeEncoder",
        )
        self.ShellcodeEncoder = self.shellcode_encoder
        self.shellcode_encoder_map = UnaryUnaryMultiCallable(
            raw.ShellcodeEncoderMap,
            commonpb.Empty,
            clientpb.ShellcodeEncoderMap,
            "ShellcodeEncoderMap",
        )
        self.ShellcodeEncoderMap = self.shellcode_encoder_map
        self.traffic_encoder_map = UnaryUnaryMultiCallable(
            raw.TrafficEncoderMap,
            commonpb.Empty,
            clientpb.TrafficEncoderMap,
            "TrafficEncoderMap",
        )
        self.TrafficEncoderMap = self.traffic_encoder_map
        self.traffic_encoder_add = UnaryUnaryMultiCallable(
            raw.TrafficEncoderAdd,
            clientpb.TrafficEncoder,
            clientpb.TrafficEncoderTests,
            "TrafficEncoderAdd",
        )
        self.TrafficEncoderAdd = self.traffic_encoder_add
        self.traffic_encoder_rm = UnaryUnaryMultiCallable(
            raw.TrafficEncoderRm,
            clientpb.TrafficEncoder,
            commonpb.Empty,
            "TrafficEncoderRm",
        )
        self.TrafficEncoderRm = self.traffic_encoder_rm
        self.websites = UnaryUnaryMultiCallable(
            raw.Websites,
            commonpb.Empty,
            clientpb.Websites,
            "Websites",
        )
        self.Websites = self.websites
        self.website = UnaryUnaryMultiCallable(
            raw.Website,
            clientpb.Website,
            clientpb.Website,
            "Website",
        )
        self.Website = self.website
        self.website_remove = UnaryUnaryMultiCallable(
            raw.WebsiteRemove,
            clientpb.Website,
            commonpb.Empty,
            "WebsiteRemove",
        )
        self.WebsiteRemove = self.website_remove
        self.website_add_content = UnaryUnaryMultiCallable(
            raw.WebsiteAddContent,
            clientpb.WebsiteAddContent,
            clientpb.Website,
            "WebsiteAddContent",
        )
        self.WebsiteAddContent = self.website_add_content
        self.website_update_content = UnaryUnaryMultiCallable(
            raw.WebsiteUpdateContent,
            clientpb.WebsiteAddContent,
            clientpb.Website,
            "WebsiteUpdateContent",
        )
        self.WebsiteUpdateContent = self.website_update_content
        self.website_remove_content = UnaryUnaryMultiCallable(
            raw.WebsiteRemoveContent,
            clientpb.WebsiteRemoveContent,
            clientpb.Website,
            "WebsiteRemoveContent",
        )
        self.WebsiteRemoveContent = self.website_remove_content
        self.ping = UnaryUnaryMultiCallable(
            raw.Ping,
            sliverpb.Ping,
            sliverpb.Ping,
            "Ping",
        )
        self.Ping = self.ping
        self.ps = UnaryUnaryMultiCallable(
            raw.Ps,
            sliverpb.PsReq,
            sliverpb.Ps,
            "Ps",
        )
        self.Ps = self.ps
        self.terminate = UnaryUnaryMultiCallable(
            raw.Terminate,
            sliverpb.TerminateReq,
            sliverpb.Terminate,
            "Terminate",
        )
        self.Terminate = self.terminate
        self.ifconfig = UnaryUnaryMultiCallable(
            raw.Ifconfig,
            sliverpb.IfconfigReq,
            sliverpb.Ifconfig,
            "Ifconfig",
        )
        self.Ifconfig = self.ifconfig
        self.netstat = UnaryUnaryMultiCallable(
            raw.Netstat,
            sliverpb.NetstatReq,
            sliverpb.Netstat,
            "Netstat",
        )
        self.Netstat = self.netstat
        self.ls = UnaryUnaryMultiCallable(
            raw.Ls,
            sliverpb.LsReq,
            sliverpb.Ls,
            "Ls",
        )
        self.Ls = self.ls
        self.cd = UnaryUnaryMultiCallable(
            raw.Cd,
            sliverpb.CdReq,
            sliverpb.Pwd,
            "Cd",
        )
        self.Cd = self.cd
        self.pwd = UnaryUnaryMultiCallable(
            raw.Pwd,
            sliverpb.PwdReq,
            sliverpb.Pwd,
            "Pwd",
        )
        self.Pwd = self.pwd
        self.mv = UnaryUnaryMultiCallable(
            raw.Mv,
            sliverpb.MvReq,
            sliverpb.Mv,
            "Mv",
        )
        self.Mv = self.mv
        self.cp = UnaryUnaryMultiCallable(
            raw.Cp,
            sliverpb.CpReq,
            sliverpb.Cp,
            "Cp",
        )
        self.Cp = self.cp
        self.rm = UnaryUnaryMultiCallable(
            raw.Rm,
            sliverpb.RmReq,
            sliverpb.Rm,
            "Rm",
        )
        self.Rm = self.rm
        self.mkdir = UnaryUnaryMultiCallable(
            raw.Mkdir,
            sliverpb.MkdirReq,
            sliverpb.Mkdir,
            "Mkdir",
        )
        self.Mkdir = self.mkdir
        self.download = UnaryUnaryMultiCallable(
            raw.Download,
            sliverpb.DownloadReq,
            sliverpb.Download,
            "Download",
        )
        self.Download = self.download
        self.upload = UnaryUnaryMultiCallable(
            raw.Upload,
            sliverpb.UploadReq,
            sliverpb.Upload,
            "Upload",
        )
        self.Upload = self.upload
        self.grep = UnaryUnaryMultiCallable(
            raw.Grep,
            sliverpb.GrepReq,
            sliverpb.Grep,
            "Grep",
        )
        self.Grep = self.grep
        self.chmod = UnaryUnaryMultiCallable(
            raw.Chmod,
            sliverpb.ChmodReq,
            sliverpb.Chmod,
            "Chmod",
        )
        self.Chmod = self.chmod
        self.chown = UnaryUnaryMultiCallable(
            raw.Chown,
            sliverpb.ChownReq,
            sliverpb.Chown,
            "Chown",
        )
        self.Chown = self.chown
        self.chtimes = UnaryUnaryMultiCallable(
            raw.Chtimes,
            sliverpb.ChtimesReq,
            sliverpb.Chtimes,
            "Chtimes",
        )
        self.Chtimes = self.chtimes
        self.memfiles_list = UnaryUnaryMultiCallable(
            raw.MemfilesList,
            sliverpb.MemfilesListReq,
            sliverpb.Ls,
            "MemfilesList",
        )
        self.MemfilesList = self.memfiles_list
        self.memfiles_add = UnaryUnaryMultiCallable(
            raw.MemfilesAdd,
            sliverpb.MemfilesAddReq,
            sliverpb.MemfilesAdd,
            "MemfilesAdd",
        )
        self.MemfilesAdd = self.memfiles_add
        self.memfiles_rm = UnaryUnaryMultiCallable(
            raw.MemfilesRm,
            sliverpb.MemfilesRmReq,
            sliverpb.MemfilesRm,
            "MemfilesRm",
        )
        self.MemfilesRm = self.memfiles_rm
        self.mount = UnaryUnaryMultiCallable(
            raw.Mount,
            sliverpb.MountReq,
            sliverpb.Mount,
            "Mount",
        )
        self.Mount = self.mount
        self.process_dump = UnaryUnaryMultiCallable(
            raw.ProcessDump,
            sliverpb.ProcessDumpReq,
            sliverpb.ProcessDump,
            "ProcessDump",
        )
        self.ProcessDump = self.process_dump
        self.run_as = UnaryUnaryMultiCallable(
            raw.RunAs,
            sliverpb.RunAsReq,
            sliverpb.RunAs,
            "RunAs",
        )
        self.RunAs = self.run_as
        self.impersonate = UnaryUnaryMultiCallable(
            raw.Impersonate,
            sliverpb.ImpersonateReq,
            sliverpb.Impersonate,
            "Impersonate",
        )
        self.Impersonate = self.impersonate
        self.rev_to_self = UnaryUnaryMultiCallable(
            raw.RevToSelf,
            sliverpb.RevToSelfReq,
            sliverpb.RevToSelf,
            "RevToSelf",
        )
        self.RevToSelf = self.rev_to_self
        self.get_system = UnaryUnaryMultiCallable(
            raw.GetSystem,
            clientpb.GetSystemReq,
            sliverpb.GetSystem,
            "GetSystem",
        )
        self.GetSystem = self.get_system
        self.task = UnaryUnaryMultiCallable(
            raw.Task,
            sliverpb.TaskReq,
            sliverpb.Task,
            "Task",
        )
        self.Task = self.task
        self.msf = UnaryUnaryMultiCallable(
            raw.Msf,
            clientpb.MSFReq,
            sliverpb.Task,
            "Msf",
        )
        self.Msf = self.msf
        self.msf_remote = UnaryUnaryMultiCallable(
            raw.MsfRemote,
            clientpb.MSFRemoteReq,
            sliverpb.Task,
            "MsfRemote",
        )
        self.MsfRemote = self.msf_remote
        self.execute_assembly = UnaryUnaryMultiCallable(
            raw.ExecuteAssembly,
            sliverpb.ExecuteAssemblyReq,
            sliverpb.ExecuteAssembly,
            "ExecuteAssembly",
        )
        self.ExecuteAssembly = self.execute_assembly
        self.migrate = UnaryUnaryMultiCallable(
            raw.Migrate,
            clientpb.MigrateReq,
            sliverpb.Migrate,
            "Migrate",
        )
        self.Migrate = self.migrate
        self.execute = UnaryUnaryMultiCallable(
            raw.Execute,
            sliverpb.ExecuteReq,
            sliverpb.Execute,
            "Execute",
        )
        self.Execute = self.execute
        self.execute_windows = UnaryUnaryMultiCallable(
            raw.ExecuteWindows,
            sliverpb.ExecuteWindowsReq,
            sliverpb.Execute,
            "ExecuteWindows",
        )
        self.ExecuteWindows = self.execute_windows
        self.execute_children = UnaryUnaryMultiCallable(
            raw.ExecuteChildren,
            sliverpb.ExecuteChildrenReq,
            sliverpb.ExecuteChildren,
            "ExecuteChildren",
        )
        self.ExecuteChildren = self.execute_children
        self.sideload = UnaryUnaryMultiCallable(
            raw.Sideload,
            sliverpb.SideloadReq,
            sliverpb.Sideload,
            "Sideload",
        )
        self.Sideload = self.sideload
        self.spawn_dll = UnaryUnaryMultiCallable(
            raw.SpawnDll,
            sliverpb.InvokeSpawnDllReq,
            sliverpb.SpawnDll,
            "SpawnDll",
        )
        self.SpawnDll = self.spawn_dll
        self.screenshot = UnaryUnaryMultiCallable(
            raw.Screenshot,
            sliverpb.ScreenshotReq,
            sliverpb.Screenshot,
            "Screenshot",
        )
        self.Screenshot = self.screenshot
        self.current_token_owner = UnaryUnaryMultiCallable(
            raw.CurrentTokenOwner,
            sliverpb.CurrentTokenOwnerReq,
            sliverpb.CurrentTokenOwner,
            "CurrentTokenOwner",
        )
        self.CurrentTokenOwner = self.current_token_owner
        self.services = UnaryUnaryMultiCallable(
            raw.Services,
            sliverpb.ServicesReq,
            sliverpb.Services,
            "Services",
        )
        self.Services = self.services
        self.service_detail = UnaryUnaryMultiCallable(
            raw.ServiceDetail,
            sliverpb.ServiceDetailReq,
            sliverpb.ServiceDetail,
            "ServiceDetail",
        )
        self.ServiceDetail = self.service_detail
        self.start_service_by_name = UnaryUnaryMultiCallable(
            raw.StartServiceByName,
            sliverpb.StartServiceByNameReq,
            sliverpb.ServiceInfo,
            "StartServiceByName",
        )
        self.StartServiceByName = self.start_service_by_name
        self.pivot_start_listener = UnaryUnaryMultiCallable(
            raw.PivotStartListener,
            sliverpb.PivotStartListenerReq,
            sliverpb.PivotListener,
            "PivotStartListener",
        )
        self.PivotStartListener = self.pivot_start_listener
        self.pivot_stop_listener = UnaryUnaryMultiCallable(
            raw.PivotStopListener,
            sliverpb.PivotStopListenerReq,
            commonpb.Empty,
            "PivotStopListener",
        )
        self.PivotStopListener = self.pivot_stop_listener
        self.pivot_session_listeners = UnaryUnaryMultiCallable(
            raw.PivotSessionListeners,
            sliverpb.PivotListenersReq,
            sliverpb.PivotListeners,
            "PivotSessionListeners",
        )
        self.PivotSessionListeners = self.pivot_session_listeners
        self.pivot_graph = UnaryUnaryMultiCallable(
            raw.PivotGraph,
            commonpb.Empty,
            clientpb.PivotGraph,
            "PivotGraph",
        )
        self.PivotGraph = self.pivot_graph
        self.start_service = UnaryUnaryMultiCallable(
            raw.StartService,
            sliverpb.StartServiceReq,
            sliverpb.ServiceInfo,
            "StartService",
        )
        self.StartService = self.start_service
        self.stop_service = UnaryUnaryMultiCallable(
            raw.StopService,
            sliverpb.StopServiceReq,
            sliverpb.ServiceInfo,
            "StopService",
        )
        self.StopService = self.stop_service
        self.remove_service = UnaryUnaryMultiCallable(
            raw.RemoveService,
            sliverpb.RemoveServiceReq,
            sliverpb.ServiceInfo,
            "RemoveService",
        )
        self.RemoveService = self.remove_service
        self.make_token = UnaryUnaryMultiCallable(
            raw.MakeToken,
            sliverpb.MakeTokenReq,
            sliverpb.MakeToken,
            "MakeToken",
        )
        self.MakeToken = self.make_token
        self.get_env = UnaryUnaryMultiCallable(
            raw.GetEnv,
            sliverpb.EnvReq,
            sliverpb.EnvInfo,
            "GetEnv",
        )
        self.GetEnv = self.get_env
        self.set_env = UnaryUnaryMultiCallable(
            raw.SetEnv,
            sliverpb.SetEnvReq,
            sliverpb.SetEnv,
            "SetEnv",
        )
        self.SetEnv = self.set_env
        self.unset_env = UnaryUnaryMultiCallable(
            raw.UnsetEnv,
            sliverpb.UnsetEnvReq,
            sliverpb.UnsetEnv,
            "UnsetEnv",
        )
        self.UnsetEnv = self.unset_env
        self.backdoor = UnaryUnaryMultiCallable(
            raw.Backdoor,
            clientpb.BackdoorReq,
            clientpb.Backdoor,
            "Backdoor",
        )
        self.Backdoor = self.backdoor
        self.registry_read = UnaryUnaryMultiCallable(
            raw.RegistryRead,
            sliverpb.RegistryReadReq,
            sliverpb.RegistryRead,
            "RegistryRead",
        )
        self.RegistryRead = self.registry_read
        self.registry_write = UnaryUnaryMultiCallable(
            raw.RegistryWrite,
            sliverpb.RegistryWriteReq,
            sliverpb.RegistryWrite,
            "RegistryWrite",
        )
        self.RegistryWrite = self.registry_write
        self.registry_create_key = UnaryUnaryMultiCallable(
            raw.RegistryCreateKey,
            sliverpb.RegistryCreateKeyReq,
            sliverpb.RegistryCreateKey,
            "RegistryCreateKey",
        )
        self.RegistryCreateKey = self.registry_create_key
        self.registry_delete_key = UnaryUnaryMultiCallable(
            raw.RegistryDeleteKey,
            sliverpb.RegistryDeleteKeyReq,
            sliverpb.RegistryDeleteKey,
            "RegistryDeleteKey",
        )
        self.RegistryDeleteKey = self.registry_delete_key
        self.registry_list_sub_keys = UnaryUnaryMultiCallable(
            raw.RegistryListSubKeys,
            sliverpb.RegistrySubKeyListReq,
            sliverpb.RegistrySubKeyList,
            "RegistryListSubKeys",
        )
        self.RegistryListSubKeys = self.registry_list_sub_keys
        self.registry_list_values = UnaryUnaryMultiCallable(
            raw.RegistryListValues,
            sliverpb.RegistryListValuesReq,
            sliverpb.RegistryValuesList,
            "RegistryListValues",
        )
        self.RegistryListValues = self.registry_list_values
        self.registry_read_hive = UnaryUnaryMultiCallable(
            raw.RegistryReadHive,
            sliverpb.RegistryReadHiveReq,
            sliverpb.RegistryReadHive,
            "RegistryReadHive",
        )
        self.RegistryReadHive = self.registry_read_hive
        self.run_ssh_command = UnaryUnaryMultiCallable(
            raw.RunSSHCommand,
            sliverpb.SSHCommandReq,
            sliverpb.SSHCommand,
            "RunSSHCommand",
        )
        self.RunSSHCommand = self.run_ssh_command
        self.hijack_dll = UnaryUnaryMultiCallable(
            raw.HijackDLL,
            clientpb.DllHijackReq,
            clientpb.DllHijack,
            "HijackDLL",
        )
        self.HijackDLL = self.hijack_dll
        self.get_privs = UnaryUnaryMultiCallable(
            raw.GetPrivs,
            sliverpb.GetPrivsReq,
            sliverpb.GetPrivs,
            "GetPrivs",
        )
        self.GetPrivs = self.get_privs
        self.start_rport_fwd_listener = UnaryUnaryMultiCallable(
            raw.StartRportFwdListener,
            sliverpb.RportFwdStartListenerReq,
            sliverpb.RportFwdListener,
            "StartRportFwdListener",
        )
        self.StartRportFwdListener = self.start_rport_fwd_listener
        self.get_rport_fwd_listeners = UnaryUnaryMultiCallable(
            raw.GetRportFwdListeners,
            sliverpb.RportFwdListenersReq,
            sliverpb.RportFwdListeners,
            "GetRportFwdListeners",
        )
        self.GetRportFwdListeners = self.get_rport_fwd_listeners
        self.stop_rport_fwd_listener = UnaryUnaryMultiCallable(
            raw.StopRportFwdListener,
            sliverpb.RportFwdStopListenerReq,
            sliverpb.RportFwdListener,
            "StopRportFwdListener",
        )
        self.StopRportFwdListener = self.stop_rport_fwd_listener
        self.open_session = UnaryUnaryMultiCallable(
            raw.OpenSession,
            sliverpb.OpenSession,
            sliverpb.OpenSession,
            "OpenSession",
        )
        self.OpenSession = self.open_session
        self.close_session = UnaryUnaryMultiCallable(
            raw.CloseSession,
            sliverpb.CloseSession,
            commonpb.Empty,
            "CloseSession",
        )
        self.CloseSession = self.close_session
        self.register_extension = UnaryUnaryMultiCallable(
            raw.RegisterExtension,
            sliverpb.RegisterExtensionReq,
            sliverpb.RegisterExtension,
            "RegisterExtension",
        )
        self.RegisterExtension = self.register_extension
        self.call_extension = UnaryUnaryMultiCallable(
            raw.CallExtension,
            sliverpb.CallExtensionReq,
            sliverpb.CallExtension,
            "CallExtension",
        )
        self.CallExtension = self.call_extension
        self.list_extensions = UnaryUnaryMultiCallable(
            raw.ListExtensions,
            sliverpb.ListExtensionsReq,
            sliverpb.ListExtensions,
            "ListExtensions",
        )
        self.ListExtensions = self.list_extensions
        self.register_wasm_extension = UnaryUnaryMultiCallable(
            raw.RegisterWasmExtension,
            sliverpb.RegisterWasmExtensionReq,
            sliverpb.RegisterWasmExtension,
            "RegisterWasmExtension",
        )
        self.RegisterWasmExtension = self.register_wasm_extension
        self.list_wasm_extensions = UnaryUnaryMultiCallable(
            raw.ListWasmExtensions,
            sliverpb.ListWasmExtensionsReq,
            sliverpb.ListWasmExtensions,
            "ListWasmExtensions",
        )
        self.ListWasmExtensions = self.list_wasm_extensions
        self.exec_wasm_extension = UnaryUnaryMultiCallable(
            raw.ExecWasmExtension,
            sliverpb.ExecWasmExtensionReq,
            sliverpb.ExecWasmExtension,
            "ExecWasmExtension",
        )
        self.ExecWasmExtension = self.exec_wasm_extension
        self.wg_start_port_forward = UnaryUnaryMultiCallable(
            raw.WGStartPortForward,
            sliverpb.WGPortForwardStartReq,
            sliverpb.WGPortForward,
            "WGStartPortForward",
        )
        self.WGStartPortForward = self.wg_start_port_forward
        self.wg_stop_port_forward = UnaryUnaryMultiCallable(
            raw.WGStopPortForward,
            sliverpb.WGPortForwardStopReq,
            sliverpb.WGPortForward,
            "WGStopPortForward",
        )
        self.WGStopPortForward = self.wg_stop_port_forward
        self.wg_start_socks = UnaryUnaryMultiCallable(
            raw.WGStartSocks,
            sliverpb.WGSocksStartReq,
            sliverpb.WGSocks,
            "WGStartSocks",
        )
        self.WGStartSocks = self.wg_start_socks
        self.wg_stop_socks = UnaryUnaryMultiCallable(
            raw.WGStopSocks,
            sliverpb.WGSocksStopReq,
            sliverpb.WGSocks,
            "WGStopSocks",
        )
        self.WGStopSocks = self.wg_stop_socks
        self.wg_list_forwarders = UnaryUnaryMultiCallable(
            raw.WGListForwarders,
            sliverpb.WGTCPForwardersReq,
            sliverpb.WGTCPForwarders,
            "WGListForwarders",
        )
        self.WGListForwarders = self.wg_list_forwarders
        self.wg_list_socks_servers = UnaryUnaryMultiCallable(
            raw.WGListSocksServers,
            sliverpb.WGSocksServersReq,
            sliverpb.WGSocksServers,
            "WGListSocksServers",
        )
        self.WGListSocksServers = self.wg_list_socks_servers
        self.shell = UnaryUnaryMultiCallable(
            raw.Shell,
            sliverpb.ShellReq,
            sliverpb.Shell,
            "Shell",
        )
        self.Shell = self.shell
        self.shell_resize = UnaryUnaryMultiCallable(
            raw.ShellResize,
            sliverpb.ShellResizeReq,
            commonpb.Empty,
            "ShellResize",
        )
        self.ShellResize = self.shell_resize
        self.portfwd = UnaryUnaryMultiCallable(
            raw.Portfwd,
            sliverpb.PortfwdReq,
            sliverpb.Portfwd,
            "Portfwd",
        )
        self.Portfwd = self.portfwd
        self.create_socks = UnaryUnaryMultiCallable(
            raw.CreateSocks,
            sliverpb.Socks,
            sliverpb.Socks,
            "CreateSocks",
        )
        self.CreateSocks = self.create_socks
        self.close_socks = UnaryUnaryMultiCallable(
            raw.CloseSocks,
            sliverpb.Socks,
            commonpb.Empty,
            "CloseSocks",
        )
        self.CloseSocks = self.close_socks
        self.socks_proxy = StreamStreamMultiCallable(
            raw.SocksProxy,
            sliverpb.SocksData,
            sliverpb.SocksData,
            "SocksProxy",
        )
        self.SocksProxy = self.socks_proxy
        self.create_tunnel = UnaryUnaryMultiCallable(
            raw.CreateTunnel,
            sliverpb.Tunnel,
            sliverpb.Tunnel,
            "CreateTunnel",
        )
        self.CreateTunnel = self.create_tunnel
        self.close_tunnel = UnaryUnaryMultiCallable(
            raw.CloseTunnel,
            sliverpb.Tunnel,
            commonpb.Empty,
            "CloseTunnel",
        )
        self.CloseTunnel = self.close_tunnel
        self.tunnel_data = StreamStreamMultiCallable(
            raw.TunnelData,
            sliverpb.TunnelData,
            sliverpb.TunnelData,
            "TunnelData",
        )
        self.TunnelData = self.tunnel_data
        self.events = UnaryStreamMultiCallable(
            raw.Events,
            commonpb.Empty,
            clientpb.Event,
            "Events",
        )
        self.Events = self.events


RPC_METHOD_COUNT = 193
