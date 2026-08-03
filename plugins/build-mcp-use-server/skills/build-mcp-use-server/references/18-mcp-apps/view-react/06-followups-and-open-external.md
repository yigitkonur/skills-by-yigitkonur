# Follow-ups and open external

*Read this when a view needs to send a message back to the conversation or open a link in the browser.*

## Send a follow-up message

Ask the model to continue the conversation by sending a natural-language prompt.

**Signature:**
```typescript
useSendFollowUp(): (args: { prompt: string }) => Promise<void>
```

**Example:**
```typescript
import { useSendFollowUp } from "mcp-use/react";

function CompareButton({ productName }: { productName: string }) {
  const sendFollowUp = useSendFollowUp();

  return (
    <button onClick={() => sendFollowUp({ prompt: `Compare ${productName} with similar products` })}>
      Compare
    </button>
  );
}
```

**What happens:**
1. Button click calls `sendFollowUp()`
2. Host receives the prompt and appends it to the conversation
3. Model sees the new message and generates a response
4. The function resolves when the host accepts the message (not when the model responds)

**Use for:**
- Actions that require model reasoning ("Show related products")
- Multi-step workflows ("Generate a report on these selections")
- Following up on user choices in the view

**Do not use for:**
- Local UI updates (use `setState` or React `useState` instead)
- Calling other tools (use `useCallTool` instead)

## Capability behavior

The hook checks the host's `message` capability. If unsupported, `sendFollowUp()` rejects before sending wire traffic; catch the error and provide fallback UI when this feature is optional.

See `references/18-mcp-apps/view-react/07-host-context-files-and-size.md` for the raw `hostCapabilities` exposed by `useHostContext()`.

## Open an external URL

Request the host to open a URL in the browser.

**Signature:**
```typescript
useOpenExternal(): (args: { url: string }) => Promise<void>
```

**Example:**
```typescript
import { useOpenExternal } from "mcp-use/react";

function DocumentationLink() {
  const openExternal = useOpenExternal();

  return (
    <button onClick={() => void openExternal({ url: "https://docs.example.com" })}>
      Open documentation
    </button>
  );
}
```

**Use for:**
- Help/documentation links
- Editing content on a separate service (e.g., "Open in Google Docs")
- Analytics or tracking URLs

**Not for:**
- Navigation within the app (use internal links or `useCallTool`)

## Combining with tool calls and state

A single button can do one main action. Order them logically:

```typescript
async function handleApprove() {
  // 1. Update local state immediately
  setLoading(true);

  // 2. Call a tool to persist the decision
  try {
    await callTool({ approve: true });
  } finally {
    setLoading(false);
  }

  // 3. Send a follow-up for model reasoning (optional)
  if (userWantsFollowUp) {
    await sendFollowUp({ prompt: "Summarize the impact of this approval" });
  }
}
```

## Gotchas

- **`sendFollowUp()` does not block on model response** → it resolves when the host queues the message, not when the model replies
- **`openExternal()` is advisory** → the host may refuse to open the URL (e.g., browser restrictions)
- **Unsupported calls reject** → if the host lacks `message` or `openLinks` capability, the returned Promise rejects
- **Both returned callbacks are referentially stable** → safe to put in a `useEffect` dependency array or pass down without a `useCallback` wrapper

Both hooks send messages outward (to the model, to the browser). To let the model or host call back *into* the mounted view, see `references/18-mcp-apps/view-react/09-useviewtool.md`.

