"""Provider-neutral embedding identity and explicit local Ollama adapter."""

from __future__ import annotations

import json
import math
from typing import Literal, Protocol
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field

from rag_workbench.providers import _validate_provider_url


class EmbeddingIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    provider: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    dimensions: int = Field(gt=0, le=65536)
    normalization: Literal["l2", "none"] = "l2"
    contract_version: Literal["1.0.0"] = "1.0.0"
    query_prefix: str = ""
    document_prefix: str = ""


class EmbeddingProvider(Protocol):
    identity: EmbeddingIdentity
    def encode(self, texts: list[str], *, purpose: Literal["query", "document"]) -> list[list[float]]: ...
    def health(self) -> bool: ...


class OllamaEmbeddingProvider:
    """Pinned embedding model; no download, truncation or hash-vector fallback."""

    def __init__(self, identity: EmbeddingIdentity, *, url: str = "http://localhost:11434",
                 batch_size: int = 16, timeout: float = 10.0, max_input_bytes: int = 32768):
        _validate_provider_url(url, False, {"ollama", "host.docker.internal"})
        if identity.provider != "ollama":
            raise ValueError("Ollama adapter requires an Ollama embedding identity")
        if batch_size <= 0 or timeout <= 0 or max_input_bytes <= 0:
            raise ValueError("embedding resource bounds must be positive")
        self.identity, self.url = identity, url.rstrip("/")
        self.batch_size, self.timeout, self.max_input_bytes = batch_size, timeout, max_input_bytes

    def _request(self, path: str, payload: dict | None = None) -> dict:
        request = Request(self.url + path, data=json.dumps(payload).encode() if payload is not None else None,
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read())

    def _assert_identity(self) -> None:
        models = self._request("/api/tags").get("models", [])
        if not any(item.get("name") == self.identity.model_id and item.get("digest") == self.identity.revision for item in models):
            raise ValueError("embedding model is unavailable or its digest changed")

    def health(self) -> bool:
        try:
            self._assert_identity()
            return True
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def encode(self, texts: list[str], *, purpose: Literal["query", "document"]) -> list[list[float]]:
        if purpose not in {"query", "document"}:
            raise ValueError("embedding purpose must be query or document")
        prefix = self.identity.query_prefix if purpose == "query" else self.identity.document_prefix
        inputs = [prefix + text for text in texts]
        if any(len(text.encode()) > self.max_input_bytes for text in inputs):
            raise ValueError("embedding input exceeds configured byte bound")
        vectors = []
        for start in range(0, len(inputs), self.batch_size):
            self._assert_identity()
            batch = inputs[start:start + self.batch_size]
            response = self._request("/api/embed", {"model": self.identity.model_id, "input": batch, "truncate": False})
            values = response.get("embeddings", [])
            if len(values) != len(batch):
                raise ValueError("embedding provider returned incorrect batch cardinality")
            for value in values:
                if len(value) != self.identity.dimensions or any(not isinstance(item, (int, float)) or not math.isfinite(item) for item in value):
                    raise ValueError("embedding vector dimensions or values are invalid")
                norm = math.sqrt(sum(item * item for item in value))
                if not norm:
                    raise ValueError("embedding provider returned a zero vector")
                vectors.append([item / norm for item in value] if self.identity.normalization == "l2" else value)
            self._assert_identity()
        return vectors
