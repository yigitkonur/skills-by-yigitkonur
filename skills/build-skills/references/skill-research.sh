#!/usr/bin/env bash
# skill-research.sh — Parallel skill discovery + download
# Usage: bash skill-research.sh "<search terms>" [output-dir] [max-parallel]
#
# Example:
#   bash skill-research.sh "agent browser" ./corpus 6
#   bash skill-research.sh "typescript testing,jest,vitest" ./corpus
#
# Discovery: scrapes Playbooks search pages for multiple query variants in parallel
# Download:  pipes discovered URLs into skill-dl with repo-level parallelism

set -euo pipefail

SEARCH_TERMS="${1:?Usage: skill-research.sh \"<terms>\" [output-dir] [max-parallel]}"
OUTPUT_DIR="${2:-./skill-research-corpus}"
MAX_PARALLEL="${3:-4}"

# Split comma-separated terms into array
IFS=',' read -ra QUERIES <<< "$SEARCH_TERMS"

echo "=== Skill Research ==="
echo "Queries:  ${QUERIES[*]}"
echo "Output:   ${OUTPUT_DIR}"
echo "Parallel: ${MAX_PARALLEL}"
echo ""

# --- Phase 1: Parallel Discovery ---
echo "--- Phase 1: Discovery ---"
URL_FILE=$(mktemp)
SEEN_FILE=$(mktemp)

discover_query() {
  local query="$1"
  local encoded="${query// /+}"
  local page=1
  local max_pages=5

  while (( page <= max_pages )); do
    local search_url="https://playbooks.com/skills?search=${encoded}&page=${page}"
    local html
    html=$(curl -sL --max-time 10 "$search_url" 2>/dev/null) || break

    # Extract skill URLs from the page
    local urls
    urls=$(echo "$html" | grep -oE '/skills/[^"]+' | grep -E '^/skills/[^/]+/[^/]+/[^/]+$' | sort -u)

    [[ -z "$urls" ]] && break

    while IFS= read -r path; do
      echo "https://playbooks.com${path}"
    done <<< "$urls"

    page=$((page + 1))
  done
}

# Run discovery for all queries in parallel
for query in "${QUERIES[@]}"; do
  query=$(echo "$query" | xargs)  # trim
  [[ -z "$query" ]] && continue
  echo "  Searching: ${query}"
  discover_query "$query" &
done | sort -u > "$URL_FILE"
wait

URL_COUNT=$(wc -l < "$URL_FILE" | tr -d ' ')
echo "  Found: ${URL_COUNT} unique skill URLs"
echo ""

if [[ "$URL_COUNT" -eq 0 ]]; then
  echo "No skills found. Try different search terms."
  rm -f "$URL_FILE" "$SEEN_FILE"
  exit 1
fi

# --- Phase 2: Parallel Download ---
echo "--- Phase 2: Download ---"

# Check skill-dl is available
if ! command -v skill-dl &>/dev/null; then
  echo "ERROR: skill-dl not found. Install with:"
  echo "  curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | bash"
  rm -f "$URL_FILE" "$SEEN_FILE"
  exit 1
fi

# Split by repo for parallel download
SPLIT_DIR=$(mktemp -d)
while IFS= read -r url; do
  [[ -z "$url" ]] && continue
  repo_key=$(echo "$url" | sed 's|.*/skills/\([^/]*/[^/]*\)/.*|\1|' | tr '/' '_')
  echo "$url" >> "${SPLIT_DIR}/${repo_key}.txt"
done < "$URL_FILE"

REPO_COUNT=$(ls "${SPLIT_DIR}"/*.txt 2>/dev/null | wc -l | tr -d ' ')
echo "  Repos: ${REPO_COUNT}"
echo "  Parallel: ${MAX_PARALLEL}"
echo ""

# Download each repo group in parallel
ls "${SPLIT_DIR}"/*.txt | xargs -P "$MAX_PARALLEL" -I {} skill-dl {} -o "$OUTPUT_DIR" --no-auto-category -f

# Cleanup
rm -rf "$SPLIT_DIR" "$URL_FILE" "$SEEN_FILE"

# --- Summary ---
echo ""
echo "=== Done ==="
SKILL_COUNT=$(find "$OUTPUT_DIR" -name "SKILL.md" -maxdepth 2 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1)
echo "  Skills: ${SKILL_COUNT}"
echo "  Size:   ${TOTAL_SIZE}"
echo "  Path:   ${OUTPUT_DIR}"
