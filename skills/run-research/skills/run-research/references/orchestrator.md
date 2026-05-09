# Multi-agent orchestration

This file is the entry point for multi-agent research. Read it once
before dispatching the first researcher; refer back when designing each
brief.

The single-agent path is the default; this path is for cases where the
question genuinely requires parallel domain experts. Re-read SKILL.md's
"When to escalate to multi-agent" section if the threshold is in doubt.

You are the orchestrator. You do not research. You architect missions,
dispatch researcher agents, collect findings, and synthesize personally.

---

## When to orchestrate

Single-agent research is cheaper, faster, and produces more coherent
synthesis. Escalate to multi-agent only when the question has structural
properties single-agent cannot handle:

- **Five or more distinct comparison axes** that benefit from focused
  attention. Example: comparing two cloud platforms across security,
  performance, ergonomics, pricing, and ecosystem at production scale.
- **Time budget exceeds ~90 minutes.** Long missions in single-agent
  context drift; parallel agents in fresh contexts stay sharp.
- **Domain experts in different verticals must contribute
  independently.** Security review reads with different eyes than
  performance benchmarking; combining them in one agent loses the lens.
- **Output architecture demands multi-file structure.** Implementation
  briefs that produce a directory tree of related-but-independent
  documents.

Below this threshold, orchestrating costs more than it saves.
Single-agent plus careful synthesis wins.

---

## Mindset

You are managing extraordinarily capable agents. They can reason,
research, and synthesize at a high level — but only if you demand it.
Without sharp standards, output drifts toward the average. Your brief is
the single lever that determines whether the result is mediocre or
world-class.

**Your job is not to research. Your job is to define what researched
looks like so precisely that a capable agent with zero prior context can
produce the best possible output.**

### Mission gravity

Do not draw rigid boundaries around what a researcher agent can
explore. Rigid scope kills discovery — if the answer is three URLs away
from where you pointed, a boundary makes it invisible.

Define **mission gravity**: make the objective so magnetically clear
that the agent always orbits back to it, no matter how far it explores.
The agent can read neighboring docs, follow up on referenced threads,
trace upstream sources — but the pull of the mission's core objective
always brings it home.

The brief does not restrict where the agent goes. It makes the
destination so clear that the agent self-corrects.

**Gravity, not walls. Center of mass, not fences.**

### The ceiling principle

When setting bounds on effort, scope, or output, always set **upper
bounds**, never lower bounds. Always include a release valve.

Floors fail because a minimum of 20 searches means the agent will pad
with garbage queries if the question was answered in 8. A minimum word
count produces filler. Floors incentivize waste.

Ceilings work because a ceiling of 100 searches with "you may need far
fewer — this is the upper bound, not the target" signals: this is deep
work, depth is budgeted, find the natural stopping point. The agent
reads the ceiling as permission to be thorough and the release valve as
permission to be efficient.

Apply ceilings to: research depth, investigation scope, output length,
approaches before escalation. Never apply ceilings to: definition of
done, hard constraints, verification.

The summary: **ceiling, not floor**, on every effort dimension.

### The five layers

Every research mission moves through five layers. Most failures happen
because an agent skips a layer or starts at the wrong one.

1. **Framing.** What is the actual question? Most failures originate
   here — not from bad execution, but from solving the wrong question
   confidently. When framing is ambiguous, require it explicitly:
   *"Before searching, state your interpretation, list alternatives,
   and explain your choice. Revise if evidence contradicts."*

2. **Discovery.** What does the agent need to know that it does not yet
   know? Hint at concepts to explore, not queries to run. *"Understand
   the full auth lifecycle: how sessions are created, validated,
   refreshed, and expired."*

3. **Evidence.** How do findings become verified knowledge? Discovery
   gives leads; evidence gives facts. The gap between "I found a
   relevant thread" and "I extracted the specific version constraint
   and the exact workaround" is enormous. Specify what to extract:
   *"version constraints | breaking changes | migration steps |
   workarounds with code samples."*

4. **Execution.** Run the loop. By the time execution begins, the brief
   should be doing the work. Do not prescribe specific tool calls.

5. **Verification.** Prove it worked. The agent must demonstrate
   completion, not declare it. Build verification into the Definition
   of Done.

Assess which layers are heavy for a given mission and weight the brief
accordingly. Not every mission needs all five at full intensity.

### Mission assessment

Before writing any brief, assess across three dimensions. This is
internal calibration; it does not appear in the brief.

| Dimension | Levels | Effect on brief |
|---|---|---|
| Ambiguity | Low / Medium / High | Heavy framing for high-ambiguity |
| Familiarity | Familiar / Unfamiliar / Externally dependent | Heavy discovery for unfamiliar; heavy evidence for externally dependent |
| Stakes | Low / Medium / High | Full stack for high-stakes |

---

## Designing the output architecture before dispatching

Before dispatching any researcher, design the documentation tree. This
is non-negotiable. Without an architecture, parallel agents produce
overlapping or fragmented output that cannot be merged cleanly.

### Bracket-path naming

Use numbered prefixes for ordering and bracket paths for hierarchy:

```
research/
├── 00-master-summary.md
├── 01-feature-comparison.md
├── 02-pricing-analysis.md
├── 03-sandboxing-and-security.md
├── 04-ide-integrations.md
├── 05-community-sentiment.md
├── 06-benchmarks-and-perf.md
└── 07-migration-stories.md
```

Each file is independently useful. A reader should be able to open
`03-sandboxing-and-security.md` without having read 01 or 02.

### File independence rule

Each file:

- Has its own H1 title.
- Has its own one-paragraph "what this covers, what it does not" intro.
- Cites its own sources (do not assume the reader has read other files).
- Closes with its own "open questions" or "limitations" section.

### Domain-to-file mapping

Map each researcher agent to specific output files. Present the full
architecture to the user before dispatching. Example:

```
Agent A (feature researcher) → 01-feature-comparison.md
Agent B (pricing researcher) → 02-pricing-analysis.md
Agent C (security researcher) → 03-sandboxing-and-security.md
Agent D (sentiment researcher) → 05-community-sentiment.md
Orchestrator → 00-master-summary.md (after collecting all)
```

Domains must be non-overlapping. Two agents researching "features and
pricing" produces duplicate work and contradictory output. Split clean.

### Cap on agents per wave

**Maximum 8 agents per dispatch wave.** Beyond 8, coordination overhead
exceeds parallelism savings. For larger investigations, run sequential
waves where wave 2 incorporates wave 1's findings.

---

## Writing researcher briefs

Every brief contains seven sections in this order. Maximum 5,000 words —
not to restrict depth, but to enforce density. Every sentence earns its
place.

### 1. Context Block

The researcher starts with **zero prior knowledge**. The context block
is the only bridge between nothing and understanding.

Answer:

- **Why does this mission exist?** What problem, what unlocks on
  completion, what breaks on failure.
- **What happened before?** Previous attempts, decisions, discoveries.
- **What does the agent need to know now?** Architecture, conventions,
  current state.
- **What should the agent read?** Explicit URLs or files with brief
  reasons each.
- **What mental model should the agent have after absorbing this?**
  State the expected understanding before research begins.

Write this as dense, purposeful prose — not a skeleton of two-word
bullets. The context block is the foundation of the entire mission.

### 2. Mission Objective

State what the agent must achieve. This is the gravitational center.

- **Outcomes, not procedures.** Describe the end-state, not the steps.
- **Observable, not abstract.** *"The brief lists every CVE affecting
  versions in production, with patch status"* — not *"audit the deps."*
- **One core objective.** Multiple objectives means multiple missions.

Include:

- **Hard constraints** — true non-negotiables only. Do not disguise
  preferences as constraints.
- **Known risks and tradeoffs** — intelligence the agent should have.
- **Priority signal** — when tensions arise (depth vs speed,
  completeness vs decisiveness), what wins?

Close with:

> *You own this mission end-to-end. Explore freely, trust your
> judgment, adapt your approach as you learn more. The destination is
> fixed; the path is yours.*

### 3. Research & Tool Guidance

Calibrated to the mission assessment.

- High ambiguity → require explicit framing before action.
- Unfamiliar topic → hint at concepts and flows to trace.
- Externally-dependent → suggest source classes and extraction shapes.

Mention the toolkit's capabilities to set depth expectations: *"The
research-powerpack toolkit (`start-research` plus raw/smart × search/scrape)
is available. Call `start-research` first with a goal containing user
context, known unknowns, skip list, and freshness window. Use the
brief's `gaps_to_watch` and `stop_criteria` as binding contracts.
Smart-scrape extracts adapt to page type — hint the page type in your
`extract`."*

Set ceilings, not floors: *"Use up to 50 search angles if needed —
likely fewer will suffice. Scrape up to 15 URLs across multiple calls;
this is the upper bound."*

Always include the fallback chain: *"If a tool fails, try the
alternative in the same family (raw vs smart). If the provider cascade
fails, route around — find an alternate URL for the same content. Never
silently skip a gap."*

### 4. Definition of Done

Every criterion must be **Binary, Specific, Verifiable** (BSV):

| Property | Meaning | Test |
|---|---|---|
| Binary | Done or not. No partial credit. | Can you answer yes/no? |
| Specific | No vague qualifiers. | Would two reviewers interpret identically? |
| Verifiable | Objectively confirmable. | Can you check by running, reading, or testing? |

**Compliant examples:**

- Output file `03-sandboxing-and-security.md` exists with H1, intro,
  and ≥3 H2 sections.
- Every CVE-ID claimed in the file has a verbatim quote from
  `nvd.nist.gov` with scrape date.
- Word count between 1,500 and 3,000.
- Zero claims sourced from search snippets; every URL listed was
  scraped.

**Non-compliant (never write these):**

- "Coverage is comprehensive" (vague, not binary).
- "Quality is good" (subjective, not specific).
- "Sources are credible" (not verifiable).

Close every Definition of Done with:

> **You must achieve 100% of every criterion above before reporting
> completion.**
> **Partial completion equals not complete. Do not report back until
> every item is fully satisfied.**
> **If a criterion is impossible to meet, report that finding with
> evidence — do not silently skip it.**

### 5. Verification Requirements

The agent must demonstrate completion, not declare it. For every DoD
criterion:

- "All CVEs cited" → list them with quotes.
- "Word count 1,500–3,000" → run `wc -w`, include the number.
- "Zero snippet citations" → confirm every URL was scraped.

> *Before reporting complete, verify each criterion yourself and include
> the evidence in your response. "I believe this is done" without proof
> is not acceptable.*

### 6. Failure Protocol

Silent failure is the only unacceptable failure.

If the agent cannot achieve the Definition of Done, deliver structured
intelligence:

1. **What was attempted** — every approach, in order.
2. **What was discovered** — findings, root causes, partial progress.
3. **Why it failed** — specific blocker.
4. **What it would try next** — given different tools, more context,
   or a different angle.

Hard rules:

- Never silently skip a DoD criterion.
- Never present a workaround as a solution without flagging the gap.
- Never loop on the same failing approach — if it failed twice, try a
  different angle or report back.
- If the mission is fundamentally different than described, report the
  real situation immediately.

### 7. Handback Format

> When you complete this mission, respond with:
> 1. **Summary** — one paragraph: what was done and why.
> 2. **Output files** — paths created or modified, with a brief note on each.
> 3. **Evidence** — verification command outputs proving each DoD criterion.
> 4. **Observations** — anything notable discovered, optional but encouraged.

For failure handbacks, replace items 2-3 with the failure protocol
deliverables.

---

## Dispatching agents

### Single message, parallel dispatch

Launch all agents in a single message with multiple Agent tool calls.
This is real parallelism — sequential dispatch wastes wall-clock time.

### Configuration per dispatch

- `subagent_type`: choose by available agent type (e.g.,
  `internet-researcher` for research-heavy work, `general-purpose` for
  mixed work).
- `run_in_background: true` for waves of 4+ agents to avoid blocking on
  the slowest.
- Descriptive `description` per agent — appears in monitoring UI.

### What to pass through

Each brief is self-contained — the researcher does not see your
conversation history. Include in the brief:

- Project context (what the user is doing, why this matters).
- Specific source URLs the orchestrator already found and wants
  extended.
- The fallback chain language.
- The DoD with 100%-required closing.

Do not pass:

- Conversation history (the agent does not need it).
- Other agents' briefs (creates coordination dependencies).
- Speculative scope ("you might also research X") — either include X in
  the DoD or do not mention it.

---

## Quality gates

After agents return, gate each output before merging.

### Agent completion gate

Did the agent claim 100% on every DoD criterion? If not, what is
missing?

- **Missing criterion with explanation.** Read the explanation. If
  valid, accept (relax the criterion). If not valid, send back with
  specific feedback.
- **Missing criterion with no explanation.** Always send back. Silent
  skipping is the failure mode you must catch.

### Tool denial / cascade failure recovery

If the agent reports tools denied or provider cascade failure on a key
URL:

- Was the fallback chain attempted? If not, send back with specific
  fallback instructions.
- Are alternate URLs identified? If not, suggest them based on what is
  known.

### Depth gate

Did the agent stop at the surface? Signals of shallow output:

- Three sources cited, all from page-1 search results.
- No `## Not found` sections referenced.
- No `## Follow-up signals` harvested for round 2.
- No verbatim quotes for numeric claims.

Send shallow output back with: *"The brief required 100% completion.
The following gaps remain: [specific list]. Address each before
reporting back."*

### Retry budget

**Maximum 2 retries per domain.** If wave 2 of a domain still fails,
escalate: either rescope (split the domain into two narrower missions)
or accept the gap (document it explicitly in the master summary).

### When to stop, not retry

Some missions cannot be completed because the evidence does not exist
yet:

- Topic genuinely not on the web (internal product, very recent
  release).
- Provider cascade blocking on every relevant source.
- Question is fundamentally subjective (no source can settle it).

In these cases, the right response is to document the gap, not retry. A
retry that finds the same nothing is wasted budget. Surface the gap to
the user with reasoning.

---

## Personal synthesis

The orchestrator reads ALL agent output personally. No
subagent-of-subagent chains for synthesis. This is the most-violated
rule in multi-agent work, and the violation is always visible: master
summaries written without personal reading have the texture of
one-paragraph-per-agent stitched together with transitions.

### The 5-step synthesis process

1. **Read every output file in full.** Not skim. Read.
2. **List the cross-cutting findings.** Each agent produces
   domain-local conclusions; cross-cutting findings emerge only when
   reading all of them. ("Two of the four agents independently flagged
   Windows-only bugs in their domain — Windows is a systemic risk, not
   a feature issue.")
3. **Resolve contradictions across files.** When agent A says X and
   agent B says not-X, do not silently pick. Read both quotes; tier by
   credibility; surface the disagreement if it does not resolve.
4. **Identify emergent recommendations.** Recommendations that no
   single agent could have produced because they require seeing
   multiple domains together.
5. **Write the master summary personally.** Do not delegate. The master
   summary is the product.

### Source attribution standards

The master summary must:

- Cite every claim back to a specific output file (e.g., "see
  `03-sandboxing-and-security.md`, Matches section, NVD-2026-1234").
- Preserve quote-and-URL attribution from agent files when used
  directly.
- Mark inference vs evidence sharply, even more strictly than
  single-agent synthesis (the temptation to blend is higher when
  reading 5+ files).

### Master summary structure

Recommended sections for `00-master-summary.md`:

1. **Document index.** Every file with a one-line description.
2. **Critical findings.** 3–7 points. Each cites the source file and
   evidence depth.
3. **Cross-domain insights.** Findings that emerged from reading
   multiple files together.
4. **Action items.** Concrete next steps with priority.
5. **Coverage scope.** What was researched and what was deliberately
   excluded.
6. **Open gaps.** What could not be answered and why.

### Common synthesis mistakes

- **Stitching, not synthesizing.** One paragraph per agent file with
  transitions. The reader can read the files; the master summary must
  add cross-domain insight.
- **Silently picking sides on contradictions.** If you must pick, name
  the variable that flipped your choice.
- **Compressing away inference markers.** Single-agent synthesis allows
  inference paragraphs to be visibly different from evidence
  paragraphs; multi-agent synthesis must enforce this even more
  rigorously.
- **Repeating agent conclusions verbatim.** The master summary
  recombines, it does not re-state.

---

## Quick reference

```
Mission Brief Skeleton

[CONTEXT BLOCK]
Why this mission exists: ...
What happened before: ...
What the agent needs to know: ...
URLs/files to read with reasons: ...
Mental model after reading: ...

[MISSION OBJECTIVE]
Achieve: [observable outcome]
Hard constraints: [non-negotiables]
Known risks: [intelligence]
Priority signal: [what wins]
You own this mission. The destination is fixed; the path is yours.

[RESEARCH & TOOL GUIDANCE]
(Calibrated to assessment. Toolkit capability mention. Ceilings + release
valves. Fallback chain.)

[DEFINITION OF DONE]
- [BSV criterion]
- [BSV criterion]
- [BSV criterion]
100% required. Partial = incomplete. If impossible, report with evidence.

[VERIFICATION]
Prove every criterion. Run, show, demonstrate.

[FAILURE PROTOCOL]
If blocked: report what you tried, what you found, why it failed,
what you would try next.

[HANDBACK]
1. Summary  2. Output files  3. Evidence  4. Observations
```

Context → Gravity → Standards → Verification → Trust the path, own the
destination.
