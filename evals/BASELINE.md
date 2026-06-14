# Evaluation baseline

Date: June 14, 2026

Dataset: `buildathon-ps02-golden-v1`

Configuration:

- Answer model: `gpt-5-mini`
- Embedding model: `text-embedding-3-small`
- Embedding dimensions: 1,536
- Retrieval limit: 8
- Minimum cosine similarity: 0.35
- Retrieval: 85% vector similarity + 15% PostgreSQL full-text rank

Latest 45-case results:

| Metric | Result |
|---|---:|
| Grounded score | 97.78% |
| Answer accuracy | 97.06% |
| Citation validity | 100% |
| Refusal precision | 100% |
| ACL leaks | 0 |
| Median latency | 3.344 seconds |
| p95 latency | 5.035 seconds |

The cases cover direct and paraphrased factual questions, unsupported questions,
personal-scope denial, cross-channel team denial, and cross-workspace tenant
denial. The single expected-term miss was semantically correct: the answer used
"VP of Sales" while the fixture expected alternate wording.

The evaluator exits non-zero below an 80% grounded score or on any ACL leak.

## Scalability smoke

`uv run slack-kb-scale-smoke` inserts 60 isolated team documents with real
1,536-dimensional pgvector values, executes 20 ACL-filtered searches, verifies
the exact document for every query, and removes the synthetic workspace.

| Metric | Result |
|---|---:|
| Documents | 60 |
| Queries | 20 |
| Retrieval accuracy | 100% |
| Ingest time | 0.235 seconds |
| Query p50 | 0.0066 seconds |
| Query p95 | 0.0073 seconds |

These are synthetic buildathon fixtures, not a substitute for evaluation on a
real organisation's documents and query distribution.
