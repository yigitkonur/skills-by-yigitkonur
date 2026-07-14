#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  gh-search.sh --query QUERY [--limit N] [--sort SORT] [--rate-limit] [gh search flags...]

Examples:
  gh-search.sh --query 'mcp server typescript' --limit 5
  gh-search.sh --query 'self-hosted wiki' --language TypeScript --archived=false

Outputs TSV:
  repo, stars, pushed, updated, language, license, archived, disabled, description, url
USAGE
}

query=""
limit="20"
sort="stars"
show_rate_limit=0
extra_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --query|-q)
      [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
      query="$2"
      shift 2
      ;;
    --limit|-L)
      [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
      limit="$2"
      shift 2
      ;;
    --sort)
      [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
      sort="$2"
      shift 2
      ;;
    --rate-limit)
      show_rate_limit=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      extra_args+=("$1")
      shift
      ;;
  esac
done

[ -n "$query" ] || { usage >&2; exit 2; }
case "$limit" in
  ''|*[!0-9]*) echo "--limit must be a positive integer" >&2; exit 2 ;;
esac
[ "$limit" -gt 0 ] || { echo "--limit must be greater than 0" >&2; exit 2; }

command -v gh >/dev/null 2>&1 || {
  echo "gh is required. Install GitHub CLI or use direct API fallback manually." >&2
  exit 127
}

if [ "$show_rate_limit" -eq 1 ]; then
  echo "# rate_limit" >&2
  gh api rate_limit --jq '.resources | {core, search, graphql}' >&2 || true
fi

printf 'repo\tstars\tpushed\tupdated\tlanguage\tlicense\tarchived\tdisabled\tdescription\turl\n'

gh search repos "$query" \
  --limit "$limit" \
  --sort "$sort" \
  "${extra_args[@]}" \
  --json fullName,stargazersCount,pushedAt,updatedAt,language,license,isArchived,isDisabled,description,url \
  --jq '
    def day: if . then split("T")[0] else "" end;
    def clean: tostring | gsub("[\t\r\n]"; " ") | gsub("  +"; " ");
    .[] |
    [
      .fullName,
      (.stargazersCount // 0 | tostring),
      (.pushedAt | day),
      (.updatedAt | day),
      (.language // ""),
      (.license.key // .license.spdxId // .license.name // "none"),
      (.isArchived // false | tostring),
      (.isDisabled // false | tostring),
      (.description // "" | clean),
      (.url // "")
    ] | @tsv
  '
