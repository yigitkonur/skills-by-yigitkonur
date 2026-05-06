# `ctx.client.can(capability)`

`ctx.client.can(capability)` returns `true` when the connected client advertised a top-level capability key. It is the **mandatory guard** before calling features that some hosts don't implement.

```typescript
if (!ctx.client.can("sampling")) {
  return error("This tool requires a client that supports sampling.");
}
```

## Signature

```typescript
ctx.client.can(capability: string): boolean
```

| Capability | What it gates |
|---|---|
| `"sampling"` | `ctx.sample()` calls — see `../13-sampling/` |
| `"elicitation"` | `ctx.elicit()` calls — see `../12-elicitation/` |
| `"roots"` | `server.listRoots(sessionId)` and `server.onRootsChanged()` — see `../14-notifications/05-roots.md` |

The implementation is intentionally generic: `can(name)` checks whether `name` is present in the raw capabilities object. Document and depend only on capability keys you can verify from the MCP protocol, package declarations, or a target host.

## Mandatory guards

| Feature | Guard |
|---|---|
| Calling `ctx.sample()` | `if (!ctx.client.can("sampling")) return error(...)` |
| Calling `ctx.elicit()` | `if (!ctx.client.can("elicitation")) return error(...)` |
| Returning a widget | `if (!ctx.client.supportsApps()) return text(...)` (see `04-supports-apps.md`) |
| Calling `server.listRoots(ctx.session.sessionId)` | `if (!ctx.client.can("roots")) return ...` |

A tool that calls `ctx.sample()` without the guard can fail on any client that did not advertise sampling.

## Inspecting all capabilities

`ctx.client.capabilities()` returns the raw capabilities object negotiated at initialize time:

```typescript
const caps = ctx.client.capabilities();
// e.g. {
//   sampling: {},
//   roots:    { listChanged: true },
//   elicitation: { form: {}, url: {} },
//   extensions: { "io.modelcontextprotocol/ui": { mimeTypes: [...] } },
// }
```

Use this for diagnostic logging or to inspect raw sub-fields. For MCP Apps widgets, prefer `ctx.client.supportsApps()` over hand-reading `capabilities().extensions`.

## Combining checks

```typescript
const hasBoth =
  ctx.client.can("sampling") &&
  ctx.client.can("elicitation");

if (hasBoth) {
  // Two-step: ask user, then sample
  const prefs = await ctx.elicit("Prefs?", schema);
  if (prefs.action !== "accept") return text("Cancelled.");
  const r = await ctx.sample(`Use prefs ${JSON.stringify(prefs.data)} to ...`);
  return text(r.content.text);
}
```

## Graceful degradation pattern

```typescript
server.tool(
  { name: "summarize", schema: z.object({ text: z.string() }) },
  async ({ text: input }, ctx) => {
    if (ctx.client.can("sampling")) {
      const r = await ctx.sample(`Summarize: ${input}`, { maxTokens: 200 });
      return text(r.content.text);
    }

    // Fall back to a simple heuristic the server can do alone
    const firstSentence = input.split(/[.!?]/)[0] + ".";
    return text(`(no LLM) First sentence: ${firstSentence}`);
  }
);
```

## Why guard explicitly

Without the guard:

- The call rejects with a cryptic transport-level error.
- Your handler crashes, surfacing as a tool failure.
- The user sees "tool failed" without knowing it was a capability mismatch.

With the guard:

- You return a clear `error("Sampling not supported.")` or fall back gracefully.
- The user understands the limitation.
- Your tool stays useful on basic clients.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Calling `ctx.sample()` without `can("sampling")` guard | Always guard |
| Probing capability with `try/catch` instead of `can()` | Use `can()` — it's a synchronous boolean |
| Treating `can("extensions")` as widget support | Use `supportsApps()`; it checks the UI extension and MIME type |
| Re-checking `can()` inside a loop | Cache once at the top of the handler |
