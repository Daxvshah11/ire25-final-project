"""Run simple interaction sessions with the simulator using the TF-IDF baseline.

Example:
  python scripts/run_session.py --index data_index --n 10 --server http://localhost:3000
"""
import argparse
import sys
import os

# Add project root to sys.path to allow running script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.sim_client import SimulatorClient
from src.retriever import Retriever, ElasticsearchRetriever
from src.logger import SessionLogger
from src.personalizer import (
    load_article_topics, 
    build_user_topic_profiles, 
    rerank_with_user_profile,
    load_user_profiles,
    save_user_profiles,
    update_user_profile
)
import time


def run_one_session(client, retriever, logger):
    q = client.get_query()
    user_id = q["user_id"]
    query_id = q["query_id"]
    query_text = q["query_text"]
    # retrieve top 10
    hits = retriever.retrieve(query_text, top_k=100)
    ranked_ids = [h[0] for h in hits]
    resp = client.post_ranklist(query_id, user_id, ranked_ids)
    logger.log({
        "user_id": user_id,
        "query_id": query_id,
        "query_text": query_text,
        "ranked_article_ids": ranked_ids,
        "actions": resp.get("actions"),
    })
    return resp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="data_index")
    parser.add_argument("--server", default="http://localhost:3000")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--retriever", choices=["tfidf", "es"], default="tfidf", help="Retrieval method: tfidf or es")
    parser.add_argument("--es-host", default="http://localhost:9200", help="Elasticsearch host")
    args = parser.parse_args()

    client = SimulatorClient(args.server)
    
    if args.retriever == "es":
        print(f"Using Elasticsearch retriever at {args.es_host}")
        retriever = ElasticsearchRetriever(host=args.es_host)
    else:
        print(f"Using TF-IDF retriever from {args.index}")
        retriever = Retriever(index_dir=args.index)
        
    logger = SessionLogger()

    # load article topics
    article_topics = load_article_topics("articles.jsonl")
    
    # Load existing profiles from disk (persistence)
    # If user_profiles.json doesn't exist, we could fall back to rebuilding from logs, 
    # but for now let's assume we start from the json or empty.
    # To be safe: try loading json, if empty, try rebuilding from logs once.
    user_profiles = load_user_profiles("user_profiles.json")
    if not user_profiles:
        print("No saved profiles found. Rebuilding from logs...")
        user_profiles = build_user_topic_profiles("logs/sessions.jsonl", article_topics)

    for i in range(args.n):
        try:
            print(f"Session {i+1}/{args.n}")
            # perform retrieval
            q = client.get_query()
            user_id = q["user_id"]
            query_id = q["query_id"]
            query_text = q["query_text"]
            hits = retriever.retrieve(query_text, top_k=100)
            ranked_ids = [h[0] for h in hits]
            
            # if we have a profile for this user, rerank
            if user_id in user_profiles:
                user_profile = user_profiles[user_id]
                reranked = rerank_with_user_profile(hits, article_topics, user_profile, alpha=0.8)
                ranked_ids = [a for a, _ in reranked]
            
            resp = client.post_ranklist(query_id, user_id, ranked_ids)
            # python -m src.es_indexer --articles articles.jsonl --host http://localhost:9200
            # python scripts/run_session.py --retriever es --es-host http://localhost:9200 --n 5

            logger.log({
                "user_id": user_id,
                "query_id": query_id,
                "query_text": query_text,
                "ranked_article_ids": ranked_ids,
                "actions": resp.get("actions"),
            })
            print("Actions:", resp.get("actions"))
            
            # Update profile IN MEMORY only
            actions = resp.get("actions", [])
            update_user_profile(user_id, actions, ranked_ids, article_topics, user_profiles)
            
        except Exception as e:
            print("Error during session:", e)
        time.sleep(0.2)

    # Save profiles to disk at the end of the run
    print("Saving user profiles to user_profiles.json...")
    save_user_profiles(user_profiles, "user_profiles.json")
 
if __name__ == "__main__":
    main()
