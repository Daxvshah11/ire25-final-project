"""A/B Testing Harness: Compare Baseline vs Personalized strategy online.

Usage:
  python scripts/ab_test.py --n 20
"""
import argparse
import random
import time
import sys
import os

# Add project root to sys.path to allow running script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.sim_client import SimulatorClient
from src.retriever import Retriever
from src.logger import SessionLogger
from src.personalizer import (
    load_article_topics, 
    load_user_profiles, 
    save_user_profiles, 
    update_user_profile, 
    rerank_with_user_profile,
    build_user_topic_profiles
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="data_index")
    parser.add_argument("--server", default="http://localhost:3000")
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()

    client = SimulatorClient(args.server)
    retriever = Retriever(index_dir=args.index)
    logger = SessionLogger()
    
    article_topics = load_article_topics("articles.jsonl")
    
    # Load profiles (or build if missing)
    user_profiles = load_user_profiles("user_profiles.json")
    if not user_profiles:
        print("No saved profiles. Building from logs...")
        user_profiles = build_user_topic_profiles("logs/sessions.jsonl", article_topics)

    stats = {
        "A": {"sessions": 0, "clicks": 0}, # Baseline
        "B": {"sessions": 0, "clicks": 0}  # Personalized
    }

    print(f"Starting A/B Test for {args.n} sessions...")

    for i in range(args.n):
        try:
            # 1. Get Query
            q = client.get_query()
            user_id = q["user_id"]
            query_id = q["query_id"]
            query_text = q["query_text"]
            
            # 2. Baseline Retrieval
            hits = retriever.retrieve(query_text, top_k=100)
            ranked_ids = [h[0] for h in hits]
            
            # 3. Assign Group (Coin Flip)
            group = "A" if random.random() < 0.5 else "B"
            
            if group == "B" and user_id in user_profiles:
                # Personalized
                user_profile = user_profiles[user_id]
                reranked = rerank_with_user_profile(hits, article_topics, user_profile, alpha=0.7)
                ranked_ids = [a for a, _ in reranked]
            
            # 4. Post Ranklist
            resp = client.post_ranklist(query_id, user_id, ranked_ids)
            actions = resp.get("actions", [])
            
            # 5. Log & Update Stats
            has_click = any(a == "Click" for group in actions for a in (group if isinstance(group, list) else []))
            
            stats[group]["sessions"] += 1
            if has_click:
                stats[group]["clicks"] += 1
                
            logger.log({
                "user_id": user_id,
                "query_id": query_id,
                "query_text": query_text,
                "ranked_article_ids": ranked_ids,
                "actions": actions,
                "ab_group": group
            })
            
            print(f"Session {i+1}: Group {group} | Click: {has_click}")
            
            # 6. Online Learning (Update Profile)
            # We update profile regardless of group, so we keep learning.
            update_user_profile(user_id, actions, ranked_ids, article_topics, user_profiles)
            
        except Exception as e:
            print("Error:", e)
        time.sleep(0.1)

    # Save profiles
    save_user_profiles(user_profiles, "user_profiles.json")

    # Results
    print("\n--- A/B Test Results ---")
    results_str = f"--- A/B Test Results (N={args.n}) ---\n"
    for g in ["A", "B"]:
        s = stats[g]["sessions"]
        c = stats[g]["clicks"]
        ctr = (c / s * 100) if s > 0 else 0.0
        name = "Baseline" if g == "A" else "Personalized"
        line = f"{name} (Group {g}): {c}/{s} sessions with clicks (CTR: {ctr:.2f}%)\n"
        print(line.strip())
        results_str += line
    
    with open("ab_test_results.txt", "a") as f:
        f.write(f"\nDate: {time.ctime()}\n")
        f.write(results_str)
        f.write("-" * 30 + "\n")
    
    print("Results saved to ab_test_results.txt")

if __name__ == "__main__":
    main()
