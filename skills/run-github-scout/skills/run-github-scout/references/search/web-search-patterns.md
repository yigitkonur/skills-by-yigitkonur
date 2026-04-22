# Optional Web Search Patterns

Use this branch only when GitHub-only search is not enough.

## When augmentation helps

- the category has fuzzy or shifting names
- the user describes a problem, not a product label
- GitHub search returns thin or noisy results
- community-curated alternatives matter
- you need to answer "what do people call this?"

## Capability-aware paths

| Capability | What to do |
|---|---|
| Research Power Pack / MCP web search available | Use semantic web discovery to learn names, alternatives, and curated lists, then map those results back to GitHub repos |
| Built-in web search or browser available | Search the open web for category language, comparison posts, Reddit threads, and `site:github.com` results |
| No web tooling available | Stay GitHub-only and widen the category phrasing instead |

## Good augmented searches

Discovery searches:
- `best self-hosted knowledge base github`
- `what do people call browser agents github`
- `site:github.com collaborative docs self hosted`
- `site:reddit.com best open source code review bot github`

Follow-up rule: web results are naming clues, not the final shortlist. Convert useful names or categories back into GitHub repo searches and filter there.

## Research Power Pack note

If your environment exposes Research Power Pack or similar tools (for example `start-research`, `web-search`, or `scrape-links`), use them for naming disambiguation or landscape context. They are an enhancement, not a prerequisite.

## Stop rules

Stop augmenting when:
- you learned the missing category language
- you discovered a few new candidate names to test on GitHub
- additional web results mostly repeat known repos or lists
