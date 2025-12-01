"""Indexing utilities: build and save a TF-IDF index over articles.jsonl

Usage:
  python -m src.indexer --articles articles.jsonl --out-dir data_index
"""
import argparse
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import joblib
import numpy as np


def load_articles(path):
    path = Path(path)
    docs = []
    ids = []
    with path.open("r", encoding="utf8") as f:
        for line in f:
            obj = json.loads(line)
            ids.append(obj.get("uuid"))
            docs.append(obj.get("text", ""))
    return ids, docs


from src.text_utils import tokenize_and_stem

def build_tfidf(docs, max_features=50000):
    vec = TfidfVectorizer(max_features=max_features, tokenizer=tokenize_and_stem)
    X = vec.fit_transform(docs)
    # normalize rows for cosine similarity via dot product
    X = normalize(X, norm="l2", axis=1)
    return vec, X


def save_index(out_dir, ids, vectorizer, matrix):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, out / "vectorizer.joblib")
    joblib.dump(matrix, out / "matrix.joblib")
    joblib.dump(ids, out / "ids.joblib")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--articles", required=True)
    parser.add_argument("--out-dir", default="data_index")
    args = parser.parse_args()

    ids, docs = load_articles(args.articles)
    print(f"Loaded {len(docs)} articles")
    vec, X = build_tfidf(docs)
    print("Built TF-IDF matrix", X.shape)
    save_index(args.out_dir, ids, vec, X)
    print("Saved index to", args.out_dir)


if __name__ == "__main__":
    main()
