# Golden evaluation baseline

Date: June 13, 2026

Dataset: `buildathon-ps02-golden-v1`

Configuration:

- Answer model: `gpt-5-mini`
- Embedding model: `text-embedding-3-small`
- Embedding dimensions: 1,536
- Retrieval limit: 8
- Minimum cosine similarity: 0.35
- Retrieval: 85% vector similarity + 15% PostgreSQL full-text rank

Results:

| Metric | Result |
|---|---:|
| Cases | 45 |
| Grounded score | 100% |
| Answer accuracy | 100% |
| Citation validity | 100% |
| Refusal precision | 100% |
| ACL leaks | 0 |
| Median latency | 2.529 seconds |
| p95 latency | 3.899 seconds |

The cases cover direct and paraphrased factual questions, unsupported questions,
personal-scope denial, cross-channel team denial, and cross-workspace tenant
denial. These are synthetic buildathon fixtures, not a substitute for evaluation
on a real organisation's documents and query distribution.

The first run at a 0.42 similarity threshold scored 91.11%. Three valid questions
had correct-source similarities between 0.366 and 0.404. Lowering the threshold
to 0.35 produced full recall while the grounded generation gate retained 100%
refusal precision and zero ACL leaks.
