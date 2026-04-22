# Optional Subagent Prompts

Use these only when the landscape is large or the user explicitly wants deeper comparison. The main agent still owns intent parsing, filtering, and final synthesis.

## Search Augmentation Agent

Use when the first pass is thin, noisy, or stuck on fuzzy naming.

```
You are helping with GitHub repo scouting for this need:

{INTERPRETED_NEED}

Current state:
- Relevant repos: {LIST}
- Maybe relevant repos: {LIST}
- Off-topic patterns: {LIST}
- Gaps to solve: {LIST}

Read:
- references/search/search-methodology.md
- references/search/web-search-patterns.md if naming is fuzzy
- references/search/gh-search-syntax-cheatsheet.md if you need exact gh syntax

Run only 2-4 new search angles that directly address the gaps above.
Return a markdown table grouped into Relevant, Maybe relevant, and Off-topic.
For each new repo, include one line on why it belongs in that group.
Do not create files unless the parent explicitly asked for artifacts.
```

## Top-N Deep Dive Agent

Use when the user wants more confidence in the top few repos.

```
You are doing a focused deep dive on these shortlisted GitHub repos:

{TOP_REPOS}

User need:
{INTERPRETED_NEED}

Read:
- references/evaluation/evaluation-methodology.md
- references/evaluation/rest-unique-signals.md
- references/evaluation/graphql-repo-deep-dive.md if cheap signals are not enough
- references/evaluation/code-level-analysis.md for README, test, and source evidence

For each repo, return:
- fit verdict (strong fit / plausible fit / stretch)
- feature evidence tied to the user's must-haves
- docs/tests/releases quality notes
- obvious maintenance risks
- 1-2 caveats

Do not produce a global ranking. The parent agent will synthesize across repos.
```

## Optional Feature Matrix Agent

Use only if the user explicitly wants a matrix.

```
Build a feature matrix for these shortlisted repos:

Repos:
{TOP_REPOS}

Features to verify:
{FEATURE_LIST}

Read references/evaluation/code-level-analysis.md.
Use README evidence first, then file tree, then targeted source reads.
Return a markdown table with one row per repo and one short evidence note per feature.
Skip features you cannot verify cleanly; mark them as unknown instead of guessing.
```

## Lean dispatch rules

- Default path: no subagents.
- Search augmentation: usually 1 helper agent, not a swarm.
- Deep comparison: usually 1-3 agents with disjoint repo ownership.
- The main agent always writes the final shortlist, recommendation, or export artifact.
- No mandatory `.githubresearch/` output tree.
