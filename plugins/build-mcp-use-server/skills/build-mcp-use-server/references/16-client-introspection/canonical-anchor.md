# Canonical Client Introspection Example

*The one reference example for capability detection and per-client adaptation.*

```typescript
import { MCPServer, inputRequired } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "smart-tool-server",
  version: "1.0.0",
});

// Tool that adapts to client capabilities
export const performAnalysis = server.tool(
  {
    name: "analyze_data",
    description: "Analyze data and return results in best format for client",
    inputSchema: z.object({
      dataUrl: z.string().url(),
    }),
    outputSchema: z.object({
      summary: z.string(),
      chart: z.unknown().optional(),
      metrics: z.array(z.number()),
    }),
    view: {
      name: "analysis-results",
      description: "Rich visualization of analysis results",
    },
  },
  async ({ dataUrl }, ctx) => {
    // Fetch and analyze data
    const response = await fetch(dataUrl);
    const data = await response.json();
    const metrics = computeMetrics(data);

    // Adapt response based on client capabilities
    const result = {
      content: [
        {
          type: "text",
          text: `Analysis of ${dataUrl}: metrics = [${metrics.join(", ")}]`,
        },
      ],
      structuredContent: {
        summary: `Processed ${data.length} items`,
        metrics,
      } as any,
    };

    // If client supports views, include chart
    if (ctx.client.supportsViews()) {
      result.structuredContent.chart = {
        type: "bar",
        data: metrics,
        title: "Analysis Results",
      };
    }

    return result;
  }
);

// Tool that uses elicitation capability detection
export const deleteDatabase = server.tool(
  {
    name: "delete_database",
    description: "Permanently delete a database",
    inputSchema: z.object({
      databaseId: z.string(),
      confirmed: z.boolean().optional(),
    }),
  },
  async ({ databaseId, confirmed }, ctx) => {
    if (!confirmed) {
      // Check if client can handle form-based elicitation
      const caps = ctx.client.capabilities();
      if (caps.elicitation?.form) {
        // Client supports form mode — ask for confirmation
        return inputRequired.elicit({
          schema: z.object({
            confirmed: z
              .boolean()
              .describe("I understand this cannot be undone"),
          }),
          correlationKey: `delete_db_${databaseId}`,
        });
      } else {
        // Client doesn't support elicitation
        return {
          isError: true,
          content: [
            {
              type: "text",
              text: `Cannot delete ${databaseId}: client does not support confirmation. Retry with confirmed: true.`,
            },
          ],
        };
      }
    }

    // Confirmed — perform deletion
    await db.delete(databaseId);
    return {
      content: [{ type: "text", text: `Deleted database ${databaseId}` }],
    };
  }
);

// Tool that logs client info
export const inspectClient = server.tool(
  {
    name: "inspect_client",
    description: "Inspect current client capabilities",
    inputSchema: z.object({}),
  },
  async (params, ctx) => {
    const info = ctx.client.info();
    const caps = ctx.client.capabilities();
    const uiExt = ctx.client.extension("io.modelcontextprotocol/ui");

    await ctx.sendLog("info", `Client: ${info.name} v${info.version}`, "client");
    await ctx.sendLog(
      "debug",
      { elicitation: caps.elicitation, extensions: !!uiExt },
      "client"
    );

    const clientProfile = {
      name: info.name || "unknown",
      version: info.version || "unknown",
      supportsViews: ctx.client.supportsViews(),
      supportsElicitation: !!caps.elicitation?.form,
      capabilities: Object.keys(caps),
    };

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(clientProfile, null, 2),
        },
      ],
    };
  }
);

await server.listen(3000);
```

## Key patterns

1. **Capability check per request:** `ctx.client.supportsViews()`, `ctx.client.capabilities()`, `ctx.client.can()`.
2. **Always return text:** Structured content is optional rendering; text block is fallback.
3. **Elicitation guard:** Check `ctx.client.capabilities().elicitation` before calling `inputRequired.elicit()`.
4. **Per-request state:** Capabilities are not cached across requests; check them inside every callback.
