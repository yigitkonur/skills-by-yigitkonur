# Dedup and Rank

How to merge results from multiple search hypotheses.

## Dedup Strategy

1. Collect all results as TSV: `fullName\tstargazersCount`
2. Sort by fullName, remove duplicates: `sort -t$'\t' -k1,1 -u`
3. Re-sort by stars descending: `sort -t$'\t' -k2 -rn`

```bash
{
  gh search repos "query1" --limit 30 --sort=stars --json fullName,stargazersCount --jq '.[] | "\(.fullName)\t\(.stargazersCount)"';
  gh search repos "query2" --limit 30 --sort=stars --json fullName,stargazersCount --jq '.[] | "\(.fullName)\t\(.stargazersCount)"';
} | sort -t$'\t' -k1,1 -u | sort -t$'\t' -k2 -rn
```

## Ranking

Primary: stars descending (best quality signal for discovery)
Secondary: last push date (recency as tiebreaker)

## Output Ceiling

**Maximum 50 candidates** in the final report.

If >50 found, take top 50 by stars. Always note:
- Total unique repos found
- How many searches produced them
- Which hypotheses were most productive

## Categorization

After ranking, scan descriptions and group into 3-5 natural categories.
Example categories for "codex mcp": Pure MCP Servers, Subagent Orchestrators, Bridges, Multi-CLI, Specialized/Domain.
