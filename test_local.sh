#!/bin/bash

# Stop any existing containers
docker stop $(docker ps -q --filter ancestor=apartment-tracker) 2>/dev/null || true

# Remove existing image
docker rmi apartment-tracker 2>/dev/null || true

# Build the image
echo "Building container..."
docker build --no-cache -t apartment-tracker .

# Run the container
echo "Starting container..."
docker run -p 9000:8080 \
  --env-file .env \
  apartment-tracker &

# Wait for container to start
echo "Waiting for container to start..."
sleep 5

# Test the function
echo "Testing function..."
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"list-only": true}'

# Keep container running
echo "Container is running. Press Ctrl+C to stop."
wait