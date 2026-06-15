# Two-Minute Demo Script

## 0:00-0:15 - Problem

"Company knowledge is scattered across documents and Slack threads. Employees
waste time searching or interrupting colleagues. This bot turns Slack into a
permission-aware, cited knowledge layer."

## 0:15-0:35 - Ingest

In `#engineering`, attach a short PDF or use:

```text
@Knowledge Base add team Project Orion uses Python 3.12 and deploys in Singapore.
```

Show the indexed document ID.

## 0:35-0:55 - Grounded answer

```text
@Knowledge Base ask Which Python version does Project Orion use?
```

Show the concise answer and source citation.

## 0:55-1:10 - Multi-turn

Reply in the bot thread:

```text
And where is it deployed?
```

Show that the thread context is retained.

## 1:10-1:25 - Refusal

```text
@Knowledge Base ask What is our office Wi-Fi password?
```

Show the explicit insufficient-evidence response.

## 1:25-1:40 - Permission isolation

Ask the Orion question from another channel or user. Show that the team-only
document is not retrieved.

## 1:40-2:00 - Proof and architecture

Show `evals/BASELINE.md`:

- 45 cases
- 100% grounded score
- 100% citation validity
- 100% refusal precision
- zero ACL leaks
- 6.998-second p95 latency
- 60-document scale smoke with 100% exact retrieval

Close with: "Authorization happens before the LLM, and every answer must survive
an evidence and citation gate."
