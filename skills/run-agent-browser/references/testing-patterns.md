# Testing Patterns

## Form Validation Testing

### Complete Form Test

```bash
# Navigate and discover form structure
agent-browser open https://example.com/signup
agent-browser snapshot -i

# Fill all fields
agent-browser fill @e1 "testuser"
agent-browser fill @e2 "test@example.com"
agent-browser fill @e3 "SecurePass123!"
agent-browser fill @e4 "SecurePass123!"
agent-browser select @e5 "United States"
agent-browser check @e6                    # Accept terms

# Screenshot before submission
agent-browser screenshot pre-submit.png

# Submit
agent-browser click @e7
agent-browser wait --load networkidle

# Verify success
agent-browser snapshot -i
SUCCESS=$(agent-browser get text ".success-message" 2>/dev/null || echo "")
if [ -n "$SUCCESS" ]; then
  echo "PASS: Form submitted successfully"
else
  echo "FAIL: No success message found"
  agent-browser screenshot failure.png
fi
```

### Validation Error Testing

```bash
# Test empty submission
agent-browser open https://example.com/signup
agent-browser snapshot -i
agent-browser click @e7                    # Submit without filling
agent-browser wait 1000

# Check for validation errors
agent-browser snapshot -i
ERRORS=$(agent-browser get text ".error" 2>/dev/null || echo "")
echo "Validation errors: $ERRORS"

# Test invalid email
agent-browser fill @e2 "not-an-email"
agent-browser click @e7
agent-browser wait 1000
agent-browser snapshot -i

# Test password mismatch
agent-browser fill @e3 "password1"
agent-browser fill @e4 "password2"
agent-browser click @e7
agent-browser wait 1000
agent-browser snapshot -i
```

## E2E User Journey

Test a complete user flow from start to finish:

```bash
#!/bin/bash
set -euo pipefail

RESULTS=()

# Step 1: Sign Up
agent-browser open https://example.com/signup
agent-browser snapshot -i
agent-browser fill @e1 "newuser_$(date +%s)"
agent-browser fill @e2 "test-$(date +%s)@example.com"
agent-browser fill @e3 "TestPass123!"
agent-browser click @e4
agent-browser wait --url "**/dashboard"
RESULTS+=("Signup: PASS")

# Step 2: Browse Products
agent-browser open https://example.com/products
agent-browser wait --load networkidle
agent-browser snapshot -i
PRODUCT_COUNT=$(agent-browser get count ".product-card")
if [ "$PRODUCT_COUNT" -gt 0 ]; then
  RESULTS+=("Browse Products ($PRODUCT_COUNT items): PASS")
else
  RESULTS+=("Browse Products: FAIL (no products)")
fi

# Step 3: Add to Cart
agent-browser click @e1
agent-browser wait --text "Added to cart"
agent-browser snapshot -i
RESULTS+=("Add to Cart: PASS")

# Step 4: Checkout
agent-browser open https://example.com/cart
agent-browser snapshot -i
agent-browser click @e5  # Checkout button
agent-browser wait --load networkidle
agent-browser snapshot -i
RESULTS+=("Checkout: PASS")

# Report
echo "=== E2E Test Results ==="
for r in "${RESULTS[@]}"; do echo "  $r"; done

agent-browser close
```

## Responsive Testing

Test the same page across multiple viewports:

```bash
#!/bin/bash
URL="https://example.com"
VIEWPORTS=("375 812 iPhone" "768 1024 iPad" "1280 720 Laptop" "1920 1080 Desktop")

agent-browser open "$URL"
agent-browser wait --load networkidle

for viewport in "${VIEWPORTS[@]}"; do
  read -r W H NAME <<< "$viewport"
  agent-browser set viewport "$W" "$H"
  agent-browser wait 500
  agent-browser screenshot "responsive-${NAME}.png"
  echo "Captured: responsive-${NAME}.png (${W}x${H})"
done

agent-browser close
```

## Visual Regression Testing

Compare screenshots against baselines to detect unintended visual changes:

```bash
#!/bin/bash
URL="https://example.com"
BASELINE_DIR="./baselines"
CURRENT_DIR="./current"
DIFF_DIR="./diffs"
mkdir -p "$BASELINE_DIR" "$CURRENT_DIR" "$DIFF_DIR"

PAGE="homepage"

agent-browser open "$URL"
agent-browser wait --load networkidle
agent-browser set viewport 1280 720
agent-browser screenshot "$CURRENT_DIR/${PAGE}.png"

if [ -f "$BASELINE_DIR/${PAGE}.png" ]; then
  # Use agent-browser diff for comparison
  agent-browser diff screenshot \
    --baseline "$BASELINE_DIR/${PAGE}.png" \
    --current "$CURRENT_DIR/${PAGE}.png"

  # Or use ImageMagick for detailed comparison
  if command -v compare &> /dev/null; then
    compare -metric RMSE \
      "$BASELINE_DIR/${PAGE}.png" \
      "$CURRENT_DIR/${PAGE}.png" \
      "$DIFF_DIR/${PAGE}-diff.png" 2>&1
  fi
else
  echo "No baseline exists. Saving current as baseline."
  cp "$CURRENT_DIR/${PAGE}.png" "$BASELINE_DIR/${PAGE}.png"
fi

agent-browser close
```

## Multi-Page Navigation Testing

### Tab Management

```bash
# Open multiple tabs and verify content
agent-browser open https://example.com
agent-browser snapshot -i

# Click a link that opens in new tab
agent-browser click @e1 --new-tab

# Switch to new tab and verify
agent-browser tab 1
agent-browser wait --load networkidle
agent-browser snapshot -i
NEW_URL=$(agent-browser get url)
echo "New tab URL: $NEW_URL"

# Switch back to original tab
agent-browser tab 0
agent-browser snapshot -i
```

### Pagination Testing

```bash
#!/bin/bash
PAGE=1
TOTAL_ITEMS=0

agent-browser open "https://example.com/products?page=1"
agent-browser wait --load networkidle

while true; do
  agent-browser snapshot -i
  ITEMS=$(agent-browser get count ".product-item")
  TOTAL_ITEMS=$((TOTAL_ITEMS + ITEMS))
  echo "Page $PAGE: $ITEMS items"

  # Check for next page button
  HAS_NEXT=$(agent-browser find text "Next" 2>/dev/null && echo "yes" || echo "no")
  if [ "$HAS_NEXT" = "no" ]; then
    break
  fi

  agent-browser find text "Next" click
  agent-browser wait --load networkidle
  PAGE=$((PAGE + 1))
done

echo "Total items across $PAGE pages: $TOTAL_ITEMS"
```

## Error Handling Patterns

### Retry with Exponential Backoff

```bash
retry_action() {
  local max_attempts=$1
  shift
  local cmd="$@"
  local attempt=1
  local wait_time=1000

  while [ $attempt -le $max_attempts ]; do
    if eval "$cmd"; then
      return 0
    fi
    echo "Attempt $attempt/$max_attempts failed. Waiting ${wait_time}ms..."
    agent-browser wait $wait_time
    wait_time=$((wait_time * 2))
    attempt=$((attempt + 1))
    agent-browser snapshot -i  # Refresh refs
  done
  return 1
}

# Usage
retry_action 3 'agent-browser click @e1'
```

### Graceful Error Recovery

```bash
# Detect and handle error modals
handle_errors() {
  local error_text
  error_text=$(agent-browser get text ".error-modal, .alert-danger, [role='alert']" 2>/dev/null || echo "")

  if [ -n "$error_text" ]; then
    echo "ERROR DETECTED: $error_text"
    agent-browser screenshot "error-$(date +%s).png"

    # Try to dismiss
    agent-browser find text "Close" click 2>/dev/null || \
    agent-browser find text "OK" click 2>/dev/null || \
    agent-browser find role button click --name "Close" 2>/dev/null || \
    agent-browser press Escape 2>/dev/null

    return 1
  fi
  return 0
}

# Use after each major action
agent-browser click @e5
agent-browser wait --load networkidle
handle_errors || echo "Recovered from error"
```

### Timeout with Screenshot on Failure

```bash
# Wrapper that captures state on failure
safe_action() {
  local description="$1"
  shift
  
  if ! eval "$@"; then
    echo "FAILED: $description"
    agent-browser screenshot "fail-${description// /-}.png"
    agent-browser snapshot -i > "fail-${description// /-}-snapshot.txt"
    return 1
  fi
  echo "OK: $description"
}

safe_action "login" 'agent-browser click @e3 && agent-browser wait --url "**/dashboard"'
safe_action "navigate" 'agent-browser open https://example.com/settings'
```

## Data-Driven Testing

### CSV Test Data

```bash
#!/bin/bash
# test-data.csv:
# name,email,expected_result
# "Valid User","valid@example.com","success"
# "","empty@example.com","error"
# "Test","invalid-email","error"

while IFS=, read -r NAME EMAIL EXPECTED; do
  echo "Testing: name=$NAME email=$EMAIL expected=$EXPECTED"

  agent-browser open https://example.com/signup
  agent-browser snapshot -i

  [ -n "$NAME" ] && agent-browser fill @e1 "$NAME"
  [ -n "$EMAIL" ] && agent-browser fill @e2 "$EMAIL"
  agent-browser click @e3
  agent-browser wait 2000
  agent-browser snapshot -i

  RESULT=$(agent-browser get text ".message" 2>/dev/null || echo "none")

  if echo "$RESULT" | grep -qi "$EXPECTED"; then
    echo "  PASS"
  else
    echo "  FAIL (got: $RESULT)"
    agent-browser screenshot "fail-${NAME:-empty}.png"
  fi
done < test-data.csv
```

### JSON Scenario Testing

```bash
#!/bin/bash
# scenarios.json:
# [
#   {"action": "fill", "selector": "@e1", "value": "test@example.com"},
#   {"action": "click", "selector": "@e2"},
#   {"action": "wait", "condition": "networkidle"},
#   {"action": "assert_text", "selector": ".result", "expected": "Success"}
# ]

agent-browser open https://example.com
agent-browser snapshot -i

jq -c '.[]' scenarios.json | while read -r step; do
  ACTION=$(echo "$step" | jq -r '.action')
  SELECTOR=$(echo "$step" | jq -r '.selector // empty')
  VALUE=$(echo "$step" | jq -r '.value // empty')
  EXPECTED=$(echo "$step" | jq -r '.expected // empty')

  case "$ACTION" in
    fill)     agent-browser fill "$SELECTOR" "$VALUE" ;;
    click)    agent-browser click "$SELECTOR" ;;
    wait)     agent-browser wait --load "$(echo "$step" | jq -r '.condition')" ;;
    snapshot) agent-browser snapshot -i ;;
    assert_text)
      ACTUAL=$(agent-browser get text "$SELECTOR")
      if echo "$ACTUAL" | grep -q "$EXPECTED"; then
        echo "PASS: $SELECTOR contains '$EXPECTED'"
      else
        echo "FAIL: $SELECTOR = '$ACTUAL', expected '$EXPECTED'"
      fi
      ;;
  esac
done
```

## Accessibility Testing

### ARIA Label Verification

```bash
agent-browser open https://example.com
agent-browser snapshot -i

# Check that interactive elements have ARIA labels
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll('button, a, input, select, textarea'))
    .filter(el => !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby') && !el.textContent.trim())
    .map(el => ({ tag: el.tagName, id: el.id, class: el.className }))
)
EVALEOF
```

### Keyboard Navigation

```bash
# Test that all interactive elements are keyboard-accessible
agent-browser open https://example.com
FOCUSED_ELEMENTS=()

for i in $(seq 1 20); do
  agent-browser press Tab
  FOCUSED=$(agent-browser eval 'document.activeElement.tagName + "#" + document.activeElement.id')
  FOCUSED_ELEMENTS+=("$FOCUSED")
  echo "Tab $i: $FOCUSED"
done

echo "Keyboard navigation path: ${FOCUSED_ELEMENTS[*]}"
```

## Performance Testing

### Page Load Timing

```bash
agent-browser open https://example.com
agent-browser wait --load networkidle

# Get navigation timing metrics
agent-browser eval --stdin <<'EVALEOF'
const t = performance.timing;
JSON.stringify({
  dns: t.domainLookupEnd - t.domainLookupStart,
  tcp: t.connectEnd - t.connectStart,
  ttfb: t.responseStart - t.requestStart,
  download: t.responseEnd - t.responseStart,
  domInteractive: t.domInteractive - t.navigationStart,
  domComplete: t.domComplete - t.navigationStart,
  fullLoad: t.loadEventEnd - t.navigationStart
}, null, 2)
EVALEOF
```

### Resource Count & Size

```bash
agent-browser eval --stdin <<'EVALEOF'
const resources = performance.getEntriesByType('resource');
const byType = {};
resources.forEach(r => {
  const ext = r.name.split('.').pop().split('?')[0];
  byType[ext] = byType[ext] || { count: 0, totalSize: 0 };
  byType[ext].count++;
  byType[ext].totalSize += r.transferSize || 0;
});
JSON.stringify(byType, null, 2)
EVALEOF
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install agent-browser
        run: |
          npm install -g agent-browser
          npx playwright install chromium
          npx playwright install-deps chromium

      - name: Start app
        run: npm start &

      - name: Run E2E tests
        run: |
          agent-browser set viewport 1280 720
          ./tests/e2e/run-all.sh

      - name: Upload artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-failures
          path: |
            *.png
            *.webm
            fail-*.txt
```

### Test Report Template

```bash
#!/bin/bash
# Generate markdown test report

REPORT="test-report.md"
TOTAL=0
PASSED=0
FAILED=0

echo "# E2E Test Report" > "$REPORT"
echo "" >> "$REPORT"
echo "**Date:** $(date -u '+%Y-%m-%d %H:%M UTC')" >> "$REPORT"
echo "" >> "$REPORT"
echo "| Test | Status | Duration |" >> "$REPORT"
echo "|------|--------|----------|" >> "$REPORT"

run_test() {
  local name="$1"
  local cmd="$2"
  local start=$(date +%s)
  TOTAL=$((TOTAL + 1))

  if eval "$cmd" 2>/dev/null; then
    local duration=$(($(date +%s) - start))
    echo "| $name | ✅ PASS | ${duration}s |" >> "$REPORT"
    PASSED=$((PASSED + 1))
  else
    local duration=$(($(date +%s) - start))
    echo "| $name | ❌ FAIL | ${duration}s |" >> "$REPORT"
    FAILED=$((FAILED + 1))
  fi
}

# Run tests
run_test "Homepage loads" 'agent-browser open https://example.com && agent-browser wait --load networkidle'
run_test "Login works" './tests/e2e/test-login.sh'
run_test "Search works" './tests/e2e/test-search.sh'

echo "" >> "$REPORT"
echo "**Total:** $TOTAL | **Passed:** $PASSED | **Failed:** $FAILED" >> "$REPORT"

cat "$REPORT"
```
