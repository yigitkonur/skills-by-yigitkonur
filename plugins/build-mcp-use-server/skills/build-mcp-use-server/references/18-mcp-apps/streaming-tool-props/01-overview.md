# Streaming Tool Props — Overview

Streaming tool props lets a widget show a partial preview of its content **while the LLM is still generating the tool arguments**. Instead of a loading spinner until the server responds, the widget renders incremental output as the model writes it — code appearing line by line, chart points appearing one at a time, summaries unfolding sentence by sentence.

## When it works

| Host | `partialToolInput` / `isStreaming` | Notes |
|---|---|---|
| Claude Desktop / Claude.ai (MCP Apps) | Yes | Sends `ui/notifications/tool-input-partial`. |
| Goose (MCP Apps) | Yes | Same. |
| MCP Inspector | Yes | Useful for testing. |
| ChatGPT (Apps SDK protocol) | No | `isStreaming` stays `false`, `partialToolInput` stays `null`. Always implement the `isPending` fallback (see `04-fallback-for-non-streaming-hosts.md`). |

## The three visible render phases

In `mcp-use@1.26.0`, the hook does **not** expose a reliable separate "executing" flag after a partial has arrived. The visible states are:

1. **Pending fallback** (`isPending = true`, `partialToolInput = null`) — render a skeleton/spinner.
2. **Streaming / waiting with partials** (`isPending = true`, `partialToolInput != null`) — render from `partialToolInput`. `isStreaming` stays `true` until the tool result clears the partial in the current runtime.
3. **Complete** (`isPending = false`) — read `props` (server-computed `structuredContent`, overlaid on `toolInput` by `useWidget`).

See `02-state-machine.md` for the full state table and `03-three-phase-render.md` for the render pattern.

## Why this is a client-only concern

The server tool handler never sees partial arguments — the runtime intercepts the protocol-level partial-args notifications and exposes them on `useWidget()`. Your server tool stays a normal `widget(...)` response. See `05-server-side-no-setup.md`.

## Files in this cluster

- `02-state-machine.md` — the four states and what's available in each.
- `03-three-phase-render.md` — the canonical render pattern.
- `04-fallback-for-non-streaming-hosts.md` — what to do when the host doesn't expose partials.
- `05-server-side-no-setup.md` — proof that the server needs no special wiring.
- `canonical-anchor.md` — reference repo and load-bearing files.

**Canonical doc:** [manufact.com/docs/typescript/server/mcp-apps](https://manufact.com/docs/typescript/server/mcp-apps)
