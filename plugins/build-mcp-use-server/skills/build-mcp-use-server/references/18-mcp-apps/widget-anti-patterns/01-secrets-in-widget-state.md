# Anti-Pattern: Secrets in Widget `state` / `setState`

`state` is a host-persisted blob that the model can read in many hosts. Treat it as **conversation-visible**. Anything you put in `state` may end up in the LLM's context.

## What goes wrong

```tsx
// BAD — API key reachable from the model's context
const { state, setState } = useWidget<Props, { apiKey: string }>();

useEffect(() => {
  setState({ apiKey: "sk-live-9f..." }); // visible to the LLM
}, []);
```

The host serializes `state` into model context in supported hosts. Either way, the secret has left your trust boundary.

The same applies to:

- API tokens
- User passwords
- Session cookies you mint client-side
- Personally identifiable data the user did not explicitly intend to share with the model

## Right channels for secrets

| Where the secret lives | Who can read it |
|---|---|
| `process.env.*` on the server | Server only |
| `widget({ metadata })` / tool-result `_meta` | Widget yes, model **no** |
| `state` / `setState` | Widget yes, model **likely yes** |
| `props` / `structuredContent` | Widget yes, model **yes** |

Server-side, hold secrets in env vars and read them in the tool handler. Pass only what the widget needs to display — never the secret itself.

```typescript
// GOOD — secret stays on the server
server.tool(
  {
    name: "fetch-private-data",
    schema: z.object({ docId: z.string() }),
    widget: { name: "doc-viewer", invoking: "Loading..." },
  },
  async ({ docId }) => {
    const apiKey = process.env.PRIVATE_API_KEY!;
    const data = await fetch(`https://api.internal/${docId}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }).then((r) => r.json());

    return widget({
      props: { title: data.title, body: data.body }, // no key
      message: `Loaded ${data.title}`,
    });
  }
);
```

## When the widget genuinely needs a token

If a widget must hit a third-party API directly (rare — prefer `useCallTool` and proxy through the server), use `_meta` so the model never sees it:

```typescript
return widget({
  props: { docId },
  metadata: { signedFetchUrl: signedUrl }, // widget reads via useWidget().metadata, model does not
  message: `Doc ${docId} ready.`,
});
```

In the widget, read it via `useWidget().metadata`, not `state`.

## Fetch on demand, never persist

Even with `_meta`, prefer issuing a fresh tool call (`useCallTool`) when the user clicks something private. That way the secret never lives in client state at all — the server brokers each access.

```tsx
// GOOD — request the private blob on demand
const { callToolAsync: fetchPrivate } = useCallTool("fetch-private-data");

const handleReveal = async () => {
  const res = await fetchPrivate({ docId: props.docId });
  setLocalUiState(res.structuredContent); // local React useState, NOT setState
};
```

Local `useState` stays in the widget's React tree and is not serialized back to the host. `setState` is.

## Severity

Critical. Once a secret reaches the model's context, you cannot retract it — every subsequent turn may carry it forward. Audit any `setState` call on every PR.
