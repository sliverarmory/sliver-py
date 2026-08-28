"""Concrete, Pydantic-only adapter for the generated Sliver gRPC stub."""

from __future__ import annotations

import grpc

from ._pb.rpcpb.services_pb2_grpc import SliverRPCStub as _WireSliverRPCStub
from ._rpc_base import (
    StreamStreamCall,
    StreamStreamMultiCallable,
    StreamUnaryCall,
    StreamUnaryMultiCallable,
    UnaryStreamCall,
    UnaryStreamMultiCallable,
    UnaryUnaryCall,
    UnaryUnaryMultiCallable,
)
from ._rpc_generated import GeneratedPydanticSliverRPCStub


class PydanticSliverRPCStub(GeneratedPydanticSliverRPCStub):
    """Expose every Sliver RPC with concrete Pydantic request/response types."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        # The protobuf stub is deliberately private. Only the converted,
        # descriptor-generated method attributes are exposed to callers.
        self.__raw = _WireSliverRPCStub(channel)
        self._initialize_rpc_methods(self.__raw)


__all__ = [
    "PydanticSliverRPCStub",
    "StreamStreamCall",
    "StreamStreamMultiCallable",
    "StreamUnaryCall",
    "StreamUnaryMultiCallable",
    "UnaryStreamCall",
    "UnaryStreamMultiCallable",
    "UnaryUnaryCall",
    "UnaryUnaryMultiCallable",
]
