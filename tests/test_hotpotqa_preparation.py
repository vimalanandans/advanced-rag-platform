import json
from hashlib import sha256
from pathlib import Path

import pytest

pa = pytest.importorskip('pyarrow')
pq = pytest.importorskip('pyarrow.parquet')
from rag_workbench.contracts import Evidence
from rag_workbench.experimentation import DatasetManifest, corpus_fingerprint
from scripts.prepare_hotpotqa import prepare, verified_hash


def sample_source(tmp_path, *, invalid=False):
    records = []
    for kind in ('bridge', 'comparison'):
        for index in range(2):
            records.append({
                'id': f'{kind}-{index}', 'question': f'Which {kind} answer {index}?',
                'answer': 'yes', 'type': kind, 'level': 'hard',
                'supporting_facts': {'title': ['Article A', 'Article B'], 'sent_id': [0, 0 if not invalid else 3]},
                'context': {'title': ['Article A', 'Article B', 'Distractor'],
                            'sentences': [['A claim.'], ['B claim.'], ['Different fact.']]},
            })
    path = tmp_path / 'sample.parquet'
    pq.write_table(pa.Table.from_pylist(records), path)
    return path, sha256(path.read_bytes()).hexdigest()


def test_preparation_is_deterministic_and_scopes_questions(tmp_path):
    source, source_hash = sample_source(tmp_path)
    output = tmp_path / 'prepared'
    first = prepare(source, output, expected_sha256=source_hash, per_stratum=1)
    second = prepare(source, output, expected_sha256=source_hash, per_stratum=1)
    assert first == second
    assert first['selected_cases'] == 2
    corpus = [Evidence.model_validate(x) for x in json.loads((output / 'corpus.json').read_text())]
    data = DatasetManifest.model_validate_json((output / 'dataset.json').read_text())
    assert len(corpus) == 6
    assert data.corpus_revision == corpus_fingerprint(corpus)
    assert len({item.metadata['corpus_id'] for item in corpus}) == 2
    for case in data.cases:
        permitted = case.policy_constraints['allowed_corpora'][0]
        assert len([item for item in corpus if item.metadata['corpus_id'] == permitted]) == 3
        assert len(case.expected_evidence_ids) == 2
        assert case.split == 'held_out'
        assert not any('yes' in item.content for item in corpus)


def test_preparation_rejects_checksum_and_invalid_support(tmp_path):
    source, source_hash = sample_source(tmp_path, invalid=True)
    with pytest.raises(ValueError, match='checksum'):
        verified_hash(source, '0' * 64)
    with pytest.raises(ValueError, match='sentence index'):
        prepare(source, tmp_path / 'output', expected_sha256=source_hash, per_stratum=1)
    assert not (tmp_path / 'output' / 'dataset.json').exists()
