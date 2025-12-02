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


class ElasticsearchRetriever:
    def __init__(self, host="http://localhost:9200", index_name="articles"):
        from elasticsearch import Elasticsearch
        self.es = Elasticsearch(host)
        self.index_name = index_name

    def retrieve(self, query_text, top_k=100):
        # Basic match query
        query = {
            "match": {
                "text": query_text
            }
        }
        
        try:
            resp = self.es.search(
                index=self.index_name,
                query=query,
                size=top_k,
                _source=["uuid"]
            )
            
            results = []
            for hit in resp['hits']['hits']:
                doc_id = hit['_source']['uuid']
                score = hit['_score']
                results.append((doc_id, float(score)))
            return results
        except Exception as e:
            print(f"Error during ES retrieval: {e}")
            return []


def simple_demo(index_dir="data_index"):
    r = Retriever(index_dir=index_dir)
    q = "economic recovery 2025"
    print(r.retrieve(q, top_k=100))


if __name__ == "__main__":
    simple_demo()
