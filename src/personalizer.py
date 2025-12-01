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
from typing import Dict, List, Any


def load_article_topics(articles_path: str) -> Dict[str, List[str]]:
    p = Path(articles_path)
    mapping = {}
    with p.open("r", encoding="utf8") as f:
        for line in f:
            obj = json.loads(line)
            mapping[obj["uuid"]] = obj.get("topics", [])
    return mapping


def load_user_profiles(path: str) -> Dict[str, Dict[str, float]]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_user_profiles(profiles: Dict[str, Dict[str, float]], path: str):
    p = Path(path)
    with p.open("w", encoding="utf8") as f:
        json.dump(profiles, f, indent=2)


def update_user_profile(user_id: str, actions: List[Any], ranked_ids: List[str], article_topics: Dict[str, List[str]], current_profiles: Dict[str, Dict[str, float]]):
    """Incrementally update a single user's profile based on new actions."""
    if user_id not in current_profiles:
        current_profiles[user_id] = {}
    
    # We need to track raw counts to do proper incremental updates, 
    # but for this simple version, we'll just do a weighted moving average 
    # or simple accumulation if we stored counts. 
    # Since the current design stores normalized vectors, exact incremental update 
    # without counts is hard. 
    # STRATEGY CHANGE: Let's store COUNTS in the profile, and normalize only when using.
    # But to keep it simple and compatible with existing code structure:
    # We will just add the new topic hits to the existing profile with a small learning rate
    # or just accumulate if we assume the profile values are roughly proportional to counts.
    
    # Actually, the best way for "persistence" is to store the raw counts.
    # But let's stick to the user's request of "retrain after session".
    # For now, let's implement a helper that takes the *current* profile (assumed normalized)
    # and mixes in the new observation.
    
    # However, to be robust, let's just re-implement build_user_topic_profiles to support
    # loading from a file, and maybe we don't need a complex incremental update 
    # if we are just saving the state.
    
    # Let's stick to the plan: Update in memory.
    # We'll treat the current profile values as "weights".
    
    clicked_topics = []
    for aid, acts in zip(ranked_ids, actions or []):
        if acts and any(a == "Click" for a in acts):
            clicked_topics.extend(article_topics.get(aid, []))
            
    if not clicked_topics:
        return

    # Simple additive update (un-normalized for a moment, then normalize)
    # This is a heuristic since we don't have the total history count.
    # We'll assume a "decay" or just add 1.0 for each new click.
    profile = current_profiles[user_id]
    
    # Heuristic: Multiply existing by 10 (simulating history) + new clicks, then normalize.
    # Or simpler: just add 1 to the score? No, score is 0-1.
    # Let's just add 0.1 for each click and re-normalize.
    for t in clicked_topics:
        profile[t] = profile.get(t, 0.0) + 1.0
        
    # Re-normalize
    total = sum(profile.values())
    if total > 0:
        for t in profile:
            profile[t] /= total


def build_user_topic_profiles(log_path: str, article_topics: Dict[str, List[str]]) -> Dict[str, Dict[str, float]]:
    """Builds profiles from scratch using the log file."""
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
            for aid, acts in zip(ranked_ids, actions or []):
                if not acts:
                    continue
                if any(a == "Click" for a in acts):
                    topics = article_topics.get(aid, [])
                    for t in topics:
                        user_counts[user][t] += 1
    
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
