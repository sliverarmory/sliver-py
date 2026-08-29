FROM ghcr.io/astral-sh/uv:0.12.7 AS uv

FROM python:3.12-slim-bookworm

ENV PATH="/sliver-py/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install --no-install-recommends --yes curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

WORKDIR /sliver-py

# Install dependencies separately so source-only changes reuse the dependency layer.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen
