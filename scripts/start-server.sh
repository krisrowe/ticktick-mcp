#!/bin/bash
# Wrapper script to ensure the TickTick MCP server Docker container is running
# This allows Gemini CLI to connect via HTTP without manually starting the container

CONTAINER_NAME="ticktick-mcp-server"
IMAGE_NAME="ticktick-mcp-server:latest"

# Check if container is already running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container ${CONTAINER_NAME} is already running" >&2
    exit 0
fi

# Check if container exists but is stopped
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Starting existing container ${CONTAINER_NAME}..." >&2
    docker start "${CONTAINER_NAME}" >&2
    exit 0
fi

# Container doesn't exist, need to create it
# Load environment variables from .env file in repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "Error: .env file not found at ${ENV_FILE}" >&2
    echo "Please create .env file in the repo root with TICKTICK_ACCESS_TOKEN" >&2
    exit 1
fi

# Source .env to get TICKTICK_ACCESS_TOKEN
source "${ENV_FILE}"

if [ -z "${TICKTICK_ACCESS_TOKEN}" ]; then
    echo "Error: TICKTICK_ACCESS_TOKEN not found in .env file" >&2
    exit 1
fi

# Check if image exists
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}$"; then
    echo "Docker image ${IMAGE_NAME} not found. Building..." >&2
    docker build -t "${IMAGE_NAME}" "${REPO_ROOT}" >&2
fi

# Create and start the container
echo "Creating and starting container ${CONTAINER_NAME}..." >&2
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p 8000:8000 \
    -e "TICKTICK_ACCESS_TOKEN=${TICKTICK_ACCESS_TOKEN}" \
    "${IMAGE_NAME}" >&2

# Wait a moment for the server to start
sleep 2

# Verify it's running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container ${CONTAINER_NAME} is now running" >&2
    exit 0
else
    echo "Error: Failed to start container ${CONTAINER_NAME}" >&2
    docker logs "${CONTAINER_NAME}" >&2
    exit 1
fi
