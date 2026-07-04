# The `ctx` Object

The handler signature is `async (args, ctx) => result`. `args` is the validated, typed input. `ctx` is the per-call context — session state, client identity, logging, and the advanced MCP capabilities (sampling, elicitation, progress).

```typescript
async (args, ctx) => {
  await ctx.log("info", "starting");
  const { name } = ctx.client.info();
  // ...
}
```

## Surface at a glance

| Property | Purpose | Deep dive |
|---|---|---|
| `ctx.session` | Session object (`sessionId`) when the call is associated with a session. | `10-sessions/` |
| `ctx.client` | Client identity and capabilities. | `16-client-introspection/` |
| `ctx.auth` | Authenticated user (OAuth). | `11-auth/` |
| `ctx.log(level, msg)` | Send log messages to the client. | `15-logging/` |
| `ctx.reportProgress?.(loaded, total, msg)` | Progress updates for long-running tools when a progress token is present. | `14-notifications/` |
| `ctx.elicit(prompt, schema)` | Request user input mid-execution. | `12-elicitation/` |
| `ctx.sample(request)` | Request LLM completion from the client. | `13-sampling/` |
| `ctx.sendNotification(method, params)` | Custom server-to-client notification. | `14-notifications/` |

## `ctx.client`

Stable session-level data plus capability checks. All values come from the MCP `initialize` handshake unless noted.

| Method | Returns |
|---|---|
| `ctx.client.info()` | `{ name, version }` of the client (e.g. `"ChatGPT", "1.0.0"`). |
| `ctx.client.can("sampling")` | `true`/`false` for a named capability. |
| `ctx.client.supportsApps()` | `true` if the client is MCP Apps / ChatGPT compatible. |
| `ctx.client.extension(id)` | Returns extension metadata by ID, or `undefined`. |
| `ctx.client.user()` | Per-invocation `UserContext` from `params._meta`, or `undefined`. Client-reported and unverified — never use for access control. |

```typescript
const { name, version } = ctx.client.info();
if (ctx.client.can("sampling")) {
  const reply = await ctx.sample({ messages: [...], maxTokens: 200 });
}
```

For verified identity, use `ctx.auth` (requires OAuth).

## `ctx.log`

Send structured log messages to the client during handler execution.

```typescript
await ctx.log("info", "Processing started");
await ctx.log("debug", `Item ${i} of ${total}`);
await ctx.log("error", "Database unavailable");
```

Levels (ascending severity): `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`. Optional third arg is a logger name string.

## `ctx.reportProgress`

For long-running tools, report progress against a total. Only effective when the client passed a progress token.

```typescript
for (let i = 0; i < files.length; i++) {
  await ctx.reportProgress?.(i, files.length, `Processing ${files[i]}`);
  await processFile(files[i]);
}
```

## `ctx.elicit`

Pause the handler and request additional input from the user. Check `ctx.client.can("elicitation")` first.

```typescript
if (!ctx.client.can("elicitation")) {
  return error("This tool requires elicitation support.");
}
const { env } = await ctx.elicit("Which environment?", z.object({
  env: z.enum(["staging", "prod"]),
}));
```

## `ctx.sample`

Request the client's LLM to generate a completion. Check `ctx.client.can("sampling")` first.

```typescript
if (!ctx.client.can("sampling")) {
  return error("This tool requires sampling support.");
}
const summary = await ctx.sample({
  messages: [{ role: "user", content: { type: "text", text: longDoc } }],
  maxTokens: 500,
});
```

## `ctx.auth`

Present only when OAuth is configured on the server.

```typescript
if (!ctx.auth) return error("Authentication required.");
const userId = ctx.auth.user.userId;
const scopes = ctx.auth.permissions;
```

## Availability matrix

| Feature | Requires |
|---|---|
| `ctx.session?.sessionId` | Stateful/sessionful calls. May be absent in stateless/no-session paths. |
| `ctx.client.info()` | Client `initialize` handshake — always present. |
| `ctx.client.can(cap)` | Client declared capability. |
| `ctx.log()` | Client logging capability — silently dropped otherwise. |
| `ctx.auth` | OAuth configured — `undefined` without it. |
| `ctx.elicit()` | `ctx.client.can("elicitation")`. |
| `ctx.sample()` | `ctx.client.can("sampling")`. |
| `ctx.reportProgress?.()` | Client sent a progress token in the request. |
| `ctx.sendNotification()` | Current call is associated with a live session. Not available in stateless/no-session paths. |
