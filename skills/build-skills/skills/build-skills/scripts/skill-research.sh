#!/usr/bin/env bash

# ============================================================================
# USAGE
# ============================================================================
# This script automates the research phase of skill building.
#
# Prerequisites:
#   - Use bash scripts/skill-dl --where to resolve the CLI
#   - If skill-dl is missing globally, install it with:
#       sudo -v ; curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | sudo bash
#   - If installation is not possible, see references/remote-sources.md for alternatives
#
# Basic usage:
#   bash scripts/skill-research.sh "keyword1,keyword2,keyword3" [output-dir] [max-parallel]
#
# Examples:
#   bash scripts/skill-research.sh "typescript,mcp,server"
#   bash scripts/skill-research.sh "react,testing,components,hooks" ./corpus
#   bash scripts/skill-research.sh "python,fastapi,authentication" ./corpus 6
#
# What it does:
#   1. Searches for skills matching your keywords using skill-dl
#   2. Downloads the top candidates in parallel
#   3. Outputs a summary of what was found
#
# Output:
#   Downloaded skills are saved to the output directory.
#   Review them using the quality assessment from source-patterns.md.
# ============================================================================
# skill-research.sh — Skill discovery, download, and corpus inspection
# Usage: bash scripts/skill-research.sh "<keyword1>,<keyword2>,<keyword3>[,...]" [output-dir] [max-parallel]
#
# Example:
#   bash scripts/skill-research.sh "agent browser,headless automation,browser testing" ./corpus 6
#   bash scripts/skill-research.sh "typescript,type safety,strict mode,ts config" ./corpus
#
# Discovery: uses `skill-dl search` (outputs a prioritized markdown table to stdout)
# Download:  pipes discovered URLs into skill-dl with repo-level parallelism
# Inspect:   trees the corpus and shows per-skill file counts after download
#
# Requires: bash scripts/skill-dl ... or a global skill-dl install

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DL_WRAPPER="${SCRIPT_DIR}/skill-dl"

show_help() {
  cat <<'EOF'
Usage: bash scripts/skill-research.sh "<keyword1>,<keyword2>,<keyword3>[,...]" [output-dir] [max-parallel]

Discover, download, and inspect skills for the build-skills research phase.

Arguments:
  "<keywords>"    Comma-separated keywords. Minimum 3, maximum 20.
  [output-dir]    Destination for downloaded skills. Default: ./skill-research-corpus
  [max-parallel]  Repo-group download parallelism. Default: 4

Examples:
  bash scripts/skill-research.sh "typescript,mcp,server"
  bash scripts/skill-research.sh "react,testing,components,hooks" ./corpus
  bash scripts/skill-research.sh "python,fastapi,authentication" ./corpus 6

Prerequisites:
  bash scripts/skill-dl --where
  sudo -v ; curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | sudo bash
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

SEARCH_TERMS="${1:?Usage: bash scripts/skill-research.sh \"<keyword1>,<keyword2>,<keyword3>[,...]\" [output-dir] [max-parallel]}"
OUTPUT_DIR="${2:-./skill-research-corpus}"
MAX_PARALLEL="${3:-4}"

# Split comma-separated terms into array and trim whitespace.
# NOTE: This script accepts comma-separated keywords in a single string (e.g. "kw1,kw2,kw3")
# because shell quoting makes it awkward to pass pre-quoted arguments through xargs/wrappers.
# Internally, skill-dl search takes space-separated quoted arguments (e.g. skill-dl search "kw1" "kw2" "kw3").
# The conversion happens automatically below — callers of this script should always use commas.
IFS=',' read -ra KEYWORDS <<< "$SEARCH_TERMS"
TRIMMED_KEYWORDS=()
for kw in "${KEYWORDS[@]}"; do
  kw=$(echo "$kw" | xargs)
  [[ -n "$kw" ]] && TRIMMED_KEYWORDS+=("$kw")
done

# Validate: skill-dl search requires at least 3 keywords
if [[ "${#TRIMMED_KEYWORDS[@]}" -lt 3 ]]; then
  echo "ERROR: skill-dl search requires at least 3 keywords. Got ${#TRIMMED_KEYWORDS[@]}." >&2
  echo "  Example: bash scripts/skill-research.sh \"agent browser,headless automation,browser testing\" ./corpus" >&2
  exit 1
fi

if [[ "${#TRIMMED_KEYWORDS[@]}" -gt 20 ]]; then
  echo "WARNING: skill-dl search accepts up to 20 keywords. Trimming to first 20." >&2
  TRIMMED_KEYWORDS=("${TRIMMED_KEYWORDS[@]:0:20}")
fi

echo "=== Skill Research ===" >&2
echo "Keywords: ${TRIMMED_KEYWORDS[*]}" >&2
echo "Output:   ${OUTPUT_DIR}" >&2
echo "Parallel: ${MAX_PARALLEL}" >&2
echo "" >&2

# Check skill-dl is available through the wrapper
if ! bash "${SKILL_DL_WRAPPER}" --where >/dev/null; then
  echo "ERROR: skill-dl is not available." >&2
  echo "Install globally with:" >&2
  echo "  sudo -v ; curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | sudo bash" >&2
  echo "Or, on macOS arm64, verify the bundled scripts/skill-dl-darwin-arm64 binary exists and retry via bash scripts/skill-dl --where." >&2
  exit 1
fi

# --- Phase 1: Discovery via skill-dl search ---
echo "--- Phase 1: Discovery ---" >&2
echo "  Running: bash scripts/skill-dl search ${TRIMMED_KEYWORDS[*]}" >&2
echo "" >&2

URL_FILE=$(mktemp)

# Run skill-dl search — it outputs a markdown table to stdout
# Parse the table to extract Playbooks URLs (last column in each data row)
bash "${SKILL_DL_WRAPPER}" search "${TRIMMED_KEYWORDS[@]}" 2>/dev/null | \
  grep -E '^\|[[:space:]]*[0-9]' | \
  grep -oE 'https://playbooks\.com/skills/[^|[:space:]]+' | \
  sed 's/\\$//' | \
  sort -u > "$URL_FILE"

URL_COUNT=$(wc -l < "$URL_FILE" | tr -d ' ')
echo "  Found: ${URL_COUNT} unique skill URLs" >&2
echo "" >&2

if [[ "$URL_COUNT" -eq 0 ]]; then
  echo "No skills found. Try different or broader keywords." >&2
  rm -f "$URL_FILE"
  exit 1
fi

# Show the URL list so the caller can review candidates before download
echo "  Discovered URLs:" >&2
while IFS= read -r url; do
  echo "    $url" >&2
done < "$URL_FILE"
echo "" >&2

# --- Phase 2: Parallel Download ---
echo "--- Phase 2: Download ---" >&2

# Split by repo for parallel download (avoids redundant clones)
SPLIT_DIR=$(mktemp -d)
while IFS= read -r url; do
  [[ -z "$url" ]] && continue
  repo_key=$(echo "$url" | sed 's|.*/skills/\([^/]*/[^/]*\)/.*|\1|' | tr '/' '_')
  echo "$url" >> "${SPLIT_DIR}/${repo_key}.txt"
done < "$URL_FILE"

REPO_COUNT=$(ls "${SPLIT_DIR}"/*.txt 2>/dev/null | wc -l | tr -d ' ')
echo "  Repos:    ${REPO_COUNT}" >&2
echo "  Parallel: ${MAX_PARALLEL}" >&2
echo "" >&2

# Download each repo group in parallel
ls "${SPLIT_DIR}"/*.txt | xargs -P "$MAX_PARALLEL" -I {} bash "${SKILL_DL_WRAPPER}" {} -o "$OUTPUT_DIR" --no-auto-category -f

# Cleanup temp files
rm -rf "$SPLIT_DIR" "$URL_FILE"

# --- Phase 3: Read the corpus ---
echo "" >&2
echo "--- Phase 3: Corpus Inspection ---" >&2

SKILL_COUNT=$(find "$OUTPUT_DIR" -name "SKILL.md" -maxdepth 2 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1)

echo "  Skills downloaded: ${SKILL_COUNT}" >&2
echo "  Total size:        ${TOTAL_SIZE}" >&2
echo "  Output path:       ${OUTPUT_DIR}" >&2
echo "" >&2

# Tree the output directory (top-level only for overview)
echo "  Corpus structure:" >&2
if command -v tree &>/dev/null; then
  tree -L 2 "$OUTPUT_DIR" 2>/dev/null >&2 || ls -1 "$OUTPUT_DIR" >&2
else
  ls -1 "$OUTPUT_DIR" >&2
fi
echo "" >&2

# List all SKILL.md files with their parent skill directory
echo "  Downloaded SKILL.md files:" >&2
find "$OUTPUT_DIR" -name "SKILL.md" -maxdepth 2 2>/dev/null | sort | while IFS= read -r skill_md; do
  skill_dir=$(dirname "$skill_md")
  skill_name=$(basename "$skill_dir")
  ref_count=$(find "$skill_dir/references" -type f 2>/dev/null | wc -l | tr -d ' ')
  script_count=$(find "$skill_dir/scripts" -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "    ${skill_name}  (references: ${ref_count}, scripts: ${script_count})" >&2
done
echo "" >&2

# Per-skill file counts
echo "  Per-skill file breakdown:" >&2
find "$OUTPUT_DIR" -name "SKILL.md" -maxdepth 2 2>/dev/null | sort | while IFS= read -r skill_md; do
  skill_dir=$(dirname "$skill_md")
  skill_name=$(basename "$skill_dir")
  total_files=$(find "$skill_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "    ${skill_name}: ${total_files} files total" >&2
  if command -v tree &>/dev/null; then
    tree -L 2 "$skill_dir" 2>/dev/null | tail -n +2 | sed 's/^/      /' >&2
  else
    find "$skill_dir" -type f 2>/dev/null | sed "s|${skill_dir}/||" | sort | sed 's/^/      /' >&2
  fi
done

echo "" >&2
echo "=== Next steps ===" >&2
echo "  1. For each high-signal skill: read its SKILL.md fully" >&2
echo "  2. Tree its references/ directory to understand structure" >&2
echo "  3. Read the 2-3 most relevant reference files" >&2
echo "  4. Check scripts/ if present for automation patterns" >&2
echo "  5. Capture notes on structure, patterns, and what to inherit vs avoid" >&2
echo "  6. Build a comparison table before drafting the final skill" >&2
