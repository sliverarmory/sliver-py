"""Validated Sliver operator configuration models."""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field


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
