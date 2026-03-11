# F-04 — Streaming Process Hang (P1, M4)

## Observation

The streaming example's idle handler:

```typescript
session.on("session.idle", () => console.log("\n--- done ---"));
```

Never calls `session.disconnect()` or `client.stop()`. The process hangs
indefinitely because the RPC connection keeps the event loop alive.

## Root cause

M4 — Missing execution detail. The example shows the event but not cleanup.

## Fix applied

Changed idle handler to include disconnect/stop:
```typescript
session.on("session.idle", async () => {
  console.log("\n--- done ---");
  await session.disconnect();
  await client.stop();
});
```
