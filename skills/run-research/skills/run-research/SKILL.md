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

This skill uses five MCP tools: `web-search`, `scrape-links`, `search-reddit`, `get-reddit-post`, and `deep-research`. If any are missing, install the research MCP server:

```bash
npx -y @anthropic-ai/claude-code@latest mcp add research-server -y -- npx -y mcp-remote@latest https://research.yigitkonur.com/mcp --allow-http
```

Restart your session after installation. If MCP tools are denied at runtime, fall back to WebFetch/WebSearch built-in tools. If those fail, use `curl` via Bash. Never stop because a tool was denied.

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

You research directly using the five tools. Read `references/tools.md` for parameters and token budgets.

### The research loop

#### 1. Search first — always

Every task begins with `web-search`. Write keywords that attack genuinely different angles — up to 100 in parallel. Exact error messages in quotes. Official docs with `site:`. Comparisons. Failure modes. Year-pinned queries. Negative signal (`"problems with"`, `"regret"`, `"switched from"`). If your keywords are minor rewrites of each other, diversify before searching.

#### 2. Read what matters

After search, scrape the 3-10 most promising URLs with `scrape-links`. Your extraction targets determine quality:
- Strong: `"root cause|fix steps|version affected|workarounds|breaking changes|migration path"`
- Weak: `"tell me about this page"`

Use 4-8 pipe-separated targets per call. Always `use_llm=true`.

#### 3. Hear from practitioners

Official docs say how things should work. Reddit says how they actually work. Use `search-reddit` with diverse queries — at least 25% negative signal (`"regret"`, `"not worth it"`, `"broke in production"`). Then fetch the best 5-10 threads with `get-reddit-post` — always `fetch_comments=true`, always `use_llm=false`. Raw threaded comments ARE the signal.

#### 4. Synthesize with evidence

For complex questions, use `deep-research` to pull everything together. By this point your KNOWN field should overflow with findings from steps 1-3. Ask 2-3 focused questions, not 10 scattered ones. Attach relevant code files.

#### 5. Verify what matters

Cross-check any claim that could change your recommendation. Stop when additional tool calls stop changing your conclusion.

### Matching depth to stakes

| Situation | Typical path |
|---|---|
| Quick fact check | web-search → scrape 2-3 pages |
| Error diagnosis | web-search → scrape → search-reddit |
| Library comparison | Full loop: all 5 tools |
| Architecture decision | Full loop, starting broad |
| Production incident | web-search (3 keywords) → scrape top 2-3 |

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

Before designing missions: read project docs, existing research, architecture files. Run a quick web-search (5-10 keywords) to map the landscape. Capture existing knowledge, gaps, and user context. This feeds Phase 2.

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
| `references/tools.md` | Single-agent: tool parameters, token budgets, failure modes |
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
- Never call deep-research first with empty KNOWN (gather evidence first).
- Never more than 8 researcher agents per wave, 2 retries per domain.
- Always design output architecture BEFORE dispatching agents.
- The orchestrator reads ALL agent output personally — no delegation of synthesis.
