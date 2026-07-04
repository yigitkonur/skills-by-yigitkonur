# Progress During Sampling

When a sample runs inside a tool call that has a progress token, mcp-use automatically emits `notifications/progress` to the connected client every `progressIntervalMs` (default 5000ms). The client UI uses these to keep its progress UI alive and to reset its timeout counter.

You generally do **not** need to call `ctx.reportProgress()` yourself during a sample — the framework does it for you.

## Automatic progress

```typescript
server.tool(
  { name: "long-llm-task", description: "LLM call with auto-progress." },
  async (args, ctx) => {
    // If the client sent a progressToken, events fire automatically every 5s.
    const result = await ctx.sample({
      messages: [{ role: "user", content: { type: "text", text: args.prompt } }],
      maxTokens: 1000,
    });
    return text(result.content.text);
  }
);
```

## Tuning the interval

```typescript
const result = await ctx.sample(prompt, {
  timeout: 120000,
  progressIntervalMs: 2000, // emit every 2s instead of 5s when progress is active
  onProgress: ({ message }) => console.log(message),
});
```

## How progress prevents client timeouts

When the client opts in with `resetTimeoutOnProgress: true` and sends a progress token:

- Each progress notification resets the client's request timeout counter.
- Long calls can run beyond the client's normal request timeout while progress keeps flowing.
- Both auto-emitted sampling progress and manual `ctx.reportProgress()` notifications use the same timer-reset path.

This means a long sample can complete beyond the client's normal request timeout, because periodic progress events keep the deadline rolling forward.

## Manual progress alongside sampling

If your tool does both work and a sample, mix manual progress for the work phase with auto-progress for the sample:

```typescript
server.tool(
  { name: "research-and-summarize", schema: z.object({ topic: z.string() }) },
  async ({ topic }, ctx) => {
    await ctx.reportProgress?.(0, 100, "Fetching documents");
    const docs = await fetchDocs(topic);

    await ctx.reportProgress?.(40, 100, "Indexing");
    const index = await buildIndex(docs);

    await ctx.reportProgress?.(60, 100, "Sampling LLM"); // auto-progress takes over here
    const summary = await ctx.sample(
      `Summarize:\n${index.text}`,
      { maxTokens: 400, progressIntervalMs: 3000 }
    );

    await ctx.reportProgress?.(100, 100, "Done");
    return text(summary.content.text);
  }
);
```

For details on `ctx.reportProgress()` itself — including progress tokens, throttling, and the parameter table — see `../14-notifications/03-progress-tokens.md`.

## Stateless caveat

Progress notifications require a stateful transport (SSE or StreamableHTTP) and a progress token. In stateless mode (Deno default, edge runtimes), notifications are not sent. Sampling itself still works — the client just won't see progress.

See `../14-notifications/06-when-notifications-fail.md` for the full stateless story.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Calling `ctx.reportProgress()` inside a fast `ctx.sample()` (sub-second) | Skip it — auto-progress is sufficient and the call may finish first |
| Setting `progressIntervalMs: 100` to "look responsive" | Floods the client; aim for 1-5s |
| Forgetting `progressIntervalMs` on a 2-minute sample | Default 5s is fine; only tune if you need faster feedback |
| Relying on progress for streaming text | Progress events carry no token deltas — see `04-callbacks.md` |
