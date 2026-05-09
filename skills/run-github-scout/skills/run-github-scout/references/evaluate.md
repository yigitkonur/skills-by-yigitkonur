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

Use labels like **strong fit**, **plausible fit**, and **stretch** by default. Do not force every repo into a fake 100-point score.

## When to deepen

Deepen only when at least one is true:
- the user asked for a closer comparison
- the top repos are close and feature evidence matters
- the shortlist is promising but README-level evidence is not enough
- the user wants a reusable artifact such as a matrix or HTML report

Limit deeper evaluation to the top 3-5 repos.

## What deeper evaluation should focus on

- feature evidence tied to the user's must-haves
- implementation maturity
- docs and onboarding quality
- test and CI presence
- release quality and maintenance rhythm
- obvious maintenance risks or missing basics

## What not to do by default

- no author follower scoring
- no org prestige scoring
- no giant weighted rubric
- no mandatory GraphQL and REST drills across the full candidate field
- no red-flag taxonomy that is detached from actual user fit

## Escalation path

1. Search metadata and README intros
2. Cheap repo signals (`rest-unique-signals.md`)
3. Optional single-repo GraphQL evidence (`graphql-repo-deep-dive.md`)
4. Optional README, file tree, and source checks (`code-level-analysis.md`)
