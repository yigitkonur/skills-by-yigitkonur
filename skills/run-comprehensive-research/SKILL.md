---
name: run-comprehensive-research
description: "Use skill if you are orchestrating multi-domain research across official docs, community forums, and practitioner experience with parallel researcher agents producing structured, implementation-ready documentation."
---

# Comprehensive Research Orchestrator

You are the orchestrator. You do not research. You architect research missions, dispatch researcher agents, collect their findings, and synthesize everything into a structured documentation corpus that anyone can consume and implement from directly.

This skill extends `run-research` (single-agent research) into multi-agent orchestrated research for topics that span multiple domains, platforms, or perspectives and need exhaustive coverage.

## Trigger boundary

**Use when:** "deep dive into X for our project", "research X comprehensively", "I need implementation-ready docs on X", any topic where a single research agent would produce a surface-level answer but you need depth across multiple facets.

**Do NOT use when:** the question has one clear answer (use `run-research`), you need to find GitHub repos (use `run-github-scout`), or the research is a simple fact check.

## Philosophy

Read `references/orchestrator-philosophy.md` before your first dispatch. Key principles:

- **You define what "done" looks like; agents find how to get there.** Outcomes, not procedures.
- **Mission gravity, not walls.** Make the objective so clear agents orbit back to it no matter how far they explore.
- **Ceilings, not floors.** "Use up to 80 search angles" — not "search at least 20 times."
- **Context is the foundation.** An agent with deep understanding makes better decisions than one with perfect instructions.
- **The brief IS the quality lever.** Mediocre brief → mediocre output. Razor-sharp brief → world-class output.

## Workflow

### Phase 0: Understand the Request (max 3 questions)

Before any research, clarify what the user actually needs. Use `AskUserQuestion`.

| Question | When to ask |
|---|---|
| "What will you DO with this research?" | Always — determines depth and format |
| "Any areas you already know well vs. need explored?" | When scope is broad |
| "Target audience for the docs?" | When output format matters |

Skip questions the user already answered. If the request is clear ("research Sentry for iOS and macOS"), go directly to Phase 1.

### Phase 1: Explore Context (orchestrator does this)

Before designing research missions, understand the landscape. The orchestrator explores — not subagents.

1. **If a codebase exists:** Read project docs, existing research, architecture files, CLAUDE.md. Understand what's already known, what's been decided, and what gaps remain.
2. **If external:** Run a quick `web-search` (5–10 keywords) to map the topic landscape — what subtopics exist, what's controversial, what's well-documented vs. poorly-documented.
3. **Capture:** existing knowledge, known gaps, related decisions, and the user's specific context.

This exploration directly feeds Phase 2. Skip it and your research domains will be generic instead of targeted.

### Phase 2: Design the Research Architecture

This is the most critical phase. The orchestrator designs three things:

#### 2a. Research Domains

Decompose the topic into 3–8 non-overlapping research domains. Each domain becomes one researcher agent's mission.

**Domain design principles:**
- Each domain should be independently researchable (no agent needs another agent's output)
- Domains should cover the topic from genuinely different angles (not overlapping paraphrases)
- Include at least one "community/practitioner experience" domain for real-world signal
- Include at least one "cross-cutting concerns" domain (privacy, performance, compatibility)

**Assessment per domain** (internal — do not include in agent prompts):
```
Ambiguity:    [ Low / Medium / High ]
Familiarity:  [ Familiar / Unfamiliar / Externally Dependent ]
Stakes:       [ Low / Medium / High ]
Heavy layers: [ Framing | Discovery | Evidence | Execution | Verification ]
```

#### 2b. Output Architecture

Design the documentation tree BEFORE dispatching agents. Use bracket-path naming where brackets signal dynamic segments that will be filled by research findings:

```
[output-root]/
├── 00-master-summary.md
├── [domain-a]/
│   ├── 01-[specific-topic].md
│   ├── 02-[specific-topic].md
│   └── 03-[specific-topic].md
├── [domain-b]/
│   ├── 01-[specific-topic].md
│   └── 02-[specific-topic].md
├── [cross-cutting]/
│   ├── 01-[concern-a].md
│   └── 02-[concern-b].md
└── [context]/
    ├── 01-[practitioner-feedback].md
    └── 02-[integration-map].md
```

**Naming rules:**
- Bracket segments (`[domain]`, `[topic]`) are replaced with descriptive kebab-case names
- Numbered prefixes (`01-`, `02-`) ensure consistent ordering
- Hyphenated topic names force specificity: `01-ios-setup-and-initialization.md` not `01-setup.md`
- Each file should be independently useful — a developer can read one file and act on it

Read `references/output-architecture.md` for the full naming system and file structure patterns.

#### 2c. Agent-to-Output Mapping

Map each researcher agent to specific output files. This is the contract — the agent knows exactly what documentation it needs to produce evidence for.

```
Agent 1 (iOS features)      → [platform]/ios/01-05
Agent 2 (macOS features)    → [platform]/macos/01-05
Agent 3 (configuration)     → [common]/07, [common]/09, [common]/10
Agent 4 (community)         → [context]/01
```

Present the full architecture to the user before dispatching. Get confirmation.

### Phase 3: Write Mission Briefs

For each researcher agent, write a mission brief following the protocol in `references/mission-prompt-templates.md`. Every brief contains:

1. **Context Block** — Why this research exists, what the project needs, what the agent should know before starting. Dense purposeful prose, not skeleton bullet points.
2. **Mission Objective** — One clear observable outcome. Outcomes, not procedures.
3. **Research Guidance** — Specific URLs to fetch, search angles to explore, extraction fields to target. Suggest capabilities and set ceilings ("up to 80 search angles if needed"). Never prescribe the exact sequence.
4. **Definition of Done** — BSV criteria (Binary, Specific, Verifiable). Every criterion answerable yes/no.
5. **Handback Format** — What the agent returns: single document, organized by sections, with source attribution.

**Critical prompt patterns:**
- Include the user's project context (not just the topic in isolation)
- Specify extraction fields for evidence gathering
- Set research depth ceilings with release valves
- Close with ownership grant: "You own this. Explore freely, adapt as needed."

### Phase 4: Dispatch Researcher Wave

Launch all researcher agents in parallel. All research domains are independent by design (Phase 2a guarantees this).

**Agent configuration:**
- **Type:** `internet-researcher`
- **Mode:** `bypassPermissions` (researchers need web access without per-tool approval)
- **Background:** `true` (parallel execution)
- **Model:** default (inherits parent)

**Dispatch rules:**
- Launch ALL agents in a single message (maximizes parallelism)
- Never more than 8 researcher agents per wave
- Name each agent descriptively (`ios-researcher`, `community-researcher`)
- Track each agent's target output files

### Phase 5: Collect and Write

As each agent completes, immediately write its findings into the planned documentation files.

**Collection protocol:**
1. Read the agent's complete output
2. Extract the structured research organized by the sections you requested
3. Write each planned documentation file, preserving the agent's evidence and source attribution
4. Mark the corresponding task as complete

**Do not wait for all agents before writing.** Write docs as they arrive. This shows progress and allows the user to review early results.

### Phase 6: Handle Failures

Read `references/quality-gates.md` for decision rules.

| Failure | Response |
|---|---|
| Agent returns "tools denied" | Relaunch with `bypassPermissions` mode and explicit fallback instructions ("use WebFetch/WebSearch built-in tools; if those fail, use curl via Bash") |
| Agent returns shallow/incomplete | Send a follow-up message with specific gaps to fill |
| Agent times out | Relaunch with narrowed scope (split the domain) |
| Agent output is off-topic | Do not relaunch — write what's usable, note the gap in synthesis |

**Retry budget:** Max 2 retries per domain. After exhaustion, proceed with what exists and document the gap.

### Phase 7: Synthesize

After all agents complete (or retry budget exhausted), the orchestrator reads ALL documentation files and creates:

1. **Master Summary** (`00-master-summary.md`) — Document index with hyperlinks, critical findings, cross-domain insights, action items, and a "what this research covers vs. what it doesn't" section.

2. **Integration Map** (if researching for an existing project) — How new research connects to existing project docs, decisions, and architecture.

Read `references/synthesis-patterns.md` for synthesis methodology.

**The orchestrator reads everything personally.** No subagent-of-subagent chains for synthesis. The orchestrator's cross-domain view is what creates the connections agents working in isolation cannot see.

## Quality Checklist

Before declaring research complete:

- [ ] Every planned documentation file exists with substantive content
- [ ] Every file follows the numbered naming convention
- [ ] Source attribution is present (not "Sentry docs say" but "docs.sentry.io/platforms/apple/..." or "u/username, r/subreddit, date")
- [ ] Platform/domain differences are explicitly called out (not buried in generic text)
- [ ] Community feedback includes real sources with dates
- [ ] Master summary cross-references all docs
- [ ] Each doc is independently actionable (a developer can follow it without reading the others)

## Decision rules

- User's request names specific subtopics → those become domains directly (skip broad discovery)
- Topic is narrow but deep → fewer agents (2–3) with deeper missions, not 7 shallow agents
- Existing project research exists → read it first, design domains to fill gaps (not re-cover ground)
- Community feedback is requested → always include a dedicated practitioner-experience agent
- Research is for implementation → every doc should include code examples and configuration details
- Research is for decision-making → every doc should include trade-offs, alternatives, and conditions

## File structure

```
[output-root]/                          # User-specified or negotiated
├── 00-master-summary.md               # Orchestrator writes last
├── [domain-a]/                         # One folder per research domain
│   └── 01-through-NN-[topic].md       # Numbered files per subtopic
├── [domain-b]/
│   └── ...
├── [cross-cutting]/                    # Concerns that span domains
│   └── ...
└── [context]/                          # Practitioner experience, integration maps
    └── ...
```

## Reference routing

| File | Read when |
|---|---|
| `references/orchestrator-philosophy.md` | Before first dispatch — establishes the mindset for writing mission briefs |
| `references/mission-prompt-templates.md` | Phase 3 — writing researcher agent prompts |
| `references/output-architecture.md` | Phase 2b — designing the documentation tree and file naming |
| `references/quality-gates.md` | Phase 6 — handling failures, deciding retry vs. proceed |
| `references/synthesis-patterns.md` | Phase 7 — reading all outputs and creating the master summary |

## Guardrails

- Never more than 8 researcher agents per wave
- Never more than 2 retries per domain
- The orchestrator reads ALL agent output personally — no delegation of synthesis
- Always design the output architecture BEFORE dispatching agents
- Always present the architecture to the user before dispatching
- Write documentation files as agents complete — do not batch everything at the end
- The master summary is always the LAST file written (requires all other docs to exist)
- If the user has a MISSION_PROTOCOL or similar orchestration philosophy doc, read it before Phase 3
