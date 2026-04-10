# Testing Recipes

These are small copy-paste checks for `mcpc 0.2.4`.
Prefer `--json` plus `jq` assertions over human-mode output.

## Recipe: assert a session connects

```bash
SESSION=@smoke
TARGET=https://research.yigitkonur.com/mcp

mcpc connect "$TARGET" "$SESSION"
mcpc --json | jq -e --arg s "$SESSION" '.sessions[] | select(.name == $s and .status == "live")' >/dev/null
mcpc close "$SESSION"
```

For fresh smoke tests, connect directly and filter by exact name.
Do not dump every saved session unless reuse or cleanup is the actual question.

## Recipe: assert a tool exists

```bash
mcpc --json @research-test tools-list | jq -e '.[] | select(.name == "search-reddit")' >/dev/null
```

## Recipe: assert the tool schema includes an array field

```bash
mcpc --json @research-test tools-get search-reddit | jq -e '.inputSchema.properties.queries.type == "array"' >/dev/null
```

## Recipe: assert a tool call did not return `isError`

```bash
RESULT=$(mcpc --json @research-test tools-call search-reddit '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Recipe: assert a validation failure still exits `0`

```bash
BAD=$(mcpc --json @research-test tools-call search-reddit queries:=OpenAI)
printf '%s' "$BAD" | jq -e '.isError == true' >/dev/null
```

Use this to catch the common array-vs-string mistake.

## Recipe: assert a network error happens during `connect`

```bash
if mcpc connect http://127.0.0.1:19999/mcp @bad >/tmp/mcpc.out 2>/tmp/mcpc.err; then
  echo "expected connect to fail" >&2
  exit 1
fi
status=$?
[ "$status" -eq 3 ]
```

Direct one-shot URL commands are gone in `0.2.x`, so test network failures on `connect`.

## Recipe: assert task-required behavior

```bash
PLAIN=$(mcpc --json @everything-http tools-call simulate-research-query topic:='"mcpc tasks"')
printf '%s' "$PLAIN" | jq -e '.isError == true' >/dev/null
```

## Recipe: run a task to completion

```bash
TASK_RESULT=$(mcpc --json @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' --task)
printf '%s' "$TASK_RESULT" | jq -e '.isError != true' >/dev/null
```

## Recipe: detach, inspect, and cancel if needed

```bash
DETACHED=$(mcpc --json @everything-http tools-call simulate-research-query topic:='"mcpc detach"' --detach)
TASK_ID=$(printf '%s' "$DETACHED" | jq -r '.taskId')
mcpc --json @everything-http tasks-get "$TASK_ID" | jq -e '.taskId == "'"$TASK_ID"'"' >/dev/null
mcpc --json @everything-http tasks-list | jq -e --arg id "$TASK_ID" '.tasks[]? | select(.taskId == $id)' >/dev/null || true
mcpc @everything-http tasks-cancel "$TASK_ID" || true
```

## Recipe: assert prompt schema validation wiring exists

```bash
if mcpc @everything-http prompts-get args-prompt city:=Paris --schema /tmp/does-not-exist.json >/tmp/mcpc.out 2>/tmp/mcpc.err; then
  echo "expected schema file lookup to fail" >&2
  exit 1
fi
rg 'Schema file not found' /tmp/mcpc.err >/dev/null
```

This confirms current `prompts-get` accepts `--schema` in the released CLI.

## Recipe: assert a proxy is live without over-claiming auth

```bash
UPSTREAM=@proxy-upstream
CHECK=@proxy-check

mcpc connect https://research.yigitkonur.com/mcp "$UPSTREAM" --proxy 127.0.0.1:8787 --proxy-bearer-token demo-token
curl -s http://127.0.0.1:8787/health | jq -e '.status == "ok"' >/dev/null
mcpc connect http://127.0.0.1:8787/mcp "$CHECK" --no-profile
mcpc close "$CHECK"
mcpc close "$UPSTREAM"
```

This proves the proxy is serving MCP traffic.
It does not prove bearer enforcement, so test auth separately on the release you ship.
