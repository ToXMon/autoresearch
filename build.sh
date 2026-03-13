#!/bin/bash
# build.sh — Build and push AutoResearch Docker image
#
# Usage:
#   ./build.sh [registry] [tag]
#
# Examples:
#   ./build.sh docker.io/youruser v1
#   ./build.sh ghcr.io/yourorg latest

set -e

REGISTRY="${1:-docker.io/youruser}"
TAG="${2:-v1}"
IMAGE="${REGISTRY}/autoresearch-agent:${TAG}"

echo "==> Building AutoResearch Autonomous Agent Image"
echo "    Image: ${IMAGE}"
echo ""

# Build the image
docker build -t "${IMAGE}" .

echo ""
echo "==> Build complete!"
echo "    Image: ${IMAGE}"
echo ""
echo "To push to registry:"
echo "    docker login <registry>"
echo "    docker push ${IMAGE}"
echo ""
echo "Then update deploy.yaml with:"
echo "    image: ${IMAGE}"
