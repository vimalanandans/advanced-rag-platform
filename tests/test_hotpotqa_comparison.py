import json

import pytest

from scripts.summarize_hotpotqa_comparison import summarize


def records(tmp_path, missing=False):
    for arm in 'ABCDEF'[:5 if missing else 6]:
        folder = tmp_path / f'arm-{arm.lower()}'
        folder.mkdir()
        record = {
            'dataset_fingerprint': 'dataset', 'dataset_snapshot': {'corpus_revision': 'corpus'},
            'candidate_strategy': {'graph_fingerprint': arm * 64},
            'configuration_snapshot': {'asset_versions': {'generation': 'g', 'generation_options': '{}'},
                                       'embedding_identity': {'model': 'e'}, 'index_revisions': {'vector': 'v'},
                                       'request': {'tenant': 'local'}, 'split': 'held_out', 'k': 5},
            'pipeline_snapshot': {'budgets': {'max_latency_ms': 60000}},
            'case_results': [
                {'case_id': f'case-{index}', 'query_class': kind, 'status': 'completed',
                 'ranking': {'recall_at_k': 1.0 if arm != 'A' or index == 0 else 0.0},
                 'latency_ms': 10, 'abstained': False}
                for index, kind in enumerate(('comparison', 'multi_hop'))],
            'metrics': {'completed_cases': 2, 'recall_at_k': {'mean': 1.0},
                        'mrr': {'mean': 1.0}, 'fixture_passes': 0, 'unsupported_claim_rate': None},
        }
        (folder / f'local-real-{arm.lower()}--test.json').write_text(json.dumps(record))


def test_comparison_is_paired_and_contains_only_aggregate_metrics(tmp_path):
    records(tmp_path)
    result = summarize(tmp_path)
    assert result['case_count'] == 2
    assert result['arms']['A']['delta_recall_at_5_vs_A'] == 0
    assert result['arms']['B']['delta_recall_at_5_vs_A'] == 0.5
    assert result['arms']['B']['all_supporting_paragraphs_in_top_5'] == 2
    assert 'case-0' not in json.dumps(result)


def test_comparison_rejects_incomplete_arms(tmp_path):
    records(tmp_path, missing=True)
    with pytest.raises(ValueError, match='exactly one'):
        summarize(tmp_path)


def test_comparison_rejects_changed_model_settings(tmp_path):
    records(tmp_path)
    path = next((tmp_path / 'arm-b').glob('*.json'))
    record = json.loads(path.read_text())
    record['configuration_snapshot']['asset_versions']['generation'] = 'other-model'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='controlled'):
        summarize(tmp_path)
