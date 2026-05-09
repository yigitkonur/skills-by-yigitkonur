# design-thinking — 8 questions before any surface, schema, or code

Before picking a surface, before drawing a single schema, before writing the first tool description, answer 8 questions about the workload. Surface selection, schema shape, error model, observability, and lifecycle policy all fall out of the answers. Skip these and you'll spend the rest of the design fighting decisions you should have made up front.

## The 8 questions in order

Walk them top-to-bottom. Don't reorder. Don't skip. The output is a one-paragraph workload description plus the 8 answers — that's the input to `decide-surface.md`, `descriptions-as-prompts.md`, and the surface-specific architect-new files.

### 1. Workload type

**What it asks.** What kind of work does the tool do? Read-only lookup? State-mutating write? Long-running batch? Streaming subscription? Multi-step orchestration with intermediate validation?

**Why it matters.** The workload type determines retry semantics, idempotency requirements, output shape, and whether the tool needs an iterative pattern. A read-only tool with idempotent semantics is trivial to retry; a multi-step orchestration with side effects is not.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| Read-only lookup / search | Free retry, free caching, simple envelope, low blast radius. |
| Single mutation (create / update / delete) | Idempotency keys, exit-code or `isError` taxonomy, dry-run flag. |
| Long-running batch / job | Job-ID pattern, status polling or streaming progress, cancellation primitive. |
| Streaming subscription | JSONL on CLI, structured-content streaming on MCP, heartbeats, reconnect strategy. |
| Multi-step orchestration | Iterative loop pattern (`phase` / `progress` / `validation_errors` / `next_action` / `state_token`); see `iterative-loops.md`. |

### 2. Audience

**What it asks.** Who calls this tool? A developer typing a command? An agent picking from `tools/list`? Both?

**Why it matters.** A developer-typed CLI can use clever flags and rely on `--help`; an agent-typed tool must self-describe inside the description. The same tool can serve both audiences but must be tested against both.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| Developer-typed only | Conventional CLI flags, terse `--help`, no JSON output required (but useful). |
| Agent-typed only | Description-as-prompt is the entire interface; no flag discovery happens. |
| Both | Description-as-prompt budget for the agent path; clean `--help` for humans; surfaces match. |

### 3. Statefulness

**What it asks.** Does any tool call need to remember state from a previous call within the same session? Across sessions?

**Why it matters.** Stateless calls are free to scale and simple to retry. Stateful calls need session management, persistence, and a story for cleanup. CLI rarely owns server-side state; MCP often does.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| Stateless per-call | Default to CLI; if MCP, ephemeral per-request sessions (see HubSpot exemplar). |
| Session-scoped | MCP with session lifecycle, or CLI with explicit `state_token` returned from one command and consumed by the next. |
| Cross-session persistent | Server-side database; MCP with auth-scoped storage; CLI must read/write a state file the user can see. |

### 4. Auth model

**What it asks.** How does the tool know who the caller is, and what they're allowed to do?

**Why it matters.** Auth fundamentally changes the surface. Local env credentials fit CLI cleanly; per-user OAuth fits MCP cleanly. Mismatch produces brittle auth plumbing on the wrong surface.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| None / single-user local | CLI with no auth; or MCP with no auth (rare; e.g., Shopify Storefront). |
| Static API key in env var | CLI default; MCP supports it but doesn't reward it. |
| Per-user OAuth (2.0 or 2.1 + PKCE) | MCP. CLI here would build per-user credential plumbing the protocol already provides. |
| OAuth + step-up consent / approvals | MCP with prompt-gates; CLI cannot model approval cleanly. |
| Multi-tenant with permission intersection | MCP with per-call permission check (see HubSpot pattern); CLI here is wrong. |

### 5. Scale

**What it asks.** How many calls per minute? How many concurrent users? How many tenants?

**Why it matters.** Scale changes the transport choice (stdio vs. Streamable HTTP), the rate-limit story, the cost model, and the deployment target.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| Single user / single machine | stdio MCP or local CLI; no rate-limit story needed beyond upstream API limits. |
| Single team (≤ 50 people) | HTTP MCP; CLI distributable via package manager. |
| Multi-tenant SaaS | Streamable HTTP MCP only; per-tenant URLs or query params; horizontal scaling. |
| Public marketplace | MCP with DCR; CLI with public package manager. |

### 6. Error semantics

**What it asks.** When something goes wrong, what does the agent need to do? Fail fast and surface to a human? Retry with backoff? Fall back to an alternate tool? Repair input and resubmit?

**Why it matters.** This shapes the error envelope, the retry-safe vs. fail-fast taxonomy, and whether the tool needs an iterative repair loop. See `error-strategy.md`.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| Fail-fast, escalate | Permanent error class; agent stops; no retry guidance. |
| Retry-with-backoff | Transient error class; `retry_after_ms` or `retry_after` in envelope. |
| Fallback to alternate tool | Error message names the alternate explicitly. |
| Iterative repair | Validation errors with `field`, `problem`, `suggested_fix`; `next_action` field. |

### 7. Observability needs

**What it asks.** What does the operator need to see in production? Plain logs? Structured events? Span tracing? Per-call audit trail?

**Why it matters.** Determines whether the tool ships with a logging schema, an audit log, or just stderr. Audit-grade observability adds non-trivial implementation cost; declare it up front so it doesn't get retrofitted.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| Logs only | stderr (CLI) or server log (MCP); no structured envelope required. |
| Structured events | JSONL events on stdout (CLI) or progress notifications (MCP). |
| Span tracing | OpenTelemetry context propagation; trace ID in every response. |
| Per-call audit | Append-only event log; every call logged with caller identity; required for governed flows. |

### 8. Lifecycle

**What it asks.** Is this tool ephemeral (one-off task), long-lived (production for years), or pinned to a specific version of an upstream API?

**Why it matters.** Lifecycle choice determines schema versioning rigor, deprecation strategy, and how aggressively the implementation can change the contract.

**Possible answers and what each implies:**

| Answer | Implies |
|---|---|
| Ephemeral / experiment | No `schema_version`; expect to break callers; document expiry. |
| Long-lived | Required `schema_version`; deprecation path documented; backwards-compatible additions only. |
| Pinned to upstream version | Version-suffixed tool name (`build-mcp-server-sdk-v1` vs. `-v2`); explicit migration path. |

## Worked example: a `create-issue` tool

Walking the questions for a hypothetical "create an issue in our project tracker."

| # | Question | Answer | Implication |
|---|---|---|---|
| 1 | Workload type | Single mutation (create) | Idempotency key required; dry-run flag useful. |
| 2 | Audience | Both — developer-typed via CLI, agent-typed via MCP | Two surfaces sharing one handler; description and `--help` both written for the agent. |
| 3 | Statefulness | Stateless per-call | No session lifecycle; idempotency from key, not server state. |
| 4 | Auth model | Per-user OAuth (project tracker is multi-tenant SaaS) | MCP is the natural surface; CLI builds an OAuth wrapper. |
| 5 | Scale | Multi-tenant SaaS | Streamable HTTP MCP; CLI uses a refresh token from the same OAuth app. |
| 6 | Error semantics | Mostly fail-fast (validation), but transient on upstream API | Validation errors are permanent (agent repairs input); upstream 5xx is transient (retry with backoff). |
| 7 | Observability | Per-call audit (issues are accountable) | Append-only event log; caller identity in every record. |
| 8 | Lifecycle | Long-lived | Required `schema_version: "1"`; new fields additive only. |

The 8 answers tell you:
- Surface: MCP (auth + multi-tenant); optional CLI for power users.
- Verb: `create-issue` with `idempotency_key` parameter; alternative `apply-issue` if upsert semantics are wanted.
- Schema: flat (≤ 6 params), required `title`, optional `body`, `labels`, `assignee`, `idempotency_key`.
- Errors: validation = permanent, upstream-503 = transient with `retry_after`, conflict = permanent with `existing_issue_id`.
- Output: `{ ok, result: { issue_id, url }, schema_version }` on success; `{ ok: false, error: { class, code, message, retryable, suggestion } }` on failure.
- Observability: append-only audit; OAuth app + user ID + tenant in every record.

That's the architecture sketch — derived from the 8 answers, not invented from intuition.

## The "questions the agent should not ask first" anti-list

Skipping the 8 questions and starting with these wastes the design pass:

- **"Should this be a CLI or an MCP server?"** — Surface comes after the workload. Ask question 1 first; the surface choice falls out by question 4.
- **"What SDK should we use?"** — Implementation detail; comes after architecture, not before. Pick the SDK from `../mcp/architect-new.md` or `../cli/code-templates.md` once the surface and the workload are fixed.
- **"What's the schema?"** — Schema follows from the verb and workload type, which come from questions 1 and 6. Drafting a schema before the workload is decided produces the wrong schema.
- **"Should it have streaming?"** — Workload type (question 1) decides. Adding streaming to a non-streaming workload is an anti-pattern (see `agent-cognitive-load.md`).
- **"What error codes should we use?"** — Error taxonomy follows from question 6. Picking codes first leads to overlapping or under-specified categories. See `error-strategy.md`.
- **"Should we add idempotency?"** — Question 1 + question 6 already answered this. Mutation + retry-safe = yes; read-only = unnecessary; permanent-on-failure = no.
- **"Where should we deploy it?"** — Question 5 + question 4 fix the deployment shape. Picking the platform first locks the surface choice prematurely.

## Output format: one-paragraph workload sketch

After answering all 8 questions, produce a single paragraph the rest of the design pass can route on:

```
This tool [creates / reads / updates / orchestrates] [resource]. It is called by
[audience] under [auth model], runs at [scale], and is [stateless / session-scoped /
persistent]. Errors are mostly [permanent / transient / iterative]. Observability
is [logs / events / audit]. Lifecycle is [ephemeral / long-lived / pinned].
```

Example:

> This tool creates issues in a multi-tenant project tracker. It is called by both
> developers (CLI) and agents (MCP) under per-user OAuth, runs at multi-tenant scale,
> and is stateless. Errors are mostly permanent (validation), with transient classes
> for upstream 5xx. Observability is per-call audit. Lifecycle is long-lived.

This paragraph plus the 8 answers is what `decide-surface.md`, `descriptions-as-prompts.md`, `output-contracts.md`, and `error-strategy.md` route on.

## Cross-references

- After the 8 answers, route to `decide-surface.md` for the surface decision.
- For the description and naming layer, read `descriptions-as-prompts.md`.
- For the output and error contracts, read `output-contracts.md` and `error-strategy.md`.
- For idempotency and verb semantics, read `idempotency-and-retries.md`.
- For multi-step workflows, read `iterative-loops.md`.
- For surface-specific architect-new files, route to `../cli/architect-new.md` or `../mcp/architect-new.md`.
