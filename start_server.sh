#!/bin/bash

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

PORT=3000

# Check if port is in use
if lsof -i :$PORT > /dev/null; then
    echo "Port $PORT is in use. Killing process..."
    # Get PID and kill safely
    lsof -t -i :$PORT | xargs kill -9
    echo "Process on port $PORT killed."
else
    echo "Port $PORT is free."
fi

# Ensure data directory exists
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Start Docker
echo "Starting server..."
# Check if image exists, if not try to load it
if [[ "$(docker images -q ire_project:1.0 2> /dev/null)" == "" ]]; then
  echo "Image ire_project:1.0 not found. Checking for tar file..."
  if [ -f "ire_project-1.0-amd64.tar" ]; then
    echo "Loading image from tar..."
    docker load -i ire_project-1.0-amd64.tar
  else
    echo "Error: ire_project:1.0 image not found and ire_project-1.0-amd64.tar not found."
    exit 1
  fi
fi

docker run --rm -p 3000:3000 \
 -v $(pwd)/data:/data \
 --tmpfs /tmp:rw,noexec,nosuid \
 --cap-drop ALL \
 --security-opt no-new-privileges \
 ire_project:1.0
