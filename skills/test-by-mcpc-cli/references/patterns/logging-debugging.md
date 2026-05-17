# Logging and Debugging

Use `--verbose`, bridge logs, and JSON mode together.

## First commands

```bash
mcpc --verbose connect https://research.yigitkonur.com/mcp @research-debug
mcpc --json @research-debug help
mcpc --json @research-debug tools-list
```

## Log files

Current per-session bridge logs look like:

- `~/.mcpc/logs/bridge-@research-debug.log`
- `~/.mcpc/logs/bridge-@everything-http.log`

Inspect them directly:

```bash
sed -n '1,160p' ~/.mcpc/logs/bridge-@research-debug.log
rg 'error|warn|task|notify|session' ~/.mcpc/logs/bridge-@research-debug.log
```

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
```

## State clues

When a session is unhealthy, focus on `connecting`, `reconnecting`, `crashed`, `unauthorized`, and `expired`.
Those states tell you whether you have a transport problem, an auth problem, or a recoverable reconnect loop.
