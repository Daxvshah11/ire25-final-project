#!/usr/bin/env zsh
set -euo pipefail

# Start the simulator docker container (if needed), wait until it's ready,
# then run the TF-IDF indexer inside the project's virtualenv.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"
REQUIREMENTS="$ROOT/requirements.txt"
CONTAINER_NAME="ire_project_sim"
IMAGE_NAME="ire_project:1.0"
TAR_PATH="$ROOT/ire_project-1.0-amd64.tar"

echo "Repo root: $ROOT"

if [ ! -d "$VENV" ]; then
  echo "Virtualenv not found at $VENV — creating and installing requirements..."
  python3 -m venv "$VENV"
  "$PIP" install --upgrade pip
  "$PIP" install -r "$REQUIREMENTS"
else
  echo "Using existing virtualenv at $VENV"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found in PATH. Please install Docker Desktop and ensure 'docker' is available." >&2
  exit 1
fi

echo "Checking simulator container ($CONTAINER_NAME) status..."
if docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" --format '{{.Names}}' | grep -q "${CONTAINER_NAME}"; then
  echo "Container ${CONTAINER_NAME} is already running."
else
  # if image not present, try to load tar
  if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    if [ -f "$TAR_PATH" ]; then
      echo "Docker image $IMAGE_NAME not found locally — loading from $TAR_PATH"
      docker load -i "$TAR_PATH"
    else
      echo "Docker image $IMAGE_NAME not found and tar $TAR_PATH does not exist." >&2
      echo "Place the Docker image tar at: $TAR_PATH or load the image manually, then re-run this script." >&2
      exit 1
    fi
  fi

  echo "Starting container $CONTAINER_NAME..."
  docker run -d --rm --name "$CONTAINER_NAME" -p 3000:3000 -v "$ROOT/data":/data --tmpfs /tmp:rw,noexec,nosuid --cap-drop ALL --security-opt no-new-privileges "$IMAGE_NAME"
fi

echo "Waiting for simulator to respond on http://localhost:3000/query ..."
for i in {1..60}; do
  if curl -sSf http://localhost:3000/query >/dev/null 2>&1; then
    echo "\nSimulator is up!"
    break
  fi
  echo -n "."
  sleep 1
  if [ "$i" -eq 60 ]; then
    echo "\nTimed out waiting for simulator to start (60s)." >&2
    exit 1
  fi
done

echo "Running TF-IDF indexer..."
"$PY" -m src.indexer --articles "$ROOT/articles.jsonl" --out-dir "$ROOT/data_index"

echo "Indexing complete. Index files are in $ROOT/data_index"
