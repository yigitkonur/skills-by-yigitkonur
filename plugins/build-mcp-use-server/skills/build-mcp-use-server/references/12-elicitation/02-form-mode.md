# Form Mode

*Read this when building a flat-schema form elicitation.*

Form mode renders an in-client structured-data form. Use for confirmations, multi-field input, preferences, or any bounded data collection.

## Schema constraints

Forms support **flat objects only**:
- Top-level primitive fields (`string`, `number`, `boolean`)
- Single-value enums (`z.enum([...])`)
- Arrays of enum values (`z.array(z.enum([...]))`) — SEP-1330 multi-select
- Optional fields via `.optional()`, defaults via `.default()` — SEP-1034 default values on every primitive type are supported
- String arrays (`z.array(z.string())`)

Nested objects and file uploads are not supported. Use URL mode for complex flows.

## API

```typescript
import { acceptedContent, inputRequired, inputResponse } from "mcp-use";

const schema = z.object({
  productId: z.string(),
  quantity: z.number().min(1),
  giftWrap: z.boolean().optional(),
});

const response = inputResponse(ctx.inputResponses, key);
if (response.kind === "elicit" && response.action !== "accept") {
  // "decline" or "cancel"
}
const form = acceptedContent(ctx.inputResponses, key, schema);
```

`inputRequired.elicit({ message, requestedSchema })` builds one `inputRequests` entry; wrap it in `inputRequired({ inputRequests: {...} })` to build the actual `InputRequiredResult` your tool returns:

```typescript
import { acceptedContent, inputRequired, inputResponse, MCPServer } from "mcp-use";
import { z } from "zod";

const confirmSchema = z.object({
  confirmGiftWrap: z.boolean().describe("Wrap as gift?"),
  shippingSpeed: z.enum(["standard", "express", "overnight"]).describe("Delivery speed"),
});

export const order = server.tool(
  {
    name: "place-order",
    description: "Place an order with optional confirmation.",
    inputSchema: z.object({ items: z.array(z.object({ sku: z.string() })) }),
  },
  async (params, ctx) => {
    const response = inputResponse(ctx.inputResponses, "order-confirm");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { content: [{ type: "text", text: `Order not placed: ${response.action}` }], isError: true };
    }

    const confirmed = acceptedContent(ctx.inputResponses, "order-confirm", confirmSchema);
    if (confirmed === undefined) {
      // First call, or the round did not carry valid accepted data yet: ask.
      return inputRequired({
        inputRequests: {
          "order-confirm": inputRequired.elicit({
            message: "Confirm order options",
            requestedSchema: confirmSchema,
          }),
        },
      });
    }

    // Now perform the actual order — confirmed is typed and schema-validated.
    const orderId = await placeOrder({
      items: params.items,
      giftWrap: confirmed.confirmGiftWrap,
      shipping: confirmed.shippingSpeed,
    });

    return {
      content: [{ type: "text", text: `Order #${orderId} placed.` }],
      structuredContent: { orderId, status: "confirmed" },
    };
  }
);
```

## Field types

| Zod type | Renders as | Notes |
|---|---|---|
| `z.string()` | Text input | Add `.email()`, `.url()`, `.min()`, `.max()` for constraints |
| `z.number()` | Number input | Add `.int()`, `.min()`, `.max()` |
| `z.boolean()` | Checkbox / toggle | Add `.default()` to pre-fill |
| `z.enum([...])` | Dropdown / radio / segmented control | Values are the selectable options |
| `z.array(z.enum([...]))` | Multi-select | SEP-1330 multi-value enum |
| `z.array(z.string())` | Tag list / repeated text input | Flat string arrays only, no nested objects |

Always add `.describe()` — it becomes field label or UI hint.

## Validation

`acceptedContent()` validates the round's raw response against the schema you pass it and returns `undefined` on any mismatch — treat `undefined` the same as "not yet answered" and return another `inputRequired(...)` result rather than trusting unvalidated data:

```typescript
z.object({
  startDate: z.string(),
  endDate: z.string(),
}).refine(
  ({ startDate, endDate }) => new Date(startDate) < new Date(endDate),
  { message: "End date must be after start date" }
)
```

## Schema design patterns

| Practice | Rationale |
|---|---|
| `.describe()` every field | Becomes UI label or LLM hint |
| Prefer `z.enum()` for known options | Prevents ambiguous input |
| Keep forms short (2-5 fields) | Higher user completion rate |
| Mark irreversible actions explicit | `z.boolean().describe("I confirm this cannot be undone")` |
| Use `.default()` for pre-filled fields | Reduces required user input |

## Related

- URL mode: `03-url-mode.md`
- Multi-round flows: `04-multi-round-and-request-state.md`
- Anti-patterns: `05-anti-patterns.md`
