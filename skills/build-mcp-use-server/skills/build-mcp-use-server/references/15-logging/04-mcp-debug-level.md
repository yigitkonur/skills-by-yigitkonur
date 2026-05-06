# `MCP_DEBUG_LEVEL` Environment Variable

`MCP_DEBUG_LEVEL` controls mcp-use's HTTP request logger. In `mcp-use@1.26.0` it is string-valued: `info`, `debug`, or `trace`.

## Levels

| Value | What you see |
|---|---|
| `info` (default) | One compact line per request: session, client, MCP method, outcome |
| `debug` | `info` output plus inline `args=<json>` for `tools/call` requests |
| `trace` | Full request/response headers and bodies after the summary line |

## Usage

```bash
# Default compact request logs
node server.js

# Tool-call args in request logs
MCP_DEBUG_LEVEL=debug node server.js

# Full wire trace
MCP_DEBUG_LEVEL=trace node server.js
```

The variable is read per request by the HTTP logging middleware, but deployed processes usually still need a restart after env changes.

## Legacy `DEBUG`

If `MCP_DEBUG_LEVEL` is unset, any truthy legacy `DEBUG` value maps the HTTP request logger to `trace`.

| Env | HTTP request logger effect |
|---|---|
| `MCP_DEBUG_LEVEL=info` | `info` |
| `MCP_DEBUG_LEVEL=debug` | `debug` |
| `MCP_DEBUG_LEVEL=trace` | `trace` |
| `DEBUG=1` and no `MCP_DEBUG_LEVEL` | `trace` |
| no env | `info` |

## What each level shows

### `info`

- One compact line for `initialize`, `notifications/initialized`, `tools/list`, `tools/call`, and errors.
- Includes a short session id when one exists.

### `debug`

Everything in `info`, plus:

- Inline JSON arguments for `tools/call`.

### `trace`

Everything in `debug`, plus:

- Full request headers and body.
- Full response headers and body.

Use `trace` only when debugging specific protocol issues; it can include sensitive request and response data.

## Tuning for production

| Environment | `MCP_DEBUG_LEVEL` |
|---|---|
| Production | `info` |
| Staging | `info` or `debug` |
| Local development | `debug` |
| Bug repro / Inspector replay | `trace` |

## Relation to `Logger`

`MCP_DEBUG_LEVEL` is not the same knob as `Logger.configure(...)` or `Logger.setDebug(...)`. Use this file for HTTP request logs; use `03-server-logger.md` for application loggers.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Leaving `MCP_DEBUG_LEVEL=trace` on in production | Logs explode; secrets leak | Set `info` in prod env config |
| Using numeric `MCP_DEBUG_LEVEL=1` / `2` | Ignored by 1.26.0 request logger | Use `debug` / `trace` |
| Using `DEBUG=true` | Enables `trace`, often too noisy | Prefer explicit `MCP_DEBUG_LEVEL=debug` |
| Conflating `MCP_DEBUG_LEVEL` with `Logger.configure({ level })` | Different logging systems | Configure both deliberately when needed |
