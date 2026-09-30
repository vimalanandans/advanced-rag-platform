"""Local provider adapters. Domain code sees only these small, replaceable contracts."""

from __future__ import annotations

import json
import ipaddress
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class VectorIndex(Protocol):
    def create_index(self, dimensions: int) -> None: ...
    def upsert(self, point_id: str, vector: list[float], payload: dict) -> None: ...
    def search(self, vector: list[float], limit: int = 5, *, allowed_point_ids: list[str]) -> list[dict]: ...
    def health(self) -> bool: ...


class QdrantVectorIndex:
    """Minimal REST adapter; no Qdrant types leak into retrieval contracts."""

    def __init__(self, url: str = "http://localhost:6333", collection: str = "rag_evidence", allow_remote: bool = False) -> None:
        _validate_provider_url(url, allow_remote, {"qdrant"})
        self.url, self.collection = url.rstrip("/"), collection

    def create_index(self, dimensions: int) -> None:
        """Create the collection once, without overwriting an existing local index."""
        try:
            existing = self._request("GET", f"/collections/{self.collection}")
            vectors = existing.get("result", {}).get("config", {}).get("params", {}).get("vectors", {})
            if vectors.get("size") != dimensions or vectors.get("distance") != "Cosine":
                raise ValueError("vector collection is incompatible; create a new versioned index")
            return
        except HTTPError as error:
            if error.code != 404:
                raise
        self._request("PUT", f"/collections/{self.collection}", {"vectors": {"size": dimensions, "distance": "Cosine"}})

    def upsert(self, point_id: str, vector: list[float], payload: dict) -> None:
        self._request("PUT", f"/collections/{self.collection}/points?wait=true", {"points": [{"id": point_id, "vector": vector, "payload": payload}]})

    def search(self, vector: list[float], limit: int = 5, *, allowed_point_ids: list[str]) -> list[dict]:
        if not allowed_point_ids:
            return []
        response = self._request("POST", f"/collections/{self.collection}/points/search", {"vector": vector, "limit": limit, "with_payload": True, "filter": {"must": [{"has_id": allowed_point_ids}]}})
        return response.get("result", [])

    def health(self) -> bool:
        try:
            return self._request("GET", "/healthz").get("title") == "qdrant - vector search engine"
        except OSError:
            return False

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(f"{self.url}{path}", data=data, method=method, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:  # nosec B310: explicit local/provider URL
            return json.loads(response.read() or b"{}")


class OllamaModelProvider:
    """Optional local generation adapter. The deterministic generator remains the test default."""

    def __init__(self, url: str = "http://localhost:11434", model: str = "llama3.2", allow_remote: bool = False, revision: str | None = None) -> None:
        _validate_provider_url(url, allow_remote, {"ollama"})
        self.url, self.model = url.rstrip("/"), model
        self.revision = revision

    def _assert_revision(self, timeout: float) -> None:
        if self.revision is not None:
            with urlopen(f"{self.url}/api/tags", timeout=timeout) as response:
                models = json.loads(response.read()).get("models", [])
            if not any(item.get("name") == self.model and item.get("digest") == self.revision for item in models):
                raise ValueError("generation model is unavailable or its digest changed")

    def generate(self, prompt: str, *, timeout: float = 90, max_tokens: int | None = None) -> str:
        self._assert_revision(timeout)
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        if max_tokens is not None:
            payload["options"] = {"num_predict": max_tokens}
        request = Request(f"{self.url}/api/generate", data=json.dumps(payload).encode(), method="POST", headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=timeout) as response:  # nosec B310: explicit local/provider URL
            answer = json.loads(response.read())["response"]
        self._assert_revision(timeout)
        return answer


@dataclass(frozen=True)
class LocalProviderProfile:
    """Platform configuration, deliberately outside public pipeline contracts."""

    dense_mode: str = "deterministic"
    generation_mode: str = "deterministic"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "rag_evidence"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    @property
    def model_version(self) -> str:
        return (
            f"ollama:{self.ollama_model}"
            if self.generation_mode == "ollama"
            else "deterministic-local-generator@1.0.0"
        )


def provider_profile_from_environment(environ: dict[str, str] | None = None) -> LocalProviderProfile:
    """Load an explicit, local-only provider selection without leaking it into graphs."""
    import os

    values = os.environ if environ is None else environ
    profile = LocalProviderProfile(
        dense_mode=values.get("RAG_WORKBENCH_DENSE_MODE", "deterministic"),
        generation_mode=values.get("RAG_WORKBENCH_GENERATION_MODE", "deterministic"),
        qdrant_url=values.get("RAG_WORKBENCH_QDRANT_URL", "http://localhost:6333"),
        qdrant_collection=values.get("RAG_WORKBENCH_QDRANT_COLLECTION", "rag_evidence"),
        ollama_url=values.get("RAG_WORKBENCH_OLLAMA_URL", "http://localhost:11434"),
        ollama_model=values.get("RAG_WORKBENCH_OLLAMA_MODEL", "llama3.2"),
    )
    if profile.dense_mode not in {"deterministic", "qdrant"}:
        raise ValueError("RAG_WORKBENCH_DENSE_MODE must be deterministic or qdrant")
    if profile.generation_mode not in {"deterministic", "ollama"}:
        raise ValueError("RAG_WORKBENCH_GENERATION_MODE must be deterministic or ollama")
    return profile


def _validate_provider_url(url: str, allow_remote: bool, docker_hosts: set[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("provider URL must be a plain http(s) endpoint")
    if allow_remote:
        return
    host = parsed.hostname.lower()
    if host in {"localhost", *docker_hosts} or host.endswith(".local"):
        return
    try:
        if ipaddress.ip_address(host).is_private or ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    raise ValueError("remote provider endpoints require explicit allow_remote=True")
