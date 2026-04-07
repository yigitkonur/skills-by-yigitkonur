# Web Search Patterns

When and how to supplement gh search with web search.

## When to Use Web Search

- gh search returns <10 results (niche topic)
- You want community-validated picks (Reddit, HN opinions)
- You suspect repos exist but use unexpected naming
- You need context about the landscape (blog posts, comparisons)

## Rules

- **Maximum 5 web searches** per skill invocation (token budget)
- Always append `site:github.com` for repo discovery
- Use search tools available in your environment, not curl
- Extract repo URLs from results, then use gh CLI for data

## Search Patterns

### GitHub-specific
```
"topic keyword" site:github.com
"topic keyword" "mcp server" site:github.com
"topic" "awesome" site:github.com
```

### Reddit (community validation)
```
"topic" github site:reddit.com
"best topic tool" site:reddit.com
"topic" recommendations site:reddit.com
```

### Hacker News (Show HN / launches)
```
"topic" site:news.ycombinator.com
"Show HN" "topic" site:news.ycombinator.com
```

### Blog/Tutorial (adoption signal)
```
"topic" tutorial github 2025 OR 2026
"how to use" "topic" github
```

## Extracting Repos from Web Results

Web search returns URLs. Extract GitHub repo URLs and feed them to gh CLI:
```bash
# For each repo URL found, get quick stats
gh api repos/owner/name --jq '{stars: .stargazers_count, desc: .description, lang: .language}'
```
