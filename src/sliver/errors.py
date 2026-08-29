"""Exceptions shared by the handwritten Sliver API."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar, cast

from pydantic import BaseModel

from .models import commonpb


class SliverError(Exception):
    """Base class for errors reported by the high-level Sliver API."""


class NotConnectedError(SliverError, RuntimeError):
    """Raised when an operation requires an active server connection."""

    def __init__(self, message: str = "the Sliver client is not connected") -> None:
        super().__init__(message)


class ResourceNotFoundError(SliverError, LookupError):
    """Raised when Sliver has no resource matching an identifier."""

    resource: str
    identifier: str | int

    def __init__(self, resource: str, identifier: str | int) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} {identifier!r} was not found")


class RPCError(SliverError):
    """A transport-level failure while invoking a Sliver RPC."""

    operation: str
    details: str
    status: str | int | None

    def __init__(
        self,
        operation: str,
        details: str,
        *,
        status: str | int | None = None,
    ) -> None:
        self.operation = operation
        self.details = details
        self.status = status
        status_text = f" [{status}]" if status is not None else ""
        super().__init__(f"{operation} RPC failed{status_text}: {details}")


class CommandError(SliverError):
    """A command reached Sliver but its Pydantic result reports an error."""

    operation: str
    message: str
    target_id: str | None
    result: BaseModel | None

    def __init__(
        self,
        operation: str,
        message: str,
        *,
        target_id: str | None = None,
        result: BaseModel | None = None,
    ) -> None:
        self.operation = operation
        self.message = message
        self.target_id = target_id
        self.result = result
        target_text = f" for target {target_id!r}" if target_id is not None else ""
        super().__init__(f"{operation} failed{target_text}: {message}")


class SliverTimeoutError(SliverError, TimeoutError):
    """Raised when a Sliver operation does not finish before its deadline."""

    operation: str
    timeout: float | None

    def __init__(self, operation: str, timeout: float | None = None) -> None:
        self.operation = operation
        self.timeout = timeout
        if timeout is None:
            message = f"{operation} timed out"
        else:
            message = f"{operation} timed out after {timeout:g} seconds"
        super().__init__(message)


class CleanupError(SliverError):
    """Raised after one or more owned resources fail to close."""

    operation: str
    failures: tuple[BaseException, ...]

    def __init__(self, operation: str, failures: Sequence[BaseException]) -> None:
        self.operation = operation
        self.failures = tuple(failures)
        count = len(self.failures)
        noun = "failure" if count == 1 else "failures"
        super().__init__(f"{operation} cleanup produced {count} {noun}")


class UnsupportedTargetError(SliverError, ValueError):
    """Raised when a host cannot be mapped to a supported GOOS/GOARCH pair."""

    system: str
    machine: str

    def __init__(self, system: str, machine: str) -> None:
        self.system = system
        self.machine = machine
        super().__init__(
            f"unsupported Sliver target: {system or '<unknown>'}/{machine or '<unknown>'}"
        )


class _ResponseCarrier(Protocol):
    response: commonpb.Response | None


_ResultT = TypeVar("_ResultT", bound=BaseModel)


def raise_for_command_error(
    result: _ResultT,
    *,
    operation: str,
    target_id: str | None = None,
) -> _ResultT:
    """Raise :class:`CommandError` when a result's response contains an error.

    Generated command results consistently place server-side command failures
    in an optional ``commonpb.Response`` field.  Centralizing that check keeps
    callers typed and leaves cancellation and Pydantic validation exceptions
    untouched.
    """

    response: commonpb.Response | None
    if isinstance(result, commonpb.Response):
        response = result
    elif "response" in type(result).model_fields:
        response = cast(_ResponseCarrier, result).response
    else:
        response = None

    if response is not None and response.err:
        raise CommandError(
            operation,
            response.err,
            target_id=target_id,
            result=result,
        )
    return result


__all__ = [
    "CleanupError",
    "CommandError",
    "NotConnectedError",
    "RPCError",
    "ResourceNotFoundError",
    "SliverError",
    "SliverTimeoutError",
    "UnsupportedTargetError",
    "raise_for_command_error",
]
