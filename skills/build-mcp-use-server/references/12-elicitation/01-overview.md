# Elicitation Overview

`ctx.elicit()` pauses tool execution to ask the connected user for structured input. The client renders a form (or routes the user to a URL); mcp-use validates the response server-side against your Zod schema before returning to the handler.

Use when a tool cannot proceed without user-supplied data: confirmations, missing parameters, OAuth handoffs, irreversible-action approvals.

## Two modes

| Mode | Trigger | Renders as | Use for |
|---|---|---|---|
| **Form** | Pass a Zod schema as the second arg | In-client form | Structured fields, confirmations, preferences |
| **URL** | Pass a URL string as the second arg | Browser redirect with callback | OAuth, secrets, payments, external approval |

Mode is detected automatically from the second argument's type. There is no `mode` flag.

→ Form-mode details: `02-form-mode.md`
→ URL-mode details: `03-url-mode.md`

## Required capability gate

Elicitation is opt-in per client. Always guard:

```typescript
import { error } from "mcp-use/server";

if (!ctx.client.can("elicitation")) {
  return error("This client does not support elicitation.");
}
```

`ctx.client.*` API is documented in `../16-client-introspection/03-can-capabilities.md`.

## Three response actions

Every `ctx.elicit()` result has an `action` field. Handle all three or the tool will hang on non-accept paths.

| Action | Meaning | `result.data` |
|---|---|---|
| `accept` | User submitted the form (or completed URL flow) | Present, validated |
| `decline` | User explicitly refused | `undefined` |
| `cancel` | User dismissed the prompt | `undefined` |

```typescript
switch (result.action) {
  case "accept":  return text(`Got: ${result.data.value}`);
  case "decline": return text("User declined.");
  case "cancel":  return text("Cancelled.");
}
```

## Minimal example

```typescript
import { MCPServer, text, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "feedback-server", version: "1.0.0" });

server.tool(
  { name: "collect-feedback", description: "Collect user feedback." },
  async (_args, ctx) => {
    if (!ctx.client.can("elicitation")) return error("Elicitation not supported.");

    const result = await ctx.elicit(
      "Please share your feedback",
      z.object({
        rating: z.number().min(1).max(5).describe("Rating from 1 to 5"),
        comment: z.string().max(500).optional().describe("Optional comment"),
      })
    );

    if (result.action !== "accept") return text("Feedback skipped.");
    return text(`Thanks! You rated us ${result.data.rating}/5.`);
  }
);
```

## Related

- Sampling (LLM completions from the client): `../13-sampling/01-overview.md`
- Combining elicitation + sampling: `04-multi-step-workflows.md`
- Anti-patterns: `05-anti-patterns.md`

**Canonical doc:** https://manufact.com/docs/typescript/server/elicitation
