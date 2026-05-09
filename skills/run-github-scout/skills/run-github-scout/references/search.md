# Search Methodology

Adaptive repo discovery is a short loop: search broadly, filter
internally, refine once, then stop when the shortlist stabilizes.

For the underlying mental model (verify-first, star thresholds, OR
traps, classify-before-deepen), read `discipline.md` first.

## Verify-first

If the user named a specific repo, project, or tool, the **first**
call is to verify what that thing is. Not to search for alternatives.
Pattern:

```bash
gh search repos 'NAME' --limit 5 --sort=stars \
  --json fullName,description,stargazersCount,updatedAt \
  --jq '.[] | [.fullName, (.stargazersCount|tostring), (.updatedAt[:10]), (.description // "" | .[:80])] | @tsv'
```

If the result reveals the named thing is unrelated to what the user is
asking for, surface that mismatch back to the user before continuing.
See `discipline.md` §2 for the canonical example (the "clink"
derailment).

Skip this step only when the user named no specific thing.

## Default loop

1. Restate the need in one sentence.
2. Choose 3-6 first-pass angles.
3. Run short, broad searches.
4. Classify results into a typed Relevant / Maybe / Off-topic table.
5. Extract better terms from the relevant and maybe-relevant set.
6. Run one refinement pass only where the first pass was thin or
   noisy.
7. Stop when new results mostly repeat known repos.

## First-pass angles

| Angle | When to use it | Example query |
|---|---|---|
| Direct phrasing | Always | `gh search repos 'notion alternative fork:false archived:false' --limit 20 --sort=stars` |
| Broader category | Always | `gh search repos 'self-hosted wiki fork:false archived:false' --limit 20 --sort=stars` |
| Known examples | When the user names tools or the category has obvious leaders | `gh search repos 'outline OR affine fork:false archived:false' --limit 20 --sort=stars` |
| Unexpected naming | When repo names may not match user wording | `gh search repos 'block editor collaborative docs fork:false archived:false' --limit 20 --sort=stars` |
| Constraint-specific | Only if a hard constraint matters | `gh search repos 'self-hosted notes language:TypeScript fork:false archived:false' --limit 20 --sort=stars` |
| Curated/meta | When you need landscape discovery, not final ranking | `gh search repos 'awesome self-hosted notes fork:false archived:false' --limit 20 --sort=stars` |

Keep the first pass intentionally small. Four good angles beats twenty
padded ones.

**Pick a star threshold per ecosystem maturity** before running the
first pass. Young niches (AI agents, MCP bridges, agent orchestrators,
recent vibe-coding tools) typically need no threshold — quality repos
exist below 100⭐. Mature ecosystems (web frameworks, classic CLIs)
need `stars:>500`+ to filter noise. See `discipline.md` §3 for the full
matrix. Default: **start without a threshold**; add one only if the
first pass is materially noisy.

**Avoid in first-pass discovery:**

- `topic:X` qualifiers — return spam in trending categories
  (`discipline.md` §5).
- `OR` between bare multi-word terms (`claude code OR codex agents`) —
  parses ambiguously (`discipline.md` §4 Class C).
- `in:readme` — high false-positive rate (`discipline.md` §6).

## Empty-result recovery

When `gh search repos` returns 0 rows, do **not** fire another search
immediately. Diagnose:

| Symptom | Likely cause | Recovery |
|---|---|---|
| 0 results, 4+ technical tokens AND-ed | Over-constrained | Drop the most specific token; re-run |
| 0 results, has `topic:X` plus free text | `topic:` filtered too aggressively | Drop the topic qualifier |
| 0 results, has `stars:>N` plus niche domain | Threshold above the niche's ceiling | Drop the threshold |
| 0 results, OR query with bare multi-word | Class C OR parsing ambiguity | Quote phrases or split into two searches |
| 0 results across 3 reasonable retries | Combination genuinely has no matches | Surface the gap; consider `web-augment.md` |

Empty results are diagnostic information. Read them before re-firing.

## Internal filtering rules

Use search results as candidate generation, then **classify into a
typed table** (this is a required gate before any deepen — see
`dedup-and-rank.md` Stage 2 and `discipline.md` §8):

| Class | Meaning | What to do |
|---|---|---|
| Relevant | Clearly matches the job to be done | Keep for shortlist and maybe deeper inspection |
| Maybe relevant | Adjacent or promising but still uncertain | Read the README intro or repo topics |
| Off-topic | Wrong category, template, abandoned, or obvious mismatch | Drop and use the mismatch to improve queries |

Prioritize these signals before reading more:

- repo name and description
- stars and recent activity
- archived status
- license
- topics if easy to inspect

## Refinement patterns

Good refinement uses words you observed in the candidate set:

- rename the problem using repo vocabulary
- search the parent category, then filter harder
- add one hard constraint that separates the good from the noisy
- search known alternatives discovered in the first pass

Bad refinement:

- piling on extra words because the first pass felt too broad
- re-running the same search with tiny wording changes
- launching multiple waves before classifying what you already have
- AND-ing 3+ technical noun-phrase tokens together (routinely returns
  empty results — see Empty-result recovery)

## Stop rules

Stop after the first pass when the shortlist is already strong.

Stop after the refinement pass when any of these is true:

- new searches mostly repeat the same repos
- remaining gaps are about uncertainty, not discovery
- the user can already make a reasonable choice from the shortlist
