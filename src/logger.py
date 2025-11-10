"""Logging utility to persist sessions and interactions."""
import json
from pathlib import Path
from datetime import datetime


class SessionLogger:
    def __init__(self, out_file: str = "logs/sessions.jsonl"):
        p = Path(out_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.path = p

    def log(self, record: dict):
        # add timestamp
        record = dict(record)
        record.setdefault("logged_at", datetime.utcnow().isoformat())
        with self.path.open("a", encoding="utf8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    l = SessionLogger()
    l.log({"test": True})
