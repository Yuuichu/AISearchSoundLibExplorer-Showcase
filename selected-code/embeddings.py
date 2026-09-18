from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .audio import AudioDecoder

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    name: str
    model: str
    version: str
    dimension: int
    preprocessing_version = "mono-48k-v1"

    @abstractmethod
    def embed_text(self, texts: Sequence[str]) -> np.ndarray: ...

    @abstractmethod
    def embed_audio(
        self, paths: Sequence[Path], ranges: Sequence[tuple[float, float] | None] | None = None
    ) -> np.ndarray: ...

    @staticmethod
    def normalize(values: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(values, axis=1, keepdims=True)
        return values / np.maximum(norms, 1e-12)


class DeterministicEmbeddingProvider(EmbeddingProvider):
    name = "deterministic"
    model = "blake2-feature-hash"
    version = "1"

    def __init__(self, dimension: int = 512):
        self.dimension = dimension

    def _features(self, data: bytes) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype=np.float32)
        text = data.decode("utf-8", "ignore").casefold()
        tokens = [token for token in re.split(r"[^a-z0-9]+", text) if token] or [text]
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            for i in range(0, len(digest), 2):
                value = int.from_bytes(digest[i : i + 2], "little")
                vector[value % self.dimension] += 1 if value & 1 else -1
        return vector

    def embed_text(self, texts: Sequence[str]) -> np.ndarray:
        return self.normalize(np.stack([self._features(text.encode("utf-8")) for text in texts]))

    def embed_audio(
        self, paths: Sequence[Path], ranges: Sequence[tuple[float, float] | None] | None = None
    ) -> np.ndarray:
        ranges = ranges or [None] * len(paths)
        vectors = []
        for path, time_range in zip(paths, ranges, strict=True):
            marker = f"{path.name.casefold()} {time_range or ''}".encode()
            vectors.append(self._features(marker))
        return self.normalize(np.stack(vectors))


class ClapEmbeddingProvider(EmbeddingProvider):
    name = "clap"
    version = "transformers-v1"
    audio_batch_size = 8

    def __init__(self, model: str = "laion/clap-htsat-unfused", device: str = "auto"):
        import torch
        import transformers
        from transformers import ClapModel, ClapProcessor

        self.model = model
        self.version = f"transformers-{transformers.__version__}"
        self.device = (
            "cuda"
            if device == "auto" and torch.cuda.is_available()
            else ("cpu" if device == "auto" else device)
        )
        self.processor = ClapProcessor.from_pretrained(model)
        self.network = ClapModel.from_pretrained(model).to(self.device).eval()
        self.dimension = int(self.network.config.projection_dim)
        self.decoder = AudioDecoder()

    def embed_text(self, texts: Sequence[str]) -> np.ndarray:
        import torch

        values = self.processor(text=list(texts), return_tensors="pt", padding=True)
        values = {k: v.to(self.device) for k, v in values.items()}
        with torch.inference_mode():
            output = self.network.get_text_features(**values, return_dict=True)
            result = output.pooler_output if hasattr(output, "pooler_output") else output
        return self.normalize(result.cpu().numpy().astype(np.float32))

    def embed_audio(
        self, paths: Sequence[Path], ranges: Sequence[tuple[float, float] | None] | None = None
    ) -> np.ndarray:
        import torch

        ranges = ranges or [None] * len(paths)
        outputs = []
        for offset in range(0, len(paths), self.audio_batch_size):
            batch_paths = paths[offset : offset + self.audio_batch_size]
            batch_ranges = ranges[offset : offset + self.audio_batch_size]
            clips = [
                self.decoder.decode(path, *(time_range or (None, None)))
                for path, time_range in zip(batch_paths, batch_ranges, strict=True)
            ]
            values = self.processor(
                audio=clips, sampling_rate=48_000, return_tensors="pt", padding=True
            )
            values = {k: v.to(self.device) for k, v in values.items()}
            with torch.inference_mode():
                output = self.network.get_audio_features(**values, return_dict=True)
                result = output.pooler_output if hasattr(output, "pooler_output") else output
            outputs.append(result.cpu().numpy().astype(np.float32))
        return self.normalize(np.concatenate(outputs))


def create_embedding_provider(
    name: str, model: str, device: str, dimension: int, allow_fallback: bool = True
) -> EmbeddingProvider:
    if name == "deterministic":
        return DeterministicEmbeddingProvider(dimension)
    if name != "clap":
        raise ValueError(f"Unsupported embedding provider: {name}")
    try:
        return ClapEmbeddingProvider(model, device)
    except (ImportError, OSError, RuntimeError) as exc:
        if not allow_fallback:
            raise
        logger.warning("CLAP unavailable; deterministic fallback active: %s", exc)
        return DeterministicEmbeddingProvider(dimension)
