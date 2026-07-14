# gh-search.sh

Wrap `gh search repos` with safe defaults for repo scouting.

## Requirements

- `bash`
- GitHub CLI (`gh`)
- `gh auth status` recommended before non-trivial runs

`gh search repos --help` is the source of valid fields and flags. The
script currently requests `fullName`, `stargazersCount`, `pushedAt`,
`updatedAt`, `language`, `license`, `isArchived`, `isDisabled`,
`description`, and `url`.

## Usage

```bash
bash scripts/gh-search.sh --query 'mcp server typescript' --limit 5
```

With rate-limit status:

```bash
bash scripts/gh-search.sh --query 'mcp server typescript' --limit 5 --rate-limit
```

With pass-through `gh search repos` flags:

```bash
bash scripts/gh-search.sh \
  --query 'self-hosted wiki' \
  --limit 20 \
  --sort stars \
  --language TypeScript \
  --archived=false
```

## Output

TSV with one header row:

```text
repo	stars	pushed	updated	language	license	archived	disabled	description	url
```

Default limit is 20. Larger limits are allowed but should be explicit.
Use fewer diverse queries before increasing limits.
