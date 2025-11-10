# ire25-final-project
IRE 2025 Final Course Project - Daksh &amp; Shivam

## Overview

This repository contains a baseline personalisation/search experiment for the course project described in `REQUIREMENTS.md`.

What this commit implements (initial MVP):

- A TF-IDF baseline retriever (no external Elasticsearch dependency). Indexing code lives in `src/indexer.py`.
- A retriever that loads the TF-IDF index and returns top-k article ids: `src/retriever.py`.
- A small HTTP client to interact with the provided user-simulator (`/query` and `/ranklist`): `src/sim_client.py`.
- Session logging (JSONL) for saved query/ranklist interactions: `src/logger.py`.
- A driver script to run sessions and log responses: `scripts/run_session.py`.
- `requirements.txt` listing Python dependencies.

This is the first iteration: baseline retrieval + simulator wiring + logging. Next steps (planned and partially scaffolded) include simple personalization models, offline training from logs, and evaluation/AB-harness.

## Quickstart (local, Python)

1. Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Build a TF-IDF index from `articles.jsonl`:

```bash
python -m src.indexer --articles articles.jsonl --out-dir data_index
```

3. Run the simulator driver (assumes the simulation docker is running on localhost:3000):

```bash
python scripts/run_session.py --index data_index --n 20 --server http://localhost:3000
```

That will fetch a query from the simulator, retrieve top-10 articles using TF-IDF, post the ranked ids to `/ranklist`, and log the resulting actions to `logs/sessions.jsonl`.

## Files of interest

- `articles.jsonl` — dataset of articles (already in repo).
- `src/indexer.py` — build TF-IDF index and persist it.
- `src/retriever.py` — load saved index and query it.
- `src/sim_client.py` — simple client for the simulator API.
- `src/logger.py` — append JSONL logs of sessions.
- `scripts/run_session.py` — run multiple sessions and log results.
 - `scripts/start_and_index.sh` — helper script: starts the simulator docker image (if needed), waits for it to be healthy, ensures the project's virtualenv exists, and runs the TF-IDF indexer. Useful to automate the sequence: start simulator -> index articles.

Usage (from repo root):

```bash
./scripts/start_and_index.sh
```

Notes:
- The script expects either the docker image `ire_project:1.0` to be present, or the image tar `ire_project-1.0-amd64.tar` at the repo root (as described in `REQUIREMENTS.md`). If neither is available it will exit and instruct you how to proceed.
- The script will create a `.venv` virtual environment if one does not exist and install `requirements.txt` into it. If you prefer to manage the venv manually, create it before running the script.

## Next steps (planned)

1. Implement a simple per-user topic model using article topics and logged clicks to compute user-topic preference vectors; re-rank baseline results by combining TF-IDF score with user-topic score.
2. Add offline evaluator to compare baseline vs personalised ranking on held-out simulator sessions (metrics: clicks, dwell-weighted reward).
3. Implement a compact AB-harness to compare two strategies while interacting with the simulator (budgeted calls).
4. Add tests and small notebooks demonstrating training & evaluation.

If you'd like, I can implement step 1 (user-topic preferences and reranker) next and run a small offline experiment using the logged sessions. Tell me to proceed and I'll implement it and add tests and documentation.

