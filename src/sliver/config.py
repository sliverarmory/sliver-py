"""Validated Sliver operator configuration models."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

CONFIG_ENV_VAR = "SLIVER_CONFIG"
DEFAULT_CONFIG_PATH = Path("~/.sliver-client/configs/default.cfg").expanduser()


class SliverWireGuardConfig(BaseModel):
    """Optional WireGuard settings embedded in newer operator configs."""

    model_config = ConfigDict(extra="ignore")

    server_pub_key: str
    client_private_key: str = Field(repr=False)
    client_pub_key: str
    client_ip: str
    server_ip: str


class SliverClientConfig(BaseModel):
    """A validated Sliver multiplayer operator configuration."""

    model_config = ConfigDict(extra="ignore")

    operator: str = Field(min_length=1)
    lhost: str = Field(min_length=1)
    lport: int = Field(ge=1, le=65535)
    ca_certificate: str = Field(repr=False)
    certificate: str = Field(repr=False)
    private_key: str = Field(repr=False)
    token: str = Field(repr=False)
    wg: SliverWireGuardConfig | None = None

    def __str__(self) -> str:
        return f"{self.operator}@{self.lhost}:{self.lport}"

    def __repr__(self) -> str:
        return f"<SliverClientConfig {self}>"

    @classmethod
    def parse_config(cls, data: str | bytes) -> SliverClientConfig:
        """Parse an operator configuration JSON document."""

        return cls.model_validate_json(data)

    @classmethod
    def parse_config_file(cls, filepath: os.PathLike[str] | str) -> SliverClientConfig:
        """Parse an operator configuration from ``filepath``."""

        with open(filepath, encoding="utf-8") as config_file:
            return cls.parse_config(config_file.read())

    @classmethod
    def resolve_path(
        cls, filepath: os.PathLike[str] | str | None = None
    ) -> Path:
        """Resolve an explicit path, ``SLIVER_CONFIG``, or Sliver's default."""

        if filepath is not None:
            return Path(filepath).expanduser()
        configured = os.environ.get(CONFIG_ENV_VAR)
        return Path(configured).expanduser() if configured else DEFAULT_CONFIG_PATH

    @classmethod
    def from_file(
        cls, filepath: os.PathLike[str] | str | None = None
    ) -> SliverClientConfig:
        """Load a validated operator config using Sliver's path conventions."""

        return cls.parse_config_file(cls.resolve_path(filepath))


class OperatorConfig(SliverClientConfig):
    """Preferred name for a Sliver multiplayer operator configuration."""

    @classmethod
    def from_file(
        cls, filepath: os.PathLike[str] | str | None = None
    ) -> OperatorConfig:
        """Load a config while preserving the preferred concrete type."""

        path = cls.resolve_path(filepath)
        with path.open(encoding="utf-8") as config_file:
            return cls.model_validate_json(config_file.read())
