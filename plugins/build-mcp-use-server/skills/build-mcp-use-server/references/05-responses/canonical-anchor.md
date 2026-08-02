# Canonical response example

*Reference: tool with structured data, media, and error paths.*

## Full tool with outputSchema, image, and error handling

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "example-server",
  version: "1.0.0",
});

export const generateChart = server.tool(
  {
    name: "generate-chart",
    description: "Generate a bar chart from data",
    inputSchema: z.object({
      title: z.string().describe("Chart title"),
      values: z.array(z.number()).describe("Data points"),
      labels: z.array(z.string()).describe("X-axis labels"),
    }),
    outputSchema: z.object({
      title: z.string(),
      dataPoints: z.number(),
      format: z.enum(["png", "svg"]),
    }),
  },
  async ({ title, values, labels }, ctx) => {
    // Validation
    if (values.length !== labels.length) {
      return {
        isError: true,
        content: [{
          type: "text",
          text: "Array mismatch: values.length !== labels.length",
        }],
      };
    }

    if (values.length === 0) {
      return {
        isError: true,
        content: [{
          type: "text",
          text: "Empty dataset; cannot generate chart",
        }],
      };
    }

    try {
      // Generate image (simulated)
      const base64Png = "iVBORw0KGgoAAAANSU..."; // actual PNG bytes, base64
      
      return {
        content: [
          {
            type: "text",
            text: `Generated chart: "${title}" with ${values.length} data points`,
          },
          {
            type: "image",
            data: base64Png,
            mimeType: "image/png",
          },
        ],
        structuredContent: {
          title,
          dataPoints: values.length,
          format: "png",
        },
        _meta: {
          min: Math.min(...values),
          max: Math.max(...values),
          avg: values.reduce((a, b) => a + b, 0) / values.length,
        },
      };
    } catch (err) {
      return {
        isError: true,
        content: [{
          type: "text",
          text: `Failed to generate chart: ${err instanceof Error ? err.message : "unknown error"}`,
        }],
      };
    }
  }
);

await server.listen(3000);
```

## Response shapes broken down

**Success path (values match):**
- `content[0]`: Text description (markdown MIME for formatting)
- `content[1]`: Image block (PNG base64)
- `structuredContent`: Matches `outputSchema`; model sees this
- `_meta`: Stats (min/max/avg); View can access but model cannot

**Error paths:**
- Array mismatch → isError=true, descriptive content
- Empty data → isError=true, clear message
- Runtime exception → caught, error returned (not thrown)

## Key patterns

1. **Always include text block** with context (even if paired with media)
2. **structuredContent must match outputSchema** or error + don't set it
3. **Use _meta for debugging/UI-only data** not in schema
4. **Return errors, don't throw** — exceptions become raw errors to client
5. **Order content blocks by usefulness** — lead with text label, then media, then caption

This example spans all response surfaces used in practice.
