from __future__ import annotations

from typing import cast, get_args, get_origin, get_type_hints

import grpc

from scripts.rpcgen import _python_method_name
from sliver import models
from sliver._pb.rpcpb import services_pb2
from sliver._pb.rpcpb.services_pb2_grpc import SliverRPCStub as _WireSliverRPCStub
from sliver._rpc import (
    PydanticSliverRPCStub,
    StreamStreamCall,
    StreamStreamMultiCallable,
    StreamUnaryCall,
    StreamUnaryMultiCallable,
    UnaryStreamCall,
    UnaryStreamMultiCallable,
    UnaryUnaryCall,
    UnaryUnaryMultiCallable,
)

_CALL_TYPES = {
    (False, False): UnaryUnaryMultiCallable,
    (False, True): UnaryStreamMultiCallable,
    (True, False): StreamUnaryMultiCallable,
    (True, True): StreamStreamMultiCallable,
}


class _FakeChannel:
    def _method(self, *args: object, **kwargs: object) -> object:
        def invoke(*call_args: object, **call_kwargs: object) -> object:
            return object()

        return invoke

    unary_unary = _method
    unary_stream = _method
    stream_unary = _method
    stream_stream = _method


def test_all_rpc_attributes_have_exact_concrete_model_types() -> None:
    service = services_pb2.DESCRIPTOR.services_by_name["SliverRPC"]
    hints = get_type_hints(PydanticSliverRPCStub)

    assert len(service.methods) == 193
    expected_names = set(service.methods_by_name)
    expected_names.update(_python_method_name(name) for name in service.methods_by_name)
    assert set(hints) == expected_names

    for method in service.methods:
        annotation = hints[method.name]
        assert (
            get_origin(annotation)
            is _CALL_TYPES[(method.client_streaming, method.server_streaming)]
        )
        assert get_args(annotation) == (
            models.MODEL_REGISTRY[method.input_type.full_name],
            models.MODEL_REGISTRY[method.output_type.full_name],
        )
        assert hints[_python_method_name(method.name)] == annotation


def test_generated_stub_eagerly_binds_every_typed_rpc_attribute() -> None:
    channel = cast(grpc.aio.Channel, _FakeChannel())
    stub = PydanticSliverRPCStub(channel)
    service = services_pb2.DESCRIPTOR.services_by_name["SliverRPC"]

    assert not any("__getattr__" in parent.__dict__ for parent in type(stub).__mro__)
    assert isinstance(stub._PydanticSliverRPCStub__raw, _WireSliverRPCStub)

    for method in service.methods:
        rpc = getattr(stub, method.name)
        python_rpc = getattr(stub, _python_method_name(method.name))
        assert isinstance(
            rpc,
            _CALL_TYPES[(method.client_streaming, method.server_streaming)],
        )
        assert rpc.request_type is models.MODEL_REGISTRY[method.input_type.full_name]
        assert rpc.response_type is models.MODEL_REGISTRY[method.output_type.full_name]
        assert rpc.operation == method.name
        assert python_rpc is rpc


def test_call_classes_only_expose_operations_supported_by_their_rpc_shape() -> None:
    assert hasattr(UnaryUnaryCall, "__await__")
    assert not hasattr(UnaryUnaryCall, "__aiter__")
    assert not hasattr(UnaryUnaryCall, "read")
    assert not hasattr(UnaryUnaryCall, "write")

    assert not hasattr(UnaryStreamCall, "__await__")
    assert hasattr(UnaryStreamCall, "__aiter__")
    assert hasattr(UnaryStreamCall, "read")
    assert not hasattr(UnaryStreamCall, "write")

    assert hasattr(StreamUnaryCall, "__await__")
    assert not hasattr(StreamUnaryCall, "__aiter__")
    assert not hasattr(StreamUnaryCall, "read")
    assert hasattr(StreamUnaryCall, "write")

    assert not hasattr(StreamStreamCall, "__await__")
    assert hasattr(StreamStreamCall, "__aiter__")
    assert hasattr(StreamStreamCall, "read")
    assert hasattr(StreamStreamCall, "write")
