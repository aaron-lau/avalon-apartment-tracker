#!/bin/bash

# Build the image
docker buildx build --platform linux/amd64 --provenance=false -t ${ECR_REPO_NAME}:${IMAGE_TAG} . --output type=docker

# Run the container with environment variables from .env
docker run -p 9000:8080 \
  --env-file .env \
  apartment-tracker &

# Wait for container to start
echo "Waiting for container to start..."
sleep 7

# Test the function
echo "Testing function..."
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"list-only": true}'

# Keep container running
echo "Container is running. Press Ctrl+C to stop."
wait