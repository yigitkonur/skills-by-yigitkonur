# Generative Composition — Context + Form → Artifact

Operation: **Generative Composition** (`Op: Composition`).

Produce a finished artifact constrained by both context (what to say) AND form (how it should look). Cover letters, demand letters, RFPs, slide decks, one-pagers, sales artifacts, code features, proposals, training docs.

This is **not** Reshape (the substance does not yet exist) and **not** Sense-Making (no verdict to defend — an artifact to deliver). The thinking discipline is **constraint juggling** — fitting context into form without breaking either.

## Triggers

- "Write a…", "Draft a…", "Compose a…"
- "Build the X feature" (code composition)
- "Create the deck / one-pager / RFP / proposal"
- "Generate the cover letter / demand letter / outreach email"

## What this operation needs

- ✅ **Form examples** — at least one reference artifact (template, prior version, well-rated example)
- ✅ **Voice / tone spec** — formal? casual? technical? regulatory? marketing?
- ✅ **Factual context** — the substance the artifact must contain
- ✅ **Audience spec** — who reads this and what decision do they make from it
- ✅ **Length budget** — implicit form constraint that often goes unstated until the artifact is twice as long as needed

## Phase A — Frame

- **A1** (Cynefin): Complicated when the form is well-defined (template-driven RFP, standard cover letter); Complex when the form is novel or the context is partially unknown.
- **A2** (Op): Composition.
- **A3** (Reframe): occasionally — the user's "write me X" may be a solution statement; the actual problem may be addressable without writing X. Run Abstraction Laddering if "why are we writing this?" doesn't have a clear answer.

## Phase B — Calibrate

- **B1** (Tier): driven by **stakes of the artifact reaching its audience wrong**.
  - Low: internal note, draft for personal use
  - Medium: external doc consumed by known audience (RFP for known prospect, cover letter for known role)
  - High: regulatory submission, legal filing, public statement, board-level deck
- **B2** (Grounding) — Composition-specific:
  1. **At least one form reference** — a template, prior version, or well-rated example
  2. **Voice / tone spec** — extract from form references if not given explicitly
  3. **Factual context** — gather what the artifact must contain; resist generating before grounding
  4. **Audience + decision** — who reads this; what they do after reading

## Phase C — Compare

### C1. Outline + assumption list (NOT 3 options)

Composition rarely benefits from 3 finished drafts. The 3-option discipline lives at the *outline* level instead:

1. **Outline** — the structure (sections, headers, key beats). Validate the outline satisfies the form constraint.
2. **Assumption list** — what facts you're treating as given. If the user didn't supply them, flag explicitly. Composing on assumed facts is the most common "looked great, was wrong" failure.
3. **(Optional) 2-3 outline variants** — only when the structural choice matters (e.g., problem-first vs solution-first vs narrative deck). Most Composition tasks have one obvious outline.

If you cannot generate a defensible outline, the grounding (B2) is incomplete — go back.

### C2. Stress-test (Composition-specific — NOT the Sense-Making trio)

Three checks before writing the full artifact, then re-checked after:

- **Form-substance match** — does the outline fit the form (length, sections, conventions)? Common failures: too long for a one-pager, too short for an RFP section, missing a required form element.
- **Voice fit** — read the outline aloud (or section-by-section). Does the voice match the form examples? Voice drift is the #1 reason artifacts feel "off" without anyone being able to say why.
- **Audience appropriateness** — for the named reader, does each section help them make their decision? Sections that don't serve the reader's decision are noise — cut.

After writing the full draft, re-run all three. The artifact is *not* done until all three pass.

**Phase C exit criterion**: outline + assumption list + 3 checks done.

## Phase D — Commit

- **D1**: ship the artifact (or queue it for human review at Tier Medium / High).
- **D2**: verification check — the artifact's intended-decision actually gets made by the audience. (For pre-ship verification: a peer or the agent itself reads the artifact in the audience's role and confirms the decision is enabled.)

## Output contract

Composition produces *the artifact itself*. The output contract has two layers:

1. **The artifact** — finished, in the requested form.
2. **The provenance / assumption trace** — what the artifact was based on, what assumptions were made.

```
[The artifact, in its target form — letter, deck slides, RFP section, code feature]

---

Provenance:
- Sourced from: <files / context provided>
- Assumptions made: <facts assumed but not verified>
- Form references used: <templates / prior versions cited>

Pre-ship checklist:
- Form-substance match: ✓ / ✗
- Voice fit: ✓ / ✗  
- Audience appropriateness: ✓ / ✗
```

## When Composition has a sub-operation

Many Composition tasks embed Iterative Self-Verification:
- "Build me a feature" (Composition outer) → "make it pass tests" (Self-Verification inner)
- "Write the proposal" (Composition outer) → "extract the prospect's stated requirements first" (Extraction inner)

Re-classify when the inner operation begins. The opening contract may be re-emitted for the inner phase.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Generating before grounding ("let me start drafting…") | Outline + assumption list FIRST. Drafting before outline is how artifacts ship with wrong substance under right voice. |
| Form-substance mismatch (right facts, wrong audience tone) | Voice drift is invisible to the writer, obvious to the reader. Read each section aloud or have a peer scan it. |
| Burying the assumption list (or omitting it) | Assumptions are *part of the artifact*. Without them, the receiver can't sanity-check the substance. |
| Treating Composition like Sense-Making (3 finished drafts) | 3 drafts is wasteful. Generate at the outline level, then commit to one. |
| Length creep — the artifact ends up 2-3× the target length | Length budget is a form constraint. If you're over, cut sections that don't serve the audience's decision. |
| Skipping pre-ship checklist on Tier Medium/High | The 3 checks take 2 minutes. Misshipped Tier-High artifacts cost reputation. |
| "While here" scope creep ("I also added a section on X") | Scope was defined at A1. New sections need to earn their place against the audience's decision. |
