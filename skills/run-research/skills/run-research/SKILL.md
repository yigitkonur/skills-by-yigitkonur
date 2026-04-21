---
name: run-research
description: >-
  Use skill if you are researching a bug, library, architecture decision, or any technical question needing web evidence, Reddit practitioner experience, and multi-source synthesis.
---

# Technical Research

You research technical questions using web search, page scraping, Reddit practitioner mining, and AI synthesis. For simple questions you work solo. For multi-domain topics you orchestrate parallel researcher agents.

## Trigger boundary

**Use when:** bug diagnosis, library comparison, architecture decision, technology evaluation, security audit, performance investigation, fact checking, landscape scan, or any question where current web evidence and practitioner experience matter.

**Do NOT use when:** finding GitHub repos (use `run-github-scout`), simple fact lookable in docs you already have, or questions answerable from the codebase alone.

## Tool prerequisites

This skill uses three MCP tools: `start-research`, `web-search`, `scrape-links`. If any are missing, install the research MCP server:

```bash
npx -y @anthropic-ai/claude-code@latest mcp add research-server -y -- npx -y mcp-remote@latest https://research.yigitkonur.com/mcp --allow-http
```

Restart your session after installation. If MCP tools are denied at runtime, fall back to WebFetch/WebSearch built-in tools. If those fail, use `curl` via Bash. Never stop because a tool was denied.

## Tool API (v6+)

| Tool | Required params | Optional | LLM? |
|---|---|---|---|
| `start-research` | — | `goal` (string), `include_playbook` (bool, default false) | Yes — returns goal-tailored brief (`primary_branch`, `first_call_sequence`, 25–50 keyword seeds, `iteration_hints`, `gaps_to_watch`, `stop_criteria`) when `goal` + planner available |
| `web-search` | `queries` (up to 50), `extract` (what you're looking for) | `raw` (skip classifier, default false), `scope` (`"web"` \| `"reddit"` \| `"both"`, default `"web"`), `verbose` (bool, default false) | Yes — tiered classifier (HIGHLY_RELEVANT / MAYBE_RELEVANT / OTHER) + synthesis + gaps + refine queries |
| `scrape-links` | `urls` (up to N), `extract` (pipe-separated shape) | — | Yes — per-URL extraction. Auto-detects `reddit.com/r/.../comments/` permalinks and routes them through the Reddit API (threaded post + full comment tree); non-reddit URLs flow through the HTTP scraper in parallel. |

There is no `search-reddit` or `get-reddit-post` tool in v6 — those collapsed into `web-search scope:"reddit"` (discovery) and `scrape-links` with reddit URLs (fetch).

## Decision: single-agent or multi-agent?

| Signal | Path |
|---|---|
| One clear question, one domain | **Single-agent** (you research directly) |
| Quick fact check, bug fix, library lookup | **Single-agent** |
| Multi-domain topic needing exhaustive coverage | **Multi-agent orchestrator** |
| "Deep dive", "comprehensive research", "implementation-ready docs" | **Multi-agent orchestrator** |
| Topic spans 3+ distinct subtopics or platforms | **Multi-agent orchestrator** |

---

## Single-Agent Path

You research directly using the three tools. Read `references/tools.md` for parameters and usage patterns.

### The research loop

#### 0. Plan with `start-research` — always

Every session begins with `start-research` using a 1–2 sentence `goal`. The server returns a goal-tailored brief: `goal_class`, `primary_branch` (reddit / web / both), `first_call_sequence` (exact next 1–3 calls), 25–50 keyword seeds, `iteration_hints`, `gaps_to_watch`, `stop_criteria`. Fire the `first_call_sequence` verbatim on round 1. If the planner is offline, the brief falls back to a compact stub — route manually by question shape.

#### 1. Search — from the brief's primary_branch

Feed the brief's `keyword_seeds` into your first `web-search` call. Pick `scope`:
- `"web"` (default) for spec / bug / pricing / CVE / changelog / API
- `"reddit"` for sentiment / migration / lived-experience (server appends `site:reddit.com` and filters to post permalinks)
- `"both"` only when opinion-heavy AND needs official sources (2× cost — don't default to this)

Write up to 50 queries per call. Orthogonal facets, not paraphrases. Exact error messages in quotes. Official docs with `site:`. Comparisons. Failure modes. Year-pinned queries. Negative signal on reddit scope (`"regret"`, `"switched from"`, `"broke in production"`) — at least 25% of reddit queries.

#### 2. Read what matters

After search, scrape the 3–10 most promising URLs with `scrape-links`. Mix reddit post permalinks + non-reddit URLs freely in one call — auto-detection routes reddit URLs through the Reddit API (threaded post + full comment tree); everything else flows through the HTTP scraper in parallel. Prefer contextually grouped batches — fire multiple parallel `scrape-links` calls when URL sets are unrelated (docs in one call, reddit threads in another).

Your `extract` instructions determine quality:
- Strong: `"root cause|fix steps|version affected|workarounds|breaking changes|migration path"`
- Weak: `"tell me about this page"`

Use 4–8 pipe-separated targets per call.

#### 3. Loop — harvest from classifier + scrape output

Each `web-search` response includes `## Gaps` (open questions with ids) and `## Suggested follow-up searches` (refine queries tied to gap ids). Each `scrape-links` response includes `## Follow-up signals` (new terms + referenced-but-unscraped URLs). Feed these into round 2's `web-search`. Safe to fire orthogonal `web-search` or `scrape-links` calls in parallel within one turn — use for unrelated subtopics.

#### 4. Verify what matters

Cross-check any claim that could change your recommendation. Stop when additional calls stop changing your conclusion AND every brief `stop_criteria` item is met AND every `gaps_to_watch` item is closed (or explicitly documented as unresolved).

### Matching depth to stakes

| Situation | Typical path |
|---|---|
| Quick fact check | `start-research` → `web-search` (5 queries) → `scrape-links` 2–3 URLs |
| Error diagnosis | `start-research` → `web-search scope:"web"` (error in quotes) → `scrape-links` top 3–5 |
| Library comparison | `start-research` → `web-search scope:"web"` (30 queries, 5 facets) → `scrape-links` on docs + benchmarks |
| Migration / sentiment | `start-research` (→ `primary_branch:"reddit"`) → `web-search scope:"reddit"` → `scrape-links` on post permalinks |
| Architecture decision | `start-research` (→ often `primary_branch:"both"`) → parallel `web-search` (web + reddit) → merged `scrape-links` |
| Production incident | `web-search` (3 queries, skip planner for speed) → `scrape-links` top 2–3 |

Read `references/workflows.md` for complete workflow templates covering bug fixes, library comparisons, architecture decisions, security audits, performance investigations, and more.

### Output formats

**Decisions:** Comparison table + recommendation + confidence + conditions that change the answer + counter-arguments section (objection in bold, evidence-backed response).

**Bug fixes:** Likely root cause with evidence + before → after fix + caveats + fallback. Start with immediate stabilization (what to deploy in 15 minutes).

**Evaluations:** Options ranked by fit + "best for [scenario A]" vs "best for [scenario B]" + specific risks per option.

All output: cite sources with specificity — Reddit usernames and dates, GitHub issue numbers, blog authors and dates, version numbers. `u/jsmith (Mar 2025, r/node): "exact quote"` is a citation. "Reddit consensus" is not.

Read `references/synthesis.md` for source credibility hierarchy, contradiction resolution, and verification checklists.

---

## Multi-Agent Orchestrator Path

You are the orchestrator. You do not research. You architect research missions, dispatch researcher agents, collect findings, and synthesize into structured documentation.

Read `references/orchestrator-philosophy.md` before your first dispatch.

### Phase 0: Understand the request (max 3 questions)

Clarify what the user needs. "What will you DO with this research?" (always). "Areas you already know vs. need explored?" (broad scope). "Target audience?" (when format matters). Skip if already answered.

### Phase 1: Explore context (orchestrator does this)

Before designing missions: read project docs, existing research, architecture files. Run a quick web-search (5-10 queries) to map the landscape. Capture existing knowledge, gaps, and user context. This feeds Phase 2.

### Phase 2: Design the research architecture

**2a. Research Domains** — Decompose into 3-8 non-overlapping domains. Each becomes one researcher agent. Include at least one community/practitioner domain and one cross-cutting concerns domain.

**2b. Output Architecture** — Design the documentation tree BEFORE dispatching. Use numbered files (`01-topic.md`). Each file independently useful. Read `references/output-architecture.md` for naming and structure patterns.

**2c. Agent-to-Output Mapping** — Map each agent to specific output files. Present the full architecture to the user before dispatching.

### Phase 3: Write mission briefs

Each brief contains: Context Block (dense prose, 200-500 words), Mission Objective (observable end-state), Research Guidance (URLs, search angles, extraction fields, ceilings not floors), Definition of Done (BSV: Binary, Specific, Verifiable), Handback Format. Read `references/mission-prompt-templates.md`.

Always include the fallback chain: "If MCP tools fail, use WebFetch/WebSearch. If those fail, use curl."

### Phase 4: Dispatch researcher wave

Launch ALL agents in a single message. Config: `subagent_type: "internet-researcher"`, `mode: "bypassPermissions"`, `run_in_background: true`. Max 8 agents per wave. Name each descriptively.

### Phase 5: Collect and write

Write docs as agents complete — do not wait for all. Extract structured research, preserve source attribution, mark tasks complete.

### Phase 6: Handle failures

Read `references/quality-gates.md` for decision rules. Tool denial → relaunch with bypassPermissions + fallback. Shallow output → follow-up with specific gaps. Timeout → relaunch with narrowed scope. Max 2 retries per domain.

### Phase 7: Synthesize

Read ALL docs personally. Create master summary (`00-master-summary.md`) with document index, critical findings, cross-domain insights, action items, and coverage scope. Read `references/synthesis-patterns.md`.

The orchestrator reads everything personally. No subagent-of-subagent chains for synthesis.

## Reference routing

| File | Read when |
|---|---|
| `references/tools.md` | Single-agent: tool parameters and usage patterns |
| `references/workflows.md` | Single-agent: step-by-step workflows for common scenarios |
| `references/synthesis.md` | Single-agent: source credibility, contradiction resolution, output patterns |
| `references/orchestrator-philosophy.md` | Multi-agent: mindset for writing mission briefs |
| `references/mission-prompt-templates.md` | Multi-agent: writing researcher agent prompts |
| `references/output-architecture.md` | Multi-agent: documentation tree design and file naming |
| `references/quality-gates.md` | Multi-agent: handling failures, retry vs proceed |
| `references/synthesis-patterns.md` | Multi-agent: cross-domain synthesis and master summary |

## Guardrails

- Query diversity > query volume. Five angles beats fifty paraphrases.
- Negative signal reveals truth. Always search for failures alongside recommendations.
- Never treat search snippets as evidence (they're leads — scrape to verify).
- Never more than 8 researcher agents per wave, 2 retries per domain.
- Always design output architecture BEFORE dispatching agents.
- The orchestrator reads ALL agent output personally — no delegation of synthesis.
