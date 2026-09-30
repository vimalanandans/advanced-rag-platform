"""Summarize complete local A-F records without copying licensed case content."""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = 'ABCDEF'


def summarize(root: Path) -> dict:
    records = {}
    for arm in ARMS:
        files = list((root / f'arm-{arm.lower()}').glob(f'local-real-{arm.lower()}--*.json'))
        if len(files) != 1:
            raise ValueError(f'expected exactly one result for arm {arm}')
        records[arm] = json.loads(files[0].read_text())
    dataset_fingerprints = {r['dataset_fingerprint'] for r in records.values()}
    source_revisions = {r['dataset_snapshot']['corpus_revision'] for r in records.values()}
    if len(dataset_fingerprints) != 1 or len(source_revisions) != 1:
        raise ValueError('strategy records use different dataset or corpus identities')
    controlled = []
    for record in records.values():
        config = record['configuration_snapshot']
        assets = config['asset_versions']
        controlled.append(json.dumps({
            'generation': assets['generation'], 'generation_options': assets['generation_options'],
            'embedding': config['embedding_identity'], 'indexes': config['index_revisions'],
            'request': config['request'], 'split': config['split'], 'k': config['k'],
            'budgets': record['pipeline_snapshot']['budgets'],
        }, sort_keys=True))
    if len(set(controlled)) != 1:
        raise ValueError('strategy records differ in controlled provider, scope, index or budget settings')
    cases = {arm: {case['case_id']: case for case in record['case_results']} for arm, record in records.items()}
    identifiers = set(cases['A'])
    if any(set(items) != identifiers or len(items) != len(identifiers) for items in cases.values()):
        raise ValueError('strategy records have different case sets')
    if any(case['status'] != 'completed' for items in cases.values() for case in items.values()):
        raise ValueError('comparison needs a completed run for every case and arm')
    by_class = defaultdict(list)
    for case_id in sorted(identifiers):
        by_class[cases['A'][case_id]['query_class']].append(case_id)
    result = {'schema_version': '1.0.0', 'dataset_fingerprint': dataset_fingerprints.pop(),
              'corpus_revision': source_revisions.pop(), 'case_count': len(identifiers),
              'setting': 'HotpotQA question-scoped distractor validation; locked held-out',
              'decision': 'iterate', 'arms': {}}
    for arm in ARMS:
        record = records[arm]
        values = list(cases[arm].values())
        def recall(case): return case['ranking']['recall_at_k']
        deltas = [recall(cases[arm][case_id]) - recall(cases['A'][case_id]) for case_id in sorted(identifiers)]
        # Stratified paired bootstrap. This describes sample variation, not a new held-out set.
        rng = random.Random(42)
        resampled = []
        for _ in range(2000):
            sample = [rng.choice(ids) for ids in by_class.values() for _ in ids]
            resampled.append(sum(recall(cases[arm][case_id]) - recall(cases['A'][case_id]) for case_id in sample) / len(sample))
        resampled.sort()
        result['arms'][arm] = {
            'graph_fingerprint': record['candidate_strategy']['graph_fingerprint'],
            'completed_cases': record['metrics']['completed_cases'],
            'retrieval_recall_at_5': record['metrics']['recall_at_k'],
            'retrieval_mrr': record['metrics']['mrr'],
            'all_supporting_paragraphs_in_top_5': sum(recall(case) == 1 for case in values),
            'delta_recall_at_5_vs_A': sum(deltas) / len(deltas),
            'paired_stratified_bootstrap_95pct_interval': [resampled[50], resampled[1949]],
            'abstained': sum(case.get('abstained', False) for case in values),
            'answer_citation_expectations_passed': record['metrics']['fixture_passes'],
            'mean_case_latency_ms': sum(case['latency_ms'] for case in values) / len(values),
            'unsupported_attempted_claim_rate': record['metrics']['unsupported_claim_rate'],
            'by_query_class': {kind: {'cases': len(ids), 'recall_at_5': sum(recall(cases[arm][case_id]) for case_id in ids) / len(ids)}
                               for kind, ids in sorted(by_class.items())},
        }
    return result


if __name__ == '__main__':
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / '.local/corpora/hotpotqa/benchmark'
    summary = summarize(directory)
    (directory / 'comparison-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
