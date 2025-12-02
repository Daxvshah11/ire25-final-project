#!/bin/bash

# Function to check if Docker is ready
wait_for_docker() {
    echo "Checking Docker status..."
    if ! docker ps > /dev/null 2>&1; then
        echo "Docker is not running."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Attempting to start Docker Desktop..."
            open -a Docker
            echo "Waiting for Docker to start (this may take a minute)..."
            while ! docker ps > /dev/null 2>&1; do
                sleep 2
                printf "."
            done
            echo ""
            echo "Docker started!"
        else
            echo "Error: Docker is not running. Please start it manually."
            exit 1
        fi
    else
        echo "Docker is running."
    fi
}

wait_for_docker

PORT=3000

# Cleanup existing containers using the port
echo "Checking for existing containers on port $PORT..."
# Find container ID mapped to port 3000
CONTAINER_ID=$(docker ps -q --filter "publish=$PORT")

if [ ! -z "$CONTAINER_ID" ]; then
    echo "Stopping existing container $CONTAINER_ID..."
    docker stop $CONTAINER_ID
    # Wait a moment for port to free up
    sleep 2
else
    echo "No container running on port $PORT."
fi

# Double check if port is still in use by a NON-Docker process (rare but possible)
if lsof -i :$PORT > /dev/null; then
    # Check if it's NOT com.docker (Docker backend)
    PID=$(lsof -t -i :$PORT)
    PROCESS_NAME=$(ps -p $PID -o comm=)
    if [[ "$PROCESS_NAME" == *"com.docker"* ]]; then
        echo "Port $PORT is held by Docker backend. Assuming it's free for a new container."
    else
        echo "Warning: Port $PORT is in use by $PROCESS_NAME (PID $PID). Attempting to kill..."
        kill -9 $PID
    fi
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

docker run --rm --platform linux/amd64 -p 3000:3000 \
 -v $(pwd)/data:/data \
 --tmpfs /tmp:rw,noexec,nosuid \
 --cap-drop ALL \
 --security-opt no-new-privileges \
 ire_project:1.0
