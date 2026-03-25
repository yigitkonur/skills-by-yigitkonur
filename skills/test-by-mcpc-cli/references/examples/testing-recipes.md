# mcpc testing recipes

Standalone, copy-paste bash functions that work inside the e2e framework
(`source test/e2e/lib/framework.sh` + `test_init`). Each recipe is a complete
test case with setup, assertion, and teardown. All recipes assume a live session
variable `$SESSION` and a reachable server at `$TEST_SERVER_URL` unless noted.

Critical syntax reminders:
- Connect: `mcpc <target> connect @<session>` — target first, session last
- Operate: `mcpc @<session> <command>` — session name must start with `@`
- JSON mode: `mcpc --json @<session> <command>` — `--json` before the session
- Close: `mcpc @<session> close`

---

## Recipe 1: Assert tool exists

Verify a named tool appears in the server's tool list. Fails fast with a
meaningful message if the tool is absent.

```bash
assert_tool_exists() {
  local session="$1"
  local tool_name="$2"

  test_case "tool '$tool_name' exists on server"
  run_xmcpc --json "$session" tools-list
  assert_success "tools-list must succeed before checking for tool"

  # jq -e returns exit code 1 when the expression is false/null
  if ! echo "$STDOUT" | jq -e --arg name "$tool_name" \
       '.[] | select(.name == $name)' > /dev/null 2>&1; then
    test_fail "tool '$tool_name' not found in tools-list output"
    echo "# Available tools: $(echo "$STDOUT" | jq -r '.[].name' | tr '\n' ' ')"
    exit 1
  fi
  test_pass
}

# Usage
assert_tool_exists "$SESSION" "echo"
assert_tool_exists "$SESSION" "search-actors"
```

---

## Recipe 2: Assert tool has required parameters

Check that a tool's `inputSchema.required` array contains every expected field.
Useful for catching schema regressions where a required field is silently
dropped.

```bash
assert_tool_required_params() {
  local session="$1"
  local tool_name="$2"
  shift 2
  local expected_params=("$@")   # remaining args are the expected required fields

  test_case "tool '$tool_name' has required params: ${expected_params[*]}"
  run_xmcpc --json "$session" tools-list
  assert_success

  # Extract the required array for this tool
  local required_json
  required_json=$(echo "$STDOUT" | jq -r \
    --arg name "$tool_name" \
    '.[] | select(.name == $name) | .inputSchema.required // [] | @json')

  if [[ -z "$required_json" || "$required_json" == "null" ]]; then
    test_fail "tool '$tool_name' not found or has no inputSchema"
    exit 1
  fi

  for param in "${expected_params[@]}"; do
    if ! echo "$required_json" | jq -e --arg p "$param" \
         '. | index($p) != null' > /dev/null 2>&1; then
      test_fail "required param '$param' missing from tool '$tool_name'"
      echo "# inputSchema.required: $required_json"
      exit 1
    fi
  done
  test_pass
}

# Usage
assert_tool_required_params "$SESSION" "echo" "message"
assert_tool_required_params "$SESSION" "search-actors" "query" "limit"
```

---

## Recipe 3: Assert tool returns valid response

Call a tool with known arguments and validate the structure of the response.
Checks MCP spec invariants: `content` array, `type` field on each item.

```bash
assert_tool_response() {
  local session="$1"
  local tool_name="$2"
  shift 2
  local tool_args=("$@")   # e.g. 'message:=hello'

  test_case "tool '$tool_name' returns valid MCP response"
  run_mcpc --json "$session" tools-call "$tool_name" "${tool_args[@]}"
  assert_success "tools-call '$tool_name' must succeed"

  # MCP spec: CallToolResult must have a content array
  assert_json_valid "$STDOUT"
  assert_json "$STDOUT" '.content' "response must have content array"
  assert_json "$STDOUT" '.content | length > 0' "content array must not be empty"
  assert_json "$STDOUT" '.content[0].type' "each content item must have a type field"

  local content_type
  content_type=$(echo "$STDOUT" | jq -r '.content[0].type')
  case "$content_type" in
    text)
      assert_json "$STDOUT" '.content[0].text' "text content must have .text field"
      ;;
    image)
      assert_json "$STDOUT" '.content[0].data' "image content must have .data field"
      assert_json "$STDOUT" '.content[0].mimeType' "image content must have .mimeType"
      ;;
    resource)
      assert_json "$STDOUT" '.content[0].resource' "resource content must have .resource field"
      ;;
    *)
      # Unknown type — only assert structural validity
      ;;
  esac
  test_pass
}

# Usage
assert_tool_response "$SESSION" "echo" "message:=hello world"
assert_tool_response "$SESSION" "add" "a:=3" "b:=4"
```

---

## Recipe 4: Assert exit codes

Test the documented CLI error categories. Exit codes:
`0` success or tool-level MCP error, `1` client error, `2` rare bridge/server error, `3` network error, `4` auth error.

```bash
assert_exit_codes() {
  local session="$1"

  # Exit code 0 — success
  test_case "exit code 0 on success"
  run_xmcpc "$session" tools-list
  assert_exit_code 0
  test_pass

  # Exit code 1 — client error (invalid argument / command not found)
  test_case "exit code 1 on client error (bad session name)"
  run_xmcpc "@nonexistent-session-$$" tools-list
  assert_exit_code 1
  test_pass

  # Exit code 1 — client error (malformed tool name)
  test_case "exit code 1 on client error (bad command)"
  # Commander.js argument validation — use run_mcpc, not run_xmcpc
  run_mcpc @nonexistent-session-$$ tools-call
  assert_exit_code 1
  test_pass

  # Exit code 0 — tool-level MCP error
  test_case "exit code 0 with isError=true on tool-level failure"
  run_xmcpc --json "$session" tools-call fail 'message:=intentional-failure'
  assert_exit_code 0
  assert_json "$STDOUT" '.isError == true' "tool failure must set isError=true"
  test_pass

  # Exit code 3 — network error (server unreachable)
  test_case "exit code 3 on network error (bad URL)"
  # Connect directly to a port nothing is listening on (no session)
  run_xmcpc "http://127.0.0.1:19999" tools-list
  assert_exit_code 3
  test_pass

  # Exit code 4 — auth error (401/403 from server)
  # Requires a server that enforces auth. Skip if no auth server is available.
  # test_case "exit code 4 on auth error"
  # run_xmcpc "https://mcp.example.com" tools-list
  # assert_exit_code 4
  # test_pass
}

# Usage
assert_exit_codes "$SESSION"
```

---

## Recipe 5: Assert session state

Verify a session is live, that its bridge PID is a running process, and that
the bridge socket file exists and is reachable.

```bash
assert_session_live() {
  local session_name="$1"   # with or without leading @
  local full_name="$session_name"
  if [[ "$full_name" != @* ]]; then
    full_name="@$full_name"
  fi

  test_case "session '$full_name' is live"
  run_mcpc --json
  assert_success

  # Status must be "live"
  local status
  status=$(echo "$STDOUT" | jq -r \
    --arg n "$full_name" '.sessions[] | select(.name == $n) | .status')
  assert_eq "$status" "live" "session status must be 'live'"

  # Bridge PID must exist and be a running process
  local pid
  pid=$(echo "$STDOUT" | jq -r \
    --arg n "$full_name" '.sessions[] | select(.name == $n) | .pid')
  assert_not_empty "$pid" "session must have a bridge PID"

  if ! kill -0 "$pid" 2>/dev/null; then
    test_fail "bridge PID $pid is not a running process"
    exit 1
  fi

  # Socket file must exist
  local bridges_dir="${MCPC_HOME_DIR:-$HOME/.mcpc}/bridges"
  local socket_path="$bridges_dir/${full_name}.sock"
  assert_file_exists "$socket_path" "bridge socket must exist at $socket_path"

  # Verify bridge responds: ping through the session
  run_xmcpc "$full_name" ping
  assert_success "ping must succeed on a live session"

  test_pass
}

# Usage
assert_session_live "$SESSION"
```

---

## Recipe 6: Assert protocol version

Verify the server negotiated a specific MCP protocol version. The current
standard version is `2025-11-25`.

```bash
assert_protocol_version() {
  local session="$1"
  local expected_version="${2:-2025-11-25}"

  test_case "server uses MCP protocol version '$expected_version'"
  run_mcpc --json "$session"
  assert_success

  assert_json_valid "$STDOUT"
  assert_json "$STDOUT" '.protocolVersion' "response must have protocolVersion field"

  local actual
  actual=$(echo "$STDOUT" | jq -r '.protocolVersion')
  assert_eq "$actual" "$expected_version" \
    "protocolVersion must be '$expected_version', got '$actual'"

  test_pass
}

# Usage — strict check
assert_protocol_version "$SESSION" "2025-11-25"

# Usage — accept any non-empty version
assert_protocol_version_nonempty() {
  local session="$1"
  test_case "server reports a non-empty protocol version"
  run_mcpc --json "$session"
  assert_success
  local v
  v=$(echo "$STDOUT" | jq -r '.protocolVersion')
  assert_not_empty "$v" "protocolVersion must not be empty"
  test_pass
}
```

---

## Recipe 7: Assert server capabilities

Inspect the `capabilities` object returned during initialization. Assert that
specific capability groups (`tools`, `resources`, `prompts`) are present.

```bash
assert_server_capabilities() {
  local session="$1"
  shift
  local expected_caps=("$@")   # e.g. "tools" "resources" "prompts"

  test_case "server capabilities include: ${expected_caps[*]}"
  run_mcpc --json "$session"
  assert_success

  assert_json_valid "$STDOUT"
  assert_json "$STDOUT" '.capabilities' "response must have capabilities object"

  for cap in "${expected_caps[@]}"; do
    if ! echo "$STDOUT" | jq -e --arg c "$cap" \
         '.capabilities | has($c)' > /dev/null 2>&1; then
      test_fail "capability '$cap' not found in server capabilities"
      echo "# Actual capabilities: $(echo "$STDOUT" | jq '.capabilities | keys')"
      exit 1
    fi
  done
  test_pass
}

# Assert a capability is explicitly absent
assert_capability_absent() {
  local session="$1"
  local cap="$2"

  test_case "server does NOT advertise capability '$cap'"
  run_mcpc --json "$session"
  assert_success

  if echo "$STDOUT" | jq -e --arg c "$cap" \
       '.capabilities | has($c)' > /dev/null 2>&1; then
    test_fail "capability '$cap' should be absent but was present"
    exit 1
  fi
  test_pass
}

# Usage
assert_server_capabilities "$SESSION" "tools" "resources" "prompts"
assert_capability_absent "$SESSION" "sampling"
```

---

## Recipe 8: Assert schema compatibility

Save a baseline schema to disk and compare the server's current schema against
it. Detects regressions where a tool's `inputSchema` changes unexpectedly.

```bash
# Step 1: Save baseline (run once, commit the file)
save_schema_baseline() {
  local session="$1"
  local tool_name="$2"
  local baseline_file="$3"   # e.g. "$TEST_TMP/echo-baseline.json"

  test_case "save schema baseline for '$tool_name'"
  run_mcpc --json "$session" tools-get "$tool_name"
  assert_success
  echo "$STDOUT" > "$baseline_file"
  test_pass
}

# Step 2: Compare live schema against baseline
assert_schema_compatible() {
  local session="$1"
  local tool_name="$2"
  local baseline_file="$3"

  test_case "schema for '$tool_name' matches baseline at '$baseline_file'"
  assert_file_exists "$baseline_file" "baseline file must exist"

  run_mcpc --json "$session" tools-get "$tool_name"
  assert_success

  # Use mcpc's built-in schema validation in strict mode
  run_mcpc --json "$session" tools-get "$tool_name" \
    --schema "$baseline_file" --schema-mode strict
  if [[ $EXIT_CODE -ne 0 ]]; then
    test_fail "schema for '$tool_name' diverged from baseline (strict mode)"
    echo "# Baseline: $(cat "$baseline_file" | jq '.inputSchema')"
    echo "# Current:  $(echo "$STDOUT" | jq '.inputSchema')"
    exit 1
  fi
  test_pass
}

# Full diff-based check using jq (no mcpc schema flags needed)
assert_schema_diff() {
  local session="$1"
  local tool_name="$2"
  local baseline_file="$3"

  test_case "schema diff for '$tool_name' is empty"
  assert_file_exists "$baseline_file"

  run_mcpc --json "$session" tools-get "$tool_name"
  assert_success

  local current_schema baseline_schema
  current_schema=$(echo "$STDOUT" | jq '.inputSchema' | jq -S .)
  baseline_schema=$(jq '.inputSchema' "$baseline_file" | jq -S .)

  if [[ "$current_schema" != "$baseline_schema" ]]; then
    test_fail "inputSchema for '$tool_name' changed"
    echo "# Expected: $baseline_schema"
    echo "# Actual:   $current_schema"
    exit 1
  fi
  test_pass
}

# Usage
save_schema_baseline "$SESSION" "echo" "$TEST_TMP/echo-baseline.json"
assert_schema_compatible "$SESSION" "echo" "$TEST_TMP/echo-baseline.json"
assert_schema_diff "$SESSION" "echo" "$TEST_TMP/echo-baseline.json"
```

---

## Recipe 9: Assert response time

Measure the wall-clock time of a tool call and fail if it exceeds a threshold.
Uses `/usr/bin/time` for portability across macOS and Linux.

```bash
assert_response_time() {
  local session="$1"
  local tool_name="$2"
  local max_seconds="$3"
  shift 3
  local tool_args=("$@")

  test_case "tool '$tool_name' responds within ${max_seconds}s"

  local start end elapsed
  start=$(date +%s%N 2>/dev/null || date +%s)   # nanoseconds on Linux, seconds on macOS fallback

  run_mcpc "$session" tools-call "$tool_name" "${tool_args[@]}"
  assert_success "tool call must succeed for timing to be meaningful"

  end=$(date +%s%N 2>/dev/null || date +%s)

  # Compute elapsed in whole seconds (integer arithmetic)
  if [[ "$start" =~ ^[0-9]{13,}$ ]]; then
    # Nanoseconds available — compute ms then convert
    elapsed_ms=$(( (end - start) / 1000000 ))
    elapsed=$(( elapsed_ms / 1000 ))
  else
    elapsed=$(( end - start ))
  fi

  if [[ $elapsed -gt $max_seconds ]]; then
    test_fail "tool '$tool_name' took ${elapsed}s, expected <= ${max_seconds}s"
    exit 1
  fi

  echo "# '$tool_name' completed in ${elapsed}s (limit: ${max_seconds}s)"
  test_pass
}

# Measure latency using mcpc --timeout as a hard ceiling
assert_response_time_with_timeout() {
  local session="$1"
  local tool_name="$2"
  local timeout_seconds="$3"
  shift 3
  local tool_args=("$@")

  test_case "tool '$tool_name' completes before ${timeout_seconds}s timeout"
  run_mcpc "$session" tools-call "$tool_name" "${tool_args[@]}" \
    --timeout "$timeout_seconds"
  assert_success "tool must not time out"
  test_pass
}

# Usage
assert_response_time "$SESSION" "echo" 5 "message:=latency-check"
assert_response_time_with_timeout "$SESSION" "echo" 10 "message:=latency-check"
```

---

## Recipe 10: Assert resource availability

Verify that all expected resources are listable and at least one can be read
back with non-empty content.

```bash
assert_resources_available() {
  local session="$1"
  shift
  local expected_uris=("$@")

  # 1. resources-list must succeed and contain all expected URIs
  test_case "resources-list succeeds"
  run_xmcpc --json "$session" resources-list
  assert_success
  assert_json_valid "$STDOUT"
  assert_json "$STDOUT" '. | type == "array"' "resources-list must return an array"
  assert_json "$STDOUT" '. | length > 0' "resource list must not be empty"
  test_pass

  # 2. Each expected URI must be present in the list
  for uri in "${expected_uris[@]}"; do
    test_case "resource URI '$uri' is listed"
    if ! echo "$STDOUT" | jq -e --arg u "$uri" \
         '.[] | select(.uri == $u)' > /dev/null 2>&1; then
      test_fail "resource URI '$uri' not found in resources-list"
      echo "# Listed URIs: $(echo "$STDOUT" | jq -r '.[].uri' | tr '\n' ' ')"
      exit 1
    fi
    test_pass
  done

  # 3. Each expected URI must be readable with non-empty content
  for uri in "${expected_uris[@]}"; do
    test_case "resource '$uri' is readable"
    run_xmcpc --json "$session" resources-read "$uri"
    assert_success "resources-read '$uri' must succeed"
    assert_json_valid "$STDOUT"
    assert_json "$STDOUT" '.contents' "read response must have contents array"
    assert_json "$STDOUT" '.contents | length > 0' "contents must not be empty"
    assert_json "$STDOUT" '.contents[0].uri' "each content item must have a uri"
    test_pass
  done
}

# Usage
assert_resources_available "$SESSION" \
  "test://static/hello" \
  "test://static/json" \
  "test://dynamic/time"
```

---

## Recipe 11: Assert notification support

Trigger a server-side list-change notification and verify the bridge records
a non-null timestamp for it. Requires the test server's `/control/notify-*`
endpoints (or equivalent).

```bash
assert_notification_support() {
  local session="$1"
  local notification_type="$2"   # "tools" | "resources" | "prompts"

  test_case "session '$session' records '$notification_type' list-changed notification"

  # Confirm no timestamp yet
  run_mcpc --json
  assert_success
  local session_name="${session#@}"
  local before
  before=$(echo "$STDOUT" | jq -r \
    --arg n "$session_name" \
    ".sessions[] | select(.name == \$n) | .notifications.${notification_type}.listChangedAt // \"null\"")
  assert_eq "$before" "null" \
    "notification timestamp should be null before triggering"

  # Trigger the notification via test server control API
  case "$notification_type" in
    tools)     server_notify_tools_changed ;;
    resources) server_notify_resources_changed ;;
    prompts)   server_notify_prompts_changed ;;
    *)
      test_fail "unknown notification type: $notification_type"
      exit 1
      ;;
  esac

  # Give the bridge time to receive and process it
  sleep 1

  # Timestamp must now be non-null
  run_mcpc --json
  assert_success
  local after
  after=$(echo "$STDOUT" | jq -r \
    --arg n "$session_name" \
    ".sessions[] | select(.name == \$n) | .notifications.${notification_type}.listChangedAt // \"null\"")

  if [[ "$after" == "null" || -z "$after" ]]; then
    test_fail "notification timestamp for '$notification_type' should be set after trigger"
    exit 1
  fi

  echo "# '$notification_type' notification recorded at: $after"
  test_pass
}

# Usage
assert_notification_support "$SESSION" "tools"
assert_notification_support "$SESSION" "resources"
assert_notification_support "$SESSION" "prompts"
```

---

## Recipe 12: Parameterized test runner

Read test cases from a JSONL file (one JSON object per line) and run each as an
independent mcpc tool call, asserting success or failure according to the spec.

JSONL format per line:
```json
{"tool":"echo","args":{"message":"hello"},"expect":"success","contains":"hello"}
{"tool":"fail","args":{"message":"boom"},"expect":"failure"}
```

```bash
run_parameterized_tests() {
  local session="$1"
  local test_cases_file="$2"

  assert_file_exists "$test_cases_file" "JSONL test cases file must exist"

  local line_no=0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    ((line_no++)) || true

    local tool expect contains args_json
    tool=$(echo "$line" | jq -r '.tool')
    expect=$(echo "$line" | jq -r '.expect // "success"')
    contains=$(echo "$line" | jq -r '.contains // ""')
    args_json=$(echo "$line" | jq -r '.args // {} | @json')

    test_case "[$line_no] $tool ($expect)"

    # Call tool with inline JSON args
    run_mcpc --json "$session" tools-call "$tool" "$args_json"

    case "$expect" in
      success)
        assert_success "tool '$tool' line $line_no should succeed"
        assert_json_valid "$STDOUT"
        if [[ -n "$contains" ]]; then
          assert_contains "$STDOUT" "$contains" \
            "response should contain '$contains'"
        fi
        ;;
      failure)
        assert_failure "tool '$tool' line $line_no should fail"
        if [[ -n "$contains" ]]; then
          assert_contains "$STDERR" "$contains" \
            "error output should contain '$contains'"
        fi
        ;;
      *)
        test_fail "unknown 'expect' value: $expect"
        exit 1
        ;;
    esac
    test_pass
  done < "$test_cases_file"
}

# Usage — write a JSONL file then pass it in
cat > "$TEST_TMP/cases.jsonl" << 'EOF'
{"tool":"echo","args":{"message":"hello"},"expect":"success","contains":"hello"}
{"tool":"add","args":{"a":2,"b":3},"expect":"success"}
{"tool":"fail","args":{"message":"boom"},"expect":"failure"}
EOF

run_parameterized_tests "$SESSION" "$TEST_TMP/cases.jsonl"
```

---

## Recipe 13: Diff-based regression

Capture a full snapshot of tools, resources, and prompts; store it as a
baseline; then compare on subsequent runs. Any addition, removal, or rename
causes a clear diff.

```bash
capture_snapshot() {
  local session="$1"
  local snapshot_file="$2"

  test_case "capture server snapshot to '$snapshot_file'"
  local tools resources prompts
  run_mcpc --json "$session" tools-list
  assert_success
  tools="$STDOUT"

  run_mcpc --json "$session" resources-list
  assert_success
  resources="$STDOUT"

  run_mcpc --json "$session" prompts-list
  assert_success
  prompts="$STDOUT"

  # Normalise: sort arrays by name so order changes don't cause false diffs
  jq -n \
    --argjson t "$tools" \
    --argjson r "$resources" \
    --argjson p "$prompts" \
    '{tools: ($t | sort_by(.name)),
      resources: ($r | sort_by(.uri)),
      prompts: ($p | sort_by(.name))}' \
    > "$snapshot_file"

  assert_file_exists "$snapshot_file" "snapshot file must be created"
  test_pass
}

assert_snapshot_unchanged() {
  local session="$1"
  local baseline_file="$2"

  test_case "server output matches baseline snapshot"
  assert_file_exists "$baseline_file" "baseline snapshot must exist"

  # Capture current state into a temp file
  local current_file="$TEST_TMP/snapshot-current-$$.json"
  capture_snapshot "$session" "$current_file"

  # Normalise both with jq -S (sorted keys) for stable comparison
  local baseline_norm current_norm
  baseline_norm=$(jq -S . "$baseline_file")
  current_norm=$(jq -S . "$current_file")

  if [[ "$baseline_norm" != "$current_norm" ]]; then
    test_fail "server snapshot diverged from baseline"
    # Show a human-readable diff if diff is available
    if command -v diff > /dev/null 2>&1; then
      echo "$baseline_norm" > "$TEST_TMP/baseline-sorted.json"
      echo "$current_norm"  > "$TEST_TMP/current-sorted.json"
      diff "$TEST_TMP/baseline-sorted.json" "$TEST_TMP/current-sorted.json" \
        | head -40 >&2 || true
    fi
    exit 1
  fi
  test_pass
}

# Usage — first run saves baseline, subsequent runs compare
BASELINE="$TEST_TMP/server-baseline.json"
capture_snapshot "$SESSION" "$BASELINE"
# ... time passes / server is upgraded ...
assert_snapshot_unchanged "$SESSION" "$BASELINE"
```

---

## Recipe 14: Concurrent test safety

Spawn multiple sessions concurrently, run operations in parallel, and verify
that responses are consistent with each session's own state (no cross-session
contamination).

```bash
assert_concurrent_session_safety() {
  local target="$1"
  local num_sessions="${2:-3}"

  # Create N sessions concurrently
  test_case "create $num_sessions sessions concurrently"
  declare -a session_names
  declare -a pids

  for i in $(seq 1 "$num_sessions"); do
    local sname
    sname=$(session_name "concurrent-$i")
    session_names+=("$sname")
    # Spawn connect in background
    (
      run_mcpc "$target" connect "$sname" --header "X-Test: true"
      if [[ $EXIT_CODE -ne 0 ]]; then
        echo "FAIL: connect $sname failed" >&2
        exit 1
      fi
    ) &
    pids+=($!)
  done

  # Wait for all connects
  local all_ok=true
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      all_ok=false
    fi
  done
  [[ "$all_ok" == "true" ]] || { test_fail "one or more concurrent connects failed"; exit 1; }

  # Register all for cleanup
  for sname in "${session_names[@]}"; do
    _SESSIONS_CREATED+=("$sname")
  done
  test_pass

  # Run tool calls in parallel across all sessions
  test_case "parallel tool calls produce correct per-session results"
  declare -a call_pids
  declare -a result_files

  for sname in "${session_names[@]}"; do
    local result_file="$TEST_TMP/concurrent-result-${sname}.json"
    result_files+=("$result_file")
    (
      run_mcpc --json "$sname" tools-call echo "message:=from-$sname"
      echo "$STDOUT" > "$result_file"
      echo "$EXIT_CODE" > "${result_file}.exit"
    ) &
    call_pids+=($!)
  done

  for pid in "${call_pids[@]}"; do
    wait "$pid" || true
  done

  # Each result file must contain the session's own message
  for sname in "${session_names[@]}"; do
    local result_file="$TEST_TMP/concurrent-result-${sname}.json"
    local exit_file="${result_file}.exit"

    if [[ ! -f "$exit_file" || "$(cat "$exit_file")" != "0" ]]; then
      test_fail "tool call failed for session '$sname'"
      exit 1
    fi
    local response
    response=$(cat "$result_file")
    if ! echo "$response" | jq -e --arg m "from-$sname" \
         '.content[0].text | contains($m)' > /dev/null 2>&1; then
      test_fail "session '$sname' returned wrong content: $response"
      exit 1
    fi
  done
  test_pass

  # Verify sessions are all still live (no PID contamination)
  test_case "all $num_sessions sessions remain live after parallel calls"
  run_mcpc --json
  assert_success
  for sname in "${session_names[@]}"; do
    local status
    status=$(echo "$STDOUT" | jq -r \
      --arg n "$sname" '.sessions[] | select(.name == $n) | .status')
    assert_eq "$status" "live" "session '$sname' must still be live"
  done
  test_pass
}

# Usage
assert_concurrent_session_safety "$TEST_SERVER_URL" 3
```

---

## Recipe 15: Cleanup verification

After closing all sessions, assert that no bridge processes, Unix sockets, or
sessions.json entries belonging to this test run remain.

```bash
assert_no_leaked_resources() {
  local session_names=("$@")   # session names to close and verify are gone

  # Close each session explicitly
  for sname in "${session_names[@]}"; do
    test_case "close session '$sname'"
    run_mcpc "$sname" close
    assert_success "close must succeed for '$sname'"
    test_pass
  done

  # Allow a moment for bridge processes to exit
  sleep 0.5

  # Assert no sessions remain in sessions.json
  test_case "sessions.json has no entries for closed sessions"
  run_mcpc --json
  assert_success

  for sname in "${session_names[@]}"; do
    local name="${sname#@}"
    local found
    found=$(echo "$STDOUT" | jq -r \
      --arg n "$sname" '.sessions[] | select(.name == $n) | .name')
    assert_empty "$found" "session '$sname' must not appear in sessions list after close"
  done
  test_pass

  # Assert no bridge processes are running for these sessions
  test_case "no bridge processes running for closed sessions"
  for sname in "${session_names[@]}"; do
    local name="${sname#@}"
    # Look for bridge processes that reference this session name
    if pgrep -f "mcpc-bridge.*${name}" > /dev/null 2>&1; then
      test_fail "leaked bridge process found for session '$name'"
      pgrep -a -f "mcpc-bridge.*${name}" >&2 || true
      exit 1
    fi
  done
  test_pass

  # Assert no stale socket files remain
  test_case "no stale socket files for closed sessions"
  local bridges_dir="${MCPC_HOME_DIR:-$HOME/.mcpc}/bridges"
  for sname in "${session_names[@]}"; do
    local socket_path="$bridges_dir/${sname}.sock"
    if [[ -e "$socket_path" ]]; then
      test_fail "stale socket file found: $socket_path"
      exit 1
    fi
  done
  test_pass
}

# Comprehensive cleanup test — creates, uses, closes, then verifies
assert_clean_lifecycle() {
  local target="$1"

  local sname
  sname=$(session_name "cleanup-check")

  test_case "full lifecycle: connect → use → close → verify clean"
  run_mcpc "$target" connect "$sname" --header "X-Test: true"
  assert_success
  run_xmcpc "$sname" tools-list
  assert_success

  # Save PID and socket path before closing
  run_mcpc --json
  local pid socket_path
  pid=$(echo "$STDOUT" | jq -r \
    --arg n "$sname" '.sessions[] | select(.name == $n) | .pid')
  socket_path="${MCPC_HOME_DIR:-$HOME/.mcpc}/bridges/${sname}.sock"

  run_mcpc "$sname" close
  assert_success
  sleep 0.5

  # PID must no longer be a running process
  if [[ -n "$pid" && "$pid" != "null" ]]; then
    if kill -0 "$pid" 2>/dev/null; then
      test_fail "bridge PID $pid still running after session close"
      exit 1
    fi
  fi

  # Socket must be gone
  if [[ -n "$socket_path" && "$socket_path" != "null" && -e "$socket_path" ]]; then
    test_fail "socket file still exists after session close: $socket_path"
    exit 1
  fi

  test_pass
}

# Usage
# Assuming SESSIONS_TO_CLOSE was populated during the test
assert_no_leaked_resources "@session-a" "@session-b" "@session-c"
assert_clean_lifecycle "$TEST_SERVER_URL"
```

---

## Putting it all together

A minimal test file that uses several recipes end-to-end:

```bash
#!/bin/bash
# Test: Comprehensive server smoke test

source "$(dirname "$0")/../../lib/framework.sh"
test_init "my-suite/smoke-test"

start_test_server

SESSION=$(session_name "smoke")
run_mcpc "$TEST_SERVER_URL" connect "$SESSION" --header "X-Test: true"
assert_success
_SESSIONS_CREATED+=("$SESSION")

# Protocol
assert_protocol_version "$SESSION" "2025-11-25"
assert_server_capabilities "$SESSION" "tools" "resources" "prompts"

# Tools
assert_tool_exists "$SESSION" "echo"
assert_tool_required_params "$SESSION" "echo" "message"
assert_tool_response "$SESSION" "echo" "message:=smoke"
assert_response_time_with_timeout "$SESSION" "echo" 10 "message:=timing"

# Resources
assert_resources_available "$SESSION" \
  "test://static/hello" "test://static/json"

# Notifications
assert_notification_support "$SESSION" "tools"

# Session health
assert_session_live "$SESSION"

# Exit codes
assert_exit_codes "$SESSION"

# Cleanup
assert_clean_lifecycle "$TEST_SERVER_URL"

test_done
```
