---
name: run-github-scout
description: "Use skill if you are finding the best GitHub repos for a technology need: searches, evaluates, and ranks repos using subagent swarms with automatic retry when results are weak."
---

# GitHub Scout

Find the best GitHub repos for any technology need. Orchestrates search and evaluation subagents, reads their results, retries when quality is low, and produces a ranked recommendation.

## Trigger boundary

**Use when:** "find the best X on GitHub", "what should I use for Y", "compare all Z options", "landscape survey for W"
**Do NOT use when:** you already know which repos to evaluate (use `run-github-repo-evaluate` directly) or just need a quick list without scoring (use `run-github-repo-search` directly)

## Workflow

### Phase 0: Understand the Need (max 4 questions)

Before any search, nail down what the user actually wants. Use the `AskUserQuestion` tool — no open-ended chat.

**Questions to consider (pick 2-4 that matter for THIS request):**

| Header | Question | When to ask |
|---|---|---|
| Need | "What problem are you solving?" | Always — clarifies the use case |
| Constraints | "Any hard requirements? (language, license, self-hosted, etc.)" | When the domain has many options |
| Scale | "Quick comparison or exhaustive landscape?" | When scope is ambiguous |
| Context | "Any repos you already know about or are currently using?" | When user mentions a specific tool |

**Do NOT ask if the user already specified these in their request.** Read what they said first. If they said "find me a self-hosted Notion alternative in TypeScript with real-time collab" — that answers Need, Constraints, and implicitly Scale. Skip straight to Phase 1.

### Phase 1: Generate Seed Strategy (orchestrator does this, NOT subagents)

Based on the user's answers, produce:

1. **Seed keywords** — 5-10 search terms that cover the space
2. **Known competitors** — any repos the user mentioned or you recognize
3. **Feature checklist** — 3-5 must-have features for scoring (becomes custom Feature Fit criteria)
4. **Search scope estimate** — will this find 10 repos or 200?

Write this strategy to `.githubresearch/strategy.md` in the working directory. This file is the orchestrator's memory — subagents don't need it, but you'll re-read it if retrying.

### Phase 2: Search (dispatch subagent)

Launch ONE search subagent (Sonnet):

```
You have a skill at ~/.claude/skills/run-github-repo-search/.
Read SKILL.md and its references, then search for: {SEED_KEYWORDS_AND_CONTEXT}

Known repos to include: {KNOWN_COMPETITORS}

Write your results (the final ranked markdown table) to:
  .githubresearch/search-findings/wave-01.md

Prefix all commands with rtk.
```

**Agent config:** model `sonnet`, mode `bypassPermissions`, `run_in_background: true`.

Wait for completion. Read `.githubresearch/search-findings/wave-01.md`.

**Quality gate — decide what happens next:**

| Result | Action |
|---|---|
| 20+ relevant repos found | Proceed to Phase 3 |
| 5-19 repos found | Acceptable — proceed, but note thin coverage |
| <5 repos found | **Retry**: tell a new subagent what was wrong and which angles to try. Write to `wave-02.md`. Max 2 retries. |
| Results are off-topic | **Retry with feedback**: "These are wrong because X. Try searching for Y instead." |

**Retry prompt template:**
```
Previous search found only {N} repos. Here's what was found:
{PASTE wave-01.md table}

This missed the mark because: {SPECIFIC_FEEDBACK}
Try these angles instead: {NEW_ANGLES}

Skill at ~/.claude/skills/run-github-repo-search/. Write to .githubresearch/search-findings/wave-02.md.
```

**Max 3 search waves total.** If still <5 after 3 waves, tell the user the topic may be too niche.

### Phase 3: Evaluate (dispatch subagent swarm)

Take ALL unique repos from all search waves. Decide swarm size:

**Swarm sizing formula:**

| Total repos | Agents | Repos per agent | Strategy |
|---|---|---|---|
| 1-5 | 1 | All | Single agent evaluates inline |
| 6-15 | 2-3 | ~5 each | Small swarm |
| 16-30 | 3-5 | ~6-10 each | Medium swarm |
| 31-60 | 5 | ~6-12 each | Full swarm (cap) |
| 61-150 | 5 | ~12-30 each | Full swarm, batch by stars (top repos get deeper eval) |
| 150+ | 5 | 30 each (top 150 by stars) | Cap at 150. Drop tail. |

**HARD CAP: Never more than 5 evaluation agents.**

Each eval subagent gets:

```
You have a skill at ~/.claude/skills/run-github-repo-evaluate/.
Read SKILL.md and its references.

Evaluate these repos: {REPO_LIST}

For each repo, run Phase 1 (batch screen) and Phase 2 (deep dive).
Use the scoring rubric from references/scoring-rubric.md.

Custom Feature Fit criteria for this search:
{FEATURE_CHECKLIST_FROM_PHASE_1}

Write your scored results to:
  .githubresearch/repo-reviews/batch-{N}.md

Use this format per repo:
  ## owner/repo
  Score: X/100 | Stars: N | Health: X | Author: X | Code: X
  Key strength: ...
  Key risk: ...
  Feature fit: [checklist with yes/no per feature]

Prefix all commands with rtk.
```

Launch all agents in parallel. Wait for all to complete.

### Phase 3.5: Feature Detection (dispatch subagent swarm)

After evaluation completes, build a cross-repo feature comparison matrix.

**Step 1: Discover canonical features.** Read all `batch-*.md` review files and the Phase 1 feature checklist. Identify 5-15 features that appear across repos. Write the list to `.githubresearch/feature-matrix/features.md`.

**Step 2: Dispatch feature-detection agents.** Same swarm sizing as Phase 3, max 5 agents. Each agent gets a batch of repos + the canonical feature list. Prompt template: see `references/subagent-prompts.md` section "Feature Detection Subagent".

Each agent writes to `.githubresearch/feature-matrix/batch-{N}.md` with structured JSON per repo (present/absent + evidence + confidence).

**Step 3: Collect results.** Build the `FEATURE_MATRIX` JSON object for the HTML template.

**Skip condition:** If the user said "quick comparison" or there are <=5 repos, skip this phase.

### Phase 4: Synthesize (orchestrator reads everything)

Read ALL files in `.githubresearch/repo-reviews/`. The orchestrator does this solo — no subagents.

**For each repo reviewed, check:**
1. Does the score make sense given the raw data?
2. Are there inconsistencies between batches? (same repo scored differently by different agents)
3. Did any agent miss critical data? (score says "no CI" but another agent found CI runs)
4. Does the Feature Fit checklist match the user's stated needs?

**Inconsistency handling:**

| Issue | Fix |
|---|---|
| Same repo scored by 2 agents with >15 point difference | Re-evaluate that repo yourself inline |
| Agent scored "no data" for a signal | Run the specific API call yourself to fill the gap |
| Feature Fit doesn't match user's checklist | Adjust score manually based on your reading of the repo |

### Phase 5: Final Report

Write `.githubresearch/summary.md`:

```markdown
# GitHub Scout: {TOPIC}
Date: {DATE}

## Recommendation
{1-3 sentences: which repo(s) to use and why}

## Ranked Results
| # | Repo | Score | Stars | Key Strength | Key Risk | Feature Fit |
|---|------|-------|-------|-------------|----------|-------------|

## Per-Repo Analysis (top 5-10)
### 1. owner/repo (Score: X)
{2-3 sentences}

## Categories
{3-5 natural groupings}

## Search Coverage
- Waves: N | Total unique repos: N | Evaluated: N | Agents used: N
- Hypotheses that found the most: {list}
- Gaps: {anything the search might have missed}
```

**Generate HTML report** by copying `references/report-template.html` to `.githubresearch/report.html` and replacing all placeholders with real data.

Placeholder reference:

| Placeholder | What to replace with |
|---|---|
| `[TOPIC]`, `[DATE]`, `[TOTAL_REPOS]`, etc. | Simple string substitution |
| `ROW_START`/`ROW_END` blocks | Duplicate per repo in ranked table |
| `CARD_START`/`CARD_END` blocks | Duplicate per top 5-10 repos for deep dive cards |
| `FEATURE_HEADER_START`/`END` | Duplicate per feature column in matrix |
| `MATRIX_ROW_START`/`END` + `MATRIX_CELL_START`/`END` | Duplicate per repo × feature |
| `CAT_START`/`CAT_END` | Duplicate per category chip |
| `[DRILL_DOWN_JSON]` | JSON object with per-repo H/A/C metric breakdowns (from Phase 4 synthesis) |
| `[FEATURE_MATRIX_JSON]` | JSON object with features and per-repo evidence (from Phase 3.5) |
| `[PUBLISH_ENDPOINT]` | Already hardcoded to `https://scout-reports.seodoold.workers.dev/publish` in template |

Score classes for bars: `excellent` (80+), `good` (60-79), `fair` (40-59), `weak` (20-39), `avoid` (<20).
Feature matrix cells: `yes` (present), `no` (absent), `partial` (medium confidence).

**Open the report in the user's browser:**
```bash
# Cross-platform open
case "$(uname)" in
  Darwin*) open .githubresearch/report.html ;;
  Linux*)  xdg-open .githubresearch/report.html ;;
  MINGW*|MSYS*|CYGWIN*) start .githubresearch/report.html ;;
esac
```

**Then tell the user:** brief summary in conversation + path to the full report.

### Phase 6: User Feedback Loop (optional)

If the user isn't satisfied:

| User says | Action |
|---|---|
| "These aren't what I wanted" | Go back to Phase 0, re-clarify need |
| "You missed X" | Add X to known repos, re-run Phase 3 for just that repo |
| "Go deeper on the top 3" | Run code-level analysis on those 3 repos (read their source code) |
| "Try different search terms" | Go back to Phase 2 with user's new angles |
| "Looks good" | Done |

**No infinite loops.** Max actions per session:
- 3 search waves
- 2 evaluation rounds
- 1 re-clarification

After that, present what you have and let the user decide.

## File structure

```
.githubresearch/
├── strategy.md              # Phase 1 output: seed keywords, features, scope
├── search-findings/
│   ├── wave-01.md           # First search results
│   ├── wave-02.md           # Retry (if needed)
│   └── wave-03.md           # Final retry (if needed)
├── repo-reviews/
│   ├── batch-01.md          # Eval agent 1 results
│   ├── batch-02.md          # Eval agent 2 results
│   └── ...                  # Up to batch-05.md
├── feature-matrix/
│   ├── features.md
│   ├── batch-01.md, ...
├── summary.md               # Final ranked report
└── report.html
```

Create `.githubresearch/` at the start. If it already exists from a prior run, archive it to `.githubresearch.bak.{timestamp}/` first.

## Decision rules

- User's request is crystal clear → skip Phase 0 questions entirely
- User provides example repos → use those to seed hypothesis generation AND as benchmark scores
- <5 total repos after 3 waves → tell user honestly, present what exists
- >150 repos → cap at 150 by stars, note truncation
- Single dominant repo (10x more stars than #2) → flag it as category leader but still evaluate alternatives
- All repos are <1 month old → warn user about volatility risk

## Reference routing

| File | Read when |
|---|---|
| `references/subagent-prompts.md` | Phase 2/3/3.5 — launching search, eval, or feature-detection subagents |
| `references/quality-gates.md` | After any search wave, evaluation, or feature detection — deciding retry vs proceed |
| `references/report-template.html` | Phase 5 — copy and fill with data to generate the HTML report |

## Guardrails

- Never more than 5 evaluation agents. Period.
- Never more than 3 search waves.
- Never more than 2 evaluation rounds.
- Always write files to `.githubresearch/` — never to the user's source tree.
- The orchestrator reads ALL agent output personally. No subagent-of-subagent chains.
- Use AskUserQuestion for requirements, not open-ended chat.
- If a subagent's output file is empty or missing, re-run that agent once. If still empty, proceed without it.
