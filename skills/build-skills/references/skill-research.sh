#!/usr/bin/env bash
# skill-research.sh — Skill discovery, download, and corpus inspection
# Usage: bash skill-research.sh "<keyword1>,<keyword2>,<keyword3>[,...]" [output-dir] [max-parallel]
#
# Example:
#   bash skill-research.sh "agent browser,headless automation,browser testing" ./corpus 6
#   bash skill-research.sh "typescript,type safety,strict mode,ts config" ./corpus
#
# Discovery: uses `skill-dl search` (outputs a prioritized markdown table to stdout)
# Download:  pipes discovered URLs into skill-dl with repo-level parallelism
# Inspect:   trees the corpus and shows per-skill file counts after download
#
# Requires: skill-dl (https://github.com/yigitkonur/cli-skill-downloader)

set -euo pipefail

SEARCH_TERMS="${1:?Usage: skill-research.sh \"<keyword1>,<keyword2>,<keyword3>[,...]\" [output-dir] [max-parallel]}"
OUTPUT_DIR="${2:-./skill-research-corpus}"
MAX_PARALLEL="${3:-4}"

# Split comma-separated terms into array and trim whitespace
IFS=',' read -ra KEYWORDS <<< "$SEARCH_TERMS"
TRIMMED_KEYWORDS=()
for kw in "${KEYWORDS[@]}"; do
  kw=$(echo "$kw" | xargs)
  [[ -n "$kw" ]] && TRIMMED_KEYWORDS+=("$kw")
done

# Validate: skill-dl search requires at least 3 keywords
if [[ "${#TRIMMED_KEYWORDS[@]}" -lt 3 ]]; then
  echo "ERROR: skill-dl search requires at least 3 keywords. Got ${#TRIMMED_KEYWORDS[@]}."
  echo "  Example: bash skill-research.sh \"agent browser,headless automation,browser testing\" ./corpus"
  exit 1
fi

if [[ "${#TRIMMED_KEYWORDS[@]}" -gt 20 ]]; then
  echo "WARNING: skill-dl search accepts up to 20 keywords. Trimming to first 20."
  TRIMMED_KEYWORDS=("${TRIMMED_KEYWORDS[@]:0:20}")
fi

echo "=== Skill Research ==="
echo "Keywords: ${TRIMMED_KEYWORDS[*]}"
echo "Output:   ${OUTPUT_DIR}"
echo "Parallel: ${MAX_PARALLEL}"
echo ""

# Check skill-dl is available
if ! command -v skill-dl &>/dev/null; then
  echo "ERROR: skill-dl not found. Install with:"
  echo "  curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | bash"
  echo "  Tool home: https://github.com/yigitkonur/cli-skill-downloader"
  exit 1
fi

# --- Phase 1: Discovery via skill-dl search ---
echo "--- Phase 1: Discovery ---"
echo "  Running: skill-dl search ${TRIMMED_KEYWORDS[*]}"
echo ""

URL_FILE=$(mktemp)

# Run skill-dl search — it outputs a markdown table to stdout
# Parse the table to extract Playbooks URLs (last column in each data row)
skill-dl search "${TRIMMED_KEYWORDS[@]}" 2>/dev/null | \
  grep -E '^\|[[:space:]]*[0-9]' | \
  grep -oE 'https://playbooks\.com/skills/[^|[:space:]]+' | \
  sort -u > "$URL_FILE"

URL_COUNT=$(wc -l < "$URL_FILE" | tr -d ' ')
echo "  Found: ${URL_COUNT} unique skill URLs"
echo ""

if [[ "$URL_COUNT" -eq 0 ]]; then
  echo "No skills found. Try different or broader keywords."
  rm -f "$URL_FILE"
  exit 1
fi

# Show the URL list so the caller can review candidates before download
echo "  Discovered URLs:"
while IFS= read -r url; do
  echo "    $url"
done < "$URL_FILE"
echo ""

# --- Phase 2: Parallel Download ---
echo "--- Phase 2: Download ---"

# Split by repo for parallel download (avoids redundant clones)
SPLIT_DIR=$(mktemp -d)
while IFS= read -r url; do
  [[ -z "$url" ]] && continue
  repo_key=$(echo "$url" | sed 's|.*/skills/\([^/]*/[^/]*\)/.*|\1|' | tr '/' '_')
  echo "$url" >> "${SPLIT_DIR}/${repo_key}.txt"
done < "$URL_FILE"

REPO_COUNT=$(ls "${SPLIT_DIR}"/*.txt 2>/dev/null | wc -l | tr -d ' ')
echo "  Repos:    ${REPO_COUNT}"
echo "  Parallel: ${MAX_PARALLEL}"
echo ""

# Download each repo group in parallel
ls "${SPLIT_DIR}"/*.txt | xargs -P "$MAX_PARALLEL" -I {} skill-dl {} -o "$OUTPUT_DIR" --no-auto-category -f

# Cleanup temp files
rm -rf "$SPLIT_DIR" "$URL_FILE"

# --- Phase 3: Read the corpus ---
echo ""
echo "--- Phase 3: Corpus Inspection ---"

SKILL_COUNT=$(find "$OUTPUT_DIR" -name "SKILL.md" -maxdepth 2 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1)

echo "  Skills downloaded: ${SKILL_COUNT}"
echo "  Total size:        ${TOTAL_SIZE}"
echo "  Output path:       ${OUTPUT_DIR}"
echo ""

# Tree the output directory (top-level only for overview)
echo "  Corpus structure:"
if command -v tree &>/dev/null; then
  tree -L 2 "$OUTPUT_DIR" 2>/dev/null || ls -1 "$OUTPUT_DIR"
else
  ls -1 "$OUTPUT_DIR"
fi
echo ""

# List all SKILL.md files with their parent skill directory
echo "  Downloaded SKILL.md files:"
find "$OUTPUT_DIR" -name "SKILL.md" -maxdepth 2 2>/dev/null | sort | while IFS= read -r skill_md; do
  skill_dir=$(dirname "$skill_md")
  skill_name=$(basename "$skill_dir")
  ref_count=$(find "$skill_dir/references" -type f 2>/dev/null | wc -l | tr -d ' ')
  script_count=$(find "$skill_dir/scripts" -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "    ${skill_name}  (references: ${ref_count}, scripts: ${script_count})"
done
echo ""

# Per-skill file counts
echo "  Per-skill file breakdown:"
find "$OUTPUT_DIR" -name "SKILL.md" -maxdepth 2 2>/dev/null | sort | while IFS= read -r skill_md; do
  skill_dir=$(dirname "$skill_md")
  skill_name=$(basename "$skill_dir")
  total_files=$(find "$skill_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "    ${skill_name}: ${total_files} files total"
  if command -v tree &>/dev/null; then
    tree -L 2 "$skill_dir" 2>/dev/null | tail -n +2 | sed 's/^/      /'
  else
    find "$skill_dir" -type f 2>/dev/null | sed "s|${skill_dir}/||" | sort | sed 's/^/      /'
  fi
done

echo ""
echo "=== Next steps ==="
echo "  1. For each high-signal skill: read its SKILL.md fully"
echo "  2. Tree its references/ directory to understand structure"
echo "  3. Read the 2-3 most relevant reference files"
echo "  4. Check scripts/ if present for automation patterns"
echo "  5. Capture notes on structure, patterns, and what to inherit vs avoid"
echo "  6. Build a comparison table before drafting the final skill"
