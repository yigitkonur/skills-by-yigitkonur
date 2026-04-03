# gh search repos — Syntax Cheatsheet

Copy-paste reference. Not a tutorial.

## Command Structure
```bash
gh search repos "QUERY" [FLAGS] --json FIELDS --jq 'EXPRESSION'
```

## Search Qualifiers (inside "QUERY" string)

### Numbers
| Qualifier | Example | Notes |
|---|---|---|
| `stars:>N` | `stars:>100` | Greater than N |
| `stars:N..M` | `stars:10..500` | Range |
| `forks:>=N` | `forks:>=50` | |
| `size:>N` | `size:>10000` | Repo size in KB |
| `topics:>N` | `topics:>3` | Number of topics |
| `good-first-issues:>N` | `good-first-issues:>5` | |

### Dates
| Qualifier | Example | Notes |
|---|---|---|
| `pushed:>DATE` | `pushed:>2025-01-01` | Last push after date |
| `created:<DATE` | `created:<2020-01-01` | Created before date |
| `created:DATE..DATE` | `created:2024-01-01..2025-01-01` | Range |

### Scope
| Qualifier | Example | Notes |
|---|---|---|
| `language:X` | `language:TypeScript` | Primary language |
| `user:X` | `user:torvalds` | Owner is user |
| `org:X` | `org:microsoft` | Owner is org |
| `in:name` | `react in:name` | Search in repo name |
| `in:description` | `mcp in:description` | Search in description |
| `in:readme` | `codex in:readme` | Search in README (noisy!) |
| `topic:X` | `topic:mcp` | Has this topic tag |
| `license:X` | `license:mit` | License SPDX key |

### Boolean
| Qualifier | Example | Notes |
|---|---|---|
| `archived:false` | | Exclude archived |
| `is:public` | | Only public |
| `fork:false` | | Exclude forks |

### Operators
| Op | Example | Notes |
|---|---|---|
| OR | `"codex OR claude"` | Either term |
| AND | `codex claude` | Implicit AND (space) |
| NOT | `-topic:linux` | Exclude |

## Flags

| Flag | Default | Recommended |
|---|---|---|
| `--sort=` | best-match | **Always `stars`** for discovery |
| `--limit N` | 30 | 30 is good. Max 1000. |
| `--json FIELDS` | — | Always use with --jq |
| `--jq EXPR` | — | Always use for token efficiency |
| `--language X` | — | Alternative to `language:X` in query |
| `--topic X` | — | Alternative to `topic:X` in query |
| `--archived` | — | `false` to exclude archived |

## Available JSON Fields

```
fullName, stargazersCount, description, language, updatedAt,
pushedAt, forksCount, openIssuesCount, license, isArchived,
owner, createdAt, defaultBranch, hasIssues, hasWiki, hasPages,
hasProjects, hasDownloads, size, visibility, watchersCount, url
```

## Warnings

- **OR only works between single terms**: `codex OR claude` WORKS. `"codex bridge" OR "codex wrapper"` → 0 results
- `--sort=updated` surfaces forks and junk. **Always use `--sort=stars`**
- Multi-word exact phrases often return 0: `"mcp server codex cli"` → 0
- `in:readme` is noisy — add `stars:>10` to suppress megarepos
- `--topic=X` is too broad for discovery — finds megarepos tangentially
- Raw `--json` without `--jq` is 7x more tokens than filtered output
- Maximum 1000 results total per search (GitHub API limit)
- **Rate limit**: max ~10 searches per 2 minutes before throttling
- `--owner=X` flag is equivalent to `user:X` or `org:X` in the query string
