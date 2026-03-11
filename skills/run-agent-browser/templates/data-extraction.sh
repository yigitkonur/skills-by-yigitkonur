#!/bin/bash
# =============================================================================
# Data Extraction Template
# =============================================================================
# Extracts structured data from web pages with optional pagination support.
#
# Usage:
#   ./data-extraction.sh <url> [output_dir]
#
# Examples:
#   ./data-extraction.sh https://example.com/products ./output
#   ./data-extraction.sh https://news.ycombinator.com ./hn-data
#
# Output:
#   - extracted-data.json   (structured JSON data)
#   - page-snapshots/       (snapshot of each page)
#   - screenshots/          (screenshot of each page)
# =============================================================================
set -euo pipefail

URL="${1:?Usage: $0 <url> [output_dir]}"
OUTPUT_DIR="${2:-./extracted-data}"
MAX_PAGES="${MAX_PAGES:-10}"        # Max pages to paginate (override with env var)
NEXT_SELECTOR="${NEXT_SELECTOR:-}"  # CSS selector for "Next" button (auto-detect if empty)

# Setup output directories
mkdir -p "$OUTPUT_DIR/page-snapshots" "$OUTPUT_DIR/screenshots"
DATA_FILE="$OUTPUT_DIR/extracted-data.json"

echo "=== Data Extraction ==="
echo "URL: $URL"
echo "Output: $OUTPUT_DIR"
echo "Max pages: $MAX_PAGES"
echo ""

# Navigate to target
agent-browser open "$URL"
agent-browser wait --load networkidle

PAGE=1
echo "[]" > "$DATA_FILE"

while [ "$PAGE" -le "$MAX_PAGES" ]; do
  echo "--- Page $PAGE ---"

  # Take snapshot for analysis
  agent-browser snapshot -i > "$OUTPUT_DIR/page-snapshots/page-${PAGE}.txt"

  # Take screenshot for reference
  agent-browser screenshot "$OUTPUT_DIR/screenshots/page-${PAGE}.png"

  # =========================================================================
  # CUSTOMIZE: Extract data from the page
  # =========================================================================
  # Option 1: Extract all text content
  # agent-browser get text body >> "$OUTPUT_DIR/all-text.txt"

  # Option 2: Extract specific elements via JavaScript (RECOMMENDED)
  # Modify the selector and field extraction below to match your target page.
  PAGE_DATA=$(agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll('.item, .card, .product, article, .result')).map(el => ({
    title: (el.querySelector('h1, h2, h3, h4, .title, .name') || {}).textContent?.trim() || '',
    description: (el.querySelector('p, .description, .summary, .excerpt') || {}).textContent?.trim() || '',
    link: (el.querySelector('a') || {}).href || '',
    image: (el.querySelector('img') || {}).src || '',
    price: (el.querySelector('.price, .cost, .amount') || {}).textContent?.trim() || '',
    metadata: (el.querySelector('.meta, .date, .author, time') || {}).textContent?.trim() || ''
  })).filter(item => item.title || item.description)
)
EVALEOF
  )

  # Option 3: Extract data using get text with specific refs
  # agent-browser get text @e1 --json

  # Option 4: Extract tabular data
  # TABLE_DATA=$(agent-browser eval --stdin <<'EVALEOF'
  # JSON.stringify(
  #   Array.from(document.querySelectorAll('table tr')).map(row =>
  #     Array.from(row.querySelectorAll('td, th')).map(cell => cell.textContent.trim())
  #   )
  # )
  # EVALEOF
  # )
  # =========================================================================

  # Append page data to results
  if [ -n "$PAGE_DATA" ] && [ "$PAGE_DATA" != "[]" ] && [ "$PAGE_DATA" != "null" ]; then
    # Merge arrays: existing + new page data
    jq -s '.[0] + .[1]' "$DATA_FILE" <(echo "$PAGE_DATA") > "${DATA_FILE}.tmp"
    mv "${DATA_FILE}.tmp" "$DATA_FILE"
    ITEM_COUNT=$(echo "$PAGE_DATA" | jq 'length')
    echo "  Extracted $ITEM_COUNT items"
  else
    echo "  No items found on this page"
  fi

  # Check for next page
  if [ -n "$NEXT_SELECTOR" ]; then
    # Use provided selector
    HAS_NEXT=$(agent-browser is visible "$NEXT_SELECTOR" 2>/dev/null || echo "false")
  else
    # Auto-detect common pagination patterns
    HAS_NEXT=$(agent-browser eval --stdin <<'EVALEOF' 2>/dev/null || echo "false"
(() => {
  const next = document.querySelector(
    'a[rel="next"], .next a, .pagination .next, [aria-label="Next"], button:has(> .next-icon)'
  );
  return next && !next.disabled && next.offsetParent !== null ? 'true' : 'false';
})()
EVALEOF
    )
  fi

  if [ "$HAS_NEXT" = "true" ] || [ "$HAS_NEXT" = '"true"' ]; then
    echo "  Navigating to next page..."
    if [ -n "$NEXT_SELECTOR" ]; then
      agent-browser click "$NEXT_SELECTOR"
    else
      agent-browser find text "Next" click 2>/dev/null || \
      agent-browser eval 'document.querySelector("a[rel=\"next\"], .next a, .pagination .next").click()' 2>/dev/null || \
      break
    fi
    agent-browser wait --load networkidle
    PAGE=$((PAGE + 1))
  else
    echo "  No more pages."
    break
  fi
done

# Summary
TOTAL=$(jq 'length' "$DATA_FILE")
echo ""
echo "=== Extraction Complete ==="
echo "Pages scraped: $((PAGE))"
echo "Total items: $TOTAL"
echo "Data file: $DATA_FILE"
echo "Screenshots: $OUTPUT_DIR/screenshots/"
echo "Snapshots: $OUTPUT_DIR/page-snapshots/"

# Optional: Convert to CSV
# jq -r '["title","description","link","price"], (.[] | [.title, .description, .link, .price]) | @csv' "$DATA_FILE" > "$OUTPUT_DIR/extracted-data.csv"
# echo "CSV file: $OUTPUT_DIR/extracted-data.csv"

agent-browser close
