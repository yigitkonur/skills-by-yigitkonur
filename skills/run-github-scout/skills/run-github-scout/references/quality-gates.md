# Quality Gates

Explicit pass-or-stop checkpoints for repo scouting. Each gate has a
**required output** the agent must produce before progressing. Soft
"decision tables" got skipped under load in real sessions; these
gates do not.

## Gate 0 — Verify-first (when the user named a thing)

**Trigger:** the user mentioned a specific repo, project, or tool by
name (e.g., "alternatives to `clink`", "find similar to
`agent-bridge`").

**Required output:** confirmed category and metadata for the named
thing — typically the result of one `gh search repos 'NAME' --limit 5
--sort=stars` plus optionally one `gh api repos/OWNER/REPO`.

**Stop / proceed rule:**

| Result | Action |
|---|---|
| Named thing matches the category the user expects | Proceed to first-pass search |
| Named thing does not match (mismatched category, archived, unrelated) | Surface the mismatch to the user before any further search |
| Multiple plausible repos share the name | One targeted `gh api repos/OWNER/REPO` on the most likely; confirm |

Skipping this gate is the #1 derailment in this skill. See
`discipline.md` §2 for the canonical "clink" example.

## Gate 1 — After interpreting the request

**Required output:** one-sentence search contract (problem, must-haves,
exclusions, ecosystem, maturity expectations).

**Stop / proceed rule:**

| Signal | Action |
|---|---|
| Problem, constraints, and exclusions are clear enough to search | Start discovery |
| One missing answer would materially change search direction | Ask 1-2 targeted questions, then continue |
| User already named examples or anti-examples | Use them as seed terms (after the verify-first gate) |

## Gate 2 — After the first pass

**Required output:** the classify table from `dedup-and-rank.md` Stage
2:

```markdown
| Repo | Class | Reason | Signals |
|---|---|---|---|
```

Every candidate from the first pass appears in this table — relevant,
maybe, or off-topic. **No deepen until this table exists.**

**Stop / proceed rule:**

| Result shape | Verdict | Next move |
|---|---|---|
| 3-8 clearly relevant repos, or a clear top cluster | Strong | Shortlist now, or one narrow refinement if a known gap remains |
| 1-2 relevant repos plus several maybes | Thin | Run one refinement pass using vocabulary from relevant + maybe set |
| Mostly off-topic results | Noisy | Broaden to category term or switch to augmented search for naming help |
| Repos look adjacent but not exact | Ambiguous | Read README intros for the best 3-5 and extract better terms before refining |

## Gate 3 — After the refinement pass

**Required output:** updated classify table reflecting refinement
results.

**Stop / proceed rule:**

| Signal | Action |
|---|---|
| New results mostly repeat known repos | Stop and synthesize |
| Field is still thin but top few are plausible | Deliver shortlist with explicit uncertainty |
| Field is still noisy because naming is fuzzy | Use optional web/MCP augmentation per `web-augment.md`, then stop after one more targeted sweep |
| User explicitly wants higher confidence | Deepen — but only on top 3-5 (hard ceiling: 5) |

## Gate 4 — Before deepening

**Required output:** classify table exists AND named top-5 candidates
with reasoning ("these 5 because X").

**Stop / proceed rule:** deepen only when at least one is true:

- the user asked for deeper comparison
- the top options are close and need feature evidence
- the shortlist would materially improve with README, test, or
  release verification
- the user asked for export, report, or a reusable artifact

**Hard ceiling: 5 repos for deep evaluation.** Going to 6+ requires an
explicit inline justification at the moment the deepening starts. See
`evaluate.md` and `discipline.md` §10.

## Gate 5 — Stop conditions

Stop when any of these is true:

- the shortlist answers the user's need well enough to act
- new searches are mostly duplicates
- remaining gaps are better stated as caveats than solved by more
  searching
- the user is satisfied with the markdown result
- 5 repos have been deeply evaluated (the hard ceiling)

## Gate summary

```
Gate 0 — Verify-first (if user named a thing)        → confirmed metadata
Gate 1 — Interpreted request                          → search contract
Gate 2 — After first pass                             → classify table (REQUIRED)
Gate 3 — After refinement                             → updated classify table
Gate 4 — Before deepen                                → top-5 with reasoning
Gate 5 — Stop conditions                              → shortlist or completion
```

Each gate's required output is explicit. Skipping a gate is a
discipline failure and surfaces in the shortlist as missing evidence
or guessed top-5 — both of which the user notices immediately.
