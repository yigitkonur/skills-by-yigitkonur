# URL Mode

Pass a URL **string** as the second argument instead of a Zod schema. The client opens the URL in a browser, the user completes the flow there, and the client signals back accept/decline/cancel.

```typescript
const result = await ctx.elicit(
  "Open the secure browser flow to connect GitHub, then return here.",
  "https://app.example.com/connect/github"
);
```

Mode is detected automatically — strings → URL mode, Zod schema → form mode.

## When to use URL mode

| Use URL mode for | Why |
|---|---|
| OAuth / SSO | The provider already owns the browser flow |
| Passwords or sensitive secrets | Avoid collecting them through the MCP transport |
| Payment approvals | PCI / browser-trust scope is needed |
| Complex onboarding | Browser UI can explain more than a compact form |
| Device pairing | Codes / QR / magic links live on the web |

## Result handling

URL mode returns the same `{ action }` shape as form mode. There is no `data` payload — the URL flow is responsible for actually capturing the data on its own backend.

```typescript
switch (result.action) {
  case "accept":
    return text("GitHub connection completed.");
  case "decline":
    return text("Connection declined.");
  case "cancel":
    return text("Connection cancelled.");
}
```

After `accept`, your tool typically calls back into your own service (over `ctx.auth` or its session) to read the now-stored token — the token does **not** flow through the MCP message.

## Security: do not collect secrets through form mode

Form mode passes user input through the MCP transport and your client process. For passwords, OAuth tokens, payment data, or any credential, always use URL mode.

Bad — collects a password via form:

```typescript
await ctx.elicit("Sign in", z.object({
  password: z.string().describe("Your password"),
}));
```

Good — sends the user to a secure browser flow:

```typescript
await ctx.elicit(
  "Complete sign-in in the browser.",
  "https://app.example.com/login?session=xyz"
);
```

## Result vocabulary

Docs sometimes describe outcomes as "accepted / declined / cancelled" while the programmatic field uses `accept` / `decline` / `cancel`. They mean the same three states.

| Human language | Programmatic value | Meaning |
|---|---|---|
| accepted | `accept` | User completed the step |
| declined | `decline` | User refused to continue |
| cancelled | `cancel` | User aborted mid-flow |

## Capability gate still applies

URL mode is part of the elicitation capability — guard with `ctx.client.can("elicitation")` before calling. See `../16-client-introspection/03-can-capabilities.md`.

## Combining with sampling

A common shape: URL-mode auth → resource fetch → sampling pass:

```typescript
const auth = await ctx.elicit("Authorize.", "https://app.example.com/oauth");
if (auth.action !== "accept") return text("Not authorized.");

const data = await fetchUserData(); // reads the now-stored token
const summary = await ctx.sample(`Summarize: ${JSON.stringify(data)}`, { maxTokens: 200 });
return text(summary.content.text);
```
