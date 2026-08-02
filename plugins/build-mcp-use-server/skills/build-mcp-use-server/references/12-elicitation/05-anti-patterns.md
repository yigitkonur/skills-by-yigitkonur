# Elicitation Anti-Patterns

*Read this for common pitfalls and their fixes.*

| Anti-pattern | Problem | Fix |
|---|---|---|
| No capability gate | Tool errors on clients without elicitation support | Always check `ctx.client.capabilities().elicitation` |
| Ignoring `cancel` status | Tool hangs waiting for user to submit | Handle all three statuses: `accept`, `cancel`, and error cases |
| Form mode for passwords | Credentials cross MCP transport | Use `inputRequired.elicitUrl()` for sensitive data |
| Missing `.describe()` on fields | Form shows field names, not user-friendly labels | Every Zod field needs `.describe()` |
| No `.default()` on optional fields | Handler code must defensively check `undefined` | Use `.default()` for total data shape |
| Unbounded retry loops | User cannot escape the prompt | Cap retries (e.g., max 3 attempts), treat `cancel` as terminal |
| Massive single form | Low completion rate | Split into 2-3 small sequential elicitations |
| Free-text instead of enum | Ambiguous parsing, LLM friction | Use `z.enum([...])` for bounded choices |
| State in module scope | Leaks across tool invocations and users | Keep state in handler closure or external DB with user scope |
| Chaining elicit + side effects | Side effects run even on cancel/decline | Only perform mutations after `status === "accept"` |

## Don't collect secrets through forms

```typescript
// BAD — password travels via MCP
return inputRequired.elicit("password", {
  schema: z.object({ password: z.string() }),
}).result;

// GOOD — browser owns the credential
return inputRequired.elicitUrl("https://app.example.com/login").result;
```

## Handle all three statuses

```typescript
// BAD — assumes accept
const r = await ctx.elicit("confirm", { schema: confirmSchema });
return { content: [{ type: "text", text: `Confirmed by ${r.data.user}` }] };

// GOOD — exhaustive branching
if (response.status === "required") {
  return response.result;
} else if (response.status === "accept") {
  return { content: [{ type: "text", text: `Confirmed by ${response.data.user}` }] };
} else {
  return { content: [{ type: "text", text: "User cancelled." }] };
}
```

## Don't loop unbounded

```typescript
// BAD — user trapped
while (true) {
  const r = await ctx.elicit("retry", { schema });
  if (r.status === "accept") break;
}

// GOOD — bounded with terminal exit
for (let attempt = 1; attempt <= 3; attempt++) {
  const r = await ctx.elicit("retry", { schema });
  if (r.status === "required") return r.result;
  if (r.status === "accept") return { content: [...] };
  if (attempt === 3) return { content: [{ type: "text", text: "Max retries reached." }] };
}
```

## Defer side effects until accept

```typescript
// BAD — transfers money even on cancel
const r = await ctx.elicit("confirm-xfer", { schema });
await transferMoney(params.amount, params.recipient);

// GOOD — mutation only after validation
if (!ctx.inputResponses) {
  // First call: ask for confirmation
  return inputRequired.elicit("confirm-xfer", { schema }).result;
}
// Re-entry: validation passed, safe to mutate
await transferMoney(params.amount, params.recipient);
```

## Pre-flight checklist

| Item | Why |
|---|---|
| Capability gated? | Prevents crashes on unsupported clients |
| All statuses handled? | Prevents hung or broken tools |
| Secrets use URL mode? | Security: credentials stay in browser |
| `.describe()` on fields? | Improves user experience |
| `.default()` where sensible? | Cleaner handler code |
| Max 3 steps? | Higher completion rate |
| Side effects after `accept`? | Avoids partial state on cancel |
| No module-scope state? | Prevents cross-user data leaks |
