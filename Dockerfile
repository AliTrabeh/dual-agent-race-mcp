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

# --role (cop|thief) is supplied per Cloud Run service at deploy time —
# see tools/deploy_cloud_run.sh. One image serves both roles.
ENTRYPOINT ["uv", "run", "python", "-m", "hw6_race.services.mcp.run_server"]
