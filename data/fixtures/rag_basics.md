# Evidence-first RAG

Retrieval-augmented generation selects relevant, permitted source evidence before an answer is generated.
Answers should include inspectable citations, and the system should abstain when approved evidence is insufficient.

# Retrieval lanes

Lexical retrieval protects exact identifiers and names. Dense retrieval helps with paraphrased conceptual questions.
Hybrid retrieval combines candidate lists. Vectorless hierarchical retrieval navigates document structure without
requiring chunk-vector similarity.

# Operational controls

Apply access, freshness, revision, and applicability filters before ranking. Record pipeline versions, component
versions, index revisions, and token use in every run manifest.
