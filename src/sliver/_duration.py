"""Conversions for Go ``time.Duration`` values used on Sliver's wire API."""

from __future__ import annotations

from datetime import timedelta

_NANOSECONDS_PER_MICROSECOND = 1_000
_NANOSECONDS_PER_SECOND = 1_000_000_000
_MICROSECONDS_PER_SECOND = 1_000_000
_SECONDS_PER_DAY = 86_400
_MAX_INT64 = 9_223_372_036_854_775_807


def duration_nanoseconds(value: timedelta | int, *, name: str) -> int:
    """Convert a duration to Sliver's signed nanosecond representation."""

    if isinstance(value, bool):
        raise TypeError(f"{name} must be a timedelta or whole seconds")
    if isinstance(value, int):
        value = timedelta(seconds=value)
    if not isinstance(value, timedelta):
        raise TypeError(f"{name} must be a timedelta or whole seconds")
    microseconds = (
        value.days * _SECONDS_PER_DAY * _MICROSECONDS_PER_SECOND
        + value.seconds * _MICROSECONDS_PER_SECOND
        + value.microseconds
    )
    nanoseconds = microseconds * _NANOSECONDS_PER_MICROSECOND
    if nanoseconds < 0:
        raise ValueError(f"{name} cannot be negative")
    if nanoseconds > _MAX_INT64:
        raise ValueError(f"{name} exceeds Sliver's signed 64-bit duration")
    return nanoseconds


def request_timeout_nanoseconds(seconds: int, *, name: str = "timeout") -> int:
    """Encode a routed-command deadline like Sliver's official Go client.

    The server casts ``commonpb.Request.Timeout`` directly to ``time.Duration``.
    Sliver's Go client subtracts one nanosecond so the server-side command
    deadline expires just before the transport deadline.
    """

    if isinstance(seconds, bool) or not isinstance(seconds, int):
        raise TypeError(f"{name} must be whole seconds")
    if seconds <= 0:
        raise ValueError(f"{name} must be greater than zero")
    if seconds > _MAX_INT64 // _NANOSECONDS_PER_SECOND:
        raise ValueError(f"{name} exceeds Sliver's signed 64-bit duration")
    return seconds * _NANOSECONDS_PER_SECOND - 1


__all__ = ["duration_nanoseconds", "request_timeout_nanoseconds"]
