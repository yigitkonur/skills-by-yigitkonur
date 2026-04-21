# Output Format — The Required Structure

Every session produces this exact section order. Missing any section means the brainstorm is incomplete. This file is the template; `communicate.md` covers the voice.

## Contents
- [Section order (required)](#section-order-required)
- [Per-section rules](#per-section-rules) — templates for all 10 sections
- [Mode differences](#mode-differences) — Interactive vs. One-shot
- [Length budgets](#length-budgets) — target word count by problem size
- [Formatting conventions](#formatting-conventions) — tables, code blocks, emphasis
- [Anti-patterns](#anti-patterns) — common failure modes and fixes

## Section order (required)

```markdown
# <Brainstorm topic>

## Approach
## Problem shape (Cynefin)
## Decomposition
## Options explored
## Evaluation
## Assumptions
## Blind spots
## Second-order effects
## Ranked summary
## Recommended next step
```

Ten sections. In this order. For interactive mode, sections emit progressively (after each workflow step). For one-shot mode, the full document emits at the end.

## Per-section rules

### 1. Approach

**Length**: 2-4 sentences. Never more than 80 words.

**Content**: chosen frameworks + one-sentence rationale per. The Minto headline — a reader skimming only this and the Ranked summary should still get the right answer.

**Template**:

```markdown
## Approach

Chosen frameworks: <framework 1>, <framework 2>, <framework 3>.
Why: <framework 1> for <reason>, <framework 2> for <reason>, <framework 3> for <reason>.
Cynefin domain: <domain>. Output mode: <Interactive | One-shot>.
```

**Example**:

```markdown
## Approach

Chosen frameworks: Cynefin (for classification), Issue Trees (to decompose the root-cause chain), Six Thinking Hats (for perspective diversity on options), Decision Matrix (to compare three architectural paths). Cynefin domain: Complicated. Output mode: Interactive.
```

### 2. Problem shape (Cynefin)

**Length**: 3-5 lines.

**Content**: the domain + the evidence from Step 1's classifier answers.

**Template**:

```markdown
## Problem shape (Cynefin)

Domain: <Clear | Complicated | Complex | Chaotic | Disorder>
Q1 (shape): <user's answer>
Q2 (cause-effect): <user's answer>
Q3 (reversibility): <user's answer>

Rationale: <one-sentence why this domain>
```

### 3. Decomposition

**Length**: scale to complexity. 10-30 lines for most problems; up to 60 for genuinely complex ones.

**Content**: the tree / fishbone / iceberg / ladder from Step 2, with priority markers.

**Template**:

```markdown
## Decomposition

Tool: <Issue Trees | Ishikawa | Iceberg Model | Abstraction Laddering | Connection Circles | Concept Map>

<The tool's output inline — tree, fishbone, iceberg levels, ladder, or circle>

Priority branches / levels: <the 1-2 marked for focus>
```

Use markdown lists for trees, markdown tables for matrices, or fenced code blocks for ASCII diagrams. Keep text — no external image files.

### 4. Options explored

**Length**: 1 paragraph per option + label. Minimum 3 options.

**Content**: each option has a label, rationale, tradeoff, and Cynefin-fit.

**Template**:

```markdown
## Options explored

Tool used: <Six Thinking Hats | First Principles | Zwicky Box | Connection Circles>

**Option A: <label>**
- Rationale: <2-3 sentences>
- Key tradeoff: <what is given up>
- Cynefin-fit: <domain this option suits best>

**Option B: <label>**
- Rationale: <...>
- Key tradeoff: <...>
- Cynefin-fit: <...>

**Option C: <label>**
- Rationale: <...>
- Key tradeoff: <...>
- Cynefin-fit: <...>

[Optional: D, E if the generative tool produced them]
```

### 5. Evaluation

**Length**: the matrix + rationale — usually 15-30 lines.

**Content**: Decision Matrix (or Impact-Effort / Eisenhower / No-brainer note) with scores, weights, and confidence flags.

**Template** (Decision Matrix case):

```markdown
## Evaluation

Decision shape (Hard Choice Model): <quadrant>
Tool: <Decision Matrix | Impact-Effort | Eisenhower | just-pick>

Factors (weights):
| Factor | Weight | Rationale for weight |
|---|---|---|

Scoring:
| Option | Factor 1 | Factor 2 | Factor 3 | Total |
|---|---|---|---|---|

Winner: <Option X, total>
Runner-up: <Option Y, total>
Gap: <meaningful | marginal | rounding-error>

Low-confidence scores:
- <score + what would raise confidence>
```

### 6. Assumptions

**Length**: bulleted list, 3-8 items typically.

**Content**: load-bearing assumptions the recommendation depends on. Surface the ones that, if wrong, would change the pick.

**Template**:

```markdown
## Assumptions

- <assumption 1 — what is taken as true>
- <assumption 2>
- <assumption 3>
```

Rules:
- One assumption per bullet
- Each assumption is checkable (specific, not vague)
- Flag which assumptions are highest-risk (asterisk or "high-risk:" prefix)

**Example**:

```markdown
## Assumptions

- Team has one engineer with Dynamo experience
- Current Postgres instance will scale to 3x traffic without hardware upgrade
- Latency regression of >200ms on hot paths is unacceptable  *
- * high-risk: user threshold for latency not empirically validated
```

### 7. Blind spots

**Length**: bulleted list, 2-5 items typically.

**Content**: what the process likely missed. What a different framework or perspective would have surfaced.

**Template**:

```markdown
## Blind spots

- <what the process likely missed>
- <what a different tool would have caught>
- <bias in the option generation>
```

**Rules**:
- Be specific about the missed thing, not generic "we might have missed something"
- Name the alternative framework that would have caught it, if known

**Example**:

```markdown
## Blind spots

- No option considered a hybrid (read-replica + cache). Zwicky Box would have surfaced it; we used Six Thinking Hats which stayed on clean alternatives.
- Operational cost at scale unknown beyond current traffic; no factor captures scaling cost over 12 months.
- Vendor lock-in risk for option C mentioned in Black hat but not scored in Decision Matrix.
```

### 8. Second-order effects

**Length**: 6-12 lines.

**Content**: both the consequence chain AND the timeline analysis from Step 5.

**Template**:

```markdown
## Second-order effects

Consequence chain:
  Immediate: <first-order>
  → Next: <second-order>
  → Next: <third-order — often diminishing clarity>

Timeline:
  - 10 minutes: <operational effect>
  - 10 months: <quarter-level impact>
  - 10 years: <strategic consequence>

Surprising effects:
- <effect that changes the pick or requires mitigation>
```

### 9. Ranked summary

**Length**: the table + optional notes.

**Content**: options ranked by total score with confidence. This is the Minto conclusion restated near the end of the document.

**Template**:

```markdown
## Ranked summary

| # | Option | Score / Rationale | Confidence | Notes |
|---|---|---|---|---|
| 1 | <Option X> | <score + 1-line rationale> | <H/M/L> | <caveat or mitigation> |
| 2 | <Option Y> | <score + 1-line> | <H/M/L> | <caveat> |
| 3 | <Option Z> | <score + 1-line> | <H/M/L> | <caveat> |

Confidence flags: <any scores that warrant follow-up>
```

### 10. Recommended next step

**Length**: 2-4 sentences + an explicit question.

**Content**: concrete action (a skill to invoke, a command to run, a decision to make) + the explicit user question at the next fork.

**Template**:

```markdown
## Recommended next step

<Concrete next action — a skill to invoke, a command, a specific decision>.

**Your input needed on:** <specific question at the next fork>.
```

**Example**:

```markdown
## Recommended next step

Proceed with Option A (keep Postgres + tune pool + add retry layer). Use `build-skills` to draft the implementation plan, or create a GitHub Issue via `run-issue-tree` with the three sub-tasks (pool tuning, retry module, monitoring). Budget: ~5 engineer-days.

**Your input needed on:** Should I open the issue tree now, or do you want to raise confidence on the latency-regression threshold first with a 2-hour benchmark?
```

## Mode differences

### Interactive mode

Sections emit **progressively**, each after its workflow step:

- After Step 1 → Approach + Problem shape
- After Step 2 → Decomposition
- After Step 3 → Options explored
- After Step 4 → Evaluation
- After Step 5 → Assumptions + Blind spots + Second-order effects
- After Step 6 → Ranked summary + Recommended next step

Each fork gives the user a chance to redirect. The final output is reassembled into the full 10-section document.

### One-shot mode

All 10 sections emit as **one document**, post-Step 5, no interim pauses. The user reviews the full document and responds once. Use this mode only when the user explicitly asks for a deliverable without mid-session involvement.

## Length budgets

| Problem size | SKILL.md output total |
|---|---|
| Small (No-brainer, Apples & Oranges) | 300-600 words |
| Medium (Big Choice) | 600-1,500 words |
| Large (Hard Choice, Complex domain) | 1,500-3,000 words |

Above 3,000 words, the brainstorm is probably too large — re-scope to a sub-problem.

## Formatting conventions

- **Tables** for matrices, ranked lists, and scoring
- **Code blocks** for ASCII diagrams, trees, iceberg levels
- **Bulleted lists** for assumptions, blind spots, options
- **Bold** for section headlines (`**Option A:**`)
- **Italic** for emphasis within prose
- Backticks for framework names on first reference — use a single pair of backticks (for example, `Six Thinking Hats`)
- Backticks for skill names (for example, `build-skills`)
- Inline citations use `file:line` format when referencing code

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Sections out of order | Follow the 10-section order exactly; it's Minto-structured for skimmability |
| Combined sections ("Assumptions and blind spots") | Keep separate; they catch different failure modes |
| Missing "Second-order effects" section | Required — Step 5 always runs; always surface results |
| "Recommended next step" that says "consider..." | Concrete action only — a skill, a command, or a specific decision |
| Ranked summary without confidence column | Confidence is required for prioritizing which scores to raise |
| Options section with <3 options | Minimum 3; if Step 3 produced fewer, go back and widen the generative tool |
| Vague assumptions ("the team is capable") | Checkable: "team has ≥1 engineer with Dynamo experience" |
| Blind spots section that reads "we might have missed things" | Name the specific thing missed and the tool that would have caught it |
