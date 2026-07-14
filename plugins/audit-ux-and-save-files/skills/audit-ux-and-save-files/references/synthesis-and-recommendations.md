# Synthesis & Recommendations (Phase 4–5)

How to turn a tree of individual usability findings into a small set of prioritized **major changes** — and where this skill stops. This is the analogue of the UI skill's fix-dispatch step, but inverted: **this skill reports; it does not fix.** No fix subagents are spawned by default.

## Phase 4 — Aggregate and find the systemic problems

After all persona subagents return:

1. **Inventory.**
   ```bash
   find ux-findings/<date> -name "*.md" -not -name README.md -not -name RECOMMENDATIONS.md | wc -l
   find ux-findings/<date> -mindepth 2 -maxdepth 2 -type d | sort   # persona × journey pairs touched
   grep -rh "^- \*\*Severity:\*\*" ux-findings/<date> | sort | uniq -c   # severity distribution
   grep -rh "^- \*\*Heuristic:\*\*" ux-findings/<date> | sort | uniq -c  # which heuristics recur
   ```
   Track counts by persona, by journey, by severity, and by heuristic.

2. **Find the systemic problems.** These are the audit's highest-value output. Two patterns dominate:
   - **Cross-persona:** the same friction appears under several `[persona]/` dirs → it's not an edge case, it's a core problem.
   - **Cross-journey / recurring-heuristic:** the same heuristic is violated across many journeys (e.g. "match real world" broken by jargon in 6 places) → one conceptual fix, many symptoms.
   Lift these to the top of the triage summary; they are what RECOMMENDATIONS.md is built around.

3. **Verify tree shape.** Every path must match `ux-findings/<date>/<persona>/<journey>/NN-<slug>.md`. Move strays before synthesizing.

4. **Report a triage summary** to the user (counts, severity breakdown, top systemic problems, worst per-persona blockers, path-to-everything). Then proceed to Phase 5 — the structured artifact.

## Phase 5 — Cluster into themes, then write RECOMMENDATIONS.md

### Theme clustering

A **theme** groups findings that share a single root cause. Cluster by whichever is dominant:
- **Broken journey step** — multiple findings pile up at one point in a flow (the value-prop on landing; the empty state after signup).
- **Recurring mental-model mismatch** — the product's concept of X doesn't match users' (what they call it, where they expect it, what they think it does).
- **One confusing concept or term** — a single piece of jargon / unlabeled affordance causing friction in many places.
- **One missing affordance** — no undo, no feedback, no back, no bulk action — felt across journeys.

Merge near-duplicate themes. A 30-finding audit usually collapses to 4–7 themes. If you have one theme per finding, you haven't synthesized — keep merging until each theme is a *change you'd make*, not a *symptom you saw*.

### Prioritize by impact × reach × confidence (not by count)

For each theme, score:
- **Impact** — worst severity in the theme (catastrophe > major > minor > cosmetic-ux). A blocked task outranks a hesitation.
- **Reach** — how many personas / how much of the core audience hits it. A mild problem hitting everyone beats a severe problem hitting one edge persona.
- **Confidence** — observed (personas visibly struggled) vs inferred (expert judgment only). Observed outranks inferred.

Order themes high → low. A `major` problem hitting 4/4 personas, observed, is your #1 even over a `catastrophe` only the rarest persona hits inferred-only. Make the ranking explicit; don't bury it.

### Write `ux-findings/<date>/RECOMMENDATIONS.md`

This is the deliverable a product lead reads to decide what to build next. Format:

```markdown
# UX Recommendations — <app> — <YY-MM-DD>

## Verdict
2–4 sentences: can the core personas accomplish their goals today? Where does the product
lose them? The single biggest opportunity.

## Personas audited
- <persona-slug> — <identity + goal> — overall: <succeeds / struggles / abandons>
- ...

## Recommended changes (priority order)

### 1. <Major change, stated as a direction>  ·  Impact: <sev> · Reach: <N/M personas> · Confidence: <observed/inferred>
**Problem:** one line — the root cause, not a symptom list.
**Who it affects:** <personas> on <journeys>.
**Evidence:** ux-findings/<date>/<persona>/<journey>/NN-slug.md, …  (the findings this rolls up)
**Recommended change:** the *direction and shape* — "Lead the hero with the outcome in one
sentence + a 5-second demo; move the feature grid below the fold." NOT "set font-size to 24px."
**Expected win:** the behavioural/business outcome — "first-time users understand the value in
<10s; fewer bounce before signup."

### 2. ...
```

Rules for the recommendations:
- **A recommendation is a direction, not a pixel spec.** "Collapse the 3-step wizard into one screen with inline preview" — yes. "Change padding to 16px" — no (that's the visual skill's job). If you're specifying coordinates, you've dropped to the wrong altitude.
- **Each recommendation is a *change*, not a *restatement*.** "The onboarding is confusing (see 8 findings)" is not a recommendation. "Replace the empty post-signup dashboard with a guided first-task prompt" is.
- **Fewer, bigger moves beat many small ones.** If 8 findings collapse into "the product never says what it does," that's ONE recommendation, ranked #1 — not eight.
- **Cite the finding paths** so the reader can drill from a recommendation to the evidence.
- **Tie every recommendation to a persona goal and a business consequence.** "Helps the buyer decide faster → less top-of-funnel drop-off."

### Then stop. Report. Do not implement.

The skill's job ends with RECOMMENDATIONS.md presented to the user. **Banned:** silently editing source, spawning fix subagents, "while I'm here" changes. The audit artifact is durable on disk for whatever the team decides next.

## Optional hand-off (default OFF — only on explicit user request)

If — and only if — the user explicitly says to act on a recommendation ("go build #1", "implement the onboarding change"), THEN hand off:
- Visual / layout / token work → `audit-ui-and-save-files` (for a fix pass) or a `build-*` skill.
- Copy / IA / flow restructuring → the relevant framework `build-*` skill, or surface it as a design task.

Even then, treat it as a new, separately-scoped request. This skill does not assume permission to implement from the act of having recommended. The recommendation is the product; building it is a different decision the user owns.

## Re-auditing

A later run gets a new `<date>` directory; old audits are durable history. To measure whether shipped changes worked, re-audit the same personas/journeys and diff the RECOMMENDATIONS.md verdicts across dates.
