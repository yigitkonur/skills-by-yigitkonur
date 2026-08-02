# Form Mode

*Read this when building a flat-schema form elicitation.*

Form mode renders an in-client structured-data form. Use for confirmations, multi-field input, preferences, or any bounded data collection.

## Schema constraints

Forms support **flat objects only**:
- Top-level primitive fields (`string`, `number`, `boolean`, enum)
- String arrays (`z.array(z.string())`)
- Optional fields via `.optional()`
- Enums via `z.enum([...])`

Nested objects and file uploads are not supported. Use URL mode for complex flows.

## API

```typescript
import { inputRequired } from "mcp-use";

const result = await ctx.elicit(key, {
  schema: z.object({
    productId: z.string(),
    quantity: z.number().min(1),
    giftWrap: z.boolean().optional(),
  }),
});
```

The helper `inputRequired.elicit()` returns an `InputRequiredResult` envelope:

```typescript
export const order = server.tool(
  {
    name: "place-order",
    description: "Place an order with optional confirmation.",
    inputSchema: z.object({ items: z.array(z.object({ sku: z.string() })) }),
  },
  async (params, ctx) => {
    // Re-entry guard: only ask for confirmation on first call
    if (!ctx.inputResponses) {
      return inputRequired.elicit("order-confirm", {
        schema: z.object({
          confirmGiftWrap: z.boolean().describe("Wrap as gift?"),
          shippingSpeed: z.enum(["standard", "express", "overnight"]).describe("Delivery speed"),
        }),
      }).result;
    }

    // Re-entry: validation is automatic; data is present
    const { confirmGiftWrap, shippingSpeed } = ctx.inputResponses;
    
    // Now perform the actual order
    const orderId = await placeOrder({
      items: params.items,
      giftWrap: confirmGiftWrap,
      shipping: shippingSpeed,
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

Always add `.describe()` — it becomes field label or UI hint.

## Validation

SDK validates the schema **before your callback re-runs**. Invalid data never reaches `ctx.inputResponses` — the client re-prompts the user:

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
