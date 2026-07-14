# Web Augmentation (Optional Branch)

Use this branch only when GitHub-only search is not enough. Even then,
augmentation is a small detour to learn category vocabulary — not a
replacement for filtering on GitHub.

## When augmentation helps

- The category has fuzzy or shifting names.
- The user describes a problem, not a product label.
- GitHub search returns thin or noisy results.
- Community-curated alternatives matter ("alternatives to X" lists,
  Reddit recommendations, HN comparison threads).
- You need to answer "what do people call this in this community?"

## Capability-aware paths

| Capability | What to do |
|---|---|
| `run-research` skill available | Preferred path. Invoke `run-research` with a tight goal scoped to "learn category vocabulary and curated lists for `<topic>`". The skill drives the 3-tool toolkit (the `get-research-consultancy` planner + `web-search` + `scrape-link`) with built-in discipline. |
| Built-in `WebSearch` / `WebFetch` only | Lighter fallback. Search for category language, comparison posts, Reddit threads, and `site:github.com` results directly. |
| No web tooling available | Stay GitHub-only. Widen the category phrasing instead, or accept the limitation explicitly. |

## When to invoke `run-research`

Reach for `run-research` when ONE of these is true:

- The category is genuinely fuzzy and you've already tried 4-6 search
  angles on GitHub without finding the right vocabulary.
- The user named a problem and you need a quick map of the named
  alternatives (e.g., curated "alternatives to X" lists).
- You suspect strong practitioner sentiment exists on Reddit or HN that
  would surface project names not visible in GitHub search.

When you invoke `run-research` for this purpose, scope it tightly. The
goal paragraph should look like:

> Discover category vocabulary and curated alternative lists for
> `<topic>` so I can return to GitHub search with better names and
> known projects. User context: I am scouting GitHub repos for
> `<concrete need>`. Done = a list of category-name candidates,
> 3-7 commonly-cited project names, and (if surfaced) one or two
> curated awesome-style lists worth scraping. Skip: deep
> per-product evaluation, pricing, in-depth reviews. Freshness:
> last 12 months for category drift. Quote discipline: project
> names verbatim from sources.

The skill returns naming clues; you return to GitHub to verify and
filter. **Web results are leads, not the final shortlist.** Convert
useful names or categories back into GitHub repo searches and filter
there.

For light naming clues where invoking `run-research` is overkill,
built-in `WebSearch` is sufficient. Use it the same way: discover
naming, then return to GitHub.

## Good augmented searches (built-in `WebSearch` or via `run-research`)

Discovery-shaped queries:
- `best self-hosted knowledge base github`
- `what do people call browser agents github`
- `site:github.com collaborative docs self hosted`
- `site:reddit.com best open source code review bot github`

Curated-list patterns:
- `awesome <topic> github`
- `<topic> alternatives github`
- `site:github.com awesome <topic>`

Sentiment patterns (Reddit-scoped):
- `site:reddit.com "<topic>" alternatives`
- `site:reddit.com "<topic>" "switched from"`

## Mapping web findings back to GitHub

After augmentation, you should have:
- 3-7 candidate project names you didn't have before.
- 1-2 category-vocabulary candidates ("oh, people call this `block
  editor` not `notion alternative`").
- Optionally, one or two curated awesome-list URLs.

For each project name surfaced: run `gh search repos 'NAME' ...` to
locate the canonical owner/repo and verify status (active / archived /
last update). Add to the relevant / maybe-relevant set.

For each new category-vocabulary candidate: re-run a GitHub search with
the new vocabulary instead of the original phrasing.

## Stop rules

Stop augmenting when ANY of:

- You learned the missing category language.
- You discovered a few new candidate names to test on GitHub.
- Additional web results mostly repeat known repos or lists.

The augmentation is a detour back to GitHub, not a parallel research
track. Do not let it become a corpus.

## Anti-patterns

- **Treating web search as the final shortlist.** Web results are
  naming leads; the shortlist comes from GitHub.
- **Spawning a full `run-research` corpus when only a name was
  needed.** If you need 3 names, scope `run-research`'s goal tightly —
  do not let it dispatch a multi-round session.
- **Skipping the return to GitHub.** Even when the augmentation
  surfaces a strong-looking project, verify on GitHub before adding to
  the shortlist (status, license, activity, fork-vs-canonical).
