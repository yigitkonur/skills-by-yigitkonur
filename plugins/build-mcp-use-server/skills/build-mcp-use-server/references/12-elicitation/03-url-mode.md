# URL Mode

*Read this when elicitation needs to redirect to a browser flow.*

URL mode opens a browser to an external flow (OAuth, payment, complex UX). The user completes the flow, then signals back accept/decline/cancel. No form schema involved.

## API

```typescript
import { inputRequired } from "mcp-use";

const result = await ctx.elicit("authorize-github", 
  inputRequired.elicitUrl("https://app.example.com/connect/github")
);
```

> Documented but not shipped in 2.0.0-beta.66 — verify against your installed version.

## When to use URL mode

| Scenario | Reason |
|---|---|
| OAuth / SSO | Provider owns the protocol flow |
| Passwords or secrets | Avoid MCP transport exposure |
| Payment approvals | Browser trust and PCI scope |
| Complex multi-step UX | Browser UI is richer than a form |
| Device pairing | Codes, QR, magic links are web-native |

## Result handling

URL mode returns `status` (not `action`):

```typescript
if (response.status === "accept") {
  return { content: [{ type: "text", text: "GitHub connected." }] };
} else if (response.status === "cancel") {
  return { content: [{ type: "text", text: "Cancelled." }] };
}
```

No `data` payload — the URL flow captures data on its own backend. After accept, read the token/secret from your service using the user's context (e.g., `ctx.auth`).

```typescript
const auth = await ctx.elicit("oauth-github", inputRequired.elicitUrl(oauthUrl));
if (auth.status !== "accept") {
  return { isError: true, content: [...] };
}

// Read token from your backend using ctx.auth.user
const token = await getStoredGithubToken(ctx.auth.user.id);
const user = await fetchGithubUser(token);
```

## Security: never collect secrets through form mode

Form-mode data travels via MCP and your client. Use URL mode for passwords, OAuth tokens, API keys, payment cards:

```typescript
// BAD — password crosses MCP transport
await ctx.elicit("password-form", {
  schema: z.object({ password: z.string() })
});

// GOOD — browser owns the credential
await ctx.elicit("login-url", inputRequired.elicitUrl("https://app.example.com/login"));
```

## Capability gate still applies

URL mode is part of elicitation. Always check before returning:

```typescript
if (!ctx.client.capabilities().elicitation?.url) {
  return { isError: true, content: [...] };
}
```

## Related

- Form mode: `02-form-mode.md`
- Multi-round flows: `04-multi-round-and-request-state.md`
- Anti-patterns: `05-anti-patterns.md`
