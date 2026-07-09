# Lens design — from 50 candidates to a minimal covering set

How to turn the Phase-1 project map into the reviewer lenses for Phase 3.
The goal: **cover every meaningful failure surface with the fewest reviewers**,
where each reviewer is one coherent mental model that reads a shared file-set
once and goes deep.

## Why not just "audit the whole app" ×N

Two failure modes bound the design:

- **Too broad / too many identical lenses** → most reviewers rediscover the
  same 2–3 issues, and the empty-handed ones **fabricate** to satisfy the
  "find something" bias. Wasted spend + noise.
- **Too narrow / too many hyper-specific lenses** → most return honestly clean
  because there is nothing there, and whole surfaces get missed. Wasted spend +
  gaps.

The optimum is a **portfolio**: mostly medium-specificity lenses that each own
a distinct real surface, a few broad safety-nets only if grouping leaves a gap,
and a few deep-dives on the highest-risk seams.

## Step 1 — Brainstorm ~50 candidates from the map

Enumerate candidate lenses across these families, **instantiated to what the
project actually has** (skip families that do not apply):

- correctness / logic / render
- state · cache · store · realtime · concurrency
- **contract fidelity** — consumer vs the real producer shape (frontend vs API
  envelopes, module vs its contract). Historically the highest-yield family;
  it also resists fabrication because it diffs two concrete artifacts.
- security / trust boundaries (tokens, injection, secrets, headers)
- accessibility
- performance / bundle
- resilience / error handling / boundaries
- cross-cutting semantics — dates/timezones, number/precision formatting, money
- build / deploy / config / dependencies / supply-chain
- test quality (assertions that assert nothing, mocks hiding behavior)
- specific flows/journeys and specific high-risk components (deep-dives)

## Step 2 — Score each candidate

Rate 1–5 on four axes and combine:

`score = 0.35·Yield + 0.25·Severity-ceiling + 0.25·Orthogonality + 0.15·Groundability`

- **Yield** — odds of a real finding given what is already fixed.
- **Severity-ceiling** — worst realistic bug it would catch.
- **Orthogonality** — how much untouched surface it uniquely owns.
- **Groundability** — how hard it is to fabricate under this lens (a lens
  pointing at a concrete artifact scores high; "find design smells" scores low
  and invites noise). Weight this because it directly fights made-up findings.

Tag each **Broad / Medium / Narrow**.

## Step 3 — Group into the minimal covering set

Merge near-neighbors so each surviving lens is **one substrate + one
failure-family** a single reviewer can hold and read once. Group by **shared
files read** (a region deep-dive) OR **shared failure-mode** (one bug class
swept everywhere), whichever gives the tighter loop. Split a group only when it
is too big for one reviewer to go deep (e.g. "all pages vs their contracts" →
split by page cluster).

Drop candidates whose yield is near-zero **now** (state the reason — e.g. "i18n:
no localization in scope"). Do not fold them in to pad a group; a diluted lens
skims.

Land on the count where adding one more mostly re-reads a file another lens owns
(dup-rate climbs faster than yield) and removing one leaves a real surface
uncovered. In practice this is **~15–26** for an app-sized scope.

## Step 4 — Assign non-overlap + the shared frame

Give each lens a **primary region + forbidden-overlap set** so reviewers do not
pile onto the richest surface. Attach the shared frame to every reviewer:
full-tree target, the cumulative already-fixed/laws ledger, the
anti-fabrication rule (see `prompt-templates.md`).

## Balance heuristics

- Give the **highest-yield family (usually contract-fidelity)** more than one
  lens if the project is large — split it by module/page cluster.
- Keep **≤3 broad safety-nets**, and only if grouping genuinely left a gap;
  a good covering set usually needs zero, because targeted lenses already tile
  the tree and broad nets are the most fabrication-prone.
- Prefer **specialists nothing else covers** (dates, number formatting, money,
  test-quality, build/deps) — they are orthogonal and under-explored, so high
  marginal yield.
- Re-derive lenses **each loop** from a fresh explore; do not reuse the prior
  set verbatim, so successive waves sample different corners.
