# Question design — the scored, multi-round alignment method

This is the Phase-1 playbook for `run-aligned-delivery`. The goal: surface every
fork that is genuinely the human's to decide, present each so well that they
choose correctly in seconds, and converge a large design across a handful of
rounds. Use your environment's structured multi-choice question tool (e.g.
`AskUserQuestion`).

## What earns a question (ask vs decide)

Ask the human ONLY for **user-only unknowns**:
- a preference with no objectively-right answer (tone, naming scheme, which of two sound architectures),
- a risk/effort tolerance (purity vs speed; big-bang vs incremental),
- a constraint only they hold (budget, a credential, a deadline, a vendor mandate),
- an irreversible or outward-facing call (data migration, a public contract, a deploy).

Decide everything else yourself and state it: anything answerable from the code,
the docs, a quick research pass, or a sensible convention. For low-stakes
auto-decisions, name them in passing ("I'm defaulting X to Y — say the word to
change") rather than spending a question card. **A question the agent could have
answered is a wasted question.**

## The option scoring rubric

Every option in every question carries a **score out of 100** and a one-line
trade-off, and the **recommended option comes first**, labeled "(Recommended)".

Score each option against (weight to the situation):
- **Fit** — how well it meets the actual goal/requirements.
- **Risk / blast radius** — how badly it bites if wrong; reversibility.
- **Cost** — effort, money, latency, operational burden.
- **Maintainability / longevity** — does it age well; lock-in.

Then **name the catch**: every option states its downside, not just its upside.
A score with no catch is a sales pitch — the human can't trust it. Example option
description: *"Score 84/100. Fastest path, matches the existing toolchain; but
loses per-account isolation — mitigate with strict module boundaries."*

If you genuinely recommend one option, make it first and say "(Recommended)". If
it's a real toss-up, say so and score them close — don't fake a winner.

## Categorize the decision space

For a large initiative, group the forks into categories so the human sees the
shape and you don't miss a dimension. Typical categories: runtime/toolchain,
architecture/topology, data/storage, security/secrets, observability, testing,
deploy/CI, repo/migration mechanics, API/contract, per-component specifics,
sequencing/priorities. Up to ~20 categories for a sprawling initiative — fewer is
fine. Announce the categories up front so the human knows the map.

## Batching within tool limits

`AskUserQuestion` (and most structured-choice tools) cap a card at **4 questions,
4 options each**. Work with that, don't fight it:
- **Group each card by theme** (one category, or closely related forks).
- Surface the **top-scored options** (≤4); "Other" lets the human write in anything
  you didn't list — so a fork with more than 4 viable options still works (list the
  best 4, scored).
- Keep an internal tally of the categories so successive cards cover the space
  without repeats.
- A 12-char header per question, a clear question ending in "?", scores + catch in
  each option description, recommendation first.

## The adaptation budget: up to ~10 rounds

Treat **~10 rounds as the default adaptation budget** — a ceiling, not a target.
Small initiatives converge in 2-3 rounds; a sprawling modernization may genuinely
use ten-plus. The number signals "I've budgeted for depth; I'll stop when the
design is locked, not when I hit a count."

**Adaptation is the point, not the count.** After each batch:
1. Record the answers as locked decisions.
2. **Re-plan the remaining questions** against them. An answer often makes a
   queued question obsolete, or splits one into two, or changes its options' scores.
3. If an answer **pivots the architecture** (e.g. "actually, put it all on platform
   X"), STOP the question flow, return to Phase 0: re-frame, run researchers on the
   new constraint to get current ground truth, and **re-score the downstream
   questions** before resuming. Never ask a question whose options were computed
   against the old design.

This adaptive re-planning — questions that bend to prior answers and to fresh
research — is what makes the rounds feel like collaboration instead of a form.

## Sequencing the rounds

Front-load the **load-bearing, hardest-to-reverse** decisions (runtime, core
architecture, the data model, the migration strategy) — they unblock or reshape
the most downstream questions. Defer cosmetic and easily-reversible choices to
later rounds (or auto-decide them). When a single answer would invalidate many
queued questions, ask it first.

## When research belongs mid-questioning

If a fork depends on current external truth (a platform's capabilities, a library's
state, a vendor limit) and you can't answer it from training, **run researchers
before** presenting that card — so the options and scores reflect reality, not a
guess. It's legitimate to pause the rounds, research, then return with corrected,
re-scored options. Cite what you found when you present them.

## Anti-patterns

- Asking what you could discover (wasted question; erodes trust).
- Options without scores or without their catch (the human can't choose well).
- A "recommended" option that isn't actually best (dishonest scoring).
- Asking 20 questions in one undifferentiated dump with no categories.
- Ignoring an answer that pivoted the design and continuing with stale downstream
  questions.
- Padding to hit a round count, or stopping before the load-bearing forks are locked.

## Exit

The phase is done when **every load-bearing fork has a locked answer** — not when
you hit a round number. Summarize the locked decisions and carry them verbatim into
the spec corpus (Phase 2). Then, and only then, build.
