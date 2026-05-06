# Canonical Anchor — `mcp-use/mcp-chart-builder`

The clearest package-adjacent streaming-widget example in the mcp-use ecosystem. Read it to verify the `useWidget` streaming surface and server-side no-setup pattern. Do not treat the current repo as the exact render-branch pattern in `03-three-phase-render.md`.

**Repo:** [github.com/mcp-use/mcp-chart-builder](https://github.com/mcp-use/mcp-chart-builder)

## Why this one

It demonstrates the streaming surface end to end:

- A widget that destructures `partialToolInput` and `isStreaming` from `useWidget`.
- A `getOption()` helper that prefers complete `props.option`, then reads `partialToolInput.option` while streaming.
- A non-streaming fallback that works in ChatGPT.
- A server-side tool definition that does **nothing** special for streaming, confirming `05-server-side-no-setup.md`.

## Load-bearing files

| File | What to look at |
|---|---|
| `resources/chart-display/widget.tsx` | The full widget. Confirm `useWidget<ChartDisplayProps>()` destructures `props`, `isPending`, `isStreaming`, and `partialToolInput`; `getOption()` reads `partialToolInput.option`; the render returns a pending skeleton whenever `isPending` is true. |
| `resources/chart-display/types.ts` | The `ChartDisplayProps` type and Zod schema used by both complete props and partial-preview reads. |

## How to read it

1. Open `widget.tsx`. Find the `useWidget<ChartProps>()` call. Confirm the four pieces destructured: `props`, `isPending`, `isStreaming`, `partialToolInput`.
2. Locate `getOption()`. Verify it reads `props.option` first and then `partialToolInput.option` when `isStreaming`.
3. Locate the render branches. The current repo uses `if (isPending) return skeleton`, so it proves API availability, not the exact preview branch this skill recommends.
4. Open `types.ts`. Confirm the schema and `ChartDisplayProps` shape.
5. Search the repo for `streaming` in the server source. You should find nothing tool-side — confirming the server handler has no streaming-specific code.

## Patterns it demonstrates

- **Partial object tolerance.** `getOption()` guards against invalid partial chart options during streaming.
- **Fallback rendering.** The pending skeleton and complete UI both work standalone — load the widget in ChatGPT (no streaming) and it still renders correctly.
- **No server streaming code.** The server only returns `widget({ props })`; partial arguments are runtime-provided.

Do not copy this repo wholesale. Use it as evidence for the API names and no-server-setup rule, then use `03-three-phase-render.md` for the recommended render branching.
