# Search Methodology

Adaptive repo discovery is a short loop: search broadly, filter internally, refine once, then stop when the shortlist stabilizes.

## Default loop

1. Restate the need in one sentence.
2. Choose 3-6 first-pass angles.
3. Run short, broad searches.
4. Classify results as relevant, maybe relevant, or off-topic.
5. Extract better terms from the relevant and maybe-relevant set.
6. Run one refinement pass only where the first pass was thin or noisy.
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

Keep the first pass intentionally small. Four good angles beats twenty padded ones.

## Internal filtering rules

Use search results as candidate generation, then classify internally:

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

## Stop rules

Stop after the first pass when the shortlist is already strong.

Stop after the refinement pass when any of these is true:
- new searches mostly repeat the same repos
- remaining gaps are about uncertainty, not discovery
- the user can already make a reasonable choice from the shortlist
