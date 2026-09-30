# V2 research plan

Status: research protocol and queue, not completed literature review. No model selection or performance claim is approved by this document. Research primary sources before each advanced technique is implemented; record the access date and source revision.

## Required research record

For each technique record: problem solved; paper/official source; architecture; dataset; metrics and claimed improvement; limitations and negative cases; runtime/memory implications; Apple Silicon feasibility; model/code/data licenses; mapping to graph/component/provider contracts; proposed baseline experiment; decision and unresolved questions. Distinguish source claims from locally reproduced results.

Save records under `docs/research/`. Revisit them when model/API/license versions change. Research may propose an ADR but cannot silently change contracts or mandatory safety gates.

## Research queue

| Order | Topic | Evaluation question / contract impact |
| --- | --- | --- |
| 1 | Local embeddings and persistent BM25 | Which query/document encoders and lexical analyzers meet M3 memory/latency and recall needs? Pin dimensions, normalization, model digest, license, batching and index migration. |
| 2 | Qdrant scope filters and index lifecycle | Can eligibility be applied before top-k with revision/tenant constraints and stable recall? Validate API behavior against the selected version. |
| 3 | Hierarchical chunks and parent-child expansion | Which structures preserve warnings/tables and source locators within context budgets? Compare with fixed chunks. |
| 4 | Local rerankers | Does RRF + reranker improve MRR/nDCG and citation coverage enough to justify measured memory/latency? |
| 5 | Query classification and safe routing | Which rules/model labels distinguish the twelve query classes without suppressing necessary lanes? |
| 6 | Claim support and contradiction/temporal checks | Which deterministic checks and calibrated verifiers detect unsupported/conflicting claims without treating confidence as truth? |
| 7 | Rewrite, expansion, multi-query, HyDE and decomposition | Which specific recall failure improves? Generated text must remain retrieval assistance, never source authority. |
| 8 | MMR, contextual chunks/compression and neighbor expansion | Does context retain evidence/qualifiers while reducing duplication and token use? |
| 9 | Late interaction, learned sparse, typed, graph and visual retrieval | Does a content-specific experiment justify extra indexing/model/runtime complexity? |
| 10 | Corrective and agentic retrieval | Do bounded corrective actions resolve known failures within remaining budgets and scope? |
| 11 | Experience memory and policy/model learning | Is trajectory quality sufficient for offline policy analysis, reranker/retriever fine-tuning or contextual bandits before broader RL? |

## Local model selection procedure

Record M3 variant, RAM, OS, serving runtime, model version/quantization, context limits and license. Compare native Ollama/MLX and supported container paths where relevant; do not assume container GPU equivalence. Measure cold load, warm latency, batch throughput, peak memory and coexistence with PostgreSQL/Qdrant/Studio. Reject defaults that exceed the measured envelope. Keep provider SDK and model-specific settings behind adapters.

The initial scope does not train a language model with RL. Later rewards may include evidence retrieval, supported claims, citations, correct abstention and resolution, with costs for unnecessary calls, latency, tokens and unsupported claims. Policy violations remain forbidden actions/hard rejection gates, not penalties that can be traded for reward. Offline learning requires leakage-controlled trajectories, a fixed baseline, versioned policy, safety evaluation and explicit promotion.
