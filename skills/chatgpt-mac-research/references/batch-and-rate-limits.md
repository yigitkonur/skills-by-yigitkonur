# Batching, Rate Limits & State Persistence

This reference defines the operational discipline for large-scale research campaigns dispatched to the ChatGPT desktop app.

---

## 1. Why Batching and Cooldown are Mandatory

When submitting large entity sets (e.g. 50–200 people or companies):

1. **OpenAI Message Rate Limits:** Standard ChatGPT Plus / Team accounts allow bounded message rates per 3-hour window. Submitting 50+ queries simultaneously triggers HTTP 429 or in-app throttle modals.
2. **Browser Tool Concurrency:** Each query triggers `@Browser`, launching multi-step web searches in parallel. Too many active browser agents degrade search quality and increase timeouts.
3. **macOS UI Responsiveness:** Creating dozens of chat tabs without cooldown causes high memory pressure in the desktop wrapper.

---

## 2. The 10-Query Burst + 5-Minute Cooldown Formula

The golden rule for stable, unattended operation:

| Parameter | Recommended Value | Rationale |
|---|---|---|
| **Batch Size** | 10 queries | Fits comfortably within ChatGPT short-term rate limits. |
| **Intra-Batch Delay** | 0.2s–0.4s | "Tak-tak-tak" rapid dispatch; 10 chats created in ~12 seconds. |
| **Inter-Batch Cooldown** | 5 minutes (300s) | Gives ChatGPT ample time to browse and synthesize without hitting queue saturation. |

---

## 3. Resumable State Persistence Ledger

Never run batch research without persisting progress to disk. If the network drops, the laptop sleeps, or the terminal restarts, the runner must resume exactly where it left off.

### Schema (`chatgpt_batch_state.json`):

```json
{
  "submittedSlugs": [
    "uzm-psk-yasemin-demir",
    "uzm-psk-selin-aksoy",
    "dr-can-atalay"
  ],
  "total": 186,
  "completedBatches": 1,
  "lastBatchTimestamp": "2026-09-16T11:13:48Z"
}
```

### Ledger Invariants:

1. Write state atomically after **each individual prompt** is successfully pasted, not only at the end of the batch.
2. Filter the target candidate list against `new Set(state.submittedSlugs)` before each run.
3. Provide a `--reset` flag to clear the ledger only when explicitly requested.
4. Keep the state file outside git tracking (e.g. in `.scratch/` or global cache directory).
