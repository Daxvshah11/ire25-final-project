"""Indexing utilities: build and save an Elasticsearch index over articles.jsonl

Usage:
  python -m src.es_indexer --articles articles.jsonl --host http://localhost:9200 --index-name articles
"""
import argparse
import json
from pathlib import Path
from elasticsearch import Elasticsearch, helpers

def load_articles(path):
    path = Path(path)
    with path.open("r", encoding="utf8") as f:
        for line in f:
            yield json.loads(line)

def create_index(es, index_name):
    if not es.indices.exists(index=index_name):
        es.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "uuid": {"type": "keyword"},
                        "text": {"type": "text"},
                        # Add other fields if necessary from articles.jsonl
                    }
                }
            }
        )
        print(f"Created index {index_name}")
    else:
        print(f"Index {index_name} already exists")

def index_articles(es, index_name, articles):
    def generate_actions():
        for article in articles:
            yield {
                "_index": index_name,
                "_id": article.get("uuid"),
                "_source": {
                    "uuid": article.get("uuid"),
                    "text": article.get("text", ""),
                    # Add other fields if necessary
                }
            }
    
    success, failed = helpers.bulk(es, generate_actions(), stats_only=True)
    print(f"Indexed {success} documents. Failed: {failed}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--articles", required=True)
    parser.add_argument("--host", default="http://localhost:9200")
    parser.add_argument("--index-name", default="articles")
    args = parser.parse_args()

    es = Elasticsearch(args.host)
    
    # Check connection
    if not es.ping():
        print(f"Could not connect to Elasticsearch at {args.host}")
        return

    create_index(es, args.index_name)
    
    articles = load_articles(args.articles)
    index_articles(es, args.index_name, articles)

if __name__ == "__main__":
    main()
