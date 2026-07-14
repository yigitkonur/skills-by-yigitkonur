# ux-findings/README.md — Format Spec

> This file is the **verbatim contents** to write to `<project>/ux-findings/README.md` during Phase 2 of `audit-ux-and-save-files`. Every persona audit subagent reads this file as its format authority. Do not paraphrase — copy the fenced block below byte-for-byte.

---

```markdown
# UX Findings — Usability Audit

Usability problems found by walking real **personas** through their core **journeys** in the running app (driven via `/run-agent-browser`). Each problem lives in its own markdown file so they can be triaged and synthesized individually. The tree is **dated, persona-scoped, and journey-scoped** so the same app can be re-audited later without overwriting history.

This is a **usability** audit, not a visual one. A finding must name a *task* impact — confusion, hesitation, a wrong turn, an abandon, a misunderstanding. "It looks slightly off" with no task consequence is NOT a finding here (that belongs in a visual/CSS audit). The question is always: *can this persona accomplish their goal, and where do they struggle?*

## Directory layout

```
ux-findings/
  README.md                                   (this file — format spec)
  [YY-MM-DD]/                                  (one dir per audit run; computed once at run start)
    screenshots/                              (flat per-date dir; per-persona prefix avoids collisions)
      <persona-prefix>-<journey>-NN-<slug>.png
    RECOMMENDATIONS.md                         (Phase 5 synthesis — prioritized major changes)
    [persona]/                                 (WHO: first-time-user / power-user / evaluator-buyer / admin / ...)
      [journey]/                               (WHAT they attempt: onboarding / first-core-task / upgrade / ...)
        01-<short-slug>.md
        02-<short-slug>.md
```

Number issue files `01-`, `02-`, ... in discovery order within each `[persona]/[journey]` pair. Slug is 3–6 words, lowercase, hyphen-separated, naming the *problem* not the page (e.g. `02-value-prop-unclear-on-landing.md`).

### Canonical path example

```
ux-findings/26-05-28/first-time-user/onboarding/02-value-prop-unclear-on-landing.md
```

Audited 2026-05-28, persona = first-time user, journey = onboarding, second problem found for that pair.

### Choosing the persona slug (WHO)

Personas must be grounded in the product's real audience — read the landing copy, pricing tiers, docs, and ask the owner. Do NOT invent a persona the product was never built for. Each persona is defined by four things; capture them in the subagent brief:

- **Identity** — one line ("a developer evaluating the tool for their team").
- **Goal** — what they came to do ("decide if this is worth adopting").
- **Expertise** — `first-time` / `returning` / `power` / `non-technical`.
- **Context** — `evaluating-to-buy` / `daily-driver` / `mobile-on-the-go` / `admin-setup` / `in-a-hurry`.

Common slugs: `first-time-user`, `returning-user`, `power-user`, `evaluator-buyer`, `admin`, `mobile-commuter`, `non-technical-user`. 2–5 personas per audit.

### Choosing the journey slug (WHAT)

A journey is a **goal-directed task**, not a page. Write it as a goal in the persona's words, never as click-by-click steps with product jargon (discoverability is half of what you test). Common slugs: `onboarding`, `first-core-task`, `find-and-evaluate`, `daily-workflow`, `upgrade`, `recover-from-error`, `share-or-invite`, `get-help`.

## File format

Every issue file follows this exact template:

```markdown
# <Short problem title — what the user struggles with>

- **Persona:** <slug> — <one-line identity + goal>
- **Journey:** <slug> — <the goal being attempted, in the persona's words>
- **Where:** <full URL / screen / step>
- **Heuristic:** <one of Nielsen's 10 — see catalog below>
- **Severity:** catastrophe | major | minor | cosmetic-ux
- **Reach:** <how many of this audit's personas hit this — e.g. "3 of 4 personas">
- **Detected via:** /run-agent-browser

## Screenshot

![friction](../../screenshots/<filename>.png)

## What happened (observed behaviour)

What the persona DID and where they stalled — narrate the think-aloud.
"The first-time user scanned the hero for 8s, clicked 'Docs' looking for
'what is this', came back, then clicked 'Sign up' without understanding
what the product does." Behaviour and consequence, not "the page is confusing."

## Why it hurts (user + business impact)

The mental-model mismatch or friction, and its consequence: drop-off,
abandon, support ticket, eroded trust, slower time-to-value, wrong choice.
Tie it to the persona's GOAL. "A buyer who can't tell what it does in 10s
leaves — this is top-of-funnel abandonment, not a cosmetic issue."

## Recommended change (a direction, not a pixel spec)

The MAJOR change that would remove the friction. Describe intent and shape,
not coordinates: "Lead the hero with the outcome in one sentence + a 5s demo,
move the feature grid below." "Collapse the 3-step wizard into one screen
with inline preview so the value is visible before commitment."

## Confidence

observed (the persona visibly struggled) | inferred (expert judgment, not
yet seen to block a real walk). Mark inferred findings honestly.
```

## Nielsen's 10 Usability Heuristics — tag every finding with one

1. **Visibility of system status** — is the user kept informed (loading, progress, confirmation, where-am-I)? *Violations:* no feedback after an action; can't tell which step of a flow; silent failures.
2. **Match between system and the real world** — does it speak the user's language? *Violations:* jargon/abbreviations, system IDs/error codes shown to users, unnatural ordering, non-standard icons.
3. **User control and freedom** — clearly marked exits, undo, cancel, back-without-data-loss. *Violations:* no undo after destructive action; modal with no close; back wipes the form.
4. **Consistency and standards** — same word/action means the same thing; platform conventions. *Violations:* "Save" here / "Submit" there; inconsistent nav; mixed terms ("account" vs "profile").
5. **Error prevention** — design out the error (constraints, sensible defaults, confirms). *Violations:* free text where a picker fits; no confirm before permanent delete; submit allowed while incomplete.
6. **Recognition rather than recall** — show options; don't make users remember across screens. *Violations:* must remember a code from a prior page; no recents/history; labels hidden in tooltips; no summary of prior choices.
7. **Flexibility and efficiency** — works for novice AND expert (shortcuts, bulk actions, sensible defaults). *Violations:* no keyboard shortcuts; no bulk operations; forced wizard with no fast path for experts.
8. **Aesthetic and minimalist design** — every extra element competes with the essential. *Violations:* everything shown at once; many competing CTAs; dense text with no hierarchy. (This is about *cognitive* clutter, not visual taste.)
9. **Help users recognize, diagnose, recover from errors** — plain-language errors that say what + how to fix, near the field. *Violations:* "Something went wrong"; error codes; error far from the field; form clears on error.
10. **Help and documentation** — contextual, searchable, task-focused help / onboarding. *Violations:* no in-app help; no onboarding; docs require leaving the app.

If a finding spans two heuristics, pick the dominant one and mention the other in the body.

## Severity rubric (task-impact framed — non-negotiable)

- **catastrophe** — the persona **cannot complete a core task** or abandons (leaves, gives up, picks a competitor). The journey is blocked.
- **major** — the task completes but at real cost: confusion, wrong turns, repeated errors, long delay, or a near-abandon. They succeed *despite* the design.
- **minor** — a hesitation/moment of doubt that resolves; they pause, re-read, proceed.
- **cosmetic-ux** — a wording/clarity nit with no task impediment (an unclear-but-guessable label).
- *Not a UX problem (do not file): purely visual issues with no task consequence — those go to a visual/CSS audit.*

Always set **Reach** (how many personas hit it). Severity × reach drives Phase 5 prioritization: a `major` problem hitting 4/4 personas usually outranks a `catastrophe` that only one edge-persona hits.

## How to walk a journey (what the subagent does)

- **Be the persona.** Adopt their goal and expertise; pursue the goal, don't tour the UI.
- **Think aloud.** Narrate every assumption, hesitation, and wrong guess — that narration is the finding's raw material.
- **Observe silently / don't rescue yourself.** Never use insider knowledge to jump past a confusing point. If a real first-time user would be stuck, you are stuck — that's the finding.
- **Tasks as goals, not steps.** "Get the thing you came for set up" — discover the path; don't follow a script.
- **Test the unhappy paths.** Empty states, errors, wrong input, recovery, the impatient user. Usability dies off the happy path.
- **Screenshot the moment of friction**, not a tidy final state.
- **One problem per file.** If the same confusion hits several journeys, file it once at the most representative spot and note the reach.

## Screenshot prefix convention

Flat `ux-findings/[YY-MM-DD]/screenshots/`. Each persona subagent uses its own prefix to avoid collisions: `<persona-prefix>-<journey>-NN-<slug>.png` — e.g. `firsttime-onboarding-02-value-prop.png`, `power-daily-05-no-bulk-actions.png`. The bundled subagent template assigns each persona its prefix.
```

---

## Why this exact format

- **Persona × journey scoping** (not page × device) makes the synthesis trivial: "the buyer is blocked" grabs `evaluator-buyer/*/*.md`; "onboarding is broken across personas" grabs `*/onboarding/*.md`. The tree is shaped for the two questions Phase 5 asks — *who is blocked* and *which journey is broken*.
- **Heuristic tag** forces the finding through an expert lens instead of "I don't like it", and clusters recurring violations (six "match real world" violations = one jargon problem, one fix).
- **`What happened` is observed behaviour**, because a product lead trusts "the user clicked Skip three times then left" far more than "onboarding is confusing." Behaviour is evidence; adjectives are opinion.
- **`Why it hurts` ties to business impact** so the finding survives prioritization — drop-off and abandonment get fixed; "minor confusion" doesn't.
- **`Recommended change` is a direction, not a pixel spec**, because this skill recommends *what to change*, and a separate pass decides *how*. Pixel specs here would pre-empt design and rot fast.
- **`Reach` is mandatory** because severity alone mis-ranks: a mild problem hitting everyone beats a severe problem hitting no one who matters.
- **`Confidence` (observed vs inferred)** keeps the audit honest — expert inference is allowed but must be labelled, never dressed up as observed behaviour.
- **One file per problem** keeps synthesis parallelizable and lets RECOMMENDATIONS.md cite exact paths.
- **Severity is four task-framed labels**, not a 0–4 abstract scale, because "can they finish the task?" is the only question that reliably sorts UX work.
