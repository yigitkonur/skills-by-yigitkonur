# The `ctx` Object (RequestContext)

*Read this when you need context methods and capabilities in your tool handler.*

The handler signature is `async (input, ctx) => result`. `input` is the validated, typed arguments. `ctx: RequestContext<TUser, HasOAuth, TEnv>` is the per-request context.

```typescript
async (input, ctx) => {
  await ctx.sendLog("info", "Starting");
  const { name } = ctx.client.info();
  if (ctx.client.supportsViews()) {
    // Send a view-compatible response
  }
  return { content: [...] };
}
```

## Full Surface

**RequestClientContext methods:**

| Method | Signature | Purpose |
|---|---|---|
| `can(capability)` | `(capability: string) => boolean` | Check if client declares a top-level capability (e.g., `"elicitation"`, `"roots"`) |
| `capabilities()` | `() => ClientCapabilities` | Get shallow copy of all advertised capabilities |
| `extension(id)` | `(id: string) => Record<string, unknown> \| undefined` | Get extension settings by namespaced ID (e.g., `"io.modelcontextprotocol/ui"`) |
| `info()` | `() => Partial<Implementation>` | Get client name/version; partial for v1 compat |
| `user()` | `() => UserContext \| undefined` | Get OpenAI-specific end-user hints (locale, userAgent, location, etc.) — unverified client-reported data |
| `supportsViews()` | `() => boolean` | Check if client declares `io.modelcontextprotocol/ui` extension with MCP App MIME type |

**RequestContextBase fields:**

| Field | Type | Purpose |
|---|---|---|
| `signal` | `AbortSignal` | Aborted when client cancels or connection drops |
| `request` | `HonoRequest \| undefined` | Hono request; raw Web Request via `request.raw` |
| `req` | `HonoRequest \| undefined` | Deprecated alias for `request` |
| `client` | `RequestClientContext` | Capability queries (see methods above) |
| `inputResponses` | `Record<string, unknown> \| undefined` | Client responses to `input_required` elicitation (on retry round) |
| `requestState` | `RequestStateAccessor` | Opaque state codec (from `createRequestStateCodec`) for round-trip validation |
| `sendNotification` | `(method: string, params?: Record<string, unknown>) => Promise<void>` | Send one-way notification on this request's response stream |
| `reportProgress` | `(progress: number, total?: number, message?: string) => Promise<boolean>` | Report progress; returns `true` if delivered, `false` if not requested |
| `sendLog` | `(level: "debug" \| "info" \| "notice" \| "warning" \| "error" \| "critical" \| "alert" \| "emergency", data: unknown, logger?: string) => Promise<void>` | Send log message to client |

**OAuthAuth fields (when OAuth configured):**

| Field | Type | Purpose |
|---|---|---|
| `user` | `TUser` | Authenticated user (provider-specific shape) |
| `payload` | `Record<string, unknown>` | Verified access-token claims or introspection data |
| `accessToken` | `string` | Raw bearer token for downstream requests |
| `scopes` | `string[]` | OAuth scopes granted to token |
| `permissions` | `string[]` | Provider-normalized permissions |
| `clientId` | `string \| undefined` | OAuth client ID from `client_id` or `azp` claim |
| `expiresAt` | `number` | Unix time (seconds) access-token expires |
| `resource` | `URL \| undefined` | Resource audience token authorizes |

## Usage Examples

Check capabilities before acting:

```typescript
if (ctx.client.supportsViews()) {
  // Shape response for View-capable client
  return {
    content: [...],
    structuredContent: { /* matches outputSchema */ },
  };
}
```

Log during execution:

```typescript
await ctx.sendLog("info", `Processing ${input.count} items`);
await ctx.sendLog("warning", "Request approaching timeout");
```

Access authenticated user:

```typescript
if (ctx.auth) {
  const { user, permissions } = ctx.auth;
  // user shape depends on OAuth provider
}
```

Report progress:

```typescript
for (let i = 0; i < total; i++) {
  const sent = await ctx.reportProgress(i, total, `Item ${i}/${total}`);
  if (!sent) console.log("No progress token supplied");
}
```

## `ctx.auth`

Present and required only when OAuth is configured on the server. Without OAuth, its type is `never`.

```typescript
const userId = ctx.auth.user.userId;
const scopes = ctx.auth.permissions;
```

## Availability matrix

| Feature | Requires |
|---|---|
| `ctx.client.info()` | Request client metadata; legacy requests may return a partial object. |
| `ctx.client.can(cap)` | Client declared capability. |
| `ctx.auth` | OAuth configured. |
| `ctx.reportProgress()` | Client sent a progress token; returns `false` otherwise. |
| `ctx.sendNotification()` | Must be called before the callback returns. |
