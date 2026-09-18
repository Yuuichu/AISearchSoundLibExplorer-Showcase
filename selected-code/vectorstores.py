from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from .domain import SearchFilters, VectorHit


class VectorStore(ABC):
    @abstractmethod
    def ensure_collection(self, name: str, dimension: int) -> None: ...

    @abstractmethod
    def upsert(
        self,
        collection: str,
        ids: Sequence[str],
        vectors: np.ndarray,
        payloads: Sequence[dict[str, Any]],
    ) -> None: ...

    @abstractmethod
    def delete(self, collection: str, ids: Sequence[str]) -> None: ...

    @abstractmethod
    def query(
        self, collection: str, vector: np.ndarray, limit: int, filters: SearchFilters | None = None
    ) -> list[VectorHit]: ...

    @abstractmethod
    def count(self, collection: str) -> int: ...

    @abstractmethod
    def health(self) -> bool: ...


class MemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self.collections: dict[str, dict[str, tuple[np.ndarray, dict[str, Any]]]] = {}

    def ensure_collection(self, name: str, dimension: int) -> None:
        self.collections.setdefault(name, {})

    def upsert(
        self,
        collection: str,
        ids: Sequence[str],
        vectors: np.ndarray,
        payloads: Sequence[dict[str, Any]],
    ) -> None:
        target = self.collections.setdefault(collection, {})
        for point_id, vector, payload in zip(ids, vectors, payloads, strict=True):
            target[str(point_id)] = (np.asarray(vector, dtype=np.float32), dict(payload))

    def delete(self, collection: str, ids: Sequence[str]) -> None:
        target = self.collections.get(collection, {})
        for point_id in ids:
            target.pop(str(point_id), None)

    def query(
        self, collection: str, vector: np.ndarray, limit: int, filters: SearchFilters | None = None
    ) -> list[VectorHit]:
        query = np.asarray(vector, dtype=np.float32)
        values = []
        for point_id, (candidate, payload) in self.collections.get(collection, {}).items():
            if filters and not _payload_matches(payload, filters):
                continue
            denominator = max(np.linalg.norm(query) * np.linalg.norm(candidate), 1e-12)
            score = float(np.dot(query, candidate) / denominator)
            values.append(
                VectorHit(point_id, str(payload.get("file_id", point_id)), score, payload)
            )
        return sorted(values, key=lambda item: item.score, reverse=True)[:limit]

    def count(self, collection: str) -> int:
        return len(self.collections.get(collection, {}))

    def health(self) -> bool:
        return True


def _payload_matches(payload: dict[str, Any], filters: SearchFilters) -> bool:
    for key in (
        "library",
        "category",
        "ucs",
        "channels",
        "sample_rate",
        "bit_depth",
        "extension",
        "favorite",
    ):
        value = getattr(filters, key)
        if value is not None and payload.get(key) != value:
            return False
    duration = float(payload.get("duration", 0))
    return not (
        (filters.duration_min is not None and duration < filters.duration_min)
        or (filters.duration_max is not None and duration > filters.duration_max)
    )


class QdrantVectorStore(VectorStore):
    def __init__(self, path: Path | None = None, url: str | None = None):
        from qdrant_client import QdrantClient

        self.client = QdrantClient(url=url) if url else QdrantClient(path=str(path))

    def ensure_collection(self, name: str, dimension: int) -> None:
        from qdrant_client import models

        if not self.client.collection_exists(name):
            self.client.create_collection(
                name,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )

    def upsert(
        self,
        collection: str,
        ids: Sequence[str],
        vectors: np.ndarray,
        payloads: Sequence[dict[str, Any]],
    ) -> None:
        from qdrant_client import models

        points = [
            models.PointStruct(id=point_id, vector=vector.tolist(), payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads, strict=True)
        ]
        self.client.upsert(collection_name=collection, wait=True, points=points)

    def delete(self, collection: str, ids: Sequence[str]) -> None:
        from qdrant_client import models

        if ids:
            selector = models.PointIdsList(points=list(ids))
            self.client.delete(collection_name=collection, wait=True, points_selector=selector)

    def _filter(self, filters: SearchFilters | None):
        if not filters:
            return None
        from qdrant_client import models

        must = []
        for key in (
            "library",
            "category",
            "ucs",
            "channels",
            "sample_rate",
            "bit_depth",
            "extension",
            "favorite",
        ):
            value = getattr(filters, key)
            if value is not None:
                must.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))
        if filters.duration_min is not None or filters.duration_max is not None:
            value_range = models.Range(gte=filters.duration_min, lte=filters.duration_max)
            must.append(models.FieldCondition(key="duration", range=value_range))
        return models.Filter(must=must) if must else None

    def query(
        self, collection: str, vector: np.ndarray, limit: int, filters: SearchFilters | None = None
    ) -> list[VectorHit]:
        result = self.client.query_points(
            collection_name=collection,
            query=vector.tolist(),
            query_filter=self._filter(filters),
            limit=limit,
        ).points
        return [
            VectorHit(
                str(item.id),
                str((item.payload or {}).get("file_id", item.id)),
                float(item.score),
                dict(item.payload or {}),
            )
            for item in result
        ]

    def count(self, collection: str) -> int:
        return int(self.client.count(collection_name=collection, exact=True).count)

    def health(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False


class FaissVectorStore(MemoryVectorStore):
    """Exact flat reference used only by benchmarks."""


def create_vector_store(provider: str, path: Path, url: str = "") -> VectorStore:
    if provider == "memory":
        return MemoryVectorStore()
    if provider == "faiss":
        return FaissVectorStore()
    if provider == "qdrant":
        return QdrantVectorStore(url=url) if url else QdrantVectorStore(path=path)
    raise ValueError(f"Unsupported vector store: {provider}")
