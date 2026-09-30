"""Measure the fixed HotpotQA question-scoped BM25 baseline without generation."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rag_workbench.contracts import Evidence
from rag_workbench.experimentation import DatasetManifest, corpus_fingerprint, ranking_metrics
from rag_workbench.lexical import PersistentBM25Retriever


def evaluate(directory: Path, *, k: int = 5) -> dict:
    provenance = json.loads((directory / 'provenance.json').read_text())
    dataset = DatasetManifest.model_validate_json((directory / 'dataset.json').read_text())
    corpus = [Evidence.model_validate(item) for item in json.loads((directory / 'corpus.json').read_text())]
    if corpus_fingerprint(corpus) != dataset.corpus_revision or provenance['dataset_fingerprint'] != dataset.fingerprint:
        raise ValueError('HotpotQA benchmark identities differ')
    by_scope = defaultdict(list)
    for item in corpus:
        by_scope[item.metadata['corpus_id']].append(item)
    retriever = PersistentBM25Retriever(directory / 'bm25.sqlite')
    groups = defaultdict(list)
    for case in dataset.cases:
        if case.split != 'held_out' or set(case.policy_constraints) != {'allowed_corpora'}:
            raise ValueError('HotpotQA case has unexpected scope or split')
        permitted = case.policy_constraints['allowed_corpora']
        if len(permitted) != 1 or not by_scope[permitted[0]]:
            raise ValueError('HotpotQA case scope is missing')
        candidates = retriever.retrieve(case.query, by_scope[permitted[0]], limit=k)
        metrics = ranking_metrics([candidate.evidence.id for candidate in candidates], case, k)
        groups[case.query_class].append(metrics)
    def summary(values):
        return {'cases': len(values), 'mean_recall_at_5': sum(x.recall_at_k for x in values) / len(values),
                'mean_mrr': sum(x.mrr for x in values) / len(values),
                'all_supporting_paragraphs_in_top_5': sum(x.recall_at_k == 1 for x in values)}
    result = {'dataset_fingerprint': dataset.fingerprint, 'corpus_revision': dataset.corpus_revision,
              'source_sha256': provenance['source_sha256'], 'strategy': 'persistent-bm25@2.0.0',
              'scope': 'question-scoped distractor passage set', 'k': k,
              'overall': summary([item for values in groups.values() for item in values]),
              'by_query_class': {name: summary(values) for name, values in sorted(groups.items())},
              'answer_quality': None, 'note': 'Retrieval only; no generation or source-sentence support measured.'}
    (directory / 'bm25-baseline.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    location = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / '.local/corpora/hotpotqa/benchmark'
    print(json.dumps(evaluate(location), indent=2))
