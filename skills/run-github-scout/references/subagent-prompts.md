# Optional Subagent Prompts

Use these only when the landscape is large or the user explicitly wants
deeper comparison. The main agent still owns intent parsing, filtering,
and final synthesis.

## Search Augmentation Agent

Use when the first GitHub-only pass is thin, noisy, or stuck on fuzzy
naming AND web augmentation would help. If the gap is genuinely
GitHub-only (e.g., not enough search angles tried yet), do another pass
yourself instead of dispatching a subagent.

```
You are helping with GitHub repo scouting for this need:

{INTERPRETED_NEED}

Current state:
- Relevant repos: {LIST}
- Maybe relevant repos: {LIST}
- Off-topic patterns: {LIST}
- Gaps to solve: {LIST}

[METHODOLOGY — REQUIRED]

This is a web augmentation mission. Your job is to surface category
vocabulary and curated alternative lists, then map findings back to
GitHub repo names — not to produce a shortlist yourself.

Use the `run-research` skill if it is available. The skill drives the
5-tool toolkit (raw/smart × search/scrape plus the `start-research`
planner) with built-in discipline:

1. First call: invoke `start-research` with a tight goal paragraph
   naming the topic, the use case (you are scouting GitHub repos for
   `{INTERPRETED_NEED}`), known unknowns to skip, freshness window
   (last 12 months for category drift), and quote discipline (project
   names verbatim).
2. Toolkit shape: `raw-web-search` for URL pool discovery,
   `smart-web-search` when the output goes directly into your context,
   `raw-scrape-links` for Reddit threads (threading preserved),
   `smart-scrape-links` for docs and curated lists with a defined
   `extract`.
3. Operational caps: `smart-scrape-links` ≤ 5 URLs and ≤ 7 facets per
   call; raw-search >25 keywords risks persistence.
4. Citation discipline: snippets are NOT evidence; only scraped
   content is citable.

If `run-research` is unavailable, fall back to built-in `WebSearch`
and `WebFetch` directly, with the same shape — discover names, then
return to GitHub.

[/METHODOLOGY]

Read also (light scan):
- references/search.md — overall first-pass + refinement loop
- references/web-augment.md — when to invoke run-research vs WebSearch,
  and how to map web findings back to GitHub
- references/gh-syntax.md — exact gh syntax for the GitHub-side
  verification step

Run only 2-4 new web search angles that directly address the gaps
above. Then for every project name surfaced from web results, verify
on GitHub via `gh search repos 'NAME'` before adding to the
shortlist.

Return a markdown table grouped into Relevant, Maybe relevant, and
Off-topic. For each new repo, include one line on why it belongs in
that group AND its discovery path (web result → GitHub verify).
Do not create files unless the parent explicitly asked for artifacts.
```

## Top-N Deep Dive Agent

Use when the user wants more confidence in the top few repos. This is a
GitHub-only mission — no `run-research` needed.

```
You are doing a focused deep dive on these shortlisted GitHub repos:

{TOP_REPOS}

User need:
{INTERPRETED_NEED}

Read:
- references/evaluate.md
- references/evaluate-rest.md
- references/evaluate-graphql.md if cheap signals are not enough
- references/evaluate-code.md for README, test, and source evidence

For each repo, return:
- fit verdict (strong fit / plausible fit / stretch)
- feature evidence tied to the user's must-haves
- docs/tests/releases quality notes
- obvious maintenance risks
- 1-2 caveats

Do not produce a global ranking. The parent agent will synthesize
across repos.
```

## Optional Feature Matrix Agent

Use only if the user explicitly wants a matrix. GitHub-only mission.

```
Build a feature matrix for these shortlisted repos:

Repos:
{TOP_REPOS}

Features to verify:
{FEATURE_LIST}

Read references/evaluate-code.md.
Use README evidence first, then file tree, then targeted source reads.
Return a markdown table with one row per repo and one short evidence
note per feature.
Skip features you cannot verify cleanly; mark them as unknown instead
of guessing.
```

## Lean dispatch rules

- **Default path: no subagents.** The main agent does the work.
- **Search augmentation:** usually 1 helper agent, not a swarm. Embeds
  the `run-research` integration block when web augmentation is the
  gap.
- **Deep comparison:** usually 1-3 agents with disjoint repo
  ownership. GitHub-only — no run-research needed.
- **The main agent always writes the final shortlist, recommendation,
  or export artifact.**
- **No mandatory `.githubresearch/` output tree.**
- **No multi-wave dispatch.** This skill's shape is a shortlist in
  conversation — wave dispatch belongs to `run-deep-research`.
- **No run-research integration in evaluation/matrix subagents.**
  Their work is GitHub-only; embedding the run-research block would
  bloat the brief and signal the wrong tool path.
