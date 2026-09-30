"""Tenant-scoped immutable originals and explicitly approved corpus releases."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rag_workbench.contracts import Evidence, RequestContext
from rag_workbench.ingestion import ingest_structural_path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: BaseModel) -> bytes:
    return json.dumps(value.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()


class DocumentRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(min_length=1)
    original_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    media_type: Literal["markdown", "pdf"]
    evidence: list[Evidence] = Field(min_length=1)


class CorpusRelease(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    tenant_id: str = Field(min_length=1)
    corpus_id: str = Field(min_length=1)
    parser_version: Literal["structural-text@2.0.0"] = "structural-text@2.0.0"
    chunker_version: Literal["heading-page@1.0.0"] = "heading-page@1.0.0"
    policy_version: Literal["local-admin-review@1.0.0"] = "local-admin-review@1.0.0"
    approved_by: str | None = None
    documents: list[DocumentRevision] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_snapshot(self):
        ids, documents = set(), set()
        for document in self.documents:
            if document.document_id in documents:
                raise ValueError("release contains duplicate document IDs")
            documents.add(document.document_id)
            for item in document.evidence:
                if item.id in ids:
                    raise ValueError("release contains duplicate evidence IDs")
                ids.add(item.id)
                if (item.tenant_id != self.tenant_id or item.document_id != document.document_id
                        or item.revision != document.original_sha256 or item.metadata.get("corpus_id") != self.corpus_id):
                    raise ValueError("evidence identity differs from release")
                expected = "approved" if self.approved_by else "review_required"
                if item.approval_state != expected:
                    raise ValueError("evidence approval differs from release")
        return self


class EvidenceStore:
    """Local-admin publication; no mutable active pointer or automatic approval."""
    def __init__(self, directory: Path, max_source_bytes: int = 20 * 1024 * 1024):
        if max_source_bytes <= 0:
            raise ValueError("source limit must be positive")
        self.directory, self.max_source_bytes = directory, max_source_bytes

    def _scope(self, request: RequestContext, corpus_id: str | None = None) -> Path:
        if request.user_id != "local-admin" or not request.tenant_id:
            raise PermissionError("evidence publication requires local administrator")
        if corpus_id is not None and request.allowed_corpora and corpus_id not in request.allowed_corpora:
            raise PermissionError("corpus is outside request scope")
        return self.directory / digest(request.tenant_id.encode())

    def _write(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temporary = tempfile.mkstemp(prefix=".publish-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes() != content:
                    raise ValueError("immutable evidence object differs")
        finally:
            os.unlink(temporary)

    def stage(self, paths: list[Path], *, corpus_id: str, request: RequestContext) -> str:
        root = self._scope(request, corpus_id)
        documents = []
        for path in paths:
            suffix = path.suffix.lower()
            if suffix not in {".md", ".pdf"}:
                raise ValueError("only Markdown and PDF originals are supported")
            with path.open("rb") as source:
                content = source.read(self.max_source_bytes + 1)
            if len(content) > self.max_source_bytes:
                raise ValueError("original exceeds configured byte limit")
            sha = digest(content)
            # Name is the caller's document key within this corpus; duplicate names fail.
            document_id = corpus_id + ":" + path.name
            object_path = root / "objects" / sha
            self._write(object_path, content)
            # Parse the snapshotted bytes, never a path that can change after hashing.
            fd, temporary = tempfile.mkstemp(suffix=suffix, dir=object_path.parent)
            try:
                with os.fdopen(fd, "wb") as output:
                    output.write(content)
                extracted = ingest_structural_path(Path(temporary), corpus_id)
            finally:
                os.unlink(temporary)
            mapping = {item.id: digest(f"{document_id}:{sha}:{item.locator}".encode()) for item in extracted}
            evidence = []
            for item in extracted:
                metadata = {**item.metadata, "source_sha256": sha, "chunker_version": "heading-page@1.0.0"}
                metadata["child_ids"] = [mapping[x] for x in metadata.get("child_ids", [])]
                if "parent_id" in metadata:
                    metadata["parent_id"] = mapping[metadata["parent_id"]]
                evidence.append(item.model_copy(update={
                    "id": mapping[item.id], "document_id": document_id, "revision": sha,
                    "tenant_id": request.tenant_id, "title": path.stem,
                    "source_uri": f"cas://{sha}", "metadata": metadata,
                    "approval_state": "review_required", "allowed_users": [request.user_id],
                }))
            documents.append(DocumentRevision(document_id=document_id, original_sha256=sha,
                                              media_type="pdf" if suffix == ".pdf" else "markdown", evidence=evidence))
        release = CorpusRelease(tenant_id=request.tenant_id, corpus_id=corpus_id,
                                documents=sorted(documents, key=lambda item: item.document_id))
        return self._save(release, request)

    def _save(self, release: CorpusRelease, request: RequestContext) -> str:
        content = canonical(CorpusRelease.model_validate(release.model_dump()))
        identifier = digest(content)
        self._write(self._scope(request, release.corpus_id) / "releases" / (identifier + ".json"), content)
        return identifier

    def load(self, identifier: str, request: RequestContext, *, require_approved: bool = True) -> CorpusRelease:
        root = self._scope(request)
        if not re.fullmatch(r"[0-9a-f]{64}", identifier):
            raise ValueError("invalid corpus release ID")
        content = (root / "releases" / (identifier + ".json")).read_bytes()
        if digest(content) != identifier:
            raise ValueError("corpus release integrity check failed")
        release = CorpusRelease.model_validate_json(content)
        self._scope(request, release.corpus_id)
        if release.tenant_id != request.tenant_id:
            raise PermissionError("corpus release tenant mismatch")
        if require_approved and release.approved_by != "local-admin":
            raise PermissionError("corpus release has not been approved")
        for document in release.documents:
            self._original(document.original_sha256, request)
        return release

    def approve(self, identifier: str, request: RequestContext) -> str:
        release = self.load(identifier, request, require_approved=False)
        release.approved_by = request.user_id
        for document in release.documents:
            for item in document.evidence:
                item.approval_state = "approved"
        return self._save(release, request)

    def _original(self, sha: str, request: RequestContext) -> bytes:
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("invalid original ID")
        content = (self._scope(request) / "objects" / sha).read_bytes()
        if digest(content) != sha:
            raise ValueError("original integrity check failed")
        return content

    def resolve_original(self, identifier: str, evidence_id: str, request: RequestContext) -> bytes:
        release = self.load(identifier, request)
        for document in release.documents:
            for item in document.evidence:
                if item.id != evidence_id:
                    continue
                if (request.user_id not in item.allowed_users
                        or (item.valid_from is not None and request.requested_at < item.valid_from)
                        or (item.valid_until is not None and request.requested_at >= item.valid_until)
                        or (item.document_id in request.allowed_revisions and request.allowed_revisions[item.document_id] != item.revision)
                        or not set(item.applicability_tags) <= set(request.applicability_tags)):
                    raise PermissionError("source is outside request scope")
                return self._original(document.original_sha256, request)
        raise KeyError("evidence is not in the selected release")
