# Search Strategies

Read this file before the first `skill-dl search` in a session. Keyword choice is the main quality lever.

## Keyword formulation rules

`skill-dl search` accepts 3-20 space-separated keywords and ranks results by how many keywords each skill matches. Cross-keyword overlap is the primary ranking signal.

### Keyword diversity beats repetition

Each keyword should attack a different angle of the topic. Do not paraphrase the same concept.

**Bad:** `typescript types typing type-safety strict` (all the same angle)

**Good:** `typescript mcp server sdk error-handling testing patterns` (covers tool, domain, quality concerns)

### Keyword categories to cover

For any search, aim to include keywords from at least 3 of these categories:

| Category | Examples | Purpose |
|---|---|---|
| Technology | `typescript`, `react`, `python`, `rust` | Filter by language or framework |
| Domain | `mcp`, `authentication`, `deployment`, `testing` | Filter by problem space |
| Activity | `build`, `debug`, `optimize`, `migrate`, `configure` | Filter by what the skill does |
| Pattern | `patterns`, `best-practices`, `anti-patterns`, `recipes` | Filter by content type |
| Scope | `server`, `client`, `agent`, `cli`, `api` | Filter by system component |

### Minimum keyword count by goal

| Goal | Minimum keywords | Rationale |
|---|---|---|
| Targeted search (known topic) | 3-5 | Specific enough to surface exact matches |
| Broad landscape scan | 8-12 | More keywords surface different result clusters |
| Exhaustive corpus building | 15-20 | Maximum coverage across the topic space |

## Multi-round search patterns

### Round 1: Broad discovery

Start with your core topic keywords. Review the result table.

```bash
skill-dl search typescript mcp server --top 30
```

### Round 2: Gap filling

Identify what Round 1 missed. Add keywords from angles not covered.

```bash
skill-dl search mcp authentication session transport streaming --top 20
```

### Round 3: Adjacent discovery

Search for related but not identical topics that may contain reusable patterns.

```bash
skill-dl search agent browser automation headless testing --top 15
```

### Deduplication across rounds

After multiple rounds, deduplicate URLs before downloading:

```bash
cat round1-urls.txt round2-urls.txt round3-urls.txt | sort -u > all-urls.txt
```

## Tuning result volume

### Too many results (50+ rows)

1. Add `--min-match 2` to require skills matching at least 2 keywords
2. Add `--top 20` to cap output
3. Add more specific keywords to shift ranking

### Too few results (under 5 rows)

1. Broaden keywords — go up one level of abstraction
2. Remove overly specific terms
3. Run a second search with different phrasing
4. Try adjacent topic keywords

### Niche topics (max match count 1-2)

When even the best results only match 1-2 keywords, the topic is niche on playbooks.com. In this case:

1. Manually review the full result list (do not use `--min-match`)
2. Evaluate by skill name relevance, not match count
3. Consider adjacent topics that might contain transferable patterns

## Search output format

`skill-dl search` outputs a markdown table to stdout with columns:

- Rank
- Skill name
- Owner/repo
- Keywords matched
- Match count
- URL

Parse URLs from this table for batch download:

```bash
skill-dl search react hooks testing | grep -oE 'https://playbooks\.com/skills/[^ |]+' | sort -u
```
