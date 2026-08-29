from __future__ import annotations

from datetime import timedelta

import pytest

from sliver._duration import duration_nanoseconds, request_timeout_nanoseconds


def test_duration_nanoseconds_accepts_whole_seconds_and_timedelta() -> None:
    assert duration_nanoseconds(17, name="duration") == 17_000_000_000
    assert (
        duration_nanoseconds(
            timedelta(seconds=1, microseconds=250_000),
            name="duration",
        )
        == 1_250_000_000
    )


def test_routed_request_timeout_matches_the_official_sliver_client() -> None:
    assert request_timeout_nanoseconds(17) == 16_999_999_999


@pytest.mark.parametrize("value", [0, -1])
def test_routed_request_timeout_rejects_nonpositive_values(value: int) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        request_timeout_nanoseconds(value)


def test_routed_request_timeout_rejects_boolean_values() -> None:
    with pytest.raises(TypeError, match="whole seconds"):
        request_timeout_nanoseconds(True)
