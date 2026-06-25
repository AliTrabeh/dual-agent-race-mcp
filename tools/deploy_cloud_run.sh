#!/usr/bin/env bash
# Deploys both MCP servers (Cop, Thief) to Google Cloud Run from one shared
# Dockerfile (Deployment Stage 2, README §8). Run this yourself after:
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT_ID
#
# Usage: tools/deploy_cloud_run.sh [region]   (region defaults to us-central1)
set -euo pipefail

REGION="${1:-us-central1}"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"
if [ -z "$PROJECT_ID" ]; then
  echo "No gcloud project set. Run: gcloud config set project YOUR_PROJECT_ID" >&2
  exit 1
fi

IMAGE="gcr.io/${PROJECT_ID}/hw6-race-mcp"
COP_TOKEN="${MCP_COP_AUTH_TOKEN:-$(openssl rand -hex 24)}"
THIEF_TOKEN="${MCP_THIEF_AUTH_TOKEN:-$(openssl rand -hex 24)}"

echo "Building and pushing ${IMAGE} ..."
gcloud builds submit --tag "${IMAGE}" .

echo "Deploying Cop server ..."
COP_URL=$(gcloud run deploy hw6-race-cop \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --args="--role=cop" \
  --set-env-vars="MCP_COP_AUTH_TOKEN=${COP_TOKEN}" \
  --format="value(status.url)")

echo "Deploying Thief server ..."
THIEF_URL=$(gcloud run deploy hw6-race-thief \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --args="--role=thief" \
  --set-env-vars="MCP_THIEF_AUTH_TOKEN=${THIEF_TOKEN}" \
  --format="value(status.url)")

cat <<EOF

Deployed. Add these to your .env to run a real match against the cloud servers:

MCP_COP_URL=${COP_URL}
MCP_THIEF_URL=${THIEF_URL}
MCP_COP_AUTH_TOKEN=${COP_TOKEN}
MCP_THIEF_AUTH_TOKEN=${THIEF_TOKEN}

Then: uv run python -m hw6_race.main
EOF
