"""Simple client to interact with the user-simulation platform.

Provides helpers to call /query and /ranklist endpoints.
"""
import requests
from typing import List, Dict, Any


class SimulatorClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip("/")

    def get_query(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/query", timeout=10)
        r.raise_for_status()
        return r.json()

    def post_ranklist(self, query_id: str, user_id: str, ranked_article_ids: List[str]) -> Dict[str, Any]:
        payload = {
            "query_id": query_id,
            "user_id": user_id,
            "ranked_article_ids": ranked_article_ids,
        }
        r = requests.post(f"{self.base_url}/ranklist", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    c = SimulatorClient()
    print(c.get_query())
