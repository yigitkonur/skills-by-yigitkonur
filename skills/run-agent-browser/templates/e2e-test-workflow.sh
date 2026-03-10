#!/usr/bin/env bash
# e2e-test-workflow.sh — PR-affected page E2E testing
# Usage: ./e2e-test-workflow.sh [base-url]
# Requires: gh CLI (for PR file detection)
set -euo pipefail

BASE_URL="${1:-http://localhost:3000}"
RESULTS_DIR="./e2e-results"
PASS=0
FAIL=0

mkdir -p "$RESULTS_DIR"

# === Detect affected routes from PR ===
echo "🔍 Detecting changed files from PR..."
if ! CHANGED_FILES=$(gh pr view --json files -q '.files[].path' 2>/dev/null); then
  echo "⚠️  No PR context found. Testing default routes."
  CHANGED_FILES=""
fi

# === Map files to routes (customize for your framework) ===
declare -a ROUTES
if [[ -n "$CHANGED_FILES" ]]; then
  while IFS= read -r file; do
    case "$file" in
      src/pages/*.tsx|src/pages/*.jsx)
        route="${file#src/pages/}"
        route="${route%.tsx}"
        route="${route%.jsx}"
        route="${route%/index}"
        ROUTES+=("/${route}")
        ;;
      src/app/*/page.tsx|src/app/*/page.jsx)
        route="${file#src/app/}"
        route="${route%/page.tsx}"
        route="${route%/page.jsx}"
        ROUTES+=("/${route}")
        ;;
      src/components/*|src/lib/*|src/utils/*)
        ROUTES+=("/")  # Shared code — test home page
        ;;
    esac
  done <<< "$CHANGED_FILES"
fi

# Fallback: test home page if no routes detected
if [[ ${#ROUTES[@]} -eq 0 ]]; then
  ROUTES=("/")
fi

# Deduplicate routes
ROUTES=($(printf '%s\n' "${ROUTES[@]}" | sort -u))

echo "🧪 Testing ${#ROUTES[@]} route(s) against ${BASE_URL}"
echo ""

# === Test each route ===
for route in "${ROUTES[@]}"; do
  full_url="${BASE_URL}${route}"
  slug=$(echo "$route" | tr '/' '-' | sed 's/^-//')
  slug="${slug:-home}"

  echo "  Testing: ${full_url}"

  # Navigate
  if ! agent-browser open "$full_url" 2>/dev/null; then
    echo "  ❌ FAIL: Could not open $full_url"
    ((FAIL++))
    continue
  fi

  agent-browser wait --load networkidle 2>/dev/null || true

  # Snapshot and screenshot
  agent-browser snapshot -i > "$RESULTS_DIR/${slug}-snapshot.txt" 2>/dev/null || true
  agent-browser screenshot "$RESULTS_DIR/${slug}.png" 2>/dev/null || true

  # Basic health check: page loaded with content
  PAGE_TITLE=$(agent-browser get title 2>/dev/null || echo "")
  if [[ -n "$PAGE_TITLE" ]]; then
    echo "  ✅ PASS: ${PAGE_TITLE}"
    ((PASS++))
  else
    echo "  ❌ FAIL: No page title (blank or error page)"
    ((FAIL++))
  fi
done

# === Cleanup ===
agent-browser close 2>/dev/null || true

# === Summary ===
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "  Screenshots: ${RESULTS_DIR}/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Exit with failure if any tests failed
[[ $FAIL -eq 0 ]] || exit 1
