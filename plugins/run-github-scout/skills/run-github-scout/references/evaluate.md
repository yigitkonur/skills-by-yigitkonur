# Evaluation Methodology

Default evaluation should stay lightweight and repo-fit focused.

## Default path: light repo signals

Use these signals first:

| Signal | What you are checking | Typical source |
|---|---|---|
| Match to the user's need | Does the repo actually solve the job? | name, description, topics, README intro |
| Popularity | Is there meaningful adoption? | stars |
| Freshness | Is the project still active? | pushed date, recent commits |
| Maintenance basics | Archived, licensed, released, docs present? | repo metadata, README, releases |
| Cheap quality signals | Tests or CI visible without deep digging? | root files, workflows, README |

Use labels like **strong fit**, **plausible fit**, and **stretch** by
default. Do not force every repo into a fake 100-point score.

## Before deepening — the classify gate

Confirm the classify table from `dedup-and-rank.md` Stage 2 exists
**before** any README read or API call beyond bare search. The table
is mandatory: without it, deep evaluation has no basis for choosing
the top 5.

The agent that skips the classify gate ends up reading READMEs for
candidates that should have been off-topic — which is the single most
expensive derailment in this skill. See `discipline.md` §8.

## When to deepen

Deepen only when at least one is true:

- the user asked for a closer comparison
- the top repos are close and feature evidence matters
- the shortlist is promising but README-level evidence is not enough
- the user wants a reusable artifact such as a matrix or HTML report

## Hard ceiling: 5 repos for deep evaluation

"Limit deeper evaluation to the top 3-5 repos" means **maximum 5**,
not "around 5."

Going to 6+ candidates for deep evaluation requires an explicit
inline justification at the moment the deepening starts. Example:

> Promoting `owner/repo6` to deep evaluation because it surfaced a
> decision-flipping signal during classify — it was the only candidate
> with feature X.

Without that justification, stop at 5. Going to 7-10 candidates
silently is a discipline failure: the synthesis at the end will be
diluted across too many repos, none deeply understood. See
`discipline.md` §10.

## What deeper evaluation should focus on

- feature evidence tied to the user's must-haves
- implementation maturity
- docs and onboarding quality
- test and CI presence
- release quality and maintenance rhythm
- obvious maintenance risks or missing basics

When reading READMEs for the deepen step, **skip the badge zone** —
modern READMEs front-load badges, sponsor banners, and trending markers
before the first useful prose. See `evaluate-code.md` for the awk
pattern that jumps past badges.

## What not to do by default

- no author follower scoring
- no org prestige scoring
- no giant weighted rubric for **fit** or **relevance**
- no mandatory GraphQL and REST drills across the full candidate field
- no red-flag taxonomy that is detached from actual user fit

The "no weighted rubric" rule applies to **semantic fit and
relevance** — those judgments belong to the agent against the user's
must-haves. The bundled `scripts/score-repos.sh` is a separate,
allowed tool: it scores **metadata only** (archived/disabled,
freshness, license, stars bucket, language, README/CI presence) and is
useful as a cheap sort within Stage 2 classify. Never use its score
as a final ranking signal — final recommendations cite repo-fit
evidence from description, topics, README, API, or code.

## Escalation path

1. Search metadata and README intros (with the badge-zone skip)
2. Cheap repo signals (`evaluate-rest.md`)
3. Optional single-repo GraphQL evidence (`evaluate-graphql.md`)
4. Optional README, file tree, and source checks (`evaluate-code.md`)

Each step is optional. Stop at the level that answers the user's
question. The default is to stop after Step 1 unless the user
explicitly asked for deeper confidence.
