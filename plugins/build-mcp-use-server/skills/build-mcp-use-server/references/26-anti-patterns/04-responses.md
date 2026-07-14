# Responses

Response-shape anti-patterns. For when to combine `content` and `structuredContent` properly, see `05-responses/08-content-vs-structured-content.md`. For helper choice (`text`, `object`, `mix`, `error`), see `05-responses/`.

## Don't return `content` and `structuredContent` with different answers

Different clients consume different surfaces. Older or content-first clients render `content`; structured-first clients (notably some host UIs) parse `structuredContent`. If the two disagree, half your users see one answer and half see another.

```typescript
// ❌ content and structured disagree (or one is empty)
return { ...text("Operation completed."), structuredContent: { status: "error" } };
return { structuredContent: { results } };  // content empty
return text(formatHits(results));            // structuredContent empty
```

```typescript
// ✅ both surfaces carry the same essential answer
return {
  ...markdown(formatHits(results)),
  structuredContent: { results, count: results.length },
};
```

The rule: the structured surface and the readable surface must encode the same answer. If you reach for `mix(...)`, the same applies — both halves must agree.

## Don't put secrets in `structuredContent`

`structuredContent` is model- and transcript-visible. Anything you put there ends up in the model's context and may end up in user-facing transcripts.

```typescript
// ❌ leaks credentials into the model's working memory
return object({
  user: { id, name },
  internal: {
    dbPassword: process.env.DB_PASSWORD,
    apiKey: process.env.API_KEY,
  },
});
```

```typescript
// ✅ redact, or signal presence without value
return object({
  user: { id, name },
  internal: {
    dbPasswordSet: !!process.env.DB_PASSWORD,
    apiKeySet: !!process.env.API_KEY,
  },
});
```

For genuinely UI-private data (theme prefs, internal display flags) put it in `_meta`, not `structuredContent` — `_meta` is for sidecar data hosts may use but the model should not consume.

## Don't use `error()` for unexpected errors

Two return paths, two meanings:

| Path | Meaning |
|---|---|
| `return error("...")` | Expected, recoverable failure (not-found, validation, rate-limit, auth) |
| `throw err` | Bug or unexpected condition — let the transport surface a real error |

```typescript
// ❌ wraps a bug as a tool result — bug silently buried
try {
  await db.query(BROKEN_QUERY);
} catch (err) {
  return error("Operation failed");
}
```

```typescript
// ✅ expected failure → error(); bug → throw
async function getUser(id: string) {
  const user = await db.findUser(id);
  if (!user) return error(`User ${id} not found.`);  // expected
  return object(user);
  // anything thrown below propagates — the transport reports it
}
```

For the full decision rubric, see `24-production/04-error-strategy.md`.

## Don't return errors as `text()`

The model can't distinguish a normal answer that happens to mention "error" from an actual failure. Use `error()` so the client sets `isError: true`.

```typescript
// ❌ model treats this as a normal answer
if (!user) return text("Error: user not found");
```

```typescript
// ✅
if (!user) return error(`User ${id} not found.`);
```

## Don't return enormous payloads

A single tool response goes into one JSON-RPC message and lives in the model's context for the rest of the turn. Returning 100 k rows costs tokens and obscures the actual answer.

```typescript
// ❌ entire table — context eaten
const users = await db.query("SELECT * FROM users");  // 100 k rows
return text(JSON.stringify(users));
```

```typescript
// ✅ paginate; select only needed columns
server.tool({
  name: "list-users",
  schema: z.object({
    page: z.number().int().min(1).default(1),
    pageSize: z.number().int().min(1).max(50).default(20),
  }),
}, async ({ page, pageSize }) => {
  const offset = (page - 1) * pageSize;
  const users = await db.query(
    "SELECT id, name FROM users LIMIT $1 OFFSET $2",
    [pageSize, offset]
  );
  return object({ page, pageSize, users });
});
```

For *legitimately* large incremental output (LLM streams, line-by-line), use `stream()` — see `24-production/07-streaming-large-results.md`.

## Don't `text(JSON.stringify(obj))`

Stringifying loses the structured surface, the MIME hint, and forces the model (or downstream) to parse JSON inline.

```typescript
// ❌
return text(JSON.stringify(result));
```

```typescript
// ✅
return object(result);
```

## Don't build `CallToolResult` by hand

Hand-built result objects miss `_meta.mimeType`, miss `isError`, and may diverge from the helper output if the helper format changes. Use the helpers.

```typescript
// ❌ hand-rolled
return {
  content: [{ type: "text", text: `Hello ${name}` }],
};
```

```typescript
// ✅
return text(`Hello ${name}`);
```

## Don't include stack traces or paths in errors

Error messages reach the model and may reach the user. Stack traces leak internal structure; paths leak deployment layout; raw exceptions leak secrets that may have been in the variable.

```typescript
// ❌
return error(`Failed: ${err.stack}`);
```

```typescript
// ✅ short, user-safe message; full detail goes to your Logger
logger.error("get-user failed", err as Error);
return error("Lookup failed. Try again or contact support.");
```

## Quick checklist

| Don't | Do |
|---|---|
| `content` and `structuredContent` disagree | Both must encode the same essential answer |
| Secrets in `structuredContent` | Redact, or signal `*_Set: true/false`; UI-only data → `_meta` |
| `error()` for bugs | `error()` only for expected failures; `throw` for bugs |
| `text("Error: ...")` for failures | `error("...")` |
| Returning the entire table | Paginate; select needed columns |
| `text(JSON.stringify(obj))` | `object(obj)` |
| Hand-rolled `CallToolResult` | Response helpers |
| Stack traces, paths, secrets in error messages | User-safe message; log details server-side |
