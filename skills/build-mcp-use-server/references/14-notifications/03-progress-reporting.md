# Progress Reporting with ctx.reportProgress()

*Read this when reporting work progress during long-running tools.*

Send standard progress updates to clients that request them. Only sent when the client explicitly supplies a progress token in the request.

## Signature

```typescript
ctx.reportProgress(
  progress: number,
  total?: number,
  message?: string
): Promise<boolean>
```

## Parameters

- **progress** (number): Current count or amount (e.g., 50).
- **total** (optional number): Total expected (e.g., 100). When omitted, clients treat progress as a single milestone.
- **message** (optional string): Brief status text, e.g., "Processing file 3 of 5".

## Return value

- `true`: Progress token was present; update sent.
- `false`: Client did not supply a progress token; no update sent. Continue working normally.

## Usage

```typescript
export const processLargeFile = server.tool(
  { name: "process_file", inputSchema: z.object({ path: z.string() }) },
  async ({ path }, ctx) => {
    const lines = await readLines(path);
    let processed = 0;

    for (const line of lines) {
      await processLine(line);
      processed++;

      const sent = await ctx.reportProgress(
        processed,
        lines.length,
        `Processed line ${processed}/${lines.length}`
      );

      // If sent is false, client didn't ask for progress
      // but work continues normally
    }

    return {
      content: [{ type: "text", text: `Processed ${processed} lines` }],
    };
  }
);
```

## Key points

- **Check return value.** `reportProgress()` returning `false` is normal — the client simply didn't request progress. Do not treat it as an error.
- **Must await before return.** Like all `ctx` notifications, progress updates must be sent before your callback returns.
- **Clients initiate.** Clients opt in to progress by supplying a progress token in their request. Without it, `reportProgress()` silently returns `false`.
- **No retry logic.** If a progress update fails to send, the callback continues. Clients handle re-sync.

See also: `ctx.sendNotification()` for custom events, `ctx.sendLog()` for structured logging.
