"""Simple personalization helper: build per-user topic preferences from logs and rerank results.

Strategy (simple, transparent):
- Parse `logs/sessions.jsonl` for past Click actions. For each clicked article, add +1 to each topic.
- User topic vector = normalized counts. Article topic vector = binary vector over topics.
- Topic score = dot(user_topic_vector, article_topic_vector).
- Final score = alpha * tfidf_score + (1-alpha) * topic_score.
"""
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List


def load_article_topics(articles_path: str) -> Dict[str, List[str]]:
    p = Path(articles_path)
    mapping = {}
    with p.open("r", encoding="utf8") as f:
        for line in f:
            obj = json.loads(line)
            mapping[obj["uuid"]] = obj.get("topics", [])
    return mapping


def build_user_topic_profiles(log_path: str, article_topics: Dict[str, List[str]]) -> Dict[str, Dict[str, float]]:
    p = Path(log_path)
    user_counts = defaultdict(Counter)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf8") as f:
        for line in f:
            rec = json.loads(line)
            user = rec.get("user_id")
            actions = rec.get("actions", [])
            ranked_ids = rec.get("ranked_article_ids", [])
            # actions is list aligned with ranked_ids
            for aid, acts in zip(ranked_ids, actions or []):
                if not acts:
                    continue
                # consider a click as feedback
                if any(a == "Click" for a in acts):
                    topics = article_topics.get(aid, [])
                    for t in topics:
                        user_counts[user][t] += 1
    # normalize
    user_profiles = {}
    for u, counter in user_counts.items():
        total = sum(counter.values())
        if total <= 0:
            continue
        user_profiles[u] = {t: c / total for t, c in counter.items()}
    return user_profiles


def rerank_with_user_profile(candidates: List[tuple], article_topics: Dict[str, List[str]], user_profile: Dict[str, float], alpha: float = 0.7):
    """candidates: list of (article_id, base_score)
    Returns list of (article_id, final_score) sorted desc
    """
    out = []
    for aid, base in candidates:
        topics = article_topics.get(aid, [])
        topic_score = 0.0
        for t in topics:
            topic_score += user_profile.get(t, 0.0)
        # normalize by number of topics (if any)
        if topics:
            topic_score = topic_score / len(topics)
        final = alpha * base + (1 - alpha) * topic_score
        out.append((aid, final))
    out.sort(key=lambda x: -x[1])
    return out


if __name__ == "__main__":
    print("Personalizer module. Use from scripts/run_session.py")
