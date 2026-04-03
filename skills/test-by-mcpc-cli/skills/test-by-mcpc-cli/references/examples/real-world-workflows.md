# Real-world workflow scripts

Complete, copy-paste-ready bash scripts for common `mcpc` testing and automation patterns.

**Critical syntax reminders:**
- Connect: `mcpc <target> connect @<session>` — target first, then connect, then session
- Close: `mcpc @session close`
- JSON output: `mcpc --json @session command`
- Arguments: `key:=value` (no spaces around `:=`)

---

## Workflow 1: MCP server smoke test suite

Tests any MCP server end-to-end: connect, verify capabilities, exercise every primitive, assert results, close.

```bash
#!/usr/bin/env bash
# smoke-test.sh — end-to-end smoke test for any MCP server
# Usage: ./smoke-test.sh <server-url-or-entry-name> [session-name]
# Example: ./smoke-test.sh mcp.apify.com @smoke
#          MCPC_CONFIG=~/.vscode/mcp.json ./smoke-test.sh filesystem @smoke

set -euo pipefail

SERVER="${1:?Usage: $0 <server> [session-name]}"
MCPC_CONFIG="${MCPC_CONFIG:-}"
SESSION="${2:-@smoke-$$}"
PASS=0
FAIL=0
ERRORS=()

# ── helpers ──────────────────────────────────────────────────────────────────

log()  { printf '\033[0;34m[INFO]\033[0m  %s\n' "$*"; }
ok()   { printf '\033[0;32m[PASS]\033[0m  %s\n' "$*"; ((PASS++)) || true; }
fail() { printf '\033[0;31m[FAIL]\033[0m  %s\n' "$*"; ((FAIL++)) || true; ERRORS+=("$*"); }

assert_exit() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    ok "$label"
  else
    fail "$label (exit $?)"
  fi
}

assert_json_field() {
  # assert_json_field <label> <jq-filter> <expected> <json-string>
  local label="$1" filter="$2" expected="$3" json="$4"
  local actual
  actual=$(printf '%s' "$json" | jq -r "$filter" 2>/dev/null || echo "__jq_error__")
  if [[ "$actual" == "$expected" ]]; then
    ok "$label"
  else
    fail "$label — expected '$expected', got '$actual'"
  fi
}

cleanup() {
  log "Closing session $SESSION"
  mcpc @"${SESSION#@}" close 2>/dev/null || true
}
trap cleanup EXIT

# ── 1. connect ────────────────────────────────────────────────────────────────

log "Connecting to $SERVER as $SESSION"
if [ -n "$MCPC_CONFIG" ]; then
  CONNECT_CMD=(mcpc --config "$MCPC_CONFIG" "$SERVER" connect "$SESSION")
else
  CONNECT_CMD=(mcpc "$SERVER" connect "$SESSION")
fi

if ! "${CONNECT_CMD[@]}" 2>&1; then
  fail "connect: could not establish session"
  echo "RESULT: 0 passed, 1 failed — aborting (no session)" >&2
  exit 3
fi
ok "connect"

# ── 2. verify session info / capabilities ────────────────────────────────────

log "Fetching session info"
INFO_JSON=$(mcpc --json "${SESSION}" 2>/dev/null)

assert_json_field "server info: protocolVersion present" \
  '.protocolVersion // empty | length > 0' "true" "$INFO_JSON"

assert_json_field "server info: serverInfo.name present" \
  '.serverInfo.name // "" | length > 0' "true" "$INFO_JSON"

assert_json_field "server info: _mcpc.sessionName matches" \
  '._mcpc.sessionName' "$SESSION" "$INFO_JSON"

PROTOCOL_VERSION=$(printf '%s' "$INFO_JSON" | jq -r '.protocolVersion // "unknown"')
log "Protocol version: $PROTOCOL_VERSION"

# ── 3. list tools ─────────────────────────────────────────────────────────────

log "Listing tools"
TOOLS_JSON=$(mcpc --json "$SESSION" tools-list 2>/dev/null)
TOOL_COUNT=$(printf '%s' "$TOOLS_JSON" | jq 'length' 2>/dev/null || echo 0)

if [[ "$TOOL_COUNT" -ge 0 ]]; then
  ok "tools-list: returned valid JSON array ($TOOL_COUNT tools)"
else
  fail "tools-list: invalid response"
fi

# ── 4. call first tool (schema introspection only — no destructive call) ──────

if [[ "$TOOL_COUNT" -gt 0 ]]; then
  FIRST_TOOL=$(printf '%s' "$TOOLS_JSON" | jq -r '.[0].name')
  log "Fetching schema for first tool: $FIRST_TOOL"
  TOOL_SCHEMA=$(mcpc --json "$SESSION" tools-get "$FIRST_TOOL" 2>/dev/null)

  assert_json_field "tools-get: name matches" '.name' "$FIRST_TOOL" "$TOOL_SCHEMA"
  assert_json_field "tools-get: inputSchema present" \
    '.inputSchema | type' "object" "$TOOL_SCHEMA"
else
  log "No tools to introspect (server has 0 tools)"
fi

# ── 5. list resources ─────────────────────────────────────────────────────────

log "Listing resources"
if RESOURCES_JSON=$(mcpc --json "$SESSION" resources-list 2>/dev/null); then
  RES_COUNT=$(printf '%s' "$RESOURCES_JSON" | jq 'length' 2>/dev/null || echo 0)
  ok "resources-list: returned JSON array ($RES_COUNT resources)"

  # If there are resources, read the first one
  if [[ "$RES_COUNT" -gt 0 ]]; then
    FIRST_URI=$(printf '%s' "$RESOURCES_JSON" | jq -r '.[0].uri')
    log "Reading first resource: $FIRST_URI"
    if RES_CONTENT=$(mcpc --json "$SESSION" resources-read "$FIRST_URI" 2>/dev/null); then
      assert_json_field "resources-read: contents array present" \
        '.contents | type' "array" "$RES_CONTENT"
    else
      fail "resources-read: failed for $FIRST_URI"
    fi
  fi
else
  log "resources-list: not supported or empty (skipping)"
fi

# ── 6. list resource templates ────────────────────────────────────────────────

log "Listing resource templates"
if TEMPLATES_JSON=$(mcpc --json "$SESSION" resources-templates-list 2>/dev/null); then
  TMPL_COUNT=$(printf '%s' "$TEMPLATES_JSON" | jq 'length' 2>/dev/null || echo 0)
  ok "resources-templates-list: returned JSON array ($TMPL_COUNT templates)"
else
  log "resources-templates-list: not supported (skipping)"
fi

# ── 7. list prompts ───────────────────────────────────────────────────────────

log "Listing prompts"
if PROMPTS_JSON=$(mcpc --json "$SESSION" prompts-list 2>/dev/null); then
  PROMPT_COUNT=$(printf '%s' "$PROMPTS_JSON" | jq 'length' 2>/dev/null || echo 0)
  ok "prompts-list: returned JSON array ($PROMPT_COUNT prompts)"
else
  log "prompts-list: not supported (skipping)"
fi

# ── 8. ping ───────────────────────────────────────────────────────────────────

log "Pinging server"
PING_JSON=$(mcpc --json "$SESSION" ping 2>/dev/null)
if printf '%s' "$PING_JSON" | jq -e '.latencyMs // .roundtripMs // .ok // true' >/dev/null 2>&1; then
  ok "ping: server responded"
else
  fail "ping: unexpected response — $PING_JSON"
fi

# ── 9. report ─────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "Server : %s\n" "$SERVER"
printf "Protocol: %s\n" "$PROTOCOL_VERSION"
printf "Tools   : %d\n" "$TOOL_COUNT"
printf "Results : \033[0;32m%d passed\033[0m, \033[0;31m%d failed\033[0m\n" "$PASS" "$FAIL"

if [[ "${#ERRORS[@]}" -gt 0 ]]; then
  echo ""
  echo "Failures:"
  for err in "${ERRORS[@]}"; do
    printf "  - %s\n" "$err"
  done
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
exit 0
```

---

## Workflow 2: Multi-server comparison

Connects to two or more servers and compares their tool names, capability flags, and protocol versions side-by-side.

```bash
#!/usr/bin/env bash
# compare-servers.sh — compare capabilities of multiple MCP servers
# Usage: ./compare-servers.sh <server1> <server2> [server3 ...]
# Example: ./compare-servers.sh mcp.apify.com localhost:3000

set -euo pipefail

SERVERS=("$@")
if [[ "${#SERVERS[@]}" -lt 2 ]]; then
  echo "Usage: $0 <server1> <server2> [server3 ...]" >&2
  exit 1
fi

SESSIONS=()
SCHEMA_DIR=$(mktemp -d)

cleanup() {
  for s in "${SESSIONS[@]}"; do
    mcpc @"${s#@}" close 2>/dev/null || true
  done
  rm -rf "$SCHEMA_DIR"
}
trap cleanup EXIT

# ── connect all servers ───────────────────────────────────────────────────────

echo "Connecting to ${#SERVERS[@]} servers..."
for i in "${!SERVERS[@]}"; do
  SESSION="@cmp-$i-$$"
  SESSIONS+=("$SESSION")
  echo "  [$((i+1))] ${SERVERS[$i]} → $SESSION"
  mcpc "${SERVERS[$i]}" connect "$SESSION" 2>/dev/null
done

echo ""

# ── collect info and tools for each server ────────────────────────────────────

declare -A SERVER_PROTO
declare -A SERVER_NAME
declare -A SERVER_TOOLS

for i in "${!SESSIONS[@]}"; do
  SESSION="${SESSIONS[$i]}"
  SERVER="${SERVERS[$i]}"

  INFO=$(mcpc --json "$SESSION" 2>/dev/null)
  SERVER_PROTO[$i]=$(printf '%s' "$INFO" | jq -r '.protocolVersion // "unknown"')
  SERVER_NAME[$i]=$(printf '%s' "$INFO" | jq -r '.serverInfo.name // "unknown"')

  TOOLS_JSON=$(mcpc --json "$SESSION" tools-list 2>/dev/null)
  printf '%s' "$TOOLS_JSON" > "$SCHEMA_DIR/tools-$i.json"
  SERVER_TOOLS[$i]=$(printf '%s' "$TOOLS_JSON" | jq -r '[.[].name] | sort | .[]' 2>/dev/null)
done

# ── print comparison table ────────────────────────────────────────────────────

echo "════════════════════════════════════════════════════════"
echo "SERVER COMPARISON"
echo "════════════════════════════════════════════════════════"
printf "%-5s %-30s %-20s %s\n" "IDX" "SERVER" "IMPL NAME" "PROTOCOL"
echo "────────────────────────────────────────────────────────"
for i in "${!SERVERS[@]}"; do
  printf "%-5s %-30s %-20s %s\n" \
    "$((i+1))" \
    "${SERVERS[$i]:0:30}" \
    "${SERVER_NAME[$i]:0:20}" \
    "${SERVER_PROTO[$i]}"
done

echo ""
echo "════════════════════════════════════════════════════════"
echo "TOOL COMPARISON (by name)"
echo "════════════════════════════════════════════════════════"

# Collect the union of all tool names
ALL_TOOLS=$(for i in "${!SESSIONS[@]}"; do
  printf '%s\n' "${SERVER_TOOLS[$i]}"
done | sort -u)

# Build header
printf "%-40s" "TOOL NAME"
for i in "${!SERVERS[@]}"; do
  printf " %-6s" "[$((i+1))]"
done
echo ""
echo "────────────────────────────────────────────────────────"

while IFS= read -r tool; do
  [[ -z "$tool" ]] && continue
  printf "%-40s" "${tool:0:40}"
  for i in "${!SESSIONS[@]}"; do
    if printf '%s' "${SERVER_TOOLS[$i]}" | grep -qx "$tool"; then
      printf " %-6s" "yes"
    else
      printf " %-6s" "-"
    fi
  done
  echo ""
done <<< "$ALL_TOOLS"

echo ""

# ── capability flags comparison ───────────────────────────────────────────────

echo "════════════════════════════════════════════════════════"
echo "CAPABILITY FLAGS"
echo "════════════════════════════════════════════════════════"
printf "%-20s" "CAPABILITY"
for i in "${!SERVERS[@]}"; do
  printf " %-6s" "[$((i+1))]"
done
echo ""
echo "────────────────────────────────────────────────────────"

CAPS=("tools" "resources" "prompts" "logging")
for cap in "${CAPS[@]}"; do
  printf "%-20s" "$cap"
  for i in "${!SESSIONS[@]}"; do
    INFO_FILE="$SCHEMA_DIR/info-$i.json"
    mcpc --json "${SESSIONS[$i]}" 2>/dev/null > "$INFO_FILE" || echo "{}" > "$INFO_FILE"
    HAS=$(jq -r ".capabilities.${cap} // \"no\" | if . == null then \"no\" else \"yes\" end" "$INFO_FILE" 2>/dev/null || echo "?")
    printf " %-6s" "$HAS"
  done
  echo ""
done

echo "════════════════════════════════════════════════════════"
echo "Done."
```

---

## Workflow 3: Server health monitoring

Cron-compatible health check script. Logs JSON results, sends alerts to stderr (redirect to email or Slack webhook as needed).

```bash
#!/usr/bin/env bash
# health-monitor.sh — monitor MCP server health, log results, alert on failures
# Usage: ./health-monitor.sh <server> [alert-webhook-url]
# Cron example: */5 * * * * /opt/scripts/health-monitor.sh mcp.apify.com 2>>/var/log/mcpc-alerts.log

set -euo pipefail

SERVER="${1:?Usage: $0 <server> [webhook-url]}"
WEBHOOK_URL="${2:-}"
SESSION="@health-monitor-$$"
LOG_DIR="${MCPC_HEALTH_LOG_DIR:-$HOME/.mcpc/health-logs}"
LOG_FILE="$LOG_DIR/$(echo "$SERVER" | tr '/:' '_').jsonl"
TIMEOUT="${MCPC_HEALTH_TIMEOUT:-30}"

mkdir -p "$LOG_DIR"

cleanup() { mcpc @"${SESSION#@}" close 2>/dev/null || true; }
trap cleanup EXIT

alert() {
  local message="$1"
  echo "[ALERT] $(date -u +%Y-%m-%dT%H:%M:%SZ) $SERVER — $message" >&2
  if [[ -n "$WEBHOOK_URL" ]]; then
    curl -s -X POST "$WEBHOOK_URL" \
      -H "Content-Type: application/json" \
      -d "{\"text\":\"MCP health alert: $SERVER — $message\"}" \
      >/dev/null 2>&1 || true
  fi
}

STATUS="healthy"
LATENCY_MS=0
ERROR_MSG=""
START_MS=$(date +%s%3N)

# ── connect ───────────────────────────────────────────────────────────────────

if ! timeout "$TIMEOUT" mcpc "$SERVER" connect "$SESSION" 2>/dev/null; then
  STATUS="connect_failed"
  ERROR_MSG="could not connect"
  alert "connect failed"
else
  # ── ping ──────────────────────────────────────────────────────────────────

  PING_START=$(date +%s%3N)
  if ! PING_JSON=$(timeout "$TIMEOUT" mcpc --json "$SESSION" ping 2>/dev/null); then
    STATUS="ping_failed"
    ERROR_MSG="ping returned non-zero exit"
    alert "ping failed"
  else
    PING_END=$(date +%s%3N)
    LATENCY_MS=$((PING_END - PING_START))

    # ── tools reachable ───────────────────────────────────────────────────

    if ! timeout "$TIMEOUT" mcpc --json "$SESSION" tools-list >/dev/null 2>&1; then
      STATUS="tools_list_failed"
      ERROR_MSG="tools-list failed"
      alert "tools-list failed (server may be degraded)"
    fi
  fi
fi

END_MS=$(date +%s%3N)
TOTAL_MS=$((END_MS - START_MS))

# ── write JSONL log entry ─────────────────────────────────────────────────────

LOG_ENTRY=$(jq -nc \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg server "$SERVER" \
  --arg status "$STATUS" \
  --argjson latency "$LATENCY_MS" \
  --argjson total "$TOTAL_MS" \
  --arg error "$ERROR_MSG" \
  '{timestamp: $ts, server: $server, status: $status, latency_ms: $latency, total_ms: $total, error: $error}')

echo "$LOG_ENTRY" >> "$LOG_FILE"

# ── stdout summary ────────────────────────────────────────────────────────────

printf '[%s] %s → %s (ping=%dms, total=%dms)\n' \
  "$(date -u +%H:%M:%SZ)" "$SERVER" "$STATUS" "$LATENCY_MS" "$TOTAL_MS"

if [[ "$STATUS" != "healthy" ]]; then
  exit 1
fi
exit 0
```

---

## Workflow 4: Tool regression testing

Saves tool schemas to disk on first run; on subsequent runs, compares live schemas against saved baselines and reports any changes.

```bash
#!/usr/bin/env bash
# tool-regression.sh — detect schema changes in MCP server tools
# Usage: ./tool-regression.sh <server> [baseline-dir]
# First run: saves baselines. Subsequent runs: diffs against them.

set -euo pipefail

SERVER="${1:?Usage: $0 <server> [baseline-dir]}"
BASELINE_DIR="${2:-$HOME/.mcpc/baselines/$(echo "$SERVER" | tr '/:.' '_')}"
SESSION="@regression-$$"
CHANGED=0
ADDED=0
REMOVED=0

cleanup() { mcpc @"${SESSION#@}" close 2>/dev/null || true; }
trap cleanup EXIT

mkdir -p "$BASELINE_DIR"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

log "Connecting to $SERVER"
mcpc "$SERVER" connect "$SESSION" 2>/dev/null

log "Fetching tool list"
TOOLS_JSON=$(mcpc --json "$SESSION" tools-list 2>/dev/null)
TOOL_NAMES=$(printf '%s' "$TOOLS_JSON" | jq -r '.[].name' | sort)

TOOL_COUNT=$(printf '%s' "$TOOL_NAMES" | wc -l | tr -d ' ')
log "Found $TOOL_COUNT tools"

# ── fetch and compare each tool schema ────────────────────────────────────────

while IFS= read -r tool; do
  [[ -z "$tool" ]] && continue
  BASELINE_FILE="$BASELINE_DIR/${tool}.json"
  CURRENT=$(mcpc --json "$SESSION" tools-get "$tool" 2>/dev/null)

  if [[ ! -f "$BASELINE_FILE" ]]; then
    printf '\033[0;33m[NEW]\033[0m    %s\n' "$tool"
    printf '%s' "$CURRENT" | jq '.' > "$BASELINE_FILE"
    ((ADDED++)) || true
    continue
  fi

  BASELINE=$(cat "$BASELINE_FILE")

  # Normalize and compare (strip descriptions to focus on structural changes)
  CURRENT_STRUCT=$(printf '%s' "$CURRENT" | jq 'del(.description, .annotations)')
  BASELINE_STRUCT=$(printf '%s' "$BASELINE" | jq 'del(.description, .annotations)')

  if ! diff <(printf '%s\n' "$BASELINE_STRUCT") <(printf '%s\n' "$CURRENT_STRUCT") >/dev/null 2>&1; then
    printf '\033[0;31m[CHANGED]\033[0m %s\n' "$tool"
    diff \
      <(printf '%s\n' "$BASELINE_STRUCT" | jq '.') \
      <(printf '%s\n' "$CURRENT_STRUCT" | jq '.') \
      | head -40
    echo ""
    ((CHANGED++)) || true

    # Update the baseline to the new version
    printf '%s' "$CURRENT" | jq '.' > "$BASELINE_FILE"
  else
    printf '\033[0;32m[OK]\033[0m     %s\n' "$tool"
  fi
done <<< "$TOOL_NAMES"

# ── detect removed tools (in baseline but not in current) ─────────────────────

for baseline_file in "$BASELINE_DIR"/*.json; do
  [[ -f "$baseline_file" ]] || continue
  tool=$(basename "$baseline_file" .json)
  if ! printf '%s' "$TOOL_NAMES" | grep -qx "$tool"; then
    printf '\033[0;31m[REMOVED]\033[0m %s\n' "$tool"
    rm "$baseline_file"
    ((REMOVED++)) || true
  fi
done

# ── summary ───────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "Server   : %s\n" "$SERVER"
printf "Baselines: %s\n" "$BASELINE_DIR"
printf "Results  : %d changed, %d added, %d removed\n" "$CHANGED" "$ADDED" "$REMOVED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$CHANGED" -gt 0 || "$REMOVED" -gt 0 ]]; then
  exit 1
fi
exit 0
```

---

## Workflow 5: Proxy sandbox testing

Full workflow: authenticate, connect with proxy enabled, connect AI agent to proxy, run tool calls through proxy, clean up.

```bash
#!/usr/bin/env bash
# proxy-sandbox-test.sh — test MCP server via proxy sandbox
# Usage: ./proxy-sandbox-test.sh <server> <proxy-port> [tool-name] [tool-args-json]
# Example: ./proxy-sandbox-test.sh mcp.apify.com 8080 search-actors '{"keywords":"test"}'

set -euo pipefail

SERVER="${1:?Usage: $0 <server> <proxy-port> [tool] [args-json]}"
PROXY_PORT="${2:?proxy port required}"
TOOL_NAME="${3:-}"
TOOL_ARGS="${4:-{}}"
PROXY_TOKEN="sandbox-$(date +%s)-$$"
UPSTREAM_SESSION="@upstream-$$"
SANDBOXED_SESSION="@sandboxed-$$"

cleanup() {
  mcpc @"${SANDBOXED_SESSION#@}" close 2>/dev/null || true
  mcpc @"${UPSTREAM_SESSION#@}" close 2>/dev/null || true
}
trap cleanup EXIT

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
ok()  { printf '\033[0;32m[PASS]\033[0m %s\n' "$*"; }
fail() { printf '\033[0;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

# ── step 1: connect upstream with proxy ───────────────────────────────────────

log "Connecting upstream $SERVER with proxy on port $PROXY_PORT"
mcpc "$SERVER" connect "$UPSTREAM_SESSION" \
  --proxy "$PROXY_PORT" \
  --proxy-bearer-token "$PROXY_TOKEN"
ok "Upstream session + proxy started at 127.0.0.1:$PROXY_PORT"

# Give proxy a moment to bind
sleep 1

# ── step 2: connect sandboxed client to proxy ─────────────────────────────────

log "Connecting sandboxed client to proxy at localhost:$PROXY_PORT"
mcpc "localhost:$PROXY_PORT" connect "$SANDBOXED_SESSION" \
  --header "Authorization: Bearer $PROXY_TOKEN"
ok "Sandboxed client connected"

# ── step 3: verify sandboxed client can see tools ─────────────────────────────

log "Listing tools via sandboxed session"
TOOLS_JSON=$(mcpc --json "$SANDBOXED_SESSION" tools-list 2>/dev/null)
TOOL_COUNT=$(printf '%s' "$TOOLS_JSON" | jq 'length')
ok "Sandboxed tools-list: $TOOL_COUNT tools visible"

# ── step 4: verify direct token is NOT exposed ────────────────────────────────

log "Verifying upstream credentials are not leaked through proxy"
# The sandboxed session's session info must not contain the upstream URL or token
SANDBOXED_INFO=$(mcpc --json "$SANDBOXED_SESSION" 2>/dev/null)
SANDBOXED_SERVER=$(printf '%s' "$SANDBOXED_INFO" | jq -r '._mcpc.server.url // ""')
if echo "$SANDBOXED_SERVER" | grep -q "$SERVER"; then
  fail "Proxy leaked upstream server URL to sandboxed client"
fi
ok "Upstream server URL not exposed to sandbox"

# ── step 5: call a tool through the proxy (optional) ──────────────────────────

if [[ -n "$TOOL_NAME" ]]; then
  log "Calling $TOOL_NAME through sandboxed session"
  RESULT=$(printf '%s' "$TOOL_ARGS" | mcpc --json "$SANDBOXED_SESSION" tools-call "$TOOL_NAME" 2>/dev/null)
  CONTENT_TYPE=$(printf '%s' "$RESULT" | jq -r '.content[0].type // "unknown"')
  ok "tools-call $TOOL_NAME via proxy: content type=$CONTENT_TYPE"
fi

# ── step 6: verify ping works through proxy ───────────────────────────────────

log "Pinging via sandboxed session"
if mcpc --json "$SANDBOXED_SESSION" ping >/dev/null 2>&1; then
  ok "Ping via proxy succeeded"
else
  fail "Ping via proxy failed"
fi

echo ""
log "Proxy sandbox test complete — all assertions passed"
```

---

## Workflow 6: OAuth session lifecycle

Full OAuth workflow: login, connect with profile, verify token works, check token metadata, logout, confirm cleanup.

```bash
#!/usr/bin/env bash
# oauth-lifecycle.sh — full OAuth session lifecycle test
# Usage: ./oauth-lifecycle.sh <server> [profile-name]
# Note: 'login' opens a browser — run this interactively, not in CI headless mode.

set -euo pipefail

SERVER="${1:?Usage: $0 <server> [profile-name]}"
PROFILE="${2:-test-profile-$$}"
SESSION="@oauth-test-$$"

cleanup() {
  mcpc @"${SESSION#@}" close 2>/dev/null || true
  # Clean up test profile if it exists
  mcpc logout "$SERVER" --profile "$PROFILE" 2>/dev/null || true
}
trap cleanup EXIT

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
ok()  { printf '\033[0;32m[PASS]\033[0m %s\n' "$*"; }
fail() { printf '\033[0;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

# ── step 1: login via OAuth (interactive — opens browser) ─────────────────────

log "Step 1: Initiating OAuth login for $SERVER (profile: $PROFILE)"
log "        A browser window will open. Complete the login flow."
if ! mcpc login "$SERVER" --profile "$PROFILE"; then
  fail "OAuth login failed"
fi
ok "OAuth login completed — profile '$PROFILE' saved"

# ── step 2: verify profile appears in session list ────────────────────────────

log "Step 2: Verifying profile is listed"
MCPC_JSON=$(mcpc --json 2>/dev/null)
FOUND=$(printf '%s' "$MCPC_JSON" | jq --arg p "$PROFILE" \
  '.profiles // [] | map(select(.name == $p)) | length' 2>/dev/null || echo 0)
if [[ "$FOUND" -eq 0 ]]; then
  # Some versions nest profiles differently — check raw JSON
  if ! printf '%s' "$MCPC_JSON" | grep -q "$PROFILE"; then
    fail "Profile '$PROFILE' not visible in mcpc output after login"
  fi
fi
ok "Profile '$PROFILE' visible in mcpc state"

# ── step 3: connect using the saved OAuth profile ─────────────────────────────

log "Step 3: Connecting with OAuth profile '$PROFILE'"
if ! mcpc "$SERVER" connect "$SESSION" --profile "$PROFILE"; then
  fail "connect with profile '$PROFILE' failed"
fi
ok "Session connected with OAuth profile"

# ── step 4: make an authenticated tool call ───────────────────────────────────

log "Step 4: Making authenticated tools-list call"
TOOLS_JSON=$(mcpc --json "$SESSION" tools-list 2>/dev/null)
TOOL_COUNT=$(printf '%s' "$TOOLS_JSON" | jq 'length' 2>/dev/null || echo -1)
if [[ "$TOOL_COUNT" -lt 0 ]]; then
  fail "Authenticated tools-list returned invalid JSON"
fi
ok "Authenticated tools-list succeeded ($TOOL_COUNT tools)"

# ── step 5: inspect session to confirm profile is referenced ──────────────────

log "Step 5: Verifying session references correct profile"
SESSION_INFO=$(mcpc --json 2>/dev/null)
SESSION_PROFILE=$(printf '%s' "$SESSION_INFO" | jq -r --arg s "$SESSION" '.sessions[] | select(.name == $s) | .profileName // ""')
if [[ "$SESSION_PROFILE" != "$PROFILE" ]]; then
  fail "Session profile mismatch: expected '$PROFILE', got '$SESSION_PROFILE'"
fi
ok "Session correctly references profile '$PROFILE'"

# ── step 6: close session (before logout) ────────────────────────────────────

log "Step 6: Closing session $SESSION"
mcpc @"${SESSION#@}" close
ok "Session closed"

# Disable trap's close attempt since we already closed
SESSION=""

# ── step 7: logout and confirm profile removed ────────────────────────────────

log "Step 7: Logging out profile '$PROFILE'"
if ! mcpc logout "$SERVER" --profile "$PROFILE"; then
  fail "logout failed"
fi
ok "Profile '$PROFILE' removed"

# ── step 8: verify profile is gone ───────────────────────────────────────────

log "Step 8: Verifying profile no longer listed"
MCPC_JSON_AFTER=$(mcpc --json 2>/dev/null)
if printf '%s' "$MCPC_JSON_AFTER" | grep -q "\"$PROFILE\""; then
  fail "Profile '$PROFILE' still appears after logout"
fi
ok "Profile absent after logout"

echo ""
log "OAuth lifecycle test complete — all steps passed"
```

---

## Workflow 7: Stdio server development loop

Watch-mode workflow for local MCP server development. Builds, connects via config file, runs a test suite, closes, and repeats on file changes.

```bash
#!/usr/bin/env bash
# dev-loop.sh — watch-mode test loop for local stdio MCP server development
# Usage: ./dev-loop.sh <config-file> <server-entry> [build-command]
# Example: ./dev-loop.sh ./mcp.json myserver "npm run build"
# Requires: inotifywait (Linux) or fswatch (macOS)

set -euo pipefail

CONFIG_FILE="${1:?Usage: $0 <config-file> <entry> [build-cmd] [src-dir] }"
ENTRY_NAME="${2:?Usage: $0 <config-file> <entry> [build-cmd] [src-dir] }"
BUILD_CMD="${3:-npm run build}"
SRC_DIR="${4:-./src}"
SESSION="@devloop-$$"

# Detect file watcher
if command -v fswatch >/dev/null 2>&1; then
  WATCH_CMD="fswatch -o -r"
elif command -v inotifywait >/dev/null 2>&1; then
  WATCH_CMD="inotifywait -r -e modify,create,delete -q"
else
  echo "Install fswatch (macOS: brew install fswatch) or inotifywait (Linux: apt install inotify-tools)" >&2
  exit 1
fi

log() { printf '\033[0;34m[dev-loop %s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }

run_test_cycle() {
  local attempt="$1"
  log "=== Cycle $attempt ==="

  # 1. Build
  log "Building..."
  if ! eval "$BUILD_CMD" 2>&1; then
    log "Build failed — skipping test"
    return 1
  fi
  log "Build succeeded"

  # 2. Clean up any leftover session
  mcpc @"${SESSION#@}" close 2>/dev/null || true

  # 3. Connect
  log "Connecting to $ENTRY_NAME via $CONFIG_FILE"
  if ! mcpc --config "$CONFIG_FILE" "$ENTRY_NAME" connect "$SESSION" 2>/dev/null; then
    log "Connect failed"
    return 1
  fi

  # 4. Quick smoke test
  log "Running smoke tests..."

  TOOLS_JSON=$(mcpc --json "$SESSION" tools-list 2>/dev/null || echo "[]")
  TOOL_COUNT=$(printf '%s' "$TOOLS_JSON" | jq 'length' 2>/dev/null || echo 0)
  log "  tools-list: $TOOL_COUNT tools"

  if mcpc --json "$SESSION" ping >/dev/null 2>&1; then
    log "  ping: OK"
  else
    log "  ping: FAILED"
  fi

  # 5. Optional: call specific tools from env
  if [[ -n "${TEST_TOOL:-}" ]]; then
    log "  Calling $TEST_TOOL..."
    if mcpc --json "$SESSION" tools-call "$TEST_TOOL" ${TEST_ARGS:-} >/dev/null 2>&1; then
      log "  $TEST_TOOL: OK"
    else
      log "  $TEST_TOOL: FAILED"
    fi
  fi

  # 6. Close
  mcpc @"${SESSION#@}" close 2>/dev/null || true
  log "Session closed — cycle $attempt complete"
  echo ""
}

# ── main loop ─────────────────────────────────────────────────────────────────

CYCLE=0
cleanup() { mcpc @"${SESSION#@}" close 2>/dev/null || true; exit 0; }
trap cleanup INT TERM

log "Starting dev loop watching $SRC_DIR"
log "Build command: $BUILD_CMD"
log "Press Ctrl+C to stop"
echo ""

# Run once immediately
run_test_cycle $((++CYCLE)) || true

# Then watch for changes
$WATCH_CMD "$SRC_DIR" | while read -r event; do
  log "Change detected — rebuilding..."
  run_test_cycle $((++CYCLE)) || true
done
```

---

## Workflow 8: Parallel load testing

Creates N concurrent sessions and fires simultaneous tool calls, measuring latency distribution and failure rates.

```bash
#!/usr/bin/env bash
# load-test.sh — parallel load test with N concurrent sessions
# Usage: ./load-test.sh <server> <tool-name> <concurrency> [iterations] [tool-args-json]
# Example: ./load-test.sh mcp.apify.com search-actors 5 10 '{"keywords":"test"}'

set -euo pipefail

SERVER="${1:?Usage: $0 <server> <tool> <concurrency> [iterations] [args-json]}"
TOOL="${2:?tool name required}"
CONCURRENCY="${3:-5}"
ITERATIONS="${4:-10}"
TOOL_ARGS="${5:-{}}"

RESULT_DIR=$(mktemp -d)
SESSIONS=()

cleanup() {
  for s in "${SESSIONS[@]}"; do
    mcpc @"${s#@}" close 2>/dev/null || true
  done
  rm -rf "$RESULT_DIR"
}
trap cleanup EXIT

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

# ── open N sessions ───────────────────────────────────────────────────────────

log "Opening $CONCURRENCY sessions to $SERVER"
for i in $(seq 1 "$CONCURRENCY"); do
  SESSION="@load-$i-$$"
  SESSIONS+=("$SESSION")
  mcpc "$SERVER" connect "$SESSION" 2>/dev/null
  log "  Session $SESSION ready"
done

log "All sessions ready. Running $ITERATIONS iterations per session..."
echo ""

# ── worker function ───────────────────────────────────────────────────────────

run_worker() {
  local session="$1"
  local worker_id="$2"
  local result_file="$RESULT_DIR/worker-${worker_id}.jsonl"

  for iter in $(seq 1 "$ITERATIONS"); do
    local start_ms end_ms latency status
    start_ms=$(date +%s%3N)

    if printf '%s' "$TOOL_ARGS" | mcpc --json "$session" tools-call "$TOOL" \
        >/dev/null 2>&1; then
      status="ok"
    else
      status="error"
    fi

    end_ms=$(date +%s%3N)
    latency=$((end_ms - start_ms))

    printf '%s\n' "$(jq -nc \
      --arg w "$worker_id" \
      --arg i "$iter" \
      --arg s "$status" \
      --argjson l "$latency" \
      '{worker: $w, iter: $i, status: $s, latency_ms: $l}')" >> "$result_file"
  done
}

# ── fire all workers in parallel ──────────────────────────────────────────────

PIDS=()
for i in "${!SESSIONS[@]}"; do
  run_worker "${SESSIONS[$i]}" "$((i+1))" &
  PIDS+=($!)
done

# Wait with progress indicator
TOTAL_CALLS=$((CONCURRENCY * ITERATIONS))
printf 'Running %d total calls (%d workers × %d iterations)...' \
  "$TOTAL_CALLS" "$CONCURRENCY" "$ITERATIONS"
for pid in "${PIDS[@]}"; do
  wait "$pid"
done
echo " done."
echo ""

# ── aggregate results ─────────────────────────────────────────────────────────

COMBINED=$(cat "$RESULT_DIR"/worker-*.jsonl 2>/dev/null)
TOTAL=$(printf '%s' "$COMBINED" | wc -l | tr -d ' ')
SUCCESSES=$(printf '%s' "$COMBINED" | jq -s '[.[] | select(.status == "ok")] | length')
FAILURES=$(printf '%s' "$COMBINED" | jq -s '[.[] | select(.status == "error")] | length')
AVG_MS=$(printf '%s' "$COMBINED" | jq -s '[.[].latency_ms] | add / length | round')
MIN_MS=$(printf '%s' "$COMBINED" | jq -s '[.[].latency_ms] | min')
MAX_MS=$(printf '%s' "$COMBINED" | jq -s '[.[].latency_ms] | max')
P95_MS=$(printf '%s' "$COMBINED" | jq -s '[.[].latency_ms] | sort | .[length * 0.95 | floor]')

echo "════════════════════════════════════════════"
echo "LOAD TEST RESULTS"
echo "════════════════════════════════════════════"
printf "Server      : %s\n" "$SERVER"
printf "Tool        : %s\n" "$TOOL"
printf "Workers     : %d\n" "$CONCURRENCY"
printf "Iterations  : %d each\n" "$ITERATIONS"
printf "Total calls : %d\n" "$TOTAL"
printf "Successes   : %d\n" "$SUCCESSES"
printf "Failures    : %d\n" "$FAILURES"
printf "Latency avg : %d ms\n" "$AVG_MS"
printf "Latency min : %d ms\n" "$MIN_MS"
printf "Latency max : %d ms\n" "$MAX_MS"
printf "Latency p95 : %d ms\n" "$P95_MS"
echo "════════════════════════════════════════════"

if [[ "$FAILURES" -gt 0 ]]; then
  exit 1
fi
exit 0
```

---

## Workflow 9: Resource change monitor

Subscribes to one or more resources, polls for changes at a configurable interval, and logs diffs when content changes.

```bash
#!/usr/bin/env bash
# resource-monitor.sh — watch for resource content changes via subscribe/unsubscribe
# Usage: ./resource-monitor.sh <server> <resource-uri> [poll-interval-seconds]
# Example: ./resource-monitor.sh mcp.apify.com "https://api.example.com/status" 15

set -euo pipefail

SERVER="${1:?Usage: $0 <server> <resource-uri> [poll-seconds]}"
RESOURCE_URI="${2:?resource URI required}"
POLL_INTERVAL="${3:-30}"
SESSION="@resmon-$$"
SNAPSHOT_DIR=$(mktemp -d)
PREV_HASH=""
CHANGE_COUNT=0

cleanup() {
  log "Unsubscribing and cleaning up..."
  mcpc "$SESSION" resources-unsubscribe "$RESOURCE_URI" 2>/dev/null || true
  mcpc @"${SESSION#@}" close 2>/dev/null || true
  rm -rf "$SNAPSHOT_DIR"
}
trap cleanup INT TERM EXIT

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

# ── connect and subscribe ─────────────────────────────────────────────────────

log "Connecting to $SERVER"
mcpc "$SERVER" connect "$SESSION" 2>/dev/null

log "Subscribing to $RESOURCE_URI"
if ! mcpc "$SESSION" resources-subscribe "$RESOURCE_URI" 2>/dev/null; then
  log "Warning: subscribe not supported or failed — falling back to polling only"
fi

log "Watching $RESOURCE_URI every ${POLL_INTERVAL}s (Ctrl+C to stop)"
echo ""

# ── poll loop ─────────────────────────────────────────────────────────────────

SNAPSHOT_FILE="$SNAPSHOT_DIR/current.json"
PREV_FILE="$SNAPSHOT_DIR/previous.json"

while true; do
  TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  if ! CONTENT_JSON=$(mcpc --json "$SESSION" resources-read "$RESOURCE_URI" 2>/dev/null); then
    log "ERROR: resources-read failed — server may be temporarily unreachable"
    sleep "$POLL_INTERVAL"
    continue
  fi

  # Compute stable hash of content
  CURRENT_HASH=$(printf '%s' "$CONTENT_JSON" | jq -cS '.contents' | sha256sum | awk '{print $1}')

  if [[ "$CURRENT_HASH" != "$PREV_HASH" ]]; then
    if [[ -z "$PREV_HASH" ]]; then
      log "Initial snapshot captured"
    else
      ((CHANGE_COUNT++)) || true
      log "CHANGE #$CHANGE_COUNT detected at $TIMESTAMP"

      # Show diff if both files exist
      if [[ -f "$PREV_FILE" ]]; then
        echo "--- previous"
        echo "+++ current"
        diff \
          <(jq -S '.contents' "$PREV_FILE") \
          <(printf '%s' "$CONTENT_JSON" | jq -S '.contents') \
          || true
        echo ""
      fi

      # Log to JSONL
      jq -nc \
        --arg ts "$TIMESTAMP" \
        --arg uri "$RESOURCE_URI" \
        --argjson change "$CHANGE_COUNT" \
        --arg hash "$CURRENT_HASH" \
        '{timestamp: $ts, uri: $uri, change_number: $change, content_hash: $hash}' \
        >> "$SNAPSHOT_DIR/changes.jsonl"
    fi

    # Save snapshot
    cp "$SNAPSHOT_FILE" "$PREV_FILE" 2>/dev/null || true
    printf '%s' "$CONTENT_JSON" > "$SNAPSHOT_FILE"
    PREV_HASH="$CURRENT_HASH"
  else
    log "No change (hash: ${CURRENT_HASH:0:12}...)"
  fi

  sleep "$POLL_INTERVAL"
done
```

---

## Workflow 10: Complete CI test pipeline

GitHub Actions-ready script for full MCP server validation. Handles Linux headless keychain, collects structured results, exits with appropriate codes.

```bash
#!/usr/bin/env bash
# ci-pipeline.sh — GitHub Actions-ready full MCP server validation
# Usage: CI=true ./ci-pipeline.sh <server>
#
# Environment variables:
#   MCP_SERVER_URL        — Server URL (overrides $1)
#   MCP_BEARER_TOKEN      — Bearer token for auth (optional)
#   MCP_EXPECTED_TOOLS    — Comma-separated expected tool names (optional)
#   MCP_MIN_TOOL_COUNT    — Minimum number of tools expected (default: 1)
#   CI_REPORT_FILE        — Path to write JSON report (default: mcp-ci-report.json)

set -euo pipefail

SERVER="${MCP_SERVER_URL:-${1:-}}"
if [[ -z "$SERVER" ]]; then
  echo "Error: provide server via MCP_SERVER_URL env or first argument" >&2
  exit 1
fi

BEARER_TOKEN="${MCP_BEARER_TOKEN:-}"
EXPECTED_TOOLS="${MCP_EXPECTED_TOOLS:-}"
MIN_TOOL_COUNT="${MCP_MIN_TOOL_COUNT:-1}"
REPORT_FILE="${CI_REPORT_FILE:-mcp-ci-report.json}"
SESSION="@ci-$$"

RESULTS=()   # Array of JSON result objects
PASS=0
FAIL=0

cleanup() {
  mcpc @"${SESSION#@}" close 2>/dev/null || true
}
trap cleanup EXIT

# ── helpers ───────────────────────────────────────────────────────────────────

ci_log() { echo "::notice::$*"; }
ci_err() { echo "::error::$*" >&2; }

record() {
  local name="$1" status="$2" message="${3:-}"
  if [[ "$status" == "pass" ]]; then
    ((PASS++)) || true
    echo "  [PASS] $name"
  else
    ((FAIL++)) || true
    echo "  [FAIL] $name${message:+ — $message}"
    ci_err "$name: $message"
  fi
  RESULTS+=("$(jq -nc --arg n "$name" --arg s "$status" --arg m "$message" \
    '{name: $n, status: $s, message: $m}')")
}

# ── linux headless keychain workaround ────────────────────────────────────────

if [[ "${CI:-}" == "true" ]] && [[ "$(uname)" == "Linux" ]]; then
  ci_log "CI Linux detected — using file-based credential store (MCPC_HOME_DIR)"
  export MCPC_HOME_DIR="${RUNNER_TEMP:-/tmp}/mcpc-ci-$$"
  mkdir -p "$MCPC_HOME_DIR"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MCP CI Pipeline"
printf "Server : %s\n" "$SERVER"
printf "Time   : %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── test 1: connect ───────────────────────────────────────────────────────────

CONNECT_ARGS=()
if [[ -n "$BEARER_TOKEN" ]]; then
  CONNECT_ARGS+=("--header" "Authorization: Bearer $BEARER_TOKEN")
fi

if mcpc "$SERVER" connect "$SESSION" "${CONNECT_ARGS[@]}" 2>/dev/null; then
  record "connect" "pass"
else
  record "connect" "fail" "could not establish session"
  # Fatal — cannot continue
  jq -n \
    --argjson pass "$PASS" \
    --argjson fail "$FAIL" \
    --argjson results "$(printf '%s\n' "${RESULTS[@]}" | jq -s '.')" \
    '{summary: {passed: $pass, failed: $fail}, results: $results}' \
    > "$REPORT_FILE"
  ci_err "Connect failed — aborting pipeline"
  exit 3
fi

# ── test 2: server info valid ─────────────────────────────────────────────────

INFO_JSON=$(mcpc --json "$SESSION" 2>/dev/null || echo "{}")
PROTO=$(printf '%s' "$INFO_JSON" | jq -r '.protocolVersion // ""')
if [[ -n "$PROTO" ]]; then
  record "server-info-protocol-version" "pass" "$PROTO"
else
  record "server-info-protocol-version" "fail" "protocolVersion missing"
fi

SERVER_NAME=$(printf '%s' "$INFO_JSON" | jq -r '.serverInfo.name // ""')
if [[ -n "$SERVER_NAME" ]]; then
  record "server-info-name" "pass" "$SERVER_NAME"
else
  record "server-info-name" "fail" "serverInfo.name missing"
fi

# ── test 3: tools-list returns valid array ────────────────────────────────────

TOOLS_JSON=$(mcpc --json "$SESSION" tools-list 2>/dev/null || echo "null")
TOOL_COUNT=$(printf '%s' "$TOOLS_JSON" | jq 'if type == "array" then length else -1 end' 2>/dev/null || echo -1)

if [[ "$TOOL_COUNT" -ge 0 ]]; then
  record "tools-list-valid-array" "pass" "$TOOL_COUNT tools"
else
  record "tools-list-valid-array" "fail" "response is not a JSON array"
fi

# ── test 4: minimum tool count ────────────────────────────────────────────────

if [[ "$TOOL_COUNT" -ge "$MIN_TOOL_COUNT" ]]; then
  record "tools-min-count" "pass" "$TOOL_COUNT >= $MIN_TOOL_COUNT"
else
  record "tools-min-count" "fail" "got $TOOL_COUNT, expected >= $MIN_TOOL_COUNT"
fi

# ── test 5: expected tools present ────────────────────────────────────────────

if [[ -n "$EXPECTED_TOOLS" ]]; then
  IFS=',' read -ra EXPECTED_ARRAY <<< "$EXPECTED_TOOLS"
  for expected_tool in "${EXPECTED_ARRAY[@]}"; do
    expected_tool="${expected_tool// /}"
    if printf '%s' "$TOOLS_JSON" | jq -e --arg t "$expected_tool" \
        '[.[].name] | index($t) != null' >/dev/null 2>&1; then
      record "tool-present:$expected_tool" "pass"
    else
      record "tool-present:$expected_tool" "fail" "tool '$expected_tool' not found"
    fi
  done
fi

# ── test 6: tools-get returns valid schema ────────────────────────────────────

FIRST_TOOL=$(printf '%s' "$TOOLS_JSON" | jq -r '.[0].name // ""')
if [[ -n "$FIRST_TOOL" ]]; then
  SCHEMA_JSON=$(mcpc --json "$SESSION" tools-get "$FIRST_TOOL" 2>/dev/null || echo "{}")
  if printf '%s' "$SCHEMA_JSON" | jq -e '.inputSchema.type == "object"' >/dev/null 2>&1; then
    record "tools-get-schema:$FIRST_TOOL" "pass"
  else
    record "tools-get-schema:$FIRST_TOOL" "fail" "inputSchema.type != object"
  fi
fi

# ── test 7: resources-list ────────────────────────────────────────────────────

if RES_JSON=$(mcpc --json "$SESSION" resources-list 2>/dev/null); then
  RES_COUNT=$(printf '%s' "$RES_JSON" | jq 'if type == "array" then length else -1 end')
  if [[ "$RES_COUNT" -ge 0 ]]; then
    record "resources-list" "pass" "$RES_COUNT resources"
  else
    record "resources-list" "fail" "non-array response"
  fi
else
  record "resources-list" "pass" "not supported (skipped)"
fi

# ── test 8: prompts-list ──────────────────────────────────────────────────────

if PROMPTS_JSON=$(mcpc --json "$SESSION" prompts-list 2>/dev/null); then
  PROMPT_COUNT=$(printf '%s' "$PROMPTS_JSON" | jq 'if type == "array" then length else -1 end')
  if [[ "$PROMPT_COUNT" -ge 0 ]]; then
    record "prompts-list" "pass" "$PROMPT_COUNT prompts"
  else
    record "prompts-list" "fail" "non-array response"
  fi
else
  record "prompts-list" "pass" "not supported (skipped)"
fi

# ── test 9: ping ──────────────────────────────────────────────────────────────

if mcpc --json "$SESSION" ping >/dev/null 2>&1; then
  record "ping" "pass"
else
  record "ping" "fail" "ping returned non-zero exit"
fi

# ── write JSON report ─────────────────────────────────────────────────────────

jq -n \
  --arg server "$SERVER" \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg proto "$PROTO" \
  --argjson pass "$PASS" \
  --argjson fail "$FAIL" \
  --argjson total "$((PASS + FAIL))" \
  --argjson results "$(printf '%s\n' "${RESULTS[@]}" | jq -s '.')" \
  '{server: $server, timestamp: $ts, protocolVersion: $proto,
    summary: {passed: $pass, failed: $fail, total: $total},
    results: $results}' \
  > "$REPORT_FILE"

# ── summary ───────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "Results: \033[0;32m%d passed\033[0m, \033[0;31m%d failed\033[0m / %d total\n" \
  "$PASS" "$FAIL" "$((PASS + FAIL))"
printf "Report : %s\n" "$REPORT_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
```

**GitHub Actions integration example:**

```yaml
# .github/workflows/mcp-validation.yml
name: MCP server validation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */6 * * *'   # every 6 hours

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install mcpc
        run: npm install -g @apify/mcpc

      - name: Run CI pipeline
        env:
          MCP_SERVER_URL: ${{ secrets.MCP_SERVER_URL }}
          MCP_BEARER_TOKEN: ${{ secrets.MCP_BEARER_TOKEN }}
          MCP_EXPECTED_TOOLS: search-actors,get-actor,run-actor
          MCP_MIN_TOOL_COUNT: 5
          CI_REPORT_FILE: mcp-ci-report.json
        run: bash ci-pipeline.sh

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: mcp-ci-report
          path: mcp-ci-report.json
```

---

## Quick reference: exit codes

| Code | Meaning | Common cause |
|------|---------|--------------|
| `0` | Success | — |
| `1` | Client error | Invalid args, command not found |
| `2` | Server error | Tool execution failed, resource not found |
| `3` | Network error | Connection failed, timeout |
| `4` | Auth error | Invalid credentials, 401/403 |

## Quick reference: argument syntax

```bash
# Scalar values
mcpc @s tools-call tool name:="hello world" count:=10 enabled:=true

# JSON objects/arrays
mcpc @s tools-call tool config:='{"key":"val"}' ids:='[1,2,3]'

# Inline JSON (first arg starts with { or [)
mcpc @s tools-call tool '{"name":"hello","count":10}'

# Stdin
echo '{"name":"hello"}' | mcpc @s tools-call tool
cat args.json          | mcpc @s tools-call tool

# Shell variables with spaces — wrap entire arg in double quotes
QUERY="hello world"
mcpc @s tools-call search "query:=${QUERY}"
```
