"""Run simple interaction sessions with the simulator using the TF-IDF baseline.

Example:
  python scripts/run_session.py --index data_index --n 10 --server http://localhost:3000
"""
import argparse
from src.sim_client import SimulatorClient
from src.retriever import Retriever
from src.logger import SessionLogger
from src.personalizer import load_article_topics, build_user_topic_profiles, rerank_with_user_profile
import time


def run_one_session(client, retriever, logger):
    q = client.get_query()
    user_id = q["user_id"]
    query_id = q["query_id"]
    query_text = q["query_text"]
    # retrieve top 10
    hits = retriever.retrieve(query_text, top_k=10)
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
    args = parser.parse_args()

    client = SimulatorClient(args.server)
    retriever = Retriever(index_dir=args.index)
    logger = SessionLogger()

    # load article topics and build user profiles from existing logs (if any)
    article_topics = load_article_topics("articles.jsonl")
    user_profiles = build_user_topic_profiles("logs/sessions.jsonl", article_topics)

    for i in range(args.n):
        try:
            print(f"Session {i+1}/{args.n}")
            # perform retrieval
            q = client.get_query()
            user_id = q["user_id"]
            query_id = q["query_id"]
            query_text = q["query_text"]
            hits = retriever.retrieve(query_text, top_k=10)
            ranked_ids = [h[0] for h in hits]
            # if we have a profile for this user, rerank
            if user_id in user_profiles:
                user_profile = user_profiles[user_id]
                reranked = rerank_with_user_profile(hits, article_topics, user_profile, alpha=0.8)
                ranked_ids = [a for a, _ in reranked]
            resp = client.post_ranklist(query_id, user_id, ranked_ids)
            logger.log({
                "user_id": user_id,
                "query_id": query_id,
                "query_text": query_text,
                "ranked_article_ids": ranked_ids,
                "actions": resp.get("actions"),
            })
            print("Actions:", resp.get("actions"))
            # update user_profiles incrementally with this session (so subsequent sessions reflect it)
            # simple incremental update: if click observed, add counts
            actions = resp.get("actions", [])
            if actions and any(a == "Click" for group in actions for a in (group if isinstance(group, list) else [])):
                # rebuild profiles for simplicity (small dataset)
                user_profiles = build_user_topic_profiles("logs/sessions.jsonl", article_topics)
        except Exception as e:
            print("Error during session:", e)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
