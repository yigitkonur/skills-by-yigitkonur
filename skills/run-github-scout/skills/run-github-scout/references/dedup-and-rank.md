# Dedup and Rank — The Four-Stage Gate

Turn raw search results into a shortlist the user can act on.

This is a **four-stage gate**. Each stage has a required output. Stage
2 (Classify) is the hard gate before any deepen — without it, the
agent has no basis for choosing the top 5 to read in depth.

## Stage 1 — Dedup

**Required output:** deduplicated `owner/repo` list.

Dedup by `owner/repo` first. Drop forks unless the fork is the actual
project you want.

When merging multiple search calls, the canonical pattern is:

```bash
{
  gh search repos 'query one' --limit 20 --sort=stars --json fullName --jq '.[].fullName';
  gh search repos 'query two' --limit 20 --sort=stars --json fullName --jq '.[].fullName';
} | sort -u
```

## Stage 2 — Classify (REQUIRED GATE)

**Required output:** classify table in this exact shape:

```markdown
| Repo | Class | Reason | Signals |
|---|---|---|---|
| owner/repo1 | relevant | Direct match for X | 4.2k⭐, pushed 2026-04, MIT |
| owner/repo2 | maybe | Adjacent — wrapper, not engine | 800⭐, active |
| owner/repo3 | off-topic | Tutorial repo, not implementation | — |
```

**Every candidate from Stage 1 appears in this table** — relevant,
maybe, or off-topic. No candidate is silently dropped without
appearing in the off-topic class.

The three classes:

| Class | Meaning | What to do downstream |
|---|---|---|
| Relevant | Clearly matches the job to be done | Eligible for top-5 deepen |
| Maybe relevant | Adjacent or promising but still uncertain | Light README intro check before promotion or demotion |
| Off-topic | Wrong category, template, abandoned, or obvious mismatch | Drop; the mismatch reason informs refinement |

Off-topic repos teach refinement. Their reasons surface naming
clusters and category boundaries. Read them before discarding.

**This stage is the gate.** No README reads, no API calls beyond bare
search, no deep evaluation runs until the classify table exists.
Skipping the table forces guessing the top 5 from a 50-row search
dump — that is the most common derailment in this skill (see
`discipline.md` §8).

## Stage 3 — Rank

**Required output:** ranked Relevant set.

Rank by user fit first, then by lightweight quality signals.

Recommended order of importance:

1. fit to the user's actual need
2. evidence from description, topics, or README intro
3. maintenance signals (pushed date, archived status, releases,
   obvious activity)
4. stars as a popularity proxy, not the sole verdict

The Maybe set is ranked separately after a quick README check. Some
Maybes promote to Relevant; the rest stay as "Worth a look."

## Stage 4 — Present

**Required output:** shortlist in default markdown shape.

```markdown
## Best fits
- owner/repo — why it matches

## Worth a look
- owner/repo — what is promising, what is uncertain

## Ruled out
- owner/repo — why it does not fit
```

Recommended supplementary table:

```markdown
| Repo | Fit | Evidence | Signals | Caveat / unknown |
|---|---|---|---|---|
```

Be explicit about uncertainty. If the category is broad or the search
was thin, say so directly. A good shortlist can still be useful
without pretending the field is fully exhausted.

## Stages 1-4 together

```
Stage 1 — Dedup       → deduplicated owner/repo list
Stage 2 — Classify    → typed table covering every candidate (GATE)
Stage 3 — Rank        → ranked Relevant set (+ Maybe after quick check)
Stage 4 — Present     → shortlist in default markdown shape
```

The gate at Stage 2 prevents the most common derailment in this
skill. Read `discipline.md` §8 for the reasoning.
