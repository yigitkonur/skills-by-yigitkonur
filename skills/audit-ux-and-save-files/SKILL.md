---
name: audit-ux-and-save-files
description: Use skill if you are auditing a running app's usability from real personas walking their journeys, saving per-issue findings to a dated persona/journey tree and recommending major changes, not fixes.
---

# Audit UX and Save Files

Disciplined **usability** evaluation of a running app, from the perspective of the people who actually use it — not a frontend pass. The deliverable is a durable on-disk artifact of usability problems and a prioritized list of the **major changes** they imply.

Dispatch parallel audit subagents that each **embody one persona** plus a UX expert's eye, drive the `run-agent-browser` skill through that persona's core **journeys**, capture screenshots at the moments friction appears, and write one markdown finding per real usability problem into a **dated, persona-scoped, journey-scoped tree** under `ux-findings/`. When the audit returns, cluster findings into UX themes, then synthesize a prioritized **recommendations** report. This skill **reports; it does not fix.**

This is not "make it look nicer." The questions are: *Can this persona accomplish their goal? Where do they hesitate, misread, backtrack, or give up? What is confusing, redundant, or unnecessary? What one change would help most?* Findings are judged by task impact and business consequence, not by pixels.

The skill owns three things: where files live, how usability findings are written (persona · journey · heuristic · severity · behavioral + business impact · recommended major change), and how the audit is synthesized into recommendations. It does NOT own visual/CSS correctness (that is `audit-ui-and-save-files`) and does NOT implement the recommendations.

## When to Use

Trigger on phrases and contexts like:

- *"audit the UX"*, *"run a usability audit"*, *"is this actually usable?"*
- *"where do users get confused / stuck / drop off?"*, *"find the friction"*
- *"evaluate it as different personas"*, *"walk a first-time user / power user / buyer through it"*
- *"do a heuristic evaluation of the app"*, *"Nielsen-audit the flows"*
- *"what's confusing here, what should we simplify or remove?"*
- *"the feature works — but is it understandable? write up the usability problems for me"*
- *"screenshot the journeys, find the usability issues, and recommend the big changes"*

Do NOT use this skill for:

- *Visual / CSS / layout / responsive bugs.* "The card overflows at 375px", "contrast is weak", "the grid breaks" → **`audit-ui-and-save-files`**. This skill ignores pixels except where they cause a *comprehension or task* failure.
- *Implementing changes.* This skill stops at the recommendations report. If the user wants the changes built, that is a separate, explicitly-requested pass (and likely a different skill).
- *Single-flow inline check.* If the user knows the one flow and just wants a quick read, drive `run-agent-browser` inline. This skill's overhead pays back at ≥2 personas or ≥3 journeys, or when the problem set is unknown.
- *Accessibility-only audits.* WCAG/AT conformance needs specialized tooling. (A persona *with a disability* is in scope as a persona; full a11y conformance is not.)
- *Quantitative testing.* Analytics, A/B tests, SUS-at-scale measure *what* happens; this skill is expert + persona-walkthrough and reveals *why*.

## Headline Capabilities (read this section)

Three commitments separate this from a generic "review the UI" run. All three are non-negotiable.

### 1. The lens is persona + journey + heuristic — never pixels

Every finding answers: **which persona**, on **which journey**, hit **which usability problem**, violating **which heuristic**, with **what behavioral and business consequence**, and **what major change** fixes it. A finding with no persona and no task impact is not a UX finding — it is either a visual nit (wrong skill) or an opinion (cut it). The full finding template, the Nielsen-10 heuristic catalog with common violations, the persona/journey rubrics, and the severity scale all live in `references/ux-finding-format.md` — plant it verbatim in Phase 2.

### 2. Findings live in a dated, persona-scoped, journey-scoped tree

```
ux-findings/[YY-MM-DD]/[persona]/[journey]/NN-short-slug.md
```

Concrete (a run on 2026-05-28, the first-time user, on the onboarding journey, second issue found):

```
ux-findings/26-05-28/first-time-user/onboarding/02-value-prop-unclear-on-landing.md
```

Each segment is mandatory. Full grammar, persona/journey slug rubrics, and screenshot convention in "Output Tree" below and `references/ux-finding-format.md`.

### 3. The audit ends in RECOMMENDATIONS, not fixes

After the audit subagents return, cluster findings into UX **themes** and write `ux-findings/[YY-MM-DD]/RECOMMENDATIONS.md` — a prioritized list of the **major changes** (by severity × persona-reach), each with the personas it helps, the journeys it unblocks, and the business rationale. Then **stop and report.** Do NOT silently implement anything. If — and only if — the user explicitly asks to act, hand off per the routing note in `references/synthesis-and-recommendations.md`. Read that file before clustering.

## The Workflow (Five Phases)

### Phase 1 — Frame the personas and journeys (the most important phase)

A UX audit is only as good as its personas. Before dispatching anything, establish:

1. **A dev or prod server is reachable.** `curl -s -o /dev/null -w "%{http_code}" <url>` must return 200. Boot the dev server in the background and wait for "Ready" if needed. Never audit a server that is not up.
2. **The `run-agent-browser` skill is available.** Check the available-skills list; if absent, surface it and stop — there is no fallback that produces real screenshots.
3. **Personas are defined and grounded in the product.** Each persona has: a name slug, a one-line identity, their **goal** ("what they came to do"), their **expertise** (first-time / returning / power / non-technical), and their **context** (mobile-on-the-go, evaluating-to-buy, daily-driver). Derive personas from the product's real audience — README, landing copy, pricing tiers, docs, the user. Do NOT invent personas the product was never built for. 2–5 personas is typical. The selection rubric is in `references/ux-finding-format.md`.
4. **Each persona's journeys are listed.** A journey is a goal-directed task: `onboarding`, `first-core-task`, `find-and-evaluate`, `recover-from-error`, `upgrade`, `daily-workflow`. Write tasks as **goals in the persona's own words**, never as click-by-click steps with product jargon — discoverability is half of what you're testing.
5. **The audit date is fixed.** Compute `YY-MM-DD` once and pin it for every subagent. Same audit = same date even across midnight.

If personas/journeys aren't obvious, ask the user once. Guessing personas wrong invalidates the whole audit.

### Phase 2 — Plant the format spec

Write `ux-findings/README.md` in the project root before dispatching. Copy it **verbatim** from `references/ux-finding-format.md` — every subagent reads this file as the single format authority (finding template, Nielsen-10 catalog, persona/journey rubrics, severity scale, path grammar). Do not paraphrase; subagents are matched against this exact file.

Also create `ux-findings/[YY-MM-DD]/screenshots/` as the known flat PNG location (per-persona prefix avoids collisions).

### Phase 3 — Dispatch one audit subagent per persona

**Partition by `[persona]`.** Each subagent owns one persona, walks that persona's listed journeys, and writes only under `ux-findings/[YY-MM-DD]/<persona>/**`. A persona with many journeys can be split, but the default unit is one-subagent-one-persona — because the subagent must *stay in character* for a coherent walkthrough.

**The subagent IS the persona.** Use the prompt template in `references/persona-subagent-template.md` (mission-protocol shape). It instructs the subagent to: adopt the persona's goal and expertise; attempt each journey as that persona would; **think aloud** (narrate confusion, hesitation, wrong guesses); **observe silently** — never use insider knowledge to rescue itself past a confusing point (the struggle *is* the finding); test the **error / empty / edge** paths, not just the happy path; screenshot the exact moment of friction; and write findings as a UX expert — what the persona *did and felt*, the heuristic violated, the business impact, the recommended major change. Fill the slots and dispatch. Do not compress the template.

**DO NOT fully parallelize browser-driven subagents.** `run-agent-browser` shares a Chrome daemon with a SingletonLock; firing many at once makes them steal each other's sessions and return empty. **Stagger** (2 at a time, wait for a batch to return) or run **sequential single-instance**. See `references/footguns.md` §1.

### Phase 4 — Aggregate and find the systemic problems

When subagents return:

1. **Inventory:**
   ```bash
   find ux-findings/<YY-MM-DD> -name "*.md" -not -name "README.md" -not -name "RECOMMENDATIONS.md" | wc -l
   find ux-findings/<YY-MM-DD> -mindepth 2 -maxdepth 2 -type d | sort   # personas × journeys touched
   ```
   Track counts by persona, by journey, by severity, and by heuristic.
2. **Surface systemic problems** — the highest-value patterns. The same confusion hitting **multiple personas**, or the same heuristic violated across **multiple journeys**, is a structural problem worth one big change, not many small ones. Lift these to the top.
3. **Verify tree shape.** Every path must match `ux-findings/<date>/<persona>/<journey>/NN-<slug>.md`. Move any stray file before continuing.
4. **Report a triage summary**: counts, severity breakdown, the top systemic problems, the worst per-persona blockers, and a path-to-everything. Do NOT start writing recommendations yet inline — that is Phase 5's structured artifact.

### Phase 5 — Synthesize recommendations (report-only)

Follow `references/synthesis-and-recommendations.md`; the summary:

1. **Cluster findings into UX themes.** A theme groups findings that share a root cause — a broken journey step, a recurring mental-model mismatch, one confusing concept, or one missing feedback affordance. Merge near-duplicates.
2. **Prioritize by severity × reach**, not by count. A severity-4 blocker hitting the primary persona outranks ten cosmetic-UX nits. Use the impact/reach/confidence rubric in the reference.
3. **Write `ux-findings/[YY-MM-DD]/RECOMMENDATIONS.md`** — for each recommended **major change**: the problem (one line), the personas + journeys it affects, the supporting finding paths, the recommended change (a *direction*, not a pixel spec — "collapse the 3-step wizard into one screen with inline preview", "lead with the outcome, not the feature list"), and the expected behavioral/business win. Order by priority.
4. **Report and stop.** Present the recommendations. Do NOT implement. Only on an explicit user "go" do you hand off (routing in the reference) — and even then, this skill's job was the audit and the recommendations.

## Output Tree

```
ux-findings/
├── README.md                                   (format spec — copy verbatim from references/ux-finding-format.md)
└── [YY-MM-DD]/                                  (audit date, pinned once at Phase 1)
    ├── screenshots/                             (flat per-date dir; per-persona prefix avoids collisions)
    │   ├── firsttime-onboarding-02-value-prop.png
    │   └── power-daily-05-no-bulk-actions.png
    ├── RECOMMENDATIONS.md                        (Phase 5 synthesis — prioritized major changes)
    └── [persona]/                                (WHO: first-time-user / power-user / evaluator-buyer / admin / ...)
        └── [journey]/                            (WHAT they're doing: onboarding / first-core-task / upgrade / recover-from-error / ...)
            ├── 01-<short-slug>.md                (one usability problem per file; NN preserves discovery order)
            └── 02-<short-slug>.md
```

**`[persona]`** — kebab-case slug for *who* is using it, grounded in the product's real audience. Rubric (identity · goal · expertise · context) in `references/ux-finding-format.md`. Examples: `first-time-user`, `returning-user`, `power-user`, `evaluator-buyer`, `admin`, `mobile-commuter`.

**`[journey]`** — kebab-case slug for the *goal-directed task* being attempted. Examples: `onboarding`, `first-core-task`, `find-and-evaluate`, `daily-workflow`, `upgrade`, `recover-from-error`, `share-or-invite`. A journey is a goal, not a page.

**`NN-short-slug.md`** — zero-padded ordinal within `[persona]/[journey]/`, then a 3–6-word kebab slug naming the *usability problem* (not the page). Examples: `02-value-prop-unclear-on-landing.md`, `05-no-way-to-undo-bulk-delete.md`, `03-jargon-blocks-first-task.md`.

Each `.md` follows the template in `references/ux-finding-format.md`.

## Severity Rubric (task-impact framed)

Non-negotiable; every finding gets one label. Severity is about **task completion and reach**, not how ugly it looks.

- **catastrophe (4)** — the persona **cannot complete a core task** or abandons (gives up, leaves, picks a competitor). The journey is blocked.
- **major (3)** — the task completes but with real cost: confusion, wrong turns, repeated errors, long delay, or a near-abandon. The persona succeeds *despite* the design.
- **minor (2)** — a hesitation or moment of doubt that resolves; the persona pauses, re-reads, then proceeds.
- **cosmetic-ux (1)** — wording/clarity nit with no task impediment (an unclear label that's still guessable).
- **(0 = not a UX problem.** Do not file. If it's purely visual, it belongs in `audit-ui-and-save-files`.)

Always annotate **reach**: how many of the audit's personas hit this. Severity × reach drives Phase 5 prioritization. The full rubric, with the persona-reaction guidance, is carried verbatim in `references/ux-finding-format.md`.

## Footguns

Catalogued with recovery protocols in `references/footguns.md`. The headline list:

1. **Fully parallel browser dispatch causes SingletonLock contention** → stagger or run sequential.
2. **Filing visual/CSS nits as UX findings** → scope bleed into `audit-ui-and-save-files`. A finding must name a *task* impact, or it's the wrong skill.
3. **Inventing personas the product wasn't built for** → personas must be grounded in the real audience; a fabricated persona produces fabricated problems.
4. **"I'd prefer X" instead of "the user is blocked by X"** → taste is not a usability finding. File behavior and consequence, not preference.
5. **Persona drift** — the subagent stops role-playing and reverts to an omniscient developer who "knows where the button is." The struggle is the data; insider rescue destroys it.
6. **Happy-path-only walks** → error, empty, and edge states are where usability dies. The DoD requires testing at least one non-happy path per journey.
7. **Findings with no screenshot** → an unscreenshotted friction claim is unverifiable; the format spec rejects it.
8. **Recommending pixel fixes** → Phase 5 recommends *directions and major changes*, not "move it 8px". Pixel work is the other skill.
9. **Recommendations that are a restatement of findings** → synthesize across findings into fewer, bigger moves; don't just relist.
10. **Implementing instead of reporting** → the skill stops at RECOMMENDATIONS.md unless the user explicitly says go.
11. **Date computed per-subagent** → findings split across two date dirs; pin the date at Phase 1.

## Reference Files

- `references/ux-finding-format.md` — verbatim contents of the `ux-findings/README.md` planted in Phase 2: the per-finding template (persona · journey · heuristic · severity · observed behavior · business impact · recommended change · screenshot), the **Nielsen-10 heuristic catalog with common violations**, the persona-selection and journey rubrics, the severity scale, the dated-tree path grammar, and the screenshot-prefix convention.
- `references/persona-subagent-template.md` — mission-protocol-shaped per-persona audit subagent prompt, with slots for `<base-url>`, `<persona>` (identity/goal/expertise/context), `<journeys>`, `<owned-paths>`, `<screenshot-prefix>`, `<floor-count>`, `<dispatch-mode>`, `<audit-date>`. Embeds stay-in-character, think-aloud, observe-silently, test-error-paths, report-don't-fix.
- `references/synthesis-and-recommendations.md` — the Phase 4–5 playbook: theme-clustering rubric, severity × reach prioritization (impact/reach/confidence), the `RECOMMENDATIONS.md` format, what a "major change" is vs a pixel fix, and the (default-off) hand-off routing.
- `references/footguns.md` — long-form failure-mode catalogue with symptoms and recovery for each, including persona drift, scope bleed, and happy-path bias.

## A Note on Tone

The audit produces files a product lead will read before deciding what to build next. Subagents describe what the persona **did and experienced** — *"the first-time user clicked 'Skip' three times looking for an exit, then closed the tab without finishing setup"* — not what they assume the user wants to hear, and not *"the onboarding is bad."* Observed behavior + consequence + heuristic + a concrete bigger-picture recommendation. The goal is to make every usability problem visible in one pass, ranked by who it blocks and how badly, then to name the handful of changes that would most improve whether the product is actually *useful.* That's the deliverable.
