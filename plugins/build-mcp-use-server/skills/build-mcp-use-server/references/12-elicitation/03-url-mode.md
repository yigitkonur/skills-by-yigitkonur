# URL Mode

*Read this when elicitation needs to redirect to a browser flow.*

URL mode opens a browser to an external flow (OAuth, payment, complex UX). The user completes the flow, then the client signals back `accept`/`decline`/`cancel`. No form schema involved.

## API

`inputRequired.elicitUrl({ message, url })` takes an object, not a bare string — build one `inputRequests` entry, then wrap it in `inputRequired({ inputRequests: {...} })`:

```typescript
import { inputRequired, inputResponse } from "mcp-use";

server.tool({ name: "link-account" }, async (_params, ctx) => {
  const response = inputResponse(ctx.inputResponses, "authorize");
  if (response.kind === "elicit") {
    return {
      content: [{
        type: "text",
        text: response.action === "accept" ? "Authorization page opened" : "Account not linked",
      }],
      ...(response.action !== "accept" ? { isError: true as const } : {}),
    };
  }

  return inputRequired({
    inputRequests: {
      authorize: inputRequired.elicitUrl({
        message: "Sign in to link your account",
        url: "https://example.com/authorize",
      }),
    },
  });
});
```

There is no `ctx.elicit()` in shipped 2.0.0-beta.66 — `elicitation.mdx` and `SPEC.md` describe it, but the shipped `dist/context.d.ts` omits it and the framework's own compile-time type test asserts it does not exist. See `01-overview.md` for the full drift note.

## When to use URL mode

| Scenario | Reason |
|---|---|
| OAuth / SSO | Provider owns the protocol flow |
| Passwords or secrets | Avoid MCP transport exposure |
| Payment approvals | Browser trust and PCI scope |
| Complex multi-step UX | Browser UI is richer than a form |
| Device pairing | Codes, QR, magic links are web-native |

## Result handling

URL mode uses the same `inputResponse().kind === "elicit"` envelope as form mode — check `.action`, which is one of `"accept"`, `"decline"`, `"cancel"`:

```typescript
const response = inputResponse(ctx.inputResponses, "oauth-github");
if (response.kind === "elicit" && response.action === "accept") {
  return { content: [{ type: "text", text: "GitHub connected." }] };
} else if (response.kind === "elicit") {
  return { content: [{ type: "text", text: "Cancelled." }], isError: true };
}
```

No form data payload — `acceptedContent()` has nothing to validate for a URL request (there is no `requestedSchema`). The URL flow captures data on its own backend. After `action === "accept"`, read the token/secret from your service using the user's context (e.g., `ctx.auth`):

```typescript
const response = inputResponse(ctx.inputResponses, "oauth-github");

if (response.kind === "missing") {
  return inputRequired({
    inputRequests: { "oauth-github": inputRequired.elicitUrl({ message: "Connect GitHub", url: oauthUrl }) },
  });
}
if (response.kind === "sampling") {
  return { content: [{ type: "text", text: "Unexpected sampling response." }], isError: true };
}
if (response.action === "decline") {
  return { content: [{ type: "text", text: "GitHub connection declined." }], isError: true };
}
if (response.action === "cancel") {
  return { content: [{ type: "text", text: "GitHub connection cancelled." }], isError: true };
}

// action === "accept": read the result from your backend using authenticated identity.
const token = await getStoredGithubToken(ctx.auth.user.id);
const user = await fetchGithubUser(token);
```

## Security: never collect secrets through form mode

Form-mode data travels via MCP and your client. Use URL mode for passwords, OAuth tokens, API keys, payment cards:

```typescript
// BAD — password crosses MCP transport
inputRequired.elicit({
  message: "Enter password",
  requestedSchema: z.object({ password: z.string() }),
});

// GOOD — browser owns the credential
inputRequired.elicitUrl({ message: "Log in", url: "https://app.example.com/login" });
```

## Capability gate still applies

URL mode is part of elicitation. Always check before returning — `ClientCapabilities["elicitation"]` exposes per-mode flags:

```typescript
if (!ctx.client.capabilities().elicitation?.url) {
  return { isError: true, content: [{ type: "text", text: "Client does not support URL-mode elicitation" }] };
}
```

## Related

- Form mode: `02-form-mode.md`
- Multi-round flows: `04-multi-round-and-request-state.md`
- Anti-patterns: `05-anti-patterns.md`
