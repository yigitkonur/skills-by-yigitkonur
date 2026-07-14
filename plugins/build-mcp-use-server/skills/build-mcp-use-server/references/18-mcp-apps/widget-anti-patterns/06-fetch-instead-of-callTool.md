# Anti-Pattern: `fetch()` From a Widget Instead of `useCallTool()`

A widget runs in a sandboxed iframe with a tight CSP, no auth context, and no MCP session. Calling your own MCP server with raw `fetch()` skips every guarantee mcp-use gives you.

## What goes wrong

```tsx
// BAD — bypasses MCP, breaks in production
function SearchContent() {
  const handleClick = async () => {
    const res = await fetch("http://localhost:3000/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "test" }),
    });
    const data = await res.json();
  };
  return <button onClick={handleClick}>Search</button>;
}
```

What breaks:

| Concern | What `fetch()` skips |
|---|---|
| Auth | The iframe has no cookies, no Authorization header, no OAuth token |
| Session | No `mcp-session-id` — server treats every call as a new session |
| Schema validation | No Zod parsing on the way in or out — type drift goes unnoticed |
| CSP | Need to whitelist your own origin in `connectDomains` (often forgotten) |
| Result state | Hand-rolled instead of `data` / `error` / `isPending` |
| Streaming | No access to `partialToolInput` |
| Host portability | `localhost:3000` only works in dev — production widgets are deployed cross-origin |

## Use `useCallTool`

`useCallTool` rides the existing MCP session over the host's `postMessage` bridge. The host already has the session, the auth, the CSP allowance, and the schema.

```tsx
// GOOD — typed, authed, sessioned, state-managed
import { useCallTool } from "mcp-use/react";

function SearchContent() {
  const { callTool, callToolAsync, isPending, data, error } = useCallTool("search");

  return (
    <>
      <button onClick={() => callTool({ query: "test" })} disabled={isPending}>
        {isPending ? "Searching..." : "Search"}
      </button>
      {error && <p className="text-red-500">{error.message}</p>}
      {data && <pre>{JSON.stringify(data.structuredContent, null, 2)}</pre>}
    </>
  );
}
```

Two flavours:

| Method | When to use |
|---|---|
| `callTool(args)` | Fire-and-forget; read result via `data` / `error` / `isPending` |
| `callToolAsync(args)` | Returns a Promise; you `await` it inline (e.g. inside `handleSubmit`) |

## When `fetch()` is genuinely fine

Only when you are calling a **third-party** API from inside the widget — and even then prefer proxying through your own MCP server tool, because:

- The browser exposes the network call to the user's devtools, including any `_meta` token you embed
- Each new third-party origin needs `connectDomains` and `resourceDomains` updates
- Rate limits hit the user, not your server pool

If you must:

```tsx
const res = await fetch("https://api.example.com/public-endpoint");
// Make sure widgetMetadata.metadata.csp.connectDomains includes "https://api.example.com"
```

## Anti-pattern in disguise: hand-rolled JSON-RPC

```tsx
// Also BAD — re-implementing useCallTool
const res = await fetch("/mcp", {
  method: "POST",
  body: JSON.stringify({
    jsonrpc: "2.0",
    id: 1,
    method: "tools/call",
    params: { name: "search", arguments: { query: "test" } },
  }),
});
```

This bypasses everything `useCallTool` solves — session ID, auth, partial input streaming, and result state. Don't.

## Migration recipe

1. Find every `fetch()` and `XMLHttpRequest` in `resources/`.
2. For each one that hits your own MCP server, swap to `useCallTool("<tool-name>")`.
3. Delete the now-unused `connectDomains` entries that only existed to allow the bypass.
4. For each one that hits a third-party API, ask: can the server tool do this instead and return the data via `widget({ props })`? Usually yes.

## Severity

Critical when targeting your own server (auth/session bypass), high when targeting third parties (CSP and token leakage).
