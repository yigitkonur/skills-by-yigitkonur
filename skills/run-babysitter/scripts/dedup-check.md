# dedup-check.sh

The mandatory "never open the same issue twice" gate for phase ⑤ ACT. Run it
immediately before any `gh issue create`.

## Usage

```bash
bash {baseDir}/scripts/dedup-check.sh "<issue title>" [agent_docs_dir]
```

- `<issue title>` — the proposed issue title (quote it).
- `agent_docs_dir` (optional) — defaults to `.agent-docs`.

## Verdicts (read stdout)

| Output | Meaning | What to do |
|---|---|---|
| `CLEAR` | No local ledger entry and no matching open/closed remote issue | Proceed to `gh issue create`. |
| `DUPLICATE <ref>` | Already filed (ledger path) or already exists (issue URL) | Do **not** create. Deepen the existing issue instead. |
| `BAIL <reason>` | `gh` missing/unauthenticated, issues disabled, or the search itself errored | **Stop.** Never create on a failed search. Degrade to draft-only and record the block. |

Exit codes: `CLEAR=0`, `DUPLICATE=10`, `BAIL=20`.

## How it decides

1. **Local ledger** — checks `<agent_docs>/issues/filed/<slug>.md`, where `<slug>`
   is the normalized title (a deterministic idempotency key). If present, we filed
   this before.
2. **Remote search** — `gh issue list --state all --search "<kw> OR <kw>"` over the
   title's significant keywords. `--state all` catches closed duplicates too.
3. **Fail-safe** — any error in the search produces `BAIL`, never `CLEAR`. This is
   the single most important rule: a failed lookup must never be read as "no
   duplicates exist."
