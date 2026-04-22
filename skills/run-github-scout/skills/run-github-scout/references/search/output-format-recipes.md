# Output Format Recipes

Token-efficient `gh` output patterns for candidate collection.

## 1. Quick scan

Good default when you want to see name, stars, freshness, and description.

```bash
gh search repos 'QUERY' --limit 20 --sort=stars           --json fullName,stargazersCount,updatedAt,description,url           --jq '.[] | [.fullName, (.stargazersCount|tostring), (.updatedAt[:10]), (.description // "" | .[:80]), .url] | @tsv'
```

## 2. Markdown-ready rows

```bash
gh search repos 'QUERY' --limit 20 --sort=stars           --json fullName,stargazersCount,updatedAt,description           --jq '.[] | "| \(.fullName) | \(.stargazersCount) | \(.updatedAt[:10]) | \(.description // "" | .[:60]) |"'
```

## 3. Candidate name capture only

```bash
gh search repos 'QUERY' --limit 20 --sort=stars           --json fullName --jq '.[].fullName'
```

## 4. Merge a few first-pass searches

```bash
{
  gh search repos 'query one' --limit 20 --sort=stars --json fullName --jq '.[].fullName';
  gh search repos 'query two' --limit 20 --sort=stars --json fullName --jq '.[].fullName';
  gh search repos 'query three' --limit 20 --sort=stars --json fullName --jq '.[].fullName';
} | sort -u
```

## 5. Compact shortlist scratchpad

After you inspect the top candidates, reformat them into a shortlist-friendly table:

```markdown
| Repo | Class | Why it is here | Signals |
|---|---|---|---|
| owner/repo | relevant | Strong fit for self-hosted docs | 12k stars, pushed 2026-04 |
| owner/repo2 | maybe relevant | More wiki-like than docs platform | MIT, active |
```

## Rules

- Prefer TSV or markdown rows over raw JSON.
- Capture URLs when you expect to open repo pages next.
- Do not over-format the first pass; the classification step matters more than pretty output.
