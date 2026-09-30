from pathlib import Path
import pytest

from rag_workbench.contracts import RequestContext
from rag_workbench.evidence_store import EvidenceStore


def scope(tenant='local', **kwargs):
    return RequestContext(tenant_id=tenant, user_id='local-admin', **kwargs)


def staged(tmp_path):
    source = tmp_path / 'manual.md'
    source.write_text('# Safety\nNever remove the guard.\n## Repair\nSwitch off before repair.')
    store = EvidenceStore(tmp_path / 'store')
    return store, source, store.stage([source], corpus_id='manuals', request=scope())


def test_stage_requires_explicit_approval_and_preserves_originals(tmp_path):
    store, source, draft = staged(tmp_path)
    with pytest.raises(PermissionError, match='approved'):
        store.load(draft, scope())
    released = store.approve(draft, scope())
    assert released != draft
    original = source.read_bytes()
    source.write_text('changed input')
    reopened = EvidenceStore(store.directory)
    release = reopened.load(released, scope())
    evidence = release.documents[0].evidence
    assert evidence[1].metadata['parent_id'] == evidence[0].id
    assert evidence[0].metadata['child_ids'] == [evidence[1].id]
    assert reopened.resolve_original(released, evidence[0].id, scope()) == original
    assert reopened.load(draft, scope(), require_approved=False).approved_by is None
    assert reopened.approve(draft, scope()) == released


def test_identical_stage_is_deterministic_and_changed_revision_is_new(tmp_path):
    store, source, first = staged(tmp_path)
    assert store.stage([source], corpus_id='manuals', request=scope()) == first
    source.write_text('# New\nChanged revision.')
    second = store.stage([source], corpus_id='manuals', request=scope())
    assert second != first
    assert store.load(first, scope(), require_approved=False).documents[0].evidence[0].content.startswith('# Safety')


def test_release_scope_and_traversal_are_rejected(tmp_path):
    store, source, draft = staged(tmp_path)
    released = store.approve(draft, scope())
    with pytest.raises(FileNotFoundError):
        store.load(released, scope('other'))
    with pytest.raises(PermissionError):
        store.load(released, scope(allowed_corpora=['other']))
    with pytest.raises(PermissionError):
        store.stage([source], corpus_id='manuals', request=RequestContext(tenant_id='local', user_id='other'))
    with pytest.raises(ValueError, match='invalid'):
        store.load('../escape', scope())


def test_duplicates_empty_unsupported_and_oversize_fail(tmp_path):
    store, source, _ = staged(tmp_path)
    with pytest.raises(ValueError, match='duplicate'):
        store.stage([source, source], corpus_id='manuals', request=scope())
    with pytest.raises(ValueError):
        store.stage([], corpus_id='manuals', request=scope())
    unsupported = tmp_path / 'script.py'
    unsupported.write_text('print(1)')
    with pytest.raises(ValueError, match='only Markdown'):
        store.stage([unsupported], corpus_id='manuals', request=scope())
    with pytest.raises(ValueError, match='byte limit'):
        EvidenceStore(tmp_path / 'small', max_source_bytes=2).stage([source], corpus_id='manuals', request=scope())


def test_tampered_original_and_release_fail_closed(tmp_path):
    store, _, draft = staged(tmp_path)
    released = store.approve(draft, scope())
    release = store.load(released, scope())
    path = next(store.directory.glob('*/objects/' + release.documents[0].original_sha256))
    original = path.read_bytes()
    path.write_bytes(b'changed')
    with pytest.raises(ValueError, match='integrity'):
        store.load(released, scope())
    path.write_bytes(original)
    next(store.directory.glob('*/releases/' + released + '.json')).write_text('{}')
    with pytest.raises(ValueError, match='integrity'):
        store.load(released, scope())


def test_local_real_loads_only_pinned_approved_release(tmp_path):
    from rag_workbench.local_real import local_real_runtime
    source = tmp_path / 'manual.md'
    source.write_text('# Local\nOnly published content enters retrieval.')
    store = EvidenceStore(tmp_path / 'evidence')
    draft = store.stage([source], corpus_id='manuals', request=scope())
    values = {'RAG_WORKBENCH_EMBEDDING_MODEL': 'test:latest', 'RAG_WORKBENCH_EMBEDDING_REVISION': 'digest',
              'RAG_WORKBENCH_EMBEDDING_DIMENSIONS': '2', 'RAG_WORKBENCH_OLLAMA_MODEL': 'generator:latest',
              'RAG_WORKBENCH_GENERATION_REVISION': 'digest', 'RAG_WORKBENCH_STORAGE': str(tmp_path),
              'RAG_WORKBENCH_CORPUS_RELEASE': draft}
    with pytest.raises(PermissionError):
        local_real_runtime(environ=values)
    released = store.approve(draft, scope())
    values['RAG_WORKBENCH_CORPUS_RELEASE'] = released
    runtime = local_real_runtime(environ=values)
    assert runtime.asset_versions['corpus_release'] == released
    assert len(runtime.evidence) == 1
    assert runtime.evidence[0].metadata['corpus_id'] == 'manuals'


def test_original_resolver_checks_selected_revision(tmp_path):
    store, _, draft = staged(tmp_path)
    released = store.approve(draft, scope())
    item = store.load(released, scope()).documents[0].evidence[0]
    with pytest.raises(PermissionError, match='scope'):
        store.resolve_original(released, item.id, scope(allowed_revisions={item.document_id:'other'}))
    with pytest.raises(KeyError):
        store.resolve_original(released, 'unknown', scope())


def test_pdf_publication_retains_page_locator_and_original(tmp_path):
    from test_ingestion import _write_text_pdf
    source = tmp_path / 'policy.pdf'
    _write_text_pdf(source)
    store = EvidenceStore(tmp_path / 'evidence')
    draft = store.stage([source], corpus_id='pdf-policy', request=scope())
    released = store.approve(draft, scope())
    document = store.load(released, scope()).documents[0]
    assert document.media_type == 'pdf'
    assert document.evidence[0].locator == 'page:1'
    assert store.resolve_original(released, document.evidence[0].id, scope()) == source.read_bytes()
