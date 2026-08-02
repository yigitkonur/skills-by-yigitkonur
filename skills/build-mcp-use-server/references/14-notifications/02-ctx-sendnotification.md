# ctx.sendNotification()

*Read this when sending a custom notification during tool execution.*

Send a one-way application-namespaced notification to the client on the originating request's response stream.

## Signature

```typescript
ctx.sendNotification(method: string, params?: Record<string, unknown>): Promise<void>
```

## Parameters

- **method** (string): Application namespace + event type, e.g., `"com.example/import-status"`, `"com.myapp/sync-complete"`. Follow vendor-namespacing conventions to avoid collisions.
- **params** (optional): Plain object carrying event data. Sent as-is; no validation.

## Usage

```typescript
export const importData = server.tool(
  { name: "import_data", inputSchema: z.object({ url: z.string() }) },
  async ({ url }, ctx) => {
    await ctx.sendNotification("com.example/import-status", {
      event: "starting",
      url,
    });

    const data = await fetch(url).then((r) => r.json());

    await ctx.sendNotification("com.example/import-status", {
      event: "complete",
      count: data.length,
    });

    return {
      content: [{ type: "text", text: `Imported ${data.length} items` }],
    };
  }
);
```

## Key points

- **Must await before return.** Notifications are sent on the request's response stream. Once your callback returns, the HTTP response ends and no more notifications can be sent.
- **No acknowledgment.** Notifications are fire-and-forget; the client may ignore them or fail to receive them if the connection drops.
- **Namespace your events.** Use reverse-domain notation (`com.company/event`) to avoid collisions with other servers.
- **No structured reply.** Use `ctx.sendNotification()` for one-way messages. For interactive back-and-forth, use `input_required` elicitation (see `references/12-elicitation/01-overview.md`).

See also: `ctx.reportProgress()` for standard progress updates, `ctx.sendLog()` for logging.
