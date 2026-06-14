# Evaluation

`golden_dataset.json` contains 45 cases covering:

- direct factual retrieval
- paraphrased questions
- unsupported questions
- personal-scope denial
- cross-channel team-scope denial
- cross-workspace tenant denial

Run the complete suite:

```powershell
uv run slack-kb-eval
```

Run a cheap smoke subset:

```powershell
uv run slack-kb-eval --limit 8 --output evals/smoke-report.json
```

The command exits non-zero when grounded score is below 80% or any ACL case
leaks. Reports are ignored by Git except for the dataset and this guide.

Run the database scalability smoke:

```powershell
uv run slack-kb-scale-smoke
```

It inserts 60 isolated team documents with real 1,536-dimensional pgvector
embeddings, runs 20 ACL-filtered retrievals, asserts exact-document recall and a
sub-10-second p95, then removes the synthetic tenant.
