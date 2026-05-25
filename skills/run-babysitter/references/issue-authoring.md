# Issue Authoring — Dedup, Template, Labels, Dashboard

This file governs phase ⑤ ACT: how to never open the same issue twice, how to write
an issue that reads like a senior engineer authored it, and how to keep the tracker
clean. Every pattern here is drawn from production maintainer bots (Renovate,
Dependabot, probot) and the idempotency discipline of durable-execution systems.

## The dedup gate (mandatory, never skipped)

Opening the same issue twice is the cardinal sin of an autonomous bot (it is
literally how Renovate's worst-known bug manifested: a failed lookup fell through to
"create", spawning a duplicate every hour). The gate has three checks, and a hard
rule: **a failed search means stop, never create.**

`scripts/dedup-check.sh` runs all three:

1. **Local ledger** — does `.agent-docs/issues/filed/<slug>.md` already exist? If
   yes → `DUPLICATE` (we filed this before). The slug is the normalized title, so
   the same idea maps to the same file deterministically (an idempotency key).
2. **Open + closed remote search** — `gh issue list --state all --search "<kw> OR
   <kw>"`. `--state all` is deliberate: a *closed* issue on the same topic still
   means "do not re-file." If it returns matches → `DUPLICATE <url>`.
3. **Fail-safe** — if `gh` errors (network, auth, rate limit, issues disabled), the
   script prints `BAIL <reason>` and exits non-zero. **You must stop.** Never
   interpret a failed search as "no duplicates."

```bash
bash {baseDir}/scripts/dedup-check.sh "observability: structured logs for install flow" .agent-docs
# → CLEAR              proceed to create
# → DUPLICATE #45 …    deepen the existing issue instead
# → BAIL gh-auth       stop; degrade to draft-only; record the block
```

If you ever run the check by hand, the core query is:

```bash
gh issue list --state all --search "retry OR backoff OR resilience" \
  --json number,title,url,state --limit 10
```

## The issue body template

Always write the body to a file and pass `--body-file` — never inline `--body`
(multi-line bodies with backticks and quotes reliably break shell quoting). Lead
with acceptance criteria; back every claim with evidence.

```markdown
## Problem
<one or two sentences: the fragility, in plain terms>

## Evidence
<a real signal — commit SHA, log line, or file:line. Never a guess.>
```
<!-- e.g. -->
```
src/Install/InstallService.swift:212 — network fetch has no timeout;
introduced in commit a1b2c3d. A hung endpoint blocks the install flow indefinitely.
```

```markdown
## Proposed approach
<the smallest change that resolves it; note alternatives considered if relevant.
Link to .agent-docs/plans/<topic>.md if a fuller plan exists.>

## Acceptance criteria
- [ ] <observable, binary-testable condition>
- [ ] <graceful-failure condition, e.g. "times out after 30s with a logged error">
- [ ] <coverage, e.g. "a test exercises the timeout path">

## Area
<component / subsystem>

## Priority / effort
P2 (resilience) · effort: S

## Dependencies
<issue numbers or external blockers, or "none">

---
*Filed by `run-babysitter` (cycle N). Reasoning: `.agent-docs/memory/RUNLOG.md`.*
```

The footer makes the bot's work transparent and traceable — humans can always find
the reasoning behind any issue.

## Filing

```bash
gh issue create \
  --title "observability: structured logs for the install flow" \
  --body-file /tmp/babysitter-issue.md \
  --label "babysitter,observability,P2"
```

Immediately after a successful create, write `issues/filed/<slug>.md` with the
returned URL (the ledger entry — this closes the idempotency loop so the next
cycle's dedup check sees it).

## Labels

- **Marker label `babysitter`** — always applied, so all bot-authored issues are
  filterable (`gh issue list --label babysitter`). Create it once if missing:

  ```bash
  gh label list --json name --jq '.[].name' | grep -qx babysitter \
    || gh label create babysitter --color BFD4F2 --description "Filed by the run-babysitter steward"
  ```

- **Type + priority** — prefer the repo's existing labels (check `gh label list`
  first; e.g. reuse `bug`, `enhancement`). Only introduce `hardening` /
  `reliability` / `observability` / `P0`–`P3` if the repo has no equivalent.

## The maintenance dashboard issue (Renovate pattern)

Maintain **one** persistent issue titled `[babysitter] maintenance dashboard`,
updated **in place** (edit the body, never comment-spam). It is the human's single
window into the steward: current point of view, the roadmap with links to filed
issues, and the last few cycles. This is the bot's own observability story.

```bash
# find-or-create, then edit body in place (never a new comment each run)
num=$(gh issue list --state open --search 'in:title "[babysitter] maintenance dashboard"' \
        --json number --jq '.[0].number // empty')
if [ -n "$num" ]; then
  gh issue edit "$num" --body-file /tmp/babysitter-dashboard.md
else
  gh issue create --title "[babysitter] maintenance dashboard" \
    --body-file /tmp/babysitter-dashboard.md --label "babysitter"
fi
```

Dashboard body = a mirror of `roadmap.md` (with issue links) + the current
`POINT-OF-VIEW.md` summary + the last 3 `RUNLOG.md` entries.

## Anti-patterns (do not do these)

| Anti-pattern | Why it's harmful | Instead |
|---|---|---|
| Create without dedup, or create on a failed search | Duplicate cascade (the Renovate bug) | Gate every create; bail on search failure |
| Inline `--body "...long..."` | Shell-quoting corruption | Always `--body-file` |
| Drive-by issues: "make it better", "add tests" | Dilutes signal; trains humans to ignore the bot | Specific title + acceptance criteria + evidence |
| Auto-closing quiet issues | Issues are a knowledge base; closing hides info | Never close; surface in triage |
| Filing N issues in one run | Notification spam | One per cycle; roadmap the rest |
| Filing without a marker label | Bot work becomes unfilterable | Always label `babysitter` |

## Degraded mode (gh unavailable / issues disabled / no remote)

Do not lose work. Write the full body to `.agent-docs/issues/drafts/<slug>.md`,
record the block in `failures.md` and `STATE.md`, and surface it to the human. On a
later cycle when `gh` works, drafts can be promoted to real issues (re-run the
dedup gate first).
