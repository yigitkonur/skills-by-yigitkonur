# stdio Testing

Use stdio when you control the local server process and want reproducible testing from config.

## Config shape

`mcpc` expects `mcpServers` in the config file.

```json
{
  "mcpServers": {
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

## Connect and inspect

```bash
mcpc connect /tmp/everything-mcp.json:everything @everything-stdio
mcpc @everything-stdio
mcpc @everything-stdio tools-list --full
mcpc @everything-stdio prompts-list
mcpc @everything-stdio resources-list
mcpc @everything-stdio resources-templates-list
mcpc @everything-stdio ping
```

If the acceptance criteria explicitly mention prompts, resources, or templates, run those commands in the first inspection pass instead of widening the read set later.

## Why `file:entry` matters

This is the current `0.6.0` surface.
Do not document the legacy `--config file entry connect @session` form — it was replaced by `mcpc connect file:entry @session` back in 0.2.0 and no longer exists.

## Bulk connects skip stdio by default

`mcpc connect <config-file>` (no `:entry`, i.e. connect every server in the file) skips stdio entries unless you pass `--stdio`. Single-entry connects (`file:entry @session`, as above) are unaffected and always connect.

Security note: a config entry's command runs on connect **even if the handshake later fails** — only connect to (or bulk-`--stdio`-include) config files whose entries you trust.

```bash
mcpc connect /tmp/everything-mcp.json --stdio
```

## stderr capture on connect failure

If the child process crashes or fails to respond, its stderr is captured to the bridge log (`~/.mcpc/logs/bridge-<session>.log`, `[server stderr]` prefix) and a tail is appended directly to the `connect` error — read the error text before reaching for the log file.

## Restart loop

```bash
mcpc restart @everything-stdio
mcpc @everything-stdio help
```

Use this after code changes or when the underlying stdio process crashed.
If `mcpc restart @everything-stdio` returns `Session not found`, create a fresh session name instead of retrying the missing one.
Note: self-heal is `ping`-specific, not universal. `ping` treats a dead pipe as a network error and silently respawns the bridge+child chain inside one invocation (exit 0, slower response, new `pid` in `mcpc --json`). `tools-list`, `resources-list`, `prompts-list`, and `server-discover` do not self-heal — they fail hard with `Not connected` (exit 2), leaving the session broken until you run `mcpc restart`. Use `ping` for a one-shot liveness check; don't expect other commands to recover a crashed child on their own.
