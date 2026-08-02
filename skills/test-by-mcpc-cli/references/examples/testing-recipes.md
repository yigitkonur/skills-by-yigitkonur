# Testing Recipes

These are small copy-paste checks, verified against `mcpc 0.6.0`.
Prefer `--json` plus `jq` assertions over human-mode output.

## Recipe: assert a session connects

```bash
SESSION=@smoke
TARGET=https://research-mcp.yigitkonur.com/mcp

mcpc connect "$TARGET" "$SESSION"
mcpc --json | jq -e --arg s "$SESSION" '.sessions[] | select(.name == $s and .status == "live")' >/dev/null
mcpc close "$SESSION"
```

For fresh smoke tests, connect directly and filter by exact name.
Do not dump every saved session unless reuse or cleanup is the actual question.

## Recipe: assert a tool exists

```bash
mcpc --json @research-test tools-list | jq -e '.[] | select(.name == "web-search")' >/dev/null
```

## Recipe: assert the tool schema includes an array field

```bash
mcpc --json @research-test tools-get web-search | jq -e '.inputSchema.properties.queries.type == "array"' >/dev/null
```

## Recipe: assert a tool call did not return `isError`

```bash
RESULT=$(mcpc --json @research-test tools-call web-search '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Recipe: assert a validation failure exits `2`

```bash
mcpc --json @research-test tools-call web-search queries:=OpenAI
[ "$?" -eq 2 ]
```

Since v0.5.0, any `isError:true` result — schema validation, unknown tool,
runtime failure — exits `2`, never `0`. Use this to catch the common
array-vs-string mistake and confirm the exit code, not just the payload.

## Recipe: assert a network error on an unreachable session

```bash
mcpc connect http://127.0.0.1:19999/mcp @bad
[ "$?" -eq 0 ]                        # connect always exits 0 — the session is
                                       # created anyway and auto-recovers later
mcpc @bad ping
[ "$?" -eq 1 ]                        # first live round-trip against the dead
                                       # server is where the failure surfaces
mcpc close @bad
```

`connect` no longer fails on an unreachable target — it creates the session
with a warning and lets it auto-recover if the server comes back. Assert the
failure on the first command that actually round-trips (`ping`, `tools-list`,
...); it exits `1` (a client-side connect failure, not the isError-driven `2`
from a live tool call).

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

## Recipe: detach, poll, fetch the result, cancel if needed

```bash
DETACHED=$(mcpc --json @everything-http tools-call simulate-research-query topic:='"mcpc detach"' --detach)
TASK_ID=$(printf '%s' "$DETACHED" | jq -r '.taskId')
mcpc --json @everything-http tasks-get "$TASK_ID" | jq -e '.taskId == "'"$TASK_ID"'"' >/dev/null
mcpc --json @everything-http tasks-list | jq -e --arg id "$TASK_ID" '.tasks[]? | select(.taskId == $id)' >/dev/null || true

# tasks-result blocks until the task finishes — works from a fresh process too,
# since state lives with the session, not the CLI invocation that started the task.
mcpc --json @everything-http tasks-result "$TASK_ID" | jq -e '.isError != true' >/dev/null

mcpc @everything-http tasks-cancel "$TASK_ID" || true   # errors (exit 2) once already
                                                          # completed — expected here
```

## Recipe: assert tool schema validation wiring exists

```bash
if mcpc @research-test tools-get web-search --schema /tmp/does-not-exist.json >/tmp/mcpc.out 2>/tmp/mcpc.err; then
  echo "expected schema file lookup to fail" >&2
  exit 1
fi
rg 'Schema file not found' /tmp/mcpc.err >/dev/null
```

`--schema`/`--schema-mode` are scoped to `tools-get` and `tools-call` only.
`prompts-get` never accepted `--schema` — do not use it for that command.

## Recipe: assert a proxy is live without over-claiming auth

```bash
UPSTREAM=@proxy-upstream
CHECK=@proxy-check

mcpc connect https://research-mcp.yigitkonur.com/mcp "$UPSTREAM" --proxy 127.0.0.1:8787
curl -s http://127.0.0.1:8787/health | jq -e '.status == "ok"' >/dev/null
mcpc connect http://127.0.0.1:8787/mcp "$CHECK" --no-profile
mcpc close "$CHECK"
mcpc close "$UPSTREAM"
```

This proves the proxy is serving MCP traffic.
It does not prove bearer enforcement, so test auth separately on the release you ship.
