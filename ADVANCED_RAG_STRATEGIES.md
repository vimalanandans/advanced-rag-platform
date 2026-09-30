# Advanced RAG Strategies: A Generic Content Guide

## Learning objective

- **Classify** advanced RAG techniques by the problem they solve.
- **Select** a suitable baseline for generic content such as policies, research, product documentation, contracts, manuals, and knowledge bases.
- **Recognise** the limitations that require an additional retrieval lane, quality gate, or human review.

📌 **Definition:** Retrieval-augmented generation (**RAG**) selects relevant, permitted source evidence and supplies it to an answer model. A RAG system is therefore an **evidence-selection system**, not merely a chat model connected to a vector database.

## Strategy index: start with the question type

| If the content or question has this property | Start with this strategy | Add this when the baseline is insufficient | Do not skip |
| --- | --- | --- | --- |
| **Exact phrases, names, IDs, citations, or codes** | Lexical / BM25 retrieval | Exact-identifier lookup; learned sparse retrieval | Normalisation and access/revision filters |
| **Paraphrased conceptual questions** | Dense semantic retrieval | Query rewriting, multi-query retrieval, HyDE, or a reranker | Candidate-recall evaluation |
| **Mixed exact and semantic questions** | Hybrid dense + lexical retrieval with RRF | Multi-channel quotas and reranking | A separate exact lane; dense retrieval alone is not enough |
| **Long reports, books, or manuals** | Structural / hierarchical chunks | Parent–child retrieval, contextual chunks, recursive summaries | Source section and page provenance |
| **Tables, procedures, warnings, or forms** | Typed-object retrieval | Contextual compression and deterministic validation | Keep structure, units, warnings, and source location together |
| **Figures, diagrams, screenshots, or layout** | Multimodal / visual-evidence retrieval | Multi-vector visual retrieval and specialist extraction | Image-backed review for ambiguous or safety-critical claims |
| **Multi-part or multi-hop questions** | Query decomposition | Iterative retrieval or evidence-backed graph traversal | A plan for combining sub-answer evidence |
| **Many similar results or conflicting sources** | RRF and metadata filters | MMR diversity, evidence-quality ranking, and claim verification | Freshness, authority, revision, and applicability controls |
| **Weak, missing, or disputed evidence** | Abstention and human review | Corrective or self-reflective retrieval approaches | Never convert a low-confidence signal into automatic truth |

### Overall RAG strategy map

```text
Question / task
    |
    +-- Is an external source needed? -- no --> answer without RAG, under product policy
    |
    `-- yes
         |
         +-- What is required? --> exact | semantic | structured | visual | multi-hop
         |
         v
    Apply access + freshness + revision + applicability filters
         |
         v
    Select one or more candidate lanes
    lexical | dense | typed | visual | graph | external tool
         |
         v
    Improve recall when needed
    rewrite | multi-query | HyDE | decomposition | parent-child
         |
         v
    Improve precision and coverage
    RRF | MMR diversity | reranker | contextual compression
         |
         v
    Build bounded, cited evidence context
         |
         +-- evidence sufficient --> answer + citations
         `-- evidence insufficient --> abstain, ask for context, or send to review
```

- **The map is a selection aid, not a mandatory pipeline.** Each additional
  stage adds cost, latency, and failure modes.
- **The safest default** is structural ingestion, metadata filters, hybrid
  lexical+dense retrieval, citations, abstention, and evaluation.
- **Add a strategy only** when evaluation identifies a specific recall,
  precision, structure, freshness, or trust gap.

## The RAG decision flow

```text
                        OFFLINE: when a source changes

  Source → convert → validate → chunk / type → index → publish approved evidence

                         ONLINE: for every question

  Query → classify → filter → retrieve candidates → rank → assemble context
        → answer with citations, or abstain
```

- **Offline work** performs expensive conversion, validation, chunking, and indexing once for a source version.
- **Online work** selects a small, applicable evidence set for each question.
- **Filters** for access, freshness, revision, and applicability execute before semantic ranking; a similar but unauthorized or obsolete source is still invalid.
- **Abstention** is a valid outcome when no approved, applicable evidence is sufficient.

## 1. Retrieval foundations

| Category | Sub-category | Strategy | Advantage | Challenges and limitations |
| --- | --- | --- | --- | --- |
| **Retrieval foundations** | **Lexical retrieval** | Rank passages by transparent keyword or token overlap. | **Cheap, deterministic, and explainable**; performs well for exact terminology. | Misses paraphrases and synonyms; provides no semantic understanding; simple overlap ranking is weak for long or ambiguous queries. |
| **Retrieval foundations** | **Dense semantic retrieval** | Embed documents and queries in a shared vector space and retrieve nearest passages. | Finds **conceptually related** material when wording differs; supports a scalable semantic baseline. | Can miss rare terms, names, and identifiers; results are less transparent; document/query embedding compatibility and index versioning matter. |
| **Retrieval foundations** | **Agent or tool routing** | Classify intent and choose document retrieval, a structured-data tool, or both. | Uses the **right source type** for each question instead of forcing all questions through RAG. | Routing mistakes hide evidence; tool permissions, latency, failures, and fallback behavior need explicit handling. |
| **Retrieval foundations** | **Multimodal grounding** | Combine text/table retrieval with inspection of a source page, figure, form, screenshot, or diagram. | Recovers **layout-bound information** that plain-text extraction loses. | Visual processing costs more and takes longer; visual-model output must remain tied to source evidence and cannot become unverified fact. |

⚠️ **Common pitfall:** Dense search is not a replacement for exact search. Identifiers, names, citations, and short codes often require a lexical or exact-match lane.

## 2. Query understanding and candidate retrieval

```text
Question
   |
   +-- identifier / exact phrase ----> lexical or exact lane
   +-- conceptual question ----------> dense semantic lane
   +-- table / procedure ------------> typed-object lane
   +-- figure / layout question -----> visual-evidence lane
   +-- relationship / multi-hop ------> graph lane, when evidence-backed
   |
   `-- every path: access + revision + applicability filters first
```

| Category | Sub-category | Strategy | Advantage | Challenges and limitations |
| --- | --- | --- | --- | --- |
| **Query understanding** | **Domain query expansion** | Add known domain terms or related expressions before retrieval. | Improves recall for **abbreviations** and underspecified questions. | Can add noise or bias; rules must be evaluated by query class and remain observable. |
| **Query understanding** | **Query classification** | Identify the information need: narrative, identifier, table, procedure, visual evidence, comparison, or relationship. | Selects the **most relevant and economical** retrieval lanes. | A wrong class can suppress the best lane; use bounded rules, a safe default, and evaluation by class. |
| **Query transformation** | **Query rewriting** | Rewrite an informal, ambiguous, or incomplete user question into a retrieval-oriented query while retaining the original question for audit. | Improves retrieval vocabulary and can resolve abbreviations, spelling variants, and implicit intent. | Rewrites can change meaning or add unsupported constraints; preserve the original and evaluate rewrite quality. |
| **Query transformation** | **Multi-query retrieval** | Generate several complementary query formulations, retrieve for each, then fuse or deduplicate the results. | Broadens recall when a single wording has blind spots. | Increases cost and duplicates; generated variants can drift from user intent, so cap the number and log each variant. |
| **Query transformation** | **HyDE** | Generate a hypothetical answer-shaped document, embed it, and use the embedding to retrieve real corpus evidence. | Can improve zero-shot dense retrieval when the query does not resemble source wording. | The hypothetical document can contain false details and must never be presented or cited as evidence; validate against real retrieved sources. [Paper](https://arxiv.org/abs/2212.10496) |
| **Query transformation** | **Self-query metadata construction** | Translate a question into structured metadata constraints plus a semantic query. | Lets natural-language requests narrow retrieval by date, region, type, owner, or other supported fields. | Generated filters can be wrong or unavailable; validate against an allow-listed schema and never bypass access controls. |
| **Query transformation** | **Query decomposition** | Split a complex question into smaller retrieval subquestions, then combine their evidence. | Improves coverage for comparison, synthesis, and multi-hop questions. | Decomposition errors cascade; each sub-answer needs its own evidence and the final combination needs contradiction handling. |
| **Query transformation** | **Iterative retrieval** | Use the first retrieved evidence to refine the next query or select the next subquestion. | Helps when later evidence depends on earlier facts. | Adds latency and can compound early mistakes; cap iterations and preserve a trace of each decision. |
| **Candidate retrieval** | **Exact identifier lookup** | Normalise and query identifiers, codes, names, part numbers, or short strings. | Delivers **high precision** for terms semantic search can miss. | Needs normalization, aliases, update discipline, and a general lexical fallback. |
| **Candidate retrieval** | **Lexical / BM25 retrieval** | Retrieve through token and term statistics alongside dense search. | Strong for **rare terms, exact phrases, citations, and IDs**; complements semantic retrieval. | Requires a maintained lexical index; tokenisation, stemming, and language choices affect quality; repeated terms can be overweighted. |
| **Candidate retrieval** | **Metadata-filtered retrieval** | Apply access, source, revision, date, locale, audience, and applicability constraints before ranking. | Blocks **unauthorized, obsolete, or inapplicable** evidence before it reaches the answer model. | Incomplete metadata can over-constrain recall; metadata ownership, backfill, and policy maintenance are required. |
| **Candidate retrieval** | **Typed-object retrieval** | Retrieve tables, procedures, warnings, FAQs, entities, or citations as structured records rather than only text chunks. | Preserves **content structure** and improves precision for values, steps, and rules. | Requires reliable schemas, extraction validation, index adapters, and object-type-specific evaluation. |
| **Candidate retrieval** | **Visual-evidence retrieval** | Retrieve rendered pages, figures, or element crops associated with text candidates. | Lets users and models inspect **source layout** without processing an entire document. | Requires stable bounds/provenance, visual ranking, storage controls, and human review for ambiguous interpretations. |
| **Candidate retrieval** | **Graph retrieval** | Traverse approved entity and relationship edges to find connected concepts, sources, or procedures. | Supports **multi-hop questions**, dependencies, comparisons, and relationship-heavy content. | Unverified edges amplify extraction errors; entity resolution, revisions, and evidence-backed links are prerequisites. |

## 3. Hybrid retrieval, ranking, and context assembly

📌 **Definition:** **Candidate retrieval** aims for recall: get the correct evidence into the pool. **Ranking** aims for precision: order that pool so the best evidence reaches the answer model. A reranker cannot recover evidence that candidate retrieval did not find.

```text
Dense candidates ─┐
Lexical candidates┼─> fuse / rerank ─> final evidence ─> bounded prompt
Typed candidates ─┤
Visual candidates ┤
Graph candidates ─┘
```

| Category | Sub-category | Strategy | Advantage | Challenges and limitations |
| --- | --- | --- | --- | --- |
| **Hybrid retrieval** | **Reciprocal-rank fusion (RRF)** | Merge rank lists from multiple lanes without assuming their raw scores are comparable. | Provides a **simple, robust** way to combine semantic and exact retrieval. | RRF combines rankings; it does not assess query–candidate meaning. Candidate depth and weights still require measurement. |
| **Hybrid retrieval** | **Multi-channel quotas** | Allocate candidate counts by query type across dense, lexical, typed, visual, and graph lanes. | Controls **latency and dominance** by a broad retrieval lane. | Bad quotas reduce recall; tune against per-query-class evidence and retain a fallback path. |
| **Hybrid retrieval** | **Maximum marginal relevance (MMR)** | Select candidates that are relevant to the question while reducing redundancy among selected candidates. | Produces a more diverse evidence set when top results repeat the same source or point. | Diversity can discard an important corroborating source; apply after mandatory filters and tune against citation quality. |
| **Ranking** | **Second-stage reranking** | Score each query–candidate pair after broad candidate retrieval, then choose final evidence. | Can improve final ordering and remove irrelevant context when the correct evidence is already present. | Adds latency and cost; must show a measured MRR, nDCG, or citation-quality gain over simpler fusion. |
| **Ranking** | **Late-interaction retrieval** | Preserve token-level query/document interactions instead of collapsing each chunk to one vector. | Can improve fine-grained matching while keeping document representations precomputed. | Requires a specialised index and more storage/compute than one-vector dense retrieval. [ColBERT paper](https://arxiv.org/abs/2004.12832) |
| **Ranking** | **Learned sparse retrieval** | Use learned sparse term expansion rather than only hand-designed lexical weighting. | Bridges exact-term matching and semantic expansion while retaining token-oriented retrieval. | Needs model/index evaluation and may be less transparent than BM25; it is not automatically better for every corpus. |
| **Ranking** | **Evidence-quality-aware ranking** | Consider approval state, confidence, revision, source authority, and content type when ordering evidence. | Prefers **current, reviewed, high-quality** evidence over merely similar text. | Confidence is not truth; low-confidence but important content may need review, not silent suppression. |
| **Context assembly** | **Structure-aware packing** | Keep headings with narrative, headers/units with tables, and warnings with the steps they govern. | Preserves **meaningful context** that fixed-size chunks can sever. | Requires content-type-aware chunk contracts and token-budget logic; large tables/procedures need controlled handling. |
| **Context assembly** | **Parent–child retrieval** | Retrieve a small child chunk for precision, then return its larger parent section for context. | Balances precise matching with sufficient surrounding context. | Parent size can exceed the token budget; parent/child links and deduplication must be stored correctly. |
| **Context assembly** | **Contextual chunks** | Add concise document, section, or source context to a chunk before embedding and indexing it. | Makes locally ambiguous chunks more retrievable and interpretable. | Adds indexing cost and can duplicate text; contextual metadata must be revised when the source changes. |
| **Context assembly** | **Contextual compression** | Extract or summarise only the relevant spans, rows, or claims from retrieved evidence before final prompting. | Reduces irrelevant tokens and can preserve room for multiple sources. | A compressor can omit qualifiers or introduce errors; retain the original evidence and cite it rather than the compression alone. |
| **Context assembly** | **Budgeting and deduplication** | Bound tokens/items while removing near-duplicates and maintaining source diversity. | Controls **cost, latency, and repetition** in the answer prompt. | Heuristics can discard a necessary qualifier; diversity must never override applicability or evidence strength. |
| **Context assembly** | **No-answer / abstention** | Return a clear bounded response when evidence is insufficient. | Safer than a fluent answer based on weak retrieval; tells the user what is missing. | Needs clear UX, thresholds, and a path to supply more context or request source review. |

⚠️ **Warning:** Do not call RRF a reranker. **RRF fuses rank lists**; **reranking scores query–candidate relationships** after candidate retrieval.

## 4. Content preparation and ingestion

```text
Document
  → structural conversion
  → confidence / source-image checks
  → review if needed
  → structural chunks + typed objects
  → versioned indexes
```

- **Parsing and extraction** belong in the offline path because the work is reusable across every query.
- **Chunking** is a content contract, not only a size setting:
  - A table title, headers, units, and rows remain interpretable together.
  - A warning remains attached to the procedure step it qualifies.
  - A source page and element location remain available for verification.

| Category | Sub-category | Strategy | Advantage | Challenges and limitations |
| --- | --- | --- | --- | --- |
| **Document conversion** | **Canonical structural conversion** | Extract layout, headings, tables, OCR, and document structure into a provenance-bearing representation. | Produces **richer source data** than plain-text extraction. | Conversion quality varies with scans and complex layouts; model/runtime resources may be needed; extracted artifacts still need indexing to affect answers. |
| **Document conversion** | **Native-text comparison** | Compare a model-free text extraction with canonical structural conversion for born-digital documents. | Provides a **low-cost fidelity diagnostic** for text-heavy sources. | Does not provide comparable layout or table confidence; it is insufficient as the sole representation for complex documents. |
| **Document conversion** | **Content-addressed caching** | Cache outputs by source hash and parser/configuration fingerprint. | Avoids repeated work and prevents **stale outputs** when a parser or setting changes. | Does not replace revision/supersession policy; retention, reprocessing, and invalidation still need governance. |
| **Page-aware parsing** | **Page profiling and treatment plans** | Detect scan quality, table, procedure, diagram, or multi-column traits before selecting additional work. | Targets expensive processing at the pages that need it and makes routing explainable. | Requires reliable signals and versioned policy; inaccurate profiles can select the wrong treatment. |
| **Chunking** | **Structural / hierarchical chunks** | Chunk by document section while retaining headings and page provenance. | Provides a practical **general-purpose default** for structured content. | Boundary choices still affect recall; evaluate across document types and languages. |
| **Chunking** | **Semantic / recursive chunks** | Split on semantic boundaries or recursive structural delimiters, optionally with overlap. | Can improve narrative coherence when source structure is weak. | There is no universal chunk size or overlap; larger overlap raises index size and duplication and can still separate qualifiers from claims. |
| **Specialist extraction** | **Tables, procedures, warnings, diagrams, charts, formulas, and parts** | Create content-specific objects and validations beyond generic chunks. | Enables **higher-precision retrieval** and content-aware quality checks. | Every specialist needs representative data, schemas, source-image validation, and separate release criteria; a vision model alone is not enough. |

## 5. Quality, provenance, and human review

```text
Conversion result
   |
   +-- confidence and deterministic checks pass --> approved evidence --> index
   |
   `-- low confidence or disagreement ---------> review evidence --> human decision
                                                          |
                                              approve | reject | reprocess
```

| Category | Sub-category | Strategy | Advantage | Challenges and limitations |
| --- | --- | --- | --- | --- |
| **Parsing quality** | **Confidence scoring** | Persist document and page confidence outcomes and route low-confidence results. | Catches likely conversion issues early and supports **unattended batch thresholds**. | Confidence measures parser/model certainty, not real-world correctness; thresholds need calibration by document type. |
| **Human-in-the-loop** | **Review queue and approval gate** | Record review reasons and artifacts, then require approval before publication. | Keeps uncertain content **auditable** and reduces corpus contamination. | Adds operational work and requires reviewer ownership, service levels, and a usable workflow. |
| **Provenance** | **Immutable evidence packages** | Store source identity, conversion output, confidence, page renders/crops, and audit artifacts together. | Supports **reproducibility, reprocessing, audit, and inspection**. | Storage grows over time; retention/access policy and stable viewer links need management. |
| **Provenance** | **Element-level evidence IDs** | Give each claimable element a stable page, bounds, source reference, and approval state. | Enables **claim-level citations** and safe reuse by chunks, typed objects, and graph edges. | Requires a durable schema and migrations; PDF coordinates and printed page labels can be inconsistent. |
| **Reconciliation** | **Deterministic critical-content checks** | Compare high-risk values, units, IDs, and relationships against source image, native text, or another approved result. | More reliable than language-model confidence for catching costly extraction errors. | Needs content-specific rules and review of disagreement; no finite rule set detects every semantic error. |
| **Local VLM assistance** | **Visual escalation** | Inspect only review-triggered pages or crops with a local vision-language model and save an audit result. | Adds **local visual triage** without making parsing a cloud or query-time dependency. | Can be slow in bulk and can misread/hallucinate; it is reviewer evidence, never an automatic authority. |

## 6. Answer generation, UX, and operations

| Category | Sub-category | Strategy | Advantage | Challenges and limitations |
| --- | --- | --- | --- | --- |
| **Answer generation** | **Evidence-constrained synthesis** | Instruct the answer model to compose from retrieved evidence rather than general knowledge. | Reduces unsupported claims and makes **citations possible**. | Faithfulness is not guaranteed; weak retrieval, conflicting sources, and oversized prompts can still cause errors. |
| **Answer generation** | **Provider selection** | Select a permitted answer model based on capability, data boundary, cost, latency, or availability. | Lets a deployment make an explicit trade-off rather than assuming one model fits every use case. | Local document parsing does not automatically mean local answer generation; each model requires independent quality, hardware, and safety evaluation. |
| **User experience** | **Citations, traces, and visual evidence** | Show retrieved evidence, processing traces, and page/figure inspection where useful. | Lets users **verify answers** and lets engineers diagnose retrieval behavior. | Broad page citations can be insufficiently precise; verbose traces can overwhelm users; links must respect permissions. |
| **Governance** | **Run manifests and configuration registry** | Record parser, chunker, index, retrieval, and model settings for each artifact or query run. | Supports **reproducible investigations** and fair configuration comparisons. | Completeness must be enforced; registries introduce schema migration and operational discipline. |
| **Operations** | **Semantic and result caching** | Reuse retrieval results or validated answers for identical or sufficiently similar questions when policy permits. | Reduces repeat latency and cost for common questions. | Similarity can return a stale or insufficiently specific result; cache keys must include source revision, access scope, configuration, and freshness policy. |
| **Operations** | **Conversational memory retrieval** | Retrieve durable user, task, or session context separately from the document corpus. | Supports multi-turn work without re-asking stable preferences or task constraints. | Memory can be stale, sensitive, or wrongly attributed; isolate it from authoritative document evidence and apply retention/access rules. |
| **Evaluation** | **Stage-specific evaluation** | Evaluate conversion, chunking, candidate recall, ranking, citations, faithfulness, latency, and cost separately. | Identifies the **actual failing stage** rather than masking it with prompt changes. | Golden data is costly to create and maintain; it must represent documents, languages, revisions, and difficult content types. |
| **Verification** | **Claim-level answer verification** | Check whether each material answer claim is entailed by, and cites, retrieved evidence before response delivery. | Detects unsupported claims that pass retrieval and generation stages. | Automated verifiers can themselves err; high-risk claims still require deterministic checks or human review. |

## Choosing a defensible generic baseline

📋 **Start with this sequence before adding specialised or agentic features:**

1. **Convert** sources structurally, preserve provenance, cache by source and configuration, and route low-quality conversions to review.
2. **Create structural chunks** plus an exact lexical/identifier lane.
3. **Apply mandatory metadata filters** for access, freshness, revision, and applicability before retrieval ranking.
4. **Fuse dense and lexical candidates** with RRF, then assemble a bounded, citation-first evidence set.
5. **Generate only from evidence** and provide an explicit abstention response.
6. **Measure candidate recall and citation correctness** before adding a reranker, graph, visual specialist, or autonomous agent.

✅ **Verification checklist:**

- [ ] Each indexed item has a **source reference**, a **current revision**, and a defined **approval state**.
- [ ] Retrieval applies **authorization and applicability filters before ranking**.
- [ ] The expected evidence reaches the candidate pool for representative questions before ranking or prompt changes are evaluated.
- [ ] Citations point to **inspectable evidence**, not only a document title.
- [ ] New retrieval lanes demonstrate an improvement on a versioned evaluation set rather than adding unmeasured complexity.

## Advanced research watchlist

⚠️ **This table is deliberately separate from the practical strategy map.**
These approaches are useful to understand and evaluate, but they add model
training, autonomous control flow, or difficult evaluation requirements. They
should not displace a measured lexical+dense baseline, metadata filtering,
provenance, and review controls.

| Research area | Core idea | Potential impact | When to evaluate it | Main caution |
| --- | --- | --- | --- | --- |
| **Self-RAG** | A model learns to decide whether to retrieve, generate, and critique using reflection tokens. | May make retrieval and self-critique adaptive rather than fixed per query. | Evaluate only when a strong baseline has evidence-attribution data and retrieval decisions need to vary by task. | It is a model-training approach, not a drop-in prompt; self-critique must not replace source-grounded evaluation. [Paper](https://arxiv.org/abs/2310.11511) |
| **Corrective RAG (CRAG)** | Evaluate retrieved-document quality, then trigger corrective actions when retrieval appears weak. | Can make the system recover from poor retrieval rather than blindly answer from it. | Evaluate when monitoring shows that the correct evidence is frequently absent or low-ranked despite good indexing. | The evaluator can be wrong; corrective actions increase latency and need a controlled source boundary. [Paper](https://arxiv.org/abs/2401.15884) |
| **RAPTOR-style recursive retrieval** | Cluster and summarise chunks into a tree, then retrieve at multiple abstraction levels. | Can help long-document questions that need both overview and local detail. | Evaluate for books, long reports, or multi-section synthesis where parent–child retrieval is insufficient. | Summaries can omit qualifiers or become stale; retain leaf evidence and do not cite a summary as the sole source. [Paper](https://arxiv.org/abs/2401.18059) |
| **Active retrieval during generation** | Retrieve again while drafting when the next claim or sentence has low confidence. | May improve long-form, knowledge-intensive answers that require changing evidence. | Evaluate for genuinely long answers after ordinary decomposition and iterative retrieval have been measured. | It multiplies latency and can create unstable traces; each retrieved source still needs normal filters and citations. [FLARE paper](https://arxiv.org/abs/2305.06983) |
| **Agentic ReAct-style retrieval** | Interleave reasoning with actions such as search, database lookup, and tool calls. | Supports complex workflows that need planning, observation, and recovery from tool results. | Evaluate for multi-step tasks with explicit tools, not simple factual Q&A. | Planning loops can be expensive and unpredictable; tool permissions, iteration limits, and trace review are mandatory. [Paper](https://arxiv.org/abs/2210.03629) |
| **Knowledge-graph RAG** | Combine retrieval with entity/relation traversal and graph-aware reasoning. | Can support relationship-heavy, multi-hop, and cross-source questions. | Evaluate after stable entities, revision handling, and evidence IDs exist. | Graph edges extracted without verification can amplify errors and outdated relationships. |
| **Retriever and reranker fine-tuning** | Train retrieval models using domain relevance labels, hard negatives, and error cases. | Can improve domain recall and ranking beyond general-purpose embeddings. | Evaluate after collecting a representative, versioned relevance set. | Training on weak labels or a narrow corpus can overfit and hide regressions on new content. |

## Summary

- **Dense retrieval** improves conceptual recall; **lexical retrieval** protects exact-term recall; **RRF** combines their rank lists.
- **Query transformation, parent–child retrieval, contextual chunks, MMR, and contextual compression** extend the baseline when evaluation reveals a specific recall, context, duplication, or token-budget problem.
- **Typed, visual, and graph retrieval** are valuable when the source has structure that generic chunks lose, but each needs evidence, validation, and dedicated evaluation.
- **Confidence, provenance, review, metadata filters, and abstention** are reliability mechanisms, not optional presentation features.
- A reliable advanced RAG system expands only when a measured baseline gap justifies the additional retrieval or processing lane.
