# Elicitation Overview

*Read this when a tool needs structured user input before proceeding.*

Elicitation is a multi-round interaction: your tool returns `InputRequiredResult` with a form or URL, the client collects user input, then re-calls your tool with `ctx.inputResponses`. The handler re-runs using the client's responses to complete the work.

Use when a tool cannot proceed without user data: confirmations, missing parameters, OAuth handoffs, multi-step workflows.

## How it works

1. Callback returns `InputRequiredResult` with form schema or URL
2. Client prompts user with form or redirects to URL
3. User submits → client re-calls your tool with input data
4. Your handler re-runs with `ctx.inputResponses` populated
5. Complete the work or return another `InputRequiredResult` for multi-round flows

## Two modes

| Mode | API | Renders as | Use for |
|---|---|---|---|
| **Form** | `inputRequired.elicit({ schema, ... })` | In-client form | Structured fields, confirmations, preferences |
| **URL** | `inputRequired.elicitUrl(url)` | Browser redirect with callback | OAuth, secrets, payments, external approval |

> Documented but not shipped in 2.0.0-beta.66 — verify against your installed version.

## Required capability gate

Elicitation is opt-in per client. Always check before returning an elicitation result:

```typescript
import { inputRequired } from "mcp-use";

export const confirmBooking = server.tool(
  { name: "book-flight", description: "Book a flight." },
  async (params, ctx) => {
    if (!ctx.client.capabilities().elicitation?.form) {
      return {
        isError: true,
        content: [{ type: "text", text: "Client does not support elicitation" }],
      };
    }
    // Safe to use elicitation; see 02-form-mode.md for full example
  }
);
```

## Status field semantics

On re-entry, check `response.status` to branch:

| Status | Meaning | `response.data` |
|---|---|---|
| `"required"` | Client is prompting; return the result as-is | (N/A) |
| `"accept"` | User submitted data; validation passed | Present, typed to schema |
| `"cancel"` | User dismissed or declined | `undefined` |

```typescript
if (response.status === "accept") {
  // Client input is validated; safe to use response.data
  return { content: [...], structuredContent: { success: true } };
} else if (response.status === "required") {
  // Client is still prompting; return the result to send back to client
  return response.result;
} else {
  // User cancelled
  return { content: [{ type: "text", text: "Cancelled." }] };
}
```

## Stable key for state tracking

Always provide a stable `key` (string) to track multi-round flows:

```typescript
const response = await ctx.elicit("confirm-booking", {
  schema: z.object({ confirmAllDetails: z.boolean() }),
});
```

The key is returned in `response.result` and must be the same across re-runs.

## Handling re-entry

Your handler re-runs on each retry. Keep re-entry idempotent:

```typescript
export const transfer = server.tool(
  { name: "transfer-funds", ... },
  async (params, ctx) => {
    // First call: params only
    if (!ctx.inputResponses) {
      return inputRequired.elicit("confirm-xfer", { schema: confirmSchema });
    }
    
    // Re-entry: ctx.inputResponses contains user data
    const { amount, confirmDetails } = ctx.inputResponses;
    if (!confirmDetails) {
      return { isError: true, content: [...] };
    }
    
    // Side effects only after validation
    await transferFunds(params.toAccount, amount);
    return { content: [...], structuredContent: { success: true } };
  }
);
```

Side effects and external calls must **not run** on the first call (when requesting elicitation). They run only after the client has collected and validated input.

## Related

- Form mode details: `02-form-mode.md`
- URL mode details: `03-url-mode.md`
- Multi-round and state: `04-multi-round-and-request-state.md`
- Anti-patterns: `05-anti-patterns.md`
- Migrating v1 `ctx.elicit()`: `../28-migration/02-v1-to-v2-overview.md`
