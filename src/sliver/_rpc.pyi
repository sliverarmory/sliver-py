"""Static Pydantic-only adapter for the generated Sliver gRPC stub."""

from ._rpc_base import (
    StreamStreamCall as StreamStreamCall,
)
from ._rpc_base import (
    StreamStreamMultiCallable as StreamStreamMultiCallable,
)
from ._rpc_base import (
    StreamUnaryCall as StreamUnaryCall,
)
from ._rpc_base import (
    StreamUnaryMultiCallable as StreamUnaryMultiCallable,
)
from ._rpc_base import (
    UnaryStreamCall as UnaryStreamCall,
)
from ._rpc_base import (
    UnaryStreamMultiCallable as UnaryStreamMultiCallable,
)
from ._rpc_base import (
    UnaryUnaryCall as UnaryUnaryCall,
)
from ._rpc_base import (
    UnaryUnaryMultiCallable as UnaryUnaryMultiCallable,
)
from ._rpc_generated import GeneratedPydanticSliverRPCStub

class PydanticSliverRPCStub(GeneratedPydanticSliverRPCStub):
    """Expose every Sliver RPC with concrete Pydantic request/response types."""

    def __init__(self, channel: object) -> None: ...

__all__: list[str]
