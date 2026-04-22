# gh search repos Cheatsheet

Copy-paste reference for valid, compact GitHub repo searches.

## Command structure

```bash
gh search repos 'QUERY' --limit 20 --sort=stars --json fullName,description,stargazersCount,updatedAt,url --jq '...'
```

Use shell quotes around the whole query string when helpful. Inside that query string, GitHub still parses search operators and qualifiers.

## Useful qualifiers

| Qualifier | Example | Use |
|---|---|---|
| `stars:>N` | `stars:>200` | Suppress tiny repos when the space is noisy |
| `pushed:>DATE` | `pushed:>2025-01-01` | Bias toward active repos |
| `language:X` | `language:TypeScript` | Hard language constraint |
| `fork:false` | `fork:false` | Drop forks from discovery |
| `archived:false` | `archived:false` | Drop archived repos |
| `license:mit` | `license:mit` | Filter by license when needed |
| `in:name` | `agent in:name` | Name-only check |
| `in:description` | `knowledge base in:description` | Description-only check |
| `in:readme` | `playwright in:readme` | Use sparingly for naming mismatches |
| `topic:X` | `topic:mcp` | Helpful for shortlisted repos, noisy for broad discovery |

## OR rules

- **Good:** OR between single terms inside the query string.
- **Bad:** OR between quoted phrases.

Examples:

```bash
# Good
gh search repos 'outline OR affine fork:false archived:false' --limit 20 --sort=stars

# Good
gh search repos 'agent OR copilot browser automation fork:false' --limit 20 --sort=stars

# Bad
gh search repos '"code review bot" OR "review agent"' --limit 20 --sort=stars
```

When the concept is multi-word, separate searches are usually clearer than phrase-OR gymnastics.

## Heuristics

- Start broad, then filter internally.
- Prefer 20-30 results per search over giant dumps.
- Use `--sort=stars` for discovery; use recency as a later signal, not the primary sort.
- Always use `--json` with `--jq`; raw JSON is noisy and expensive.
- If you need repo topics or README intros, inspect only the top few candidates after the first pass.
