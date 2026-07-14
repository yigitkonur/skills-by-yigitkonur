# Elicitation Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| No `ctx.client.can("elicitation")` guard | Crashes on clients without support | Capability-check before calling, return `error()` on mismatch |
| Ignoring `decline` / `cancel` | Tool hangs or returns wrong path on non-accept | Handle all three actions explicitly |
| Form mode for passwords / tokens | Credentials pass through the MCP transport | Use URL mode for sensitive data |
| No `try/catch` around `ctx.elicit()` | Timeouts and validation errors crash the handler | Wrap in try/catch, return `error()` on failure |
| Unbounded loops re-prompting on decline | User cannot escape | Cap retry count or treat decline as terminal |
| Missing `.describe()` on fields | Form labels are field names, not human text | Always add `.describe()` |
| No `.default()` on optional fields | Defensive code in handler unwrapping `undefined` | Use `.default()` so the data shape is total |
| Free-text where an enum fits | Ambiguous parsing, slower paths | `z.enum([...])` with concrete values |
| Massive single-step form | Low completion rate | Split into 2-3 small steps |
| Storing in-flight state in module scope | Bleeds across sessions and users | Keep state inside the handler closure or backend per-user |

## Don't elicit secrets

```typescript
// BAD — password reaches the MCP transport
await ctx.elicit("Sign in", z.object({
  password: z.string().describe("Password"),
}));

// GOOD — browser owns the credential
await ctx.elicit("Sign in via browser.", "https://app.example.com/login");
```

## Don't loop unbounded

```typescript
// BAD — loops forever on decline
while (true) {
  const r = await ctx.elicit("Confirm?", schema);
  if (r.action === "accept") break;
}

// GOOD — bounded retries with terminal exit
for (let i = 0; i < 3; i++) {
  const r = await ctx.elicit(`Confirm? (attempt ${i + 1}/3)`, schema);
  if (r.action === "accept") return text("Confirmed.");
  if (r.action === "decline") return text("User declined."); // terminal
}
return text("No confirmation after 3 attempts.");
```

## Always provide defaults where sensible

```typescript
// BAD — handler must defensively check undefined
z.object({ theme: z.enum(["light", "dark"]).optional() })

// GOOD — total data shape
z.object({ theme: z.enum(["light", "dark"]).default("light") })
```

## Always handle all three actions

```typescript
// BAD — assumes accept
const r = await ctx.elicit("Approve?", schema);
return text(`Approved by ${r.data.name}`); // crashes on decline/cancel

// GOOD — exhaustive switch
switch (r.action) {
  case "accept":  return text(`Approved by ${r.data.name}`);
  case "decline": return text("User declined.");
  case "cancel":  return text("Cancelled.");
}
```

## Pre-flight checklist

| Check | Why |
|---|---|
| Capability gated? | Avoids runtime crash on unsupported clients |
| All three actions handled? | Avoids hung tools |
| Sensitive steps use URL mode? | Better security posture |
| `.describe()` on every field? | Improves form clarity |
| `maxTokens` on any chained `ctx.sample()` call? | Cost control |
| Step count ≤ 3? | Better completion |
| Irreversible actions gated by explicit boolean? | Reduces accidents |
