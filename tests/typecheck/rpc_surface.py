"""Static consumer contract for the concrete Pydantic RPC surface."""

from __future__ import annotations

from typing_extensions import assert_type

from sliver._rpc import (
    PydanticSliverRPCStub,
    StreamStreamCall,
    StreamUnaryCall,
    UnaryStreamCall,
    UnaryUnaryCall,
)
from sliver.models import clientpb, commonpb, sliverpb


async def check_rpc_types(stub: PydanticSliverRPCStub) -> None:
    version_call = stub.GetVersion(commonpb.Empty())
    assert_type(version_call, UnaryUnaryCall[clientpb.Version])
    assert_type(await version_call, clientpb.Version)

    event_call = stub.Events(commonpb.Empty())
    assert_type(event_call, UnaryStreamCall[clientpb.Event])
    async for event in event_call:
        assert_type(event, clientpb.Event)

    log_call = stub.ClientLog()
    assert_type(
        log_call,
        StreamUnaryCall[clientpb.ClientLogData, commonpb.Empty],
    )
    await log_call.write(clientpb.ClientLogData(stream="stdout", data=b"data"))
    assert_type(await log_call, commonpb.Empty)

    tunnel_call = stub.TunnelData()
    assert_type(
        tunnel_call,
        StreamStreamCall[sliverpb.TunnelData, sliverpb.TunnelData],
    )
    await tunnel_call.write(sliverpb.TunnelData())
    async for tunnel_data in tunnel_call:
        assert_type(tunnel_data, sliverpb.TunnelData)
