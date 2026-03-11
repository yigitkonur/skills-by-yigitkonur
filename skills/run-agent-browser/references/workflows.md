# Workflow Patterns

Reusable patterns for common agent-browser automation scenarios.

## 1. Snapshot-First Loop

The fundamental pattern for all browser automation:

```bash
# 1. Navigate
agent-browser open https://example.com
agent-browser wait --load networkidle

# 2. Snapshot to discover interactive elements
agent-browser snapshot -i

# 3. Interact using refs from snapshot
agent-browser fill @e1 "search query"
agent-browser click @e2

# 4. Re-snapshot after DOM changes
agent-browser wait --load networkidle
agent-browser snapshot -i
```

**Rule:** Always re-snapshot after any action that changes the page. Old refs become invalid after navigation, form submissions, SPA route changes, or dynamic content loading.

## 2. JSON-First Workflow (AI Agents)

Use structured JSON output for deterministic agent parsing:

```bash
# JSON snapshot
agent-browser snapshot -i --json

# JSON element data
agent-browser get text @e1 --json

# Pipe to downstream tools — the JSON schema is {success, data: {origin, refs, snapshot}, error}
agent-browser snapshot -i --json | jq '.data.refs | to_entries[] | select(.value.role == "button")'
```

### Selector Priority (for AI agents)

When targeting elements, prefer this order:

1. **@refs** — always prefer (from `snapshot -i`). Most stable and concise.
2. **Semantic locators** — `find role button click --name "Submit"`. Framework-agnostic.
3. **CSS selectors** — `click "button.submit-btn"`. When refs/semantic unavailable.
4. **XPath** — last resort. Brittle, hard to maintain.

## 3. Error Recovery

Handle failures gracefully in multi-step automations:

```bash
#!/usr/bin/env bash
set -euo pipefail

MAX_RETRIES=3

for ((attempt=1; attempt<=MAX_RETRIES; attempt++)); do
  agent-browser open https://example.com/form
  agent-browser wait --load networkidle

  # Check if redirected (e.g., expired session)
  current_url=$(agent-browser get url)
  if [[ "$current_url" == *"/login"* ]]; then
    echo "Session expired — re-authenticating..."
    agent-browser state load auth.json
    continue
  fi

  # Attempt automation
  agent-browser snapshot -i
  if agent-browser fill @e1 "data" && agent-browser click @e2; then
    agent-browser wait --load networkidle
    echo "✅ Success on attempt $attempt"
    break
  fi

  echo "Attempt $attempt failed, retrying..."
  agent-browser wait 2000
done
```

## 4. Safe Automation Loop

Restrict agent actions to a safe subset with boundaries:

```bash
# Set safety boundaries
export AGENT_BROWSER_ALLOWED_DOMAINS="app.example.com,*.example.com"
export AGENT_BROWSER_CONTENT_BOUNDARIES=1
export AGENT_BROWSER_MAX_OUTPUT=50000
export AGENT_BROWSER_ACTION_POLICY=./policy.json

# Automate within boundaries
agent-browser open https://app.example.com
agent-browser snapshot -i
# ... safe operations only ...
```

See [safety.md](safety.md) for the full governance framework and action policy file format.

## 5. PR-Affected E2E Testing

Test only pages affected by a pull request — fast, targeted validation:

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:3000}"

# Get changed files from current PR
CHANGED_FILES=$(gh pr view --json files -q '.files[].path')

# Map source files to routes (adjust mapping for your framework)
declare -a ROUTES
for file in $CHANGED_FILES; do
  case "$file" in
    src/pages/*.tsx)       ROUTES+=("/${file#src/pages/}") ;;
    src/app/*/page.tsx)    ROUTES+=("/${file#src/app/}") ;;
    src/components/*)      ROUTES+=("/") ;;  # Component change — test home
  esac
done

# Deduplicate
ROUTES=($(printf '%s\n' "${ROUTES[@]}" | sort -u))

# Test each affected route
mkdir -p ./e2e-results
for route in "${ROUTES[@]}"; do
  echo "Testing: ${BASE_URL}${route}"
  agent-browser open "${BASE_URL}${route}"
  agent-browser wait --load networkidle
  agent-browser snapshot -i
  slug=$(echo "$route" | tr '/' '-' | sed 's/^-//')
  agent-browser screenshot "./e2e-results/${slug:-home}.png"
done

agent-browser close
echo "✅ Tested ${#ROUTES[@]} routes"
```

## 6. DOM-Evidence Validation

Prioritize DOM assertions over visual checks for reliable, deterministic verification:

```bash
# After performing an action
agent-browser click @e3  # Submit form
agent-browser wait --load networkidle

# DOM evidence (preferred — deterministic, scriptable)
agent-browser snapshot -i
RESULT=$(agent-browser get text @e1)

if [[ "$RESULT" == *"Success"* ]]; then
  echo "✅ PASS: $RESULT"
else
  # Visual evidence as supplement (for human review)
  agent-browser screenshot "./evidence/failure-$(date +%s).png"
  echo "❌ FAIL: Expected 'Success', got: $RESULT"
  exit 1
fi
```

**Principle:** DOM evidence is the source of truth. Screenshots are supplementary evidence for human review, not primary assertions.

## 7. Multi-Account Parallel Testing

Test role-based permissions with concurrent sessions:

```bash
# Login each account in its own session
for account in admin editor viewer; do
  agent-browser --session "$account" open https://app.example.com/login
  agent-browser --session "$account" snapshot -i
  agent-browser --session "$account" fill @e1 "${account}@example.com"
  agent-browser --session "$account" fill @e2 "password"
  agent-browser --session "$account" click @e3
  agent-browser --session "$account" wait --url "**/dashboard"
done

# Test permissions per role
agent-browser --session admin open https://app.example.com/admin
ADMIN_URL=$(agent-browser --session admin get url)

agent-browser --session editor open https://app.example.com/admin
EDITOR_URL=$(agent-browser --session editor get url)

agent-browser --session viewer open https://app.example.com/admin
VIEWER_URL=$(agent-browser --session viewer get url)

echo "Admin:  $ADMIN_URL"    # → /admin (access granted)
echo "Editor: $EDITOR_URL"   # → /forbidden or /dashboard
echo "Viewer: $VIEWER_URL"   # → /forbidden or /dashboard

# Cleanup
for account in admin editor viewer; do
  agent-browser --session "$account" close
done
```

## 8. Data Extraction Pipeline

Scrape structured data across multiple pages:

```bash
#!/usr/bin/env bash
set -euo pipefail

agent-browser open https://example.com/products
agent-browser wait --load networkidle

# Extract data from listing page
agent-browser snapshot -i --json | jq -r '.data.refs | to_entries[] | select(.value.role == "link") | .value.name' > products.txt

# Follow each link and extract detail
while IFS= read -r product; do
  # Use find text for safer matching (handles special chars)
  agent-browser find text "$product" click
  agent-browser wait --load networkidle
  
  PRICE=$(agent-browser get text ".price")
  DESC=$(agent-browser get text ".description")
  echo "$product|$PRICE|$DESC" >> product-details.csv
  
  agent-browser back
  agent-browser wait --load networkidle
  agent-browser snapshot -i
done < products.txt

agent-browser close
```

## 9. Multi-Element Data Extraction (AI Agent Pattern)

When `get text` fails due to strict mode (multiple matches), use `eval --stdin`:

```bash
# Step 1: Scope the snapshot
agent-browser snapshot -i -s "article"

# Step 2: Extract via eval heredoc
agent-browser eval --stdin <<'EVALEOF'
const items = document.querySelectorAll('article.story h2 a');
JSON.stringify(
  Array.from(items).slice(0, 10).map(el => ({
    title: el.textContent.trim(),
    url: el.href
  })),
  null, 2
);
EVALEOF

# Step 3: Verify count
agent-browser get count "article.story h2 a"
```

**Key rule:** `eval --stdin` with a heredoc is the reliable JS execution pattern. Inline `eval "..."` breaks on complex JS due to shell escaping.

## 10. Hidden UI Component Discovery

Custom UI components (dropdowns, popovers, accordions) hide children until activated:

```bash
# 1. Initial snapshot -- dropdown content is hidden
agent-browser snapshot -i
# Shows: button "Language" [ref=e5] -- options hidden

# 2. Click the trigger
agent-browser click @e5
agent-browser wait 500
agent-browser snapshot -i
# Now shows: link "Python" [ref=e12], link "JavaScript" [ref=e13]

# 3. Interact with revealed options
agent-browser click @e13
```

Signs of hidden components: expected UI elements missing from snapshot, buttons with arrows/chevrons, interactive widgets.

## Agent Steering Notes

### Snapshot output is not the full page

`snapshot -i` omits non-interactive text to save tokens. Use `get text` or `eval` for page content extraction.

### Refs are ephemeral

After navigation, SPA route changes, tab switches, or dynamic content loads, all refs are invalid. Always re-snapshot.

### CSS selectors have strict mode

`get text`, `get value`, `is visible` require exactly ONE element match. Use `eval --stdin` for multiple elements.

### diff requires a subcommand

`agent-browser diff` alone fails. Valid: `diff snapshot`, `diff screenshot --baseline`, `diff url url1 url2`.

### back works, go back does not

Use `agent-browser back` (not `go back`).
