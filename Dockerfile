FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
COPY config/ ./config/
RUN uv sync --frozen --no-dev

ENV PORT=8080
EXPOSE 8080

# No ENTRYPOINT/CMD here on purpose: each deployed service supplies its own
# full command (role and all) via render.yaml's dockerCommand, removing any
# ambiguity about how a platform's command-override merges with a Dockerfile
# ENTRYPOINT. One image serves both roles.
