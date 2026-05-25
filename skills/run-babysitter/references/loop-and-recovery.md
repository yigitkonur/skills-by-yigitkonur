# The Loop, the State Machine, and Recovery

This file governs how the babysitter behaves *as a long-running, resumable
process*: its named states, its budgets, how it fails gracefully, and how to run it
continuously. The principles are distilled from durable-execution systems
(Temporal, Step Functions, XState, Celery/Sidekiq, the Saga pattern) but kept light
enough to live in markdown files — no engine, no infrastructure.

## One invocation = one tick

The skill defines exactly one cycle. It does **not** loop internally or spawn its
own infinite schedule. Looping is the caller's choice:

| To loop… | Do this |
|---|---|
| Interactively, continuously | `/loop /run-babysitter` — Claude Code re-invokes each tick. |
| On a schedule | A cron / scheduled task that runs `/run-babysitter` (e.g. hourly, daily). |
| Self-paced (dynamic) | The runtime's wakeup scheduler, with the same `/run-babysitter` prompt re-fired. |
| Once | Just `/run-babysitter`. |

Because all state is in `.agent-docs/`, every tick is independent and idempotent.
Re-running after a crash, an interrupt, or a week away always resumes cleanly from
`STATE.md` (or, if that is lost, from `RUNLOG.md`).

## The state machine

`STATE.md` carries exactly one `Lifecycle state` from this bounded set. Read it at
the start of a cycle; write the next state atomically before exiting.

```
INITIALIZING ─► IDLE ─► TRIAGING ─► DECIDING ─► DRAFTING ─► FILING ─► REFLECTING ─► IDLE
                 ▲                                   │            │
                 │                                   ▼            ▼
                 └──────────────── COOLDOWN ◄──── BLOCKED    AWAITING_HUMAN
```

| State | Meaning | Normal exit |
|---|---|---|
| `INITIALIZING` | INIT mode scaffolding `.agent-docs/` | → `IDLE` once seeded |
| `IDLE` | Between cycles; nothing in flight | → `TRIAGING` on next tick |
| `TRIAGING` | Reading world + memory, ranking tiers | → `DECIDING` |
| `DECIDING` | Choosing the one next rung | → `DRAFTING` |
| `DRAFTING` | Writing the plan + issue body | → `FILING` |
| `FILING` | Dedup gate + `gh issue create` | → `REFLECTING` |
| `REFLECTING` | Persisting memory; periodic point-of-view synthesis | → `IDLE` |
| `COOLDOWN` | Deliberately resting (e.g. budget hit, nothing worthy) | → `IDLE` next tick |
| `BLOCKED` | A failure halted progress; details in `BLOCKED.md` | → `IDLE` after the block clears |
| `AWAITING_HUMAN` | Parked on a question; details in `AWAITING_HUMAN.md` | → `IDLE` after a human replies |

No state is implicit. If you cannot name the current state, you have lost the
thread — re-read `RUNLOG.md` and rebuild `STATE.md`.

## Budget guards

| Guard | Limit | On breach |
|---|---|---|
| New issues per cycle | 1 | Queue the rest on `roadmap.md`; → `COOLDOWN` |
| Tool calls per cycle | ~12 | Persist memory, report what you reached, exit |
| Cycles with the same task `in_progress` | 3 | → `AWAITING_HUMAN` |
| Consecutive `gh`/network failures | 5 (with backoff) | Classify, → `BLOCKED` |

Budgets exist because the two classic autonomous-loop failure modes are *runaway
spawning* (file 20 issues in seconds) and *churning without progress* (retry the
same failure forever). Both are prevented by caps.

## Failure handling — classify, bound, dead-letter

On any failure, classify it before reacting (the discipline every durable queue
enforces). Append the classification to `failures.md`.

| Class | Examples | Response |
|---|---|---|
| **transient** | network blip, 403 secondary-rate-limit, timeout | Exponential backoff (e.g. 5s, 15s, 60s…), **max 5** retries. Then treat as a block. |
| **permanent** | auth failure, repo not found, issues disabled, malformed input | Do not retry. Degrade (draft-only) and → `BLOCKED` immediately. |
| **human-needed** | a judgment call ("close this as wontfix?"), ambiguous scope | → `AWAITING_HUMAN`. |

### BLOCKED.md (the dead-letter file)

When you give up on an action, write `.agent-docs/BLOCKED.md` with what failed, the
classification, and what would unblock it. This is the bot's dead-letter queue — it
makes stuck work *visible* instead of silently retried forever. Surface it in the
next cycle's triage and in the dashboard.

```markdown
# Blocked — 2026-05-23T19:00Z
- **Action:** file issue "resilience: retry remote-MCP fetch"
- **Error:** gh auth token expired (permanent)
- **Unblock:** run `gh auth login`; the draft is saved at issues/drafts/resilience-retry-remote-mcp.md
```

### AWAITING_HUMAN.md (durable pause)

This is the file-based equivalent of Temporal's `waitForTaskToken` / Prefect's
`pause_flow_run`: park a question durably and exit. On the next cycle, check this
file first; if a human has appended an answer, consume it, delete the file,
transition out of `AWAITING_HUMAN`, and proceed.

```markdown
# Awaiting human — 2026-05-23T19:00Z
**Question:** Issue #31 has been open 90 days with no repro. Close as stale, or keep?
**Context:** No activity since cycle 2; not on the critical path.
**Options:** keep | close-as-stale | needs-investigation

<!-- Human: write your answer on the line below and save. -->
ANSWER:
```

## Idempotency and determinism on resume

- **Idempotency:** the `issues/filed/<slug>.md` ledger + the dedup gate guarantee an
  issue is opened at most once, no matter how many times a cycle re-runs (the
  Outbox/Inbox pattern in markdown form). Write the ledger entry as part of filing.
- **Atomic writes:** projections (`STATE.md`, `POINT-OF-VIEW.md`) are written
  tmp→rename so a crash mid-write never corrupts them (see
  `references/agent-docs-layout.md`).
- **Don't re-derive on replay:** within a resumed cycle, trust the snapshot you
  already wrote rather than re-querying and re-triaging from scratch — re-deriving
  live can produce a *different* decision and duplicate work. Fresh `gh`/`git`
  reads belong only at the start of a *new* cycle's ORIENT.

## Recovery moves

- **`STATE.md` missing or corrupt** → rebuild it by reading `RUNLOG.md` (the
  append-only truth), then continue.
- **Unsure whether an issue was filed** → check `issues/filed/` and `gh issue list
  --label babysitter`; the ledger is authoritative.
- **Stuck in `BLOCKED`** → read `BLOCKED.md`, fix the named cause, clear it, → `IDLE`.
- **Stuck in `AWAITING_HUMAN`** with no answer → re-surface the question, stay
  parked; do not guess on a human-needed decision.
