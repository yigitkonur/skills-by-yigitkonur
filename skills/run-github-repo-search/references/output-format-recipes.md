# Output Format Recipes

Token-efficient --jq patterns for gh search repos. Copy-paste ready.

## Recipes by Use Case

### 1. Enumeration Only (26 bytes/result)
When you just need names for dedup or piping:
```bash
--json fullName --jq '.[].fullName'
```

### 2. Quick Scan (32 bytes/result) — RECOMMENDED DEFAULT
Name + stars. Enough to decide what to investigate:
```bash
--json fullName,stargazersCount \
--jq '.[] | "\(.fullName) \(.stargazersCount)★"'
```

### 3. Full Detail TSV (68 bytes/result)
Name, stars, language, date, description:
```bash
--json fullName,stargazersCount,language,description,updatedAt \
--jq '.[] | [.fullName, (.stargazersCount|tostring), .language // "?", (.updatedAt[:10]), (.description // "" | .[:60])] | @tsv'
```

### 4. Markdown Table Row
For direct copy into reports:
```bash
--json fullName,stargazersCount,language,description,updatedAt \
--jq '.[] | "| \(.fullName) | \(.stargazersCount) | \(.language // "?") | \(.updatedAt[:10]) | \(.description // "" | .[:50]) |"'
```

## Dedup Across Multiple Searches

```bash
{
  gh search repos "query1" --limit 30 --sort=stars --json fullName,stargazersCount --jq '.[] | "\(.fullName)\t\(.stargazersCount)"';
  gh search repos "query2" --limit 30 --sort=stars --json fullName,stargazersCount --jq '.[] | "\(.fullName)\t\(.stargazersCount)"';
  gh search repos "query3" --limit 30 --sort=stars --json fullName,stargazersCount --jq '.[] | "\(.fullName)\t\(.stargazersCount)"';
} | sort -t$'\t' -k1,1 -u | sort -t$'\t' -k2 -rn
```

## Token Efficiency Comparison (20 results)

| Format | Bytes | Ratio |
|---|---|---|
| Raw --json (no --jq) | 3,734 | 7.1x (NEVER use) |
| Default table (no flags) | 2,551 | 4.8x |
| Full detail TSV | 1,363 | 2.6x |
| Quick scan (name+stars) | 644 | 1.2x |
| Names only | 529 | 1.0x (baseline) |

**RULE: Always use --jq. Never output raw JSON.**

## Null Handling in jq

Always handle nulls for optional fields:
- `(.description // "")` — empty string fallback
- `(.language // "?")` — question mark fallback
- `(.description // "" | .[:50])` — truncate with null safety
