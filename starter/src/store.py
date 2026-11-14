"""Persistent Qdrant collections and exact cosine search."""
from pathlib import Path

from qdrant_client import QdrantClient, models

from .embeddings import DIMENSIONS


class VectorStore:
    def __init__(self, path: Path):
        self.client = QdrantClient(path=str(path))

    def replace(self, name, chunks, vectors):
        if len(chunks) != len(vectors) or any(len(vector) != DIMENSIONS for vector in vectors):
            raise ValueError("Embedding count or dimensions do not match")
        points = [
            models.PointStruct(id=c.chunk_id, vector=v, payload={
                "document_id": c.document_id, "source": c.source, "page": c.page,
                "text": c.text, **c.metadata,
            })
            for c, v in zip(chunks, vectors, strict=True)
        ]
        if self.client.collection_exists(name):
            self.client.delete_collection(name)
        self.client.create_collection(name, vectors_config=models.VectorParams(
            size=DIMENSIONS, distance=models.Distance.COSINE))
        self.upsert(name, points)
        return points

    def upsert(self, name, points):
        for start in range(0, len(points), 128):
            self.client.upsert(name, points[start:start + 128], wait=True)

    def count(self, name):
        return self.client.count(name, exact=True).count

    def search(self, name, vector, chapter=None):
        query_filter = None
        if chapter:
            query_filter = models.Filter(must=[
                models.FieldCondition(key="chapter", match=models.MatchValue(value=chapter)),
            ])
        results = self.client.query_points(
            collection_name=name, query=vector, query_filter=query_filter,
            search_params=models.SearchParams(exact=True), limit=3, with_payload=True,
        ).points
        return [{"chunk_id": hit.id, "score": hit.score, **hit.payload} for hit in results]

