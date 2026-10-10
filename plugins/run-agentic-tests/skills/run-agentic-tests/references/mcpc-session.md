# Client-owned MCP stdio with MCPC

Use this reference when MCPC is the selected test client. Refer to
[test-by-mcpc-cli](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/test-by-mcpc-cli)
for the authoritative command and session reference. The bundled
[session adapter](../assets/examples/mcpc-session.mjs) uses the installed client
and owns one namespaced session. Inspect `mcpc --version` before setup; the
current contract targets verified **MCPC 0.7.x** (`0.7.0`) session-first syntax.

## Prepare the actual server

Write a project configuration containing the real server executable and args:

```json
{
  "mcpServers": {
    "app": {
      "command": "/absolute/path/to/node",
      "args": ["/absolute/project/dist/server.mjs"]
    }
  }
}
```

Use actual project startup requirements; do not invent a `dist` build or tool.
Secrets belong in inherited ignored configuration, not this example or logs.
Single-entry `FILE:ENTRY` selection starts only the intended server. Avoid
auto-discovery or bulk connection during a bounded campaign.

## Bind the operator draft

Keep the generated record/task/actor/target IDs. Set `runtime_type: mcp_stdio`,
declare its real Git or files source provider, and make one argv list using
absolute paths:

```yaml
command:
  argv:
    - /absolute/path/to/node
    - /installed/skill/assets/examples/mcpc-session.mjs
    - --state-dir
    - /campaign/environments/G001/mcpc
    - --config
    - /absolute/project/mcp.json:app
    - --required-tool
    - actual_tool_name
  cwd: /absolute/project
  env_names: []
readiness:
  type: tool
  body_contains: actual_tool_name
  timeout_ms: 30000
session:
  tool: {name: mcpc, version: "0.7.0"}
  owner_id: A00003
  session_id: "@campaign-g001"
  attachment: "MCPC_HOME_DIR=/campaign/environments/G001/mcpc/client mcpc @campaign-g001"
  probe:
    argv: [COPY_THE_EXACT_COMMAND_ARGV_LIST]
  inspect:
    argv: [COPY_THE_EXACT_COMMAND_ARGV_LIST]
  cleanup:
    argv: [COPY_THE_EXACT_COMMAND_ARGV_LIST]
```

Replace the three illustrative lists with the same actual `command.argv` array.
The controller injects the action; no separate action argument is needed. Avoid
YAML anchors because the strict record parser rejects aliases. Set the tool
version (e.g. `0.7.0`) and owner/session IDs to their actual assigned values. Optional
`--binary PATH` selects an installed MCPC executable; `--timeout-ms N` bounds an
individual client command and must fit within the outer readiness timeout.

Publish with the generated `runtime start` command. Attach records the native
client's PID, creation time, and server identity. Probe performs `tools-list`
through the initialized session and requires the named tool. The readiness
receipt proves attachment and discovery; it does not prove the acceptance case.

## Execute through the same client

The executor uses the exact recorded client state and session using **mcpc 0.7.x session-first syntax** (`mcpc @session <command>` or `mcpc <command> @session`):

```bash
# Tool invocation
MCPC_HOME_DIR="$OWNED_STATE/client" mcpc @session tools-list --json
MCPC_HOME_DIR="$OWNED_STATE/client" mcpc @session tools-call "$TOOL" "$ARGUMENTS_JSON" --json

# Official MCP Skills Extension
MCPC_HOME_DIR="$OWNED_STATE/client" mcpc @session skills-list --json
MCPC_HOME_DIR="$OWNED_STATE/client" mcpc @session skills-get "$SKILL_NAME" --json
MCPC_HOME_DIR="$OWNED_STATE/client" mcpc @session skills-get "$SKILL_NAME" "$SPECIFIC_FILE" --json

# Resources and Directory Reading
MCPC_HOME_DIR="$OWNED_STATE/client" mcpc @session resources-directory-read "$URI" --json
```

Save the real calls, arguments, output, exit status, and relevant protocol errors
under the assigned evidence directory. Note exit codes:
- **Exit 0**: Clean success with valid JSON payload.
- **Exit 1**: Transport failure, broken pipe, missing connection, or invalid CLI parameters.
- **Exit 2**: MCP protocol-level error (`isError: true` returned by server, tool exception, or invocation timeout).
The verifier reads those saved artifacts.

## Inspect, recover, and close

Use the campaign's `runtime inspect` and `runtime stop`. Inspection reads the
owned client's `sessions.json` and OS process identity. Both `mcpc --json` session
listing and `ping` can restart a broken bridge; the adapter invokes neither for
inspection. A native PID/session or process-creation change produces an
ownership mismatch; it never authorizes closing the replacement session.

Recovery uses a fresh target, state directory, and session name. The adapter
refuses to adopt a same-name session without its own saved ownership record.
Cleanup invokes `mcpc close @session` for only the verified session and preserves logs.
It does not run global `mcpc clean`, kill matching processes, or delete unrelated
client state. Keep the final session available when user inspection requires it.
