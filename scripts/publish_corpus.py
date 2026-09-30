"""Stage originals, inspect a release, or explicitly approve a corpus snapshot."""
from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_workbench.contracts import RequestContext
from rag_workbench.evidence_store import EvidenceStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--storage', type=Path, default=Path('.local/evidence'))
    parser.add_argument('--tenant', default='local')
    actions = parser.add_subparsers(dest='action', required=True)
    stage = actions.add_parser('stage')
    stage.add_argument('--corpus', required=True)
    stage.add_argument('sources', nargs='+', type=Path)
    for name in ['inspect', 'approve']:
        action = actions.add_parser(name)
        action.add_argument('release')
    args = parser.parse_args()
    store = EvidenceStore(args.storage)
    request = RequestContext(tenant_id=args.tenant, user_id='local-admin')
    if args.action == 'stage':
        print(store.stage(args.sources, corpus_id=args.corpus, request=request))
    elif args.action == 'inspect':
        print(store.load(args.release, request, require_approved=False).model_dump_json(indent=2))
    else:
        print(store.approve(args.release, request))


if __name__ == '__main__':
    main()
