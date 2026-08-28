from typing import Protocol, TypeVar

from ._rpc import PydanticSliverRPCStub
from .models import ProtobufModel


class RequestRoutedModel(Protocol):
    """Protocol for generated Pydantic models with a request field."""

    request: ProtobufModel | None


_RequestT = TypeVar("_RequestT", bound=RequestRoutedModel)
_ResultT = TypeVar("_ResultT", bound=ProtobufModel)


class InteractiveObject(Protocol):
    """Protocol for objects with interactive methods."""

    @property
    def timeout(self) -> int: ...

    @property
    def _stub(self) -> PydanticSliverRPCStub: ...

    def _request(self, model: _RequestT) -> _RequestT: ...

    async def _execute(
        self,
        rpc_name: str,
        request: RequestRoutedModel,
        result_type: type[_ResultT],
    ) -> _ResultT: ...
