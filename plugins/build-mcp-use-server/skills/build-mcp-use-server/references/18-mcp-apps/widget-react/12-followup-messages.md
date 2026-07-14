# `sendFollowUpMessage(content)` — Push a Message into the Conversation

Lets the widget inject a follow-up message into the chat as if the user typed it. Useful for "tell me more about this row" interactions where clicking inside the widget should kick the conversation forward.

```typescript
const { sendFollowUpMessage } = useWidget();

await sendFollowUpMessage("Tell me more about the active users metric.");
```

## Signature

```typescript
sendFollowUpMessage(
  content: string | MessageContentBlock[]
): Promise<void>;
```

- **String shorthand** — sends a plain text message.
- **`MessageContentBlock[]`** — full SEP-1865 content blocks. Use for multi-modal follow-ups (text + image, etc.).

```tsx
// Plain text
await sendFollowUpMessage("What's the breakdown by region?");

// Multi-block (SEP-1865 hosts only)
await sendFollowUpMessage([
  { type: "text", text: "Compare with this image:" },
  { type: "image", data: base64Image, mimeType: "image/png" },
]);
```

## Pattern — explore action on table rows

```tsx
import { useWidget } from "mcp-use/react";

const DataExplorer: React.FC = () => {
  const { props, sendFollowUpMessage } =
    useWidget<{ data: Record<string, number> }>();

  const askAbout = (metric: string) => {
    sendFollowUpMessage(`Tell me more about the ${metric} metric and what factors influence it.`);
  };

  return (
    <table>
      <tbody>
        {Object.entries(props.data ?? {}).map(([key, val]) => (
          <tr key={key}>
            <td>{key}</td>
            <td>{val}</td>
            <td><button onClick={() => askAbout(key)}>Ask</button></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

## Anti-patterns

- **Don't loop.** Never call `sendFollowUpMessage` from a `useEffect` that runs on every render — you will spam the conversation.
- **Don't auto-fire on mount.** The user did not request a follow-up; wait for an explicit click.
- **Don't bypass `callTool`.** If you want to do work, use `callTool` directly — `sendFollowUpMessage` re-routes through the LLM, which is slow and non-deterministic.
- **Don't dump raw widget props.** Compose a natural-language sentence instead of `sendFollowUpMessage(JSON.stringify(props))`.

## Awaiting

The promise resolves once the host has accepted the message. You don't usually need to await it — it's fire-and-forget — but `await` lets you sequence it before another action (e.g. close a modal once the message has been queued).

## Host support

| Host | Behavior |
|---|---|
| ChatGPT Apps SDK | `window.openai.sendFollowUpMessage({ prompt })` — prompt text only. Multi-block content is flattened to text. |
| MCP Apps (SEP-1865) | Full `MessageContentBlock[]` support. |
