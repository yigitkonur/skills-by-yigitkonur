# score-repos.sh

Score cheap repository metadata captured by `gh-search.sh`.

This script does **not** score semantic relevance. It is a quick sort
helper for freshness, archived/disabled status, license presence, stars
bucket, language, and optional README/CI fields if present in the TSV.
The agent still owns fit judgment against the user's must-haves.

## Requirements

- `bash`
- `awk`
- `date`

## Usage

```bash
bash scripts/gh-search.sh --query 'mcp server typescript' --limit 5 > /tmp/repos.tsv
bash scripts/score-repos.sh --input /tmp/repos.tsv
```

Or pipe directly:

```bash
bash scripts/gh-search.sh --query 'mcp server typescript' --limit 5 |
  bash scripts/score-repos.sh
```

## Output

TSV with one header row:

```text
owner/repo	signal_score	signal_notes	caveats
```

Use the score to prioritize inspection, not to rank final recommendations.
Final recommendations must cite repo-fit evidence from description,
topics, README, API, or code.
