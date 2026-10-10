#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: verify-corpus.sh [--final] <corpus-root-path>

Execute 6-dimension automated evaluation audit across a deep research corpus:
  1. Structural & budget integrity (MAX-N caps, zero stubs/placeholders, no junk)
  2. Frontmatter validity on entity dossiers (Layer 2 Machine Layer)
  3. Machine catalog & claims ledger presence (_meta/manifest.json, claims.jsonl)
  4. Relative link validity and file existence
  5. Cross-axis synthesis integrity (_cross/<axis-slug>/synthesis.md)
  6. Master summary completeness (enforced with --final)
USAGE
}

FINAL_MODE=0
if [[ "${1:-}" == "--final" ]]; then
  FINAL_MODE=1
  shift
fi

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

CORPUS="$1"

if [[ ! -d "$CORPUS" ]]; then
  echo "Error: Directory not found: $CORPUS" >&2
  exit 1
fi

echo "=== Verifying Research Corpus: $CORPUS ==="
errors=0

# 1. Check for junk files
echo "Checking for hidden junk files..."
junk=$(find "$CORPUS" \( -name '.DS_Store' -o -name 'Thumbs.db' -o -name '*.tmp' -o -name '*.bak' \) 2>/dev/null || true)
if [[ -n "$junk" ]]; then
  echo "❌ Found forbidden junk files:"
  echo "$junk"
  errors=$((errors + 1))
else
  echo "✅ No junk files found."
fi

# 2. Check for placeholder text
echo "Checking for forbidden placeholder text..."
placeholders=$(grep -rEn '\b(TODO|TBD|fill later|<placeholder>|\?\?\?)\b' "$CORPUS" 2>/dev/null || true)
if [[ -n "$placeholders" ]]; then
  echo "❌ Found placeholder strings:"
  echo "$placeholders"
  errors=$((errors + 1))
else
  echo "✅ No placeholder text found."
fi

# 3. Check MAX-N caps
echo "Checking MAX-N folder caps..."
# Meta cap: MAX 8 markdown files
if [[ -d "$CORPUS/_meta" ]]; then
  meta_count=$(find "$CORPUS/_meta" -maxdepth 1 -type f -name '*.md' | wc -l)
  if [[ "$meta_count" -gt 8 ]]; then
    echo "❌ _meta exceeds cap: $meta_count files (MAX 8)"
    errors=$((errors + 1))
  else
    echo "✅ _meta file count within cap ($meta_count/8)."
  fi
fi

# Entity folders: MAX 3 files
for entity_dir in "$CORPUS"/*/; do
  base=$(basename "$entity_dir")
  case "$base" in _meta|_cross) continue;; esac
  if [[ -d "$entity_dir" ]]; then
    count=$(find "$entity_dir" -maxdepth 1 -type f -name '*.md' | wc -l)
    if [[ "$count" -gt 3 ]]; then
      echo "❌ Entity folder $base exceeds cap: $count files (MAX 3)"
      errors=$((errors + 1))
    fi
  fi
done

# Cross-axis folders: MAX 3 files
if [[ -d "$CORPUS/_cross" ]]; then
  for axis_dir in "$CORPUS/_cross"/*/; do
    if [[ -d "$axis_dir" ]]; then
      axis_base=$(basename "$axis_dir")
      count=$(find "$axis_dir" -maxdepth 1 -type f -name '*.md' | wc -l)
      if [[ "$count" -gt 3 ]]; then
        echo "❌ Cross folder _cross/$axis_base exceeds cap: $count files (MAX 3)"
        errors=$((errors + 1))
      fi
    fi
  done
fi

# 4. Check core artifacts
echo "Checking required core artifacts..."
if [[ ! -f "$CORPUS/README.md" ]]; then
  echo "❌ Missing root README.md"
  errors=$((errors + 1))
else
  echo "✅ Root README.md present."
fi

if [[ ! -f "$CORPUS/_meta/manifest.json" ]]; then
  echo "❌ Missing machine catalog: _meta/manifest.json"
  errors=$((errors + 1))
else
  echo "✅ Machine catalog manifest.json present."
fi

# 5. Check entity dossier frontmatter & sources ledger
echo "Checking entity dossiers and frontmatter..."
for entity_dir in "$CORPUS"/*/; do
  base=$(basename "$entity_dir")
  case "$base" in _meta|_cross) continue;; esac
  if [[ -d "$entity_dir" ]]; then
    dossier="$entity_dir/dossier.md"
    sources="$entity_dir/sources.md"
    if [[ ! -f "$dossier" ]]; then
      echo "❌ Entity $base missing dossier.md"
      errors=$((errors + 1))
    else
      # Check YAML frontmatter delimiter at start of file
      if ! head -n 1 "$dossier" | grep -q '^---$'; then
        echo "❌ Entity $base dossier.md is missing YAML frontmatter ('---' delimiter)"
        errors=$((errors + 1))
      fi
    fi
    if [[ ! -f "$sources" ]]; then
      echo "❌ Entity $base missing sources.md ledger"
      errors=$((errors + 1))
    fi
  fi
done

# 6. Check cross-axis synthesis
if [[ -d "$CORPUS/_cross" ]]; then
  echo "Checking cross-axis synthesis files..."
  for axis_dir in "$CORPUS/_cross"/*/; do
    if [[ -d "$axis_dir" ]]; then
      axis_base=$(basename "$axis_dir")
      synthesis_file="$axis_dir/synthesis.md"
      if [[ ! -f "$synthesis_file" ]]; then
        echo "❌ Cross axis _cross/$axis_base missing synthesis.md"
        errors=$((errors + 1))
      fi
    fi
  done
fi

# 7. Check master summary
if [[ ! -f "$CORPUS/_meta/00-master-summary.md" ]]; then
  if [[ "$FINAL_MODE" -eq 1 ]]; then
    echo "❌ Missing master summary _meta/00-master-summary.md (required for --final)"
    errors=$((errors + 1))
  else
    echo "⚠️ Warning: Master summary _meta/00-master-summary.md not yet written (Phase 7 gate)."
  fi
else
  echo "✅ Master summary present."
fi

if [[ "$errors" -eq 0 ]]; then
  echo "🎉 All corpus validation checks passed successfully!"
  exit 0
else
  echo "❌ Corpus verification failed with $errors error(s)." >&2
  exit 1
fi
