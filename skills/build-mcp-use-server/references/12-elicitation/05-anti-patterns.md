# Elicitation Anti-Patterns

*Read this for common pitfalls and their fixes.*

| Anti-pattern | Problem | Fix |
|---|---|---|
| Calling `ctx.elicit()` | Does not exist in shipped 2.0.0-beta.66 — compile error | Use `inputRequired()` + `inputRequired.elicit()`/`.elicitUrl()`; read responses with `inputResponse()`/`acceptedContent()` |
| No capability gate | Tool errors on clients without elicitation support | Always check `ctx.client.capabilities().elicitation` |
| Ignoring `decline`/`cancel` | Tool proceeds as if the user answered, or hangs | Handle all `kind`/`action` combinations: `missing`, `elicit`+`accept`, `elicit`+`decline`, `elicit`+`cancel` |
| Reading `ctx.inputResponses` directly | Skips schema validation; trusts unvalidated wire data | Read through `acceptedContent(ctx.inputResponses, key, schema)`, never destructure `ctx.inputResponses` by hand |
| Form mode for passwords | Credentials cross MCP transport | Use `inputRequired.elicitUrl({ message, url })` for sensitive data |
| Missing `.describe()` on fields | Form shows field names, not user-friendly labels | Every Zod field needs `.describe()` |
| No `.default()` on optional fields | Handler code must defensively check `undefined` | Use `.default()` for total data shape |
| Unbounded retry loops | User cannot escape the prompt | Cap retries (e.g., max 3 attempts), treat `decline`/`cancel` as terminal |
| Massive single form | Low completion rate | Split into 2-3 small elicitations, or batch only truly related fields into one `inputRequests` object |
| Free-text instead of enum | Ambiguous parsing, LLM friction | Use `z.enum([...])` for bounded choices |
| State in module scope | Leaks across requests and users — the module is shared, not per-flow | Keep state in handler closure, `requestState` codec, or external DB with user scope |
| Chaining elicit + side effects | Side effects run even on decline/cancel | Only perform mutations after `acceptedContent()` returns validated data |
| Wrong `createRequestStateCodec` shape | `{ secret, maxAge }` is not the real signature | Use `{ key: Uint8Array, ttlSeconds: number }` |
| `new MCPServer({ requestState: codec.verify })` | Wrong wiring — `requestState` expects an object | Use `{ requestState: { verify: codec.verify } }` |
| `ctx.requestState.parse()` | Not a real method | `ctx.requestState<T>()` is a generic function call, no `.parse()` |

## Don't call `ctx.elicit()`

```typescript
// BAD — ctx.elicit does not exist in shipped beta.66; fails to compile
const result = await ctx.elicit("confirm", { schema: confirmSchema });

// GOOD — the real, shipped, tested surface
const response = inputResponse(ctx.inputResponses, "confirm");
if (response.kind === "elicit" && response.action !== "accept") {
  return { content: [{ type: "text", text: `Cancelled: ${response.action}` }], isError: true };
}
const confirmed = acceptedContent(ctx.inputResponses, "confirm", confirmSchema);
if (confirmed === undefined) {
  return inputRequired({
    inputRequests: { confirm: inputRequired.elicit({ message: "Confirm?", requestedSchema: confirmSchema }) },
  });
}
```

## Don't collect secrets through forms

```typescript
// BAD — password travels via MCP
inputRequired.elicit({ message: "Password", requestedSchema: z.object({ password: z.string() }) });

// GOOD — browser owns the credential
inputRequired.elicitUrl({ message: "Log in", url: "https://app.example.com/login" });
```

## Handle every response kind and action

```typescript
// BAD — assumes accept, and reads unvalidated data directly
const r = ctx.inputResponses?.confirm;
return { content: [{ type: "text", text: `Confirmed by ${r.user}` }] };

// GOOD — exhaustive branching through the real helpers
const response = inputResponse(ctx.inputResponses, "confirm");
if (response.kind === "missing") {
  return inputRequired({
    inputRequests: { confirm: inputRequired.elicit({ message: "Confirm?", requestedSchema: confirmSchema }) },
  });
}
if (response.kind === "sampling") {
  return { content: [{ type: "text", text: "Unexpected sampling response." }], isError: true };
}
if (response.action === "decline") {
  return { content: [{ type: "text", text: "User declined." }], isError: true };
}
if (response.action === "cancel") {
  return { content: [{ type: "text", text: "User cancelled." }], isError: true };
}

const confirmed = acceptedContent(ctx.inputResponses, "confirm", confirmSchema);
if (confirmed === undefined) {
  return { content: [{ type: "text", text: "Accepted confirmation failed validation." }], isError: true };
}
return { content: [{ type: "text", text: `Confirmed by ${confirmed.user}` }] };
```

## Don't loop unbounded

```typescript
// BAD — no bound, and ctx.elicit doesn't exist
while (true) {
  const r = await ctx.elicit("retry", { schema });
  if (r.status === "accept") break;
}

// GOOD — signed, persistent attempt count across handler re-entry
import { acceptedContent, createRequestStateCodec, inputRequired, inputResponse, MCPServer } from "mcp-use";
import { z } from "zod";

const MAX_ATTEMPTS = 3;
type RetryState = { phase: "awaiting-retry"; attempts: number };

const retryStateKey = process.env.REQUEST_STATE_SECRET;
if (!retryStateKey) throw new Error("REQUEST_STATE_SECRET is required");

const retrySchema = z.object({ value: z.string().min(1).describe("Non-empty value") });
const retryStateCodec = createRequestStateCodec<RetryState>({
  key: retryStateKey, // >= 32 bytes/chars
  ttlSeconds: 300,
});
const retryServer = new MCPServer({
  name: "bounded-retry-server",
  version: "1.0.0",
  requestState: { verify: retryStateCodec.verify },
});

retryServer.tool({ name: "bounded-retry", inputSchema: z.object({}) }, async (_params, ctx) => {
  // Verified workflow state must be read before this round's response.
  const state = ctx.requestState<RetryState>();
  if (state !== undefined && state.phase !== "awaiting-retry") {
    return { content: [{ type: "text", text: "Invalid retry phase." }], isError: true };
  }

  const response = inputResponse(ctx.inputResponses, "retry");
  if (response.kind === "elicit" && response.action !== "accept") {
    return { content: [{ type: "text", text: `Retry ${response.action}.` }], isError: true };
  }
  if (response.kind === "sampling") {
    return { content: [{ type: "text", text: "Unexpected sampling response." }], isError: true };
  }

  if (response.kind !== "missing" && state === undefined) {
    return { content: [{ type: "text", text: "Retry state missing or expired." }], isError: true };
  }

  const value = acceptedContent(ctx.inputResponses, "retry", retrySchema);
  if (value !== undefined) {
    return { content: [{ type: "text", text: "Accepted valid input." }] };
  }

  const attempts = state?.attempts ?? 0;
  if (attempts >= MAX_ATTEMPTS) {
    return { content: [{ type: "text", text: `Maximum ${MAX_ATTEMPTS} attempts reached.` }], isError: true };
  }

  const nextAttempt = attempts + 1;
  return inputRequired({
    inputRequests: {
      retry: inputRequired.elicit({ message: `Try again (${nextAttempt}/${MAX_ATTEMPTS})`, requestedSchema: retrySchema }),
    },
    requestState: await retryStateCodec.mint({ phase: "awaiting-retry", attempts: nextAttempt }),
  });
});
```

Track attempt counts with `requestState`, not a loop — the handler re-enters from the top on every round; there is no live loop to bound.

## Defer side effects until accept

```typescript
// BAD — transfers money even on cancel
const r = await ctx.elicit("confirm-xfer", { schema });
await transferMoney(params.amount, params.recipient);

// GOOD — mutation only after validated accept
const response = inputResponse(ctx.inputResponses, "confirm-xfer");
if (response.kind === "elicit" && response.action !== "accept") {
  return { content: [{ type: "text", text: "Transfer not confirmed." }], isError: true };
}
const confirmed = acceptedContent(ctx.inputResponses, "confirm-xfer", confirmSchema);
if (confirmed === undefined) {
  return inputRequired({
    inputRequests: { "confirm-xfer": inputRequired.elicit({ message: "Confirm transfer?", requestedSchema: confirmSchema }) },
  });
}
// Re-entry with validated accept: safe to mutate
await transferMoney(params.amount, params.recipient);
```

## Pre-flight checklist

| Item | Why |
|---|---|
| No `ctx.elicit()` anywhere? | It does not exist in shipped beta.66; use `inputRequired`/`inputResponse`/`acceptedContent` |
| Capability gated? | Prevents crashes on unsupported clients |
| Every `kind`/`action` handled? | Prevents hung or broken tools on `decline`/`cancel` |
| Reads go through `acceptedContent()`? | Never trust `ctx.inputResponses` unvalidated |
| Secrets use URL mode? | Security: credentials stay in browser |
| `.describe()` on fields? | Improves user experience |
| `.default()` where sensible? | Cleaner handler code |
| Max 2-3 rounds, batched where related? | Higher completion rate |
| Side effects after validated accept? | Avoids partial state on decline/cancel |
| No module-scope state? | Prevents cross-request/cross-user data leaks |
| `createRequestStateCodec({ key, ttlSeconds })`? | Not `{ secret, maxAge }` |
| `requestState: { verify }` on `MCPServer`? | Not the bare verify function |
