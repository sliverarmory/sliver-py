from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from sliver import SliverClientConfig, SliverWireGuardConfig


def _config_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "operator": "alice",
        "lhost": "sliver.example",
        "lport": 31337,
        "ca_certificate": "ca-pem",
        "certificate": "cert-pem",
        "private_key": "private-key-pem",
        "token": "secret-token",
    }
    data.update(overrides)
    return data


def test_operator_config_is_a_validated_pydantic_model() -> None:
    config = SliverClientConfig.model_validate(_config_data())

    assert config.lhost == "sliver.example"
    assert str(config) == "alice@sliver.example:31337"
    assert "secret-token" not in repr(config)
    assert "private-key-pem" not in repr(config)


def test_operator_config_parses_latest_wireguard_shape() -> None:
    config = SliverClientConfig.parse_config(
        json.dumps(
            _config_data(
                wg={
                    "server_pub_key": "server-public",
                    "client_private_key": "client-private",
                    "client_pub_key": "client-public",
                    "client_ip": "100.64.0.2",
                    "server_ip": "100.64.0.1",
                },
                future_server_field=True,
            )
        )
    )

    assert isinstance(config.wg, SliverWireGuardConfig)
    assert config.wg.client_ip == "100.64.0.2"
    assert "client-private" not in repr(config.wg)


@pytest.mark.parametrize("port", [0, 65536])
def test_operator_config_rejects_invalid_ports(port: int) -> None:
    with pytest.raises(ValidationError):
        SliverClientConfig.model_validate(_config_data(lport=port))
