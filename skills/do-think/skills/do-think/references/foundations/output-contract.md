# Output Contract

What deep thinking produces. Two top-level shapes — pick by Mode (Solo vs Interactive). Within Solo, the artifact also varies by **Op** — see the per-op shape in `operation-classification.md` (Sense-Making produces a verdict + evidence Minto; Extraction produces a filled schema + ambiguity log; Composition produces the artifact + provenance + assumptions; etc.).

The structure below covers the **Sense-Making** Solo shape and the universal Interactive shape. For non-Sense-Making Solo outputs, follow the per-op shape in the relevant workflow file.

## Solo mode — Minto Pyramid

**Required structure**:

1. **First sentence** = the chosen path. Not background, not framing, not "after consideration." The verdict.
2. **Body**: 3-5 supporting key arguments, one line each. Evidence under each.
3. **Last sentence** = the verification check. What you'll observe to confirm the path worked.

**Fast-fail check**: missing first-sentence verdict OR missing last-sentence verification = output incomplete. Re-write before declaring done.

### Why Minto

Busy readers skim. The agent's user often skims. Bury the conclusion in paragraph 4 and the user will miss it. Lead with the verdict, support with evidence, end with the verifiable next move.

### Worked example

```
Recommendation: keep Postgres + tune the connection pool, add a retry layer at the
session-store boundary.

Why:
- Latency benchmark (latest, 3 weeks old): pool tuning recovers 60ms p95 — gets us
  inside the 200ms SLO without the operational complexity of a new datastore.
- Migration risk for Redis is High; team has no production Redis experience and the
  hot-read path is on the user-login flow.
- Reversibility: pool tuning is fully reversible; Redis migration is one-shot at this
  scale.

Stress-test passes:
- Inversion: most likely failure is "tuning regresses under 10x load" — mitigated by
  load-test in staging before rollout.
- Second-order: cache-coherence concerns at quarter-scale handled by retry layer.

Verification: deploy to staging, run the 10x load script, confirm p95 ≤ 200ms and
error rate ≤ 0.1% for 30 minutes; promote to prod with the canary at 5% for 1 hour
before full rollout.
```

First sentence = verdict. Last sentence = verifiable check. Body = scannable evidence.

### What does NOT belong in Solo output

- A narration of your thinking process ("After running Cynefin, then exploring three options…")
- The full Phase A → D trace
- "Let me know what you think" or "Hope this helps"
- Discussion of the tradeoffs *without* a chosen path

The reasoning trace is internal; the output is the decision, the evidence, and the check.

## Interactive mode — 10-section contract

Interactive mode produces a long-form deliverable. Required section order:

```markdown
# <Topic>

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

Ten sections. In this order. Reordering breaks the Minto skim — Approach is the headline; Ranked summary is the conclusion restated near the end. Both must be present.

### Per-section rules

#### 1. Approach (2-4 sentences, ≤80 words)
Chosen frameworks + one-sentence rationale per. The Minto headline of the document.

```markdown
## Approach

Chosen frameworks: <framework 1>, <framework 2>, <framework 3>.
Why: <framework 1> for <reason>; <framework 2> for <reason>; <framework 3> for <reason>.
Cynefin domain: <domain>. Op: <op>. Emit style: <progressive | one-shot> (Interactive only — Solo emits as a single Minto artifact).
```

#### 2. Problem shape (Cynefin) (3-5 lines)
Domain + the evidence from the 3-question classifier.

```markdown
## Problem shape (Cynefin)

Domain: <Clear | Complicated | Complex | Chaotic | Disorder>
Q1 (shape): <answer>
Q2 (cause-effect): <answer>
Q3 (reversibility): <answer>

Rationale: <one-sentence why this domain>
```

#### 3. Decomposition (10-30 lines, scale to complexity)
The decomposition artifact (tree, fishbone, iceberg, ladder, or connection-circle) produced in Phase A — see SKILL.md master table for the framework that was selected.

#### 4. Options explored (1 paragraph per option, ≥3 options)
Each option: label, rationale, key tradeoff, Cynefin-fit.

```markdown
## Options explored

Tool used: <Six Thinking Hats | First Principles | Zwicky Box | Connection Circles>

**Option A: <label>**
- Rationale: <2-3 sentences>
- Key tradeoff: <what is given up>
- Cynefin-fit: <domain>

**Option B: <label>**
- Rationale: <...>
- Key tradeoff: <...>
- Cynefin-fit: <...>

**Option C: <label>**
- Rationale: <...>
- Key tradeoff: <...>
- Cynefin-fit: <...>
```

#### 5. Evaluation (matrix + rationale, 15-30 lines)
Hard Choice classifier output + Decision Matrix / Impact-Effort / Eisenhower (whichever fits) with weights, scores, confidence flags.

#### 6. Assumptions (3-8 bulleted items)
Load-bearing assumptions the recommendation depends on. Each checkable. Mark high-risk ones.

```markdown
## Assumptions

- <assumption 1 — checkable, not vague>
- <assumption 2>
- <assumption 3>  *
- * high-risk: <why this one matters most>
```

#### 7. Blind spots (2-5 bulleted items)
What the process likely missed. Be specific; name the alternative tool that would have caught it.

#### 8. Second-order effects (6-12 lines)
Both consequence chain AND timeline analysis from `stress-test-trio.md`.

#### 9. Ranked summary (table + optional notes)
Options ranked by total score with confidence column. The Minto conclusion restated.

```markdown
## Ranked summary

| # | Option | Score / Rationale | Confidence | Notes |
|---|---|---|---|---|
| 1 | <X> | <score + 1-line> | <H/M/L> | <caveat> |
| 2 | <Y> | <score + 1-line> | <H/M/L> | <caveat> |
| 3 | <Z> | <score + 1-line> | <H/M/L> | <caveat> |
```

#### 10. Recommended next step (2-4 sentences + explicit question)
Concrete action — a skill to invoke, a command, a specific decision. Plus the explicit user question at the next fork.

```markdown
## Recommended next step

<Concrete next action — skill, command, or specific decision>.

**Your input needed on:** <specific question at the next fork>.
```

### Mode differences inside Interactive

- **Progressive emit** (default in Interactive): sections emit after their generating phase. Each fork gives the user a chance to redirect.
- **One-shot**: full document emits at the end, no fork pauses. Use only when the user explicitly asks for a deliverable without mid-session involvement.

### Length budgets

| Problem size | Total words |
|---|---|
| Small (No-brainer, Apples & Oranges) | 300-600 |
| Medium (Big Choice) | 600-1,500 |
| Large (Hard Choice, Complex domain) | 1,500-3,000 |

Above 3,000 words, the brainstorm is too large — re-scope to a sub-problem.

### Formatting conventions

- Tables for matrices, ranked lists, scoring
- Code blocks for ASCII diagrams (trees, iceberg levels)
- Bulleted lists for assumptions, blind spots, options
- Backticks on first reference for framework names (e.g., `Six Thinking Hats`) and skill names (e.g., `build-skills`)
- `file:line` for code references

## Voice rules (both modes)

| Do | Don't |
|---|---|
| Lead sections / responses with the conclusion | Bury conclusions in paragraph 4 |
| Cite evidence per claim | "It seems like…" / "I think…" |
| Flag confidence where low | Uniform confidence across all claims |
| Name the next step concretely | "Consider next steps" |
| End with an explicit question (Interactive) or a verification check (Solo) | "Let me know what you think" |
| Use tables for what's a table | Prose where structure would be cleaner |

### Forbidden phrases (shared across the pack's review-related skills)

- "Thanks for the great discussion"
- "Hope this helps"
- "Please feel free to"
- "You're absolutely right" (even when they are)

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Solo output missing first-sentence verdict | Rewrite. Verdict first, always. |
| Solo output missing verification check | Add it. Unwritten = skipped. |
| Interactive output with sections out of order | Re-order. Minto skim depends on it. |
| Interactive output missing Assumptions or Blind spots | Both required. They catch different failure modes. |
| Interactive "Recommended next step" that says "consider X" | Concrete only — a skill, a command, a decision fork. |
| Output that narrates the thinking process instead of producing the artifact | Move the trace internal. The output is the artifact, not the trace. |
