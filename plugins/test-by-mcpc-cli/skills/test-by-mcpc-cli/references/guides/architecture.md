# Architecture

`mcpc 0.2.x` is a session-oriented CLI layered over detached bridge processes.

## Mental model

1. `mcpc connect <server> @session` resolves the target and starts a bridge.
2. The bridge owns the live transport session to the MCP server.
3. Later commands reuse the named session instead of reconnecting from scratch.
4. `mcpc --json` and `mcpc --json @session` read from session state plus live server calls.

## Transport model that matters for this skill

- `stdio` via `file:entry` config targets
- Streamable HTTP for remote and localhost URLs
- not SSE as a practical `mcpc 0.2.4` test target

## Capability model

Separate three layers when you document behavior:

1. what the server advertises
2. what `mcpc` advertises as a client during initialize
3. what the CLI actually exposes as commands

That distinction explains why you can see `completions`, `roots`, or sampling-related capability signals without getting polished top-level CLI commands for them.

## Useful implementation details

- `tools-get` is a CLI convenience built from tool metadata rather than a native MCP `tools/get` request
- the bridge maintains cached discovery data and refreshes it when list-changed notifications arrive
- task support is now first-class at the CLI layer through `tools-call --task`, `tools-call --detach`, and `tasks-*`

Use live behavior over README prose when they conflict.
