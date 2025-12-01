"""Retrieval utilities using a saved TF-IDF index."""
from pathlib import Path
import joblib
import numpy as np


class Retriever:
    def __init__(self, index_dir="data_index"):
        p = Path(index_dir)
        self.vectorizer = joblib.load(p / "vectorizer.joblib")
        self.matrix = joblib.load(p / "matrix.joblib")
        self.ids = joblib.load(p / "ids.joblib")

    def retrieve(self, query_text, top_k=100):
        qv = self.vectorizer.transform([query_text])
        # normalize qv
        qv = qv / (np.linalg.norm(qv.data) + 1e-12)
        scores = (self.matrix @ qv.T).toarray().ravel()
        rank_idx = np.argsort(-scores)[:top_k]
        results = [(self.ids[i], float(scores[i])) for i in rank_idx]
        return results


def simple_demo(index_dir="data_index"):
    r = Retriever(index_dir=index_dir)
    q = "economic recovery 2025"
    print(r.retrieve(q, top_k=100))


if __name__ == "__main__":
    simple_demo()
