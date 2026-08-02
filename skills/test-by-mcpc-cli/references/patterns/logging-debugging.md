# Logging and Debugging

Verified against `mcpc` 0.6.0. Use `--verbose`, `logs`, and JSON mode together.

## First commands

```bash
mcpc --verbose connect https://research-mcp.yigitkonur.com/mcp @research-debug
mcpc --json @research-debug help
mcpc --json @research-debug tools-list
```

## Read logs with `logs`, not raw files

`mcpc <@session> logs` is the sanctioned way to read a session's bridge log — it spans
rotated files (`.log.1`…`.log.5`) automatically and folds stack-trace continuation lines
into the entry they belong to, which a raw `sed`/`rg` pass over the file does not. The raw
path is still `~/.mcpc/logs/bridge-<@session>.log` (exposed as `_mcpc.logPath` in
`mcpc --json @<session>`), but reach for `logs` first.

```bash
mcpc @research-debug logs                    # last 50 lines (default)
mcpc @research-debug logs -n 500 | rg 'error|warn|task|notify|session'
mcpc @research-debug logs --follow            # stream new lines (ESC/Ctrl+C/q to stop)
mcpc @research-debug logs --since 1h          # entries newer than a duration or ISO timestamp
mcpc --json @research-debug logs -n 200       # `[{ time, level, context?, msg } | { raw }, ...]`
```

For a **local stdio server** (`mcpc connect <command> @session`), the bridge captures the
child process's stderr into the same log. If the child crashes on startup (missing env var,
bad TLS trust, missing credentials), `mcpc connect` also appends a stderr tail to its own
error output — `logs` has the full detail if that tail isn't enough.

## TLS and transport debugging

Use `--insecure` for self-signed TLS during troubleshooting.
Do not treat it as a normal deployment path.

For transport mismatch failures, check whether the server is really Streamable HTTP.
If the log shows `Cannot POST /sse` or `Cannot POST /`, you are likely pointing `mcpc` at an SSE endpoint.

## Task debugging

```bash
mcpc --json @everything-http tools-call simulate-research-query topic:='"debug"' --detach
mcpc --json @everything-http tasks-list
mcpc --json @everything-http tasks-get <taskId>
mcpc --json @everything-http tasks-result <taskId>
```

## State clues

Full state set: `live`, `connecting`, `reconnecting`, `disconnected`, `crashed`, `unauthorized`, `expired`.
`live` is healthy; the rest tell you whether you have a transport problem, an auth problem, or a
recoverable reconnect loop — `crashed` and `disconnected` auto-recover on the next command, `unauthorized`
needs `mcpc login` + `restart`, `expired` needs `restart`.
