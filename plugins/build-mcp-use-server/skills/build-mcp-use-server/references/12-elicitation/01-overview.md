# Elicitation Overview

*Read this when a tool needs structured user input before proceeding.*

Elicitation is a multi-round interaction: your tool returns an `InputRequiredResult` (built with `inputRequired()`) carrying a form or URL request, the client collects user input, then re-calls your tool with the same arguments plus `ctx.inputResponses` populated for that round. The handler re-runs from the top using `inputResponse()` and `acceptedContent()` to read the round's response.

Use when a tool cannot proceed without user data: confirmations, missing parameters, OAuth handoffs, multi-step workflows.

> **`ctx.elicit()` was permanently removed in v2.4.3 (#2409).** In official `mcp-use` v2, elicitation is executed via the `input_required` protocol primitives: returning `inputRequired({ inputRequests: { [key]: inputRequired.elicit(...) } })`, reading client input responses with `inputResponse(ctx.inputResponses, key)`, and validating responses with `acceptedContent()`. `RequestContext` does not have an `elicit()` method.

## How it works

1. Callback returns `inputRequired({ inputRequests: { key: inputRequired.elicit({...}) | inputRequired.elicitUrl({...}) } })`
2. Client prompts user with a form or redirects to a URL
3. User submits or dismisses → client re-calls your tool with the original arguments; `ctx.inputResponses` now carries that round's response
4. Your handler re-runs from the top; read `inputResponse(ctx.inputResponses, key)` to branch, and `acceptedContent(ctx.inputResponses, key, schema)` to get validated typed data
5. Complete the work or return another `inputRequired(...)` result for multi-round flows

## Two modes

| Mode | API | Renders as | Use for |
|---|---|---|---|
| **Form** | `inputRequired.elicit({ message, requestedSchema })` | In-client form | Structured fields, confirmations, preferences |
| **URL** | `inputRequired.elicitUrl({ message, url })` | Browser redirect with callback | OAuth, secrets, payments, external approval |

Both entries go inside `inputRequired({ inputRequests: { <key>: ... } })` — `inputRequired()` builds the actual `InputRequiredResult` envelope your tool returns; `inputRequired.elicit()` and `inputRequired.elicitUrl()` only build one entry's value.

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

On re-entry, call `inputResponse(ctx.inputResponses, key)` and branch on `.kind`, then `.action` when `kind === "elicit"`:

| `kind` | Meaning | `.action` values |
|---|---|---|
| `"missing"` | No response for this key yet — first call, or a different key answered this round | (N/A) |
| `"elicit"` | Client answered a form/URL request | `"accept"` (submitted, validate with `acceptedContent`) · `"decline"` (user explicitly declined) · `"cancel"` (user dismissed) |

```typescript
import { acceptedContent, inputRequired, inputResponse } from "mcp-use";

const response = inputResponse(ctx.inputResponses, "confirm-booking");
if (response.kind === "elicit" && response.action !== "accept") {
  // "decline" or "cancel" — do not proceed
  return { content: [{ type: "text", text: "Booking cancelled." }], isError: true };
}

const confirmed = acceptedContent(ctx.inputResponses, "confirm-booking", confirmSchema);
if (confirmed === undefined) {
  // First call, or the round did not carry valid accepted data yet: ask.
  return inputRequired({
    inputRequests: {
      "confirm-booking": inputRequired.elicit({
        message: "Confirm all booking details?",
        requestedSchema: confirmSchema,
      }),
    },
  });
}

// confirmed is typed to confirmSchema and validated.
return { content: [{ type: "text", text: "Booked." }], structuredContent: { success: true } };
```

## Stable key for state tracking

Always use the same string key for a given input request across re-runs — it is the object key inside `inputRequests` (e.g. `"confirm-booking"` above), not a function argument. `inputResponse()` and `acceptedContent()` both take that key as their second argument to look up the matching round response.

## Handling re-entry

Your handler re-runs from the top on each retry — there is no suspended stack frame. Keep re-entry idempotent:

```typescript
export const transfer = server.tool(
  { name: "transfer-funds", inputSchema: z.object({ toAccount: z.string(), amount: z.number() }) },
  async (params, ctx) => {
    const response = inputResponse(ctx.inputResponses, "confirm-xfer");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { isError: true, content: [{ type: "text", text: "Transfer cancelled." }] };
    }

    const confirmed = acceptedContent(ctx.inputResponses, "confirm-xfer", confirmSchema);
    if (confirmed === undefined) {
      return inputRequired({
        inputRequests: {
          "confirm-xfer": inputRequired.elicit({ message: "Confirm transfer?", requestedSchema: confirmSchema }),
        },
      });
    }

    // Side effects only after validation
    await transferFunds(params.toAccount, params.amount);
    return { content: [{ type: "text", text: "Transferred." }], structuredContent: { success: true } };
  }
);
```

Side effects and external calls must **not run** on the first call (when requesting elicitation). They run only after `acceptedContent()` returns validated data.

## Related

- Form mode details: `02-form-mode.md`
- URL mode details: `03-url-mode.md`
- Multi-round and state: `04-multi-round-and-request-state.md`
- Anti-patterns: `05-anti-patterns.md`
- Migrating v1 elicitation and request state: `../28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md`
