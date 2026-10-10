#!/usr/bin/env bash
# ==============================================================================
# validate-capture-gate.sh — Screen & State Capture Verification Gate
#
# Validates that audit screenshot artifacts match the schema, exist,
# contain non-empty valid PNG magic bytes, and meet the state gate.
#
# Usage:
#   bash skills/audit-ui-ux/scripts/validate-capture-gate.sh <artifacts-dir>
# Example:
#   bash skills/audit-ui-ux/scripts/validate-capture-gate.sh audit-artifacts/2026-10-10
# ==============================================================================

set -euo pipefail

TARGET_DIR="${1:-}"

if [[ -z "$TARGET_DIR" ]]; then
  echo "❌ Error: Missing target directory."
  echo "Usage: $0 <path-to-audit-artifacts-or-date-dir>"
  exit 1
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "❌ Error: Target directory does not exist: $TARGET_DIR"
  exit 1
fi

echo "🔍 Validating capture gate for: $TARGET_DIR"

ERRORS=0
WARNINGS=0
TOTAL_SCREENS=0
TOTAL_IMAGES=0

STANDARD_STATES=(
  "default.png"
  "hover.png"
  "active.png"
  "empty-state.png"
  "error-state.png"
  "loading.png"
  "modal-open.png"
)

# Function to check PNG magic bytes (89 50 4E 47 0D 0A 1A 0A)
validate_png_file() {
  local file_path="$1"
  local screen_name="$2"

  if [[ ! -s "$file_path" ]]; then
    echo "  ❌ [Empty File] $screen_name/$(basename "$file_path") has 0 bytes."
    ERRORS=$((ERRORS + 1))
    return
  fi

  # Read first 8 bytes in hex
  local magic
  magic=$(od -N 8 -t x1 "$file_path" 2>/dev/null | head -n 1 | awk '{$1=""; print $0}' | tr -d ' ' | tr '[:upper:]' '[:lower:]')
  if [[ "$magic" != "89504e470d0a1a0a" ]]; then
    # Fallback check using file utility
    if file "$file_path" 2>/dev/null | grep -q "PNG image data"; then
      : # valid via file utility
    else
      echo "  ❌ [Corrupt PNG] $screen_name/$(basename "$file_path") is not a valid PNG (magic: $magic)."
      ERRORS=$((ERRORS + 1))
      return
    fi
  fi

  TOTAL_IMAGES=$((TOTAL_IMAGES + 1))
}

# Identify screen directories
SCREEN_DIRS=()
while IFS= read -r dir; do
  if [[ -d "$dir" && "$dir" != "$TARGET_DIR" ]]; then
    SCREEN_DIRS+=("$dir")
  fi
done < <(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -type d | sort)

# If target directory itself contains PNGs directly, treat it as a single screen
if [[ ${#SCREEN_DIRS[@]} -eq 0 ]]; then
  if ls "$TARGET_DIR"/*.png &>/dev/null; then
    SCREEN_DIRS=("$TARGET_DIR")
  fi
fi

if [[ ${#SCREEN_DIRS[@]} -eq 0 ]]; then
  echo "❌ Error: No screen subdirectories or PNG artifacts found in $TARGET_DIR"
  exit 1
fi

echo "📋 Found ${#SCREEN_DIRS[@]} screen target(s) to inspect."
echo "--------------------------------------------------------"

for screen_dir in "${SCREEN_DIRS[@]}"; do
  screen_slug=$(basename "$screen_dir")
  TOTAL_SCREENS=$((TOTAL_SCREENS + 1))
  echo "Checking screen: [$screen_slug]"

  # Rule 1: default.png is strictly required
  if [[ ! -f "$screen_dir/default.png" ]]; then
    echo "  ❌ [Missing Default State] $screen_slug/default.png does not exist."
    ERRORS=$((ERRORS + 1))
  fi

  # Validate all PNG files present in the screen directory
  shopt -s nullglob
  png_files=("$screen_dir"/*.png)
  shopt -u nullglob

  if [[ ${#png_files[@]} -eq 0 ]]; then
    echo "  ❌ [No Screenshots] Screen directory has zero PNG images: $screen_slug"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  for img in "${png_files[@]}"; do
    validate_png_file "$img" "$screen_slug"
  done

  # Check standard states and warn if interactive states are missing
  missing_states=()
  for state in "${STANDARD_STATES[@]}"; do
    if [[ ! -f "$screen_dir/$state" ]]; then
      missing_states+=("$state")
    fi
  done

  if [[ ${#missing_states[@]} -gt 0 ]]; then
    # If default exists but other states are absent, log informational note
    echo "  ℹ️  [State Coverage] Present: $((${#png_files[@]})) state(s). Absent: ${missing_states[*]}"
  fi
done

echo "--------------------------------------------------------"
echo "📊 Validation Summary:"
echo "   Screens evaluated : $TOTAL_SCREENS"
echo "   Images verified   : $TOTAL_IMAGES"
echo "   Total errors      : $ERRORS"
echo "   Total warnings    : $WARNINGS"

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ Capture Gate Status: FAILED ($ERRORS errors detected). Fix issues before vision evaluation."
  exit 1
else
  echo "✅ Capture Gate Status: PASSED. All screenshots are verified and valid."
  exit 0
fi
