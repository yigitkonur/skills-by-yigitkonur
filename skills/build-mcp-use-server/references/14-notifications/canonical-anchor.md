# Canonical Notification Example

*The one reference example for notifications: request-scoped and cross-request patterns.*

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "example", version: "1.0.0" });

// Shared state
let documentCount = 0;

// REQUEST-SCOPED: Progress + custom notification during tool execution
export const importDocuments = server.tool(
  {
    name: "import_documents",
    description: "Import documents from a URL",
    inputSchema: z.object({
      sourceUrl: z.string().url(),
    }),
  },
  async ({ sourceUrl }, ctx) => {
    // Notify start
    await ctx.sendNotification("com.example/import-status", {
      event: "started",
      source: sourceUrl,
    });

    // Fetch and process
    const response = await fetch(sourceUrl);
    const documents = await response.json();
    let processed = 0;

    for (const doc of documents) {
      await processDocument(doc);
      processed++;

      // Send progress (may not be delivered if client didn't ask)
      const reported = await ctx.reportProgress(
        processed,
        documents.length,
        `Processed ${processed}/${documents.length}`
      );

      // Notify with each batch
      if (processed % 10 === 0) {
        await ctx.sendNotification("com.example/import-status", {
          event: "batch_complete",
          batch_number: Math.floor(processed / 10),
          items_processed: processed,
        });
      }
    }

    documentCount += processed;

    // Notify completion
    await ctx.sendNotification("com.example/import-status", {
      event: "complete",
      total_imported: processed,
    });

    // All notifications must be sent before returning
    return {
      content: [
        {
          type: "text",
          text: `Imported ${processed} documents from ${sourceUrl}`,
        },
      ],
    };
  }
);

// CROSS-REQUEST: Resource changed notification
server.resource(
  {
    name: "import-stats",
    uri: "app://import-stats",
    description: "Document import statistics",
  },
  async (uri, ctx) => ({
    contents: [
      {
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify({
          total_documents: documentCount,
          timestamp: new Date().toISOString(),
        }),
      },
    ],
  })
);

// Custom API endpoint that triggers a cross-request notification
server.post("/api/reset-import", async (c) => {
  documentCount = 0;

  // Notify all listening clients that import stats changed
  await server.notifyResourceUpdated("app://import-stats");

  return c.json({ ok: true, documentCount: 0 });
});

// Tool list changed (e.g., register new tool dynamically)
server.post("/api/register-importer", async (c) => {
  const { format } = await c.req.json();

  server.tool(
    {
      name: `import_${format}`,
      description: `Import ${format} documents`,
      inputSchema: z.object({ url: z.string() }),
    },
    async ({ url }, ctx) => {
      // ... implementation
      return { content: [{ type: "text", text: "OK" }] };
    }
  );

  // Notify clients that tool list changed
  await server.notifyToolsChanged();

  return c.json({ ok: true });
});

await server.listen(3000);
```

## Key patterns

1. **Request-scoped within callback:** `ctx.sendNotification()`, `ctx.reportProgress()`, `ctx.sendLog()` — all must await before callback returns.
2. **Cross-request outside callback:** `server.notifyToolsChanged()`, `server.notifyResourceUpdated()` — publish when state changes.
3. **Client subscription required:** Cross-request notifications only reach clients actively listening (`subscriptions/listen`).
4. **Stateless recovery:** After receiving a `resourceUpdated` notification, clients re-read the resource. No delivery queue or backlog.
