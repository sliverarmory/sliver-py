from typing import Protocol

from ._rpc import PydanticSliverRPCStub
from .models import ProtobufModel


class PbWithRequestProp(Protocol):
    """Protocol for generated Pydantic models with a request field."""

    @property
    def request(self) -> ProtobufModel | None: ...


class InteractiveObject(Protocol):
    """Protocol for objects with interactive methods."""

    @property
    def timeout(self) -> int: ...

    @property
    def _stub(self) -> PydanticSliverRPCStub: ...

    def _request(self, pb: PbWithRequestProp) -> PbWithRequestProp: ...
