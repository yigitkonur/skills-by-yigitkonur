# Design Rationale — Why This Skill Is Shaped This Way

This skill was synthesized from a survey of ~54 systems across four families. This
file records what was taken from where, so a future reviser understands the *why*
behind each decision and does not undo a load-bearing choice by accident.

## The four corpora surveyed

1. **15 Claude skills** — `long-task-coordinator`, `autonomous-agent-harness`,
   `self-improving-agent`, `self-improvement`, `github-ops`, `planning-with-files`,
   `autonomous-loops`, `continuous-agent-loop`, `verification-loop`, `canary-watch`,
   `production-audit`, `skill-stocktake`, `audit-completion`, plus local
   `run-repo-cleanup` and `run-github-scout` for house style.
2. **14 autonomous-agent frameworks** — BabyAGI, AutoGPT, LangGraph, CrewAI,
   AutoGen/Magentic-One, OpenHands, SWE-agent, Aider, GPT-Engineer, MetaGPT,
   Reflexion, Voyager, Generative Agents, Claude Code (+ the Manus/OpenClaw
   markdown-memory convergence).
3. **11 BPM / durable-execution systems** — Temporal, AWS Step Functions,
   Camunda/Zeebe, Airflow, Prefect, Dagster, n8n, the Saga pattern, XState, the
   Transactional Outbox + Idempotency-Key pattern, Celery/Sidekiq.
4. **14 maintainer / triage bots** — Renovate, Dependabot, actions/stale,
   probot/no-response, Sweep, Mergify, CodeRabbit, all-contributors, Sourcegraph
   Batch Changes, VSCode triage actions, and AI-maintainer scripts; plus GitHub
   issue-hygiene practice.

## What was inherited, and from where

| Design element here | Inherited from | Why |
|---|---|---|
| `ORIENT→RECALL→TRIAGE→DECIDE→ACT→REMEMBER` cycle | `long-task-coordinator`'s READ→RECOVER→DECIDE→PERSIST→REPORT; Generative Agents' perceive→retrieve→plan→act→reflect | Cleanest articulation of a memory-bookended loop. |
| Outer (invocation) vs inner (cycle) split | Magentic-One Task Ledger vs Progress Ledger | `STATE.md` persists across runs; scratchpad is per-run. |
| `RUNLOG.md` append-only = truth; `STATE.md` = projection | Temporal Event History, Zeebe journal, event sourcing | A crash never corrupts truth; state is rebuildable. |
| Markdown memory in `.agent-docs/` (not a vector DB) | Claude Code / Manus / OpenClaw convergence | At O(10–100) facts, files are git-versioned, grep-able, human-editable; vector DBs are overkill. |
| `POINT-OF-VIEW.md` refined by periodic reflection | Generative Agents (importance-triggered reflection) | This is how the steward earns "has a point of view." |
| `failures.md` episodic buffer | Reflexion (verbal self-reflection in `mem`) | Remember what failed so it isn't retried. |
| `roadmap.md` gradual curriculum ("Bulgaria→Romania→Vienna") | Voyager automatic curriculum (bottom-up difficulty) | Operationalizes the brief's gradual-expansion philosophy. |
| `issues/filed/<slug>.md` idempotency ledger | Transactional Outbox + Idempotency-Key / Inbox | "Never open the same issue twice" as an at-most-once *effect*. |
| Dedup gate: `gh issue list --state all --search`, bail on failure | Renovate Dependency Dashboard (and its #12131 duplicate-cascade bug) | The single most important anti-duplicate control. |
| One dashboard issue edited in place | Renovate Dependency Dashboard | Human-facing observability of the bot, without comment spam. |
| `--body-file`, AC-first, evidence-backed issue bodies | probot/architect templates; PaulDuvall AI-dev-patterns | Avoids shell-quoting bugs; produces actionable, non-noisy issues. |
| ≤1 issue/cycle, budgets, never auto-close | Renovate rate limits; the "stale-bot considered harmful" consensus | Anti-noise; issues are a knowledge base, not an action queue. |
| Named state machine + durable pause file | XState/Prefect/Step Functions states; `waitForTaskToken` | Resumability and human-in-the-loop without an engine. |
| Failure classes + bounded retry + dead-letter | Celery/Sidekiq + Saga | Graceful failure (which is also the skill's own hardening scope). |
| Phases, "Think first", gates, red-flags, scripts+`.md` pairing | `run-repo-cleanup`, `run-github-scout` | Repo-native house style. |

## What was explicitly rejected, and why

| Rejected | Seen in | Why not here |
|---|---|---|
| Vector-DB memory | Voyager, Generative Agents, BabyAGI, AutoGPT | Infrastructure + a new failure mode for a O(10–100)-fact agent. Markdown suffices. |
| Unbounded task spawning | BabyAGI `task_creation_agent`, early AutoGPT | Runaway loops. Capped at 1 issue/cycle with a roadmap queue. |
| Assuming the framework resumes/coordinates for you | LangGraph, CrewAI `@persist` (no auto-resume, no dedup) | We own resume (read `STATE.md`) and dedup (ledger + search) explicitly. |
| Auto-closing stale issues | actions/stale defaults | Hides information; widely considered harmful. Never close. |
| Inline issue bodies, create-before-search | common bot bugs | Quoting corruption; duplicate cascades. |
| SKILL.md bloat with inline templates | `autonomous-loops` (610 lines), `self-improving-agent` (408) | Templates/schemas live in `references/`; SKILL.md stays the decision layer. |
| Editing code / opening PRs autonomously | Sweep, AI-maintainer experiments | Out of scope by the user's mandate: this steward thinks and files, never executes. |

## The user's mandate (the constraints that overrode defaults)

- **Plan + always file issues, fully autonomous, no code edits.** → The MAY/MAY-NOT
  contract; `disable-model-invocation: true` so it only runs when explicitly invoked.
- **Memory in `.agent-docs/`, committed, except `scratchpad/` git-ignored, used to
  force step-by-step thinking.** → The directory layout and the scratchpad-first
  discipline in RECALL.
- **Name `run-babysitter`; init vs enhance modes.** → The mode-selection gate.
- **Generic mental model that works for any repo.** → No project coupling; the skill
  baselines whatever repo it is invoked in.

## If you revise this skill

Keep the three commitments intact (memory before action; never the same issue
twice; smallest meaningful step). They are the load-bearing walls. Everything else
— the exact phases, the label names, the reflection cadence — can be tuned against
real run feedback (see how a real cycle behaves, then adjust).
