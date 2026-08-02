# Runtime Detection: ChatGPT vs. MCP Apps

*Read this if your view needs to detect which platform is running (rarely needed).*

The `useHostContext()` hook provides platform hints via `hostContext.client`. These hints are **low-trust** (client can spoof them), but useful for diagnostic logging or graceful fallbacks.

## Getting Platform Info

```typescript
import { useHostContext } from "mcp-use/react";

export default function MyView() {
  const hostContext = useHostContext();
  
  console.log(hostContext.client.name);           // "ChatGPT", "Claude", undefined
  console.log(hostContext.client.locale);         // "en-US"
  console.log(hostContext.client.userAgent);      // browser user agent string
  console.log(hostContext.client.organizationId); // if available
}
```

## Capability-Based Detection (Preferred)

Instead of detecting by name, query capabilities:

```typescript
// GOOD: Detect by capability
const hasMessage = hostContext.availableCapabilities.includes("message");
if (hasMessage) {
  await useSendFollowUp({ prompt: "..." });
}

// AVOID: Detect by client name
if (hostContext.client.name === "ChatGPT") {
  // This can be spoofed; use capability detection instead
}
```

**Always gate features on capabilities, not client name.**

## Client Info Schema

```typescript
type ClientInfo = {
  name?: string;              // "ChatGPT", "Claude", etc.
  locale?: string;            // "en-US", "fr-FR", etc.
  userAgent?: string;         // Full browser user-agent
  organizationId?: string;    // Organization ID if available
  conversationId?: string;    // Conversation ID (ChatGPT)
  threadId?: string;          // Thread ID (if applicable)
  safeAreaInsets?: {          // Notch/safe-area info
    top: number;
    bottom: number;
    left: number;
    right: number;
  };
};
```

Only fields present are populated. Treat all as optional hints.

## Honest Logging Example

```typescript
export default function DataView() {
  const hostContext = useHostContext();
  
  useEffect(() => {
    // Log client info for debugging (not security gating)
    console.log("[view-init]", {
      clientName: hostContext.client.name,
      locale: hostContext.client.locale,
      capabilities: hostContext.availableCapabilities,
    });
  }, [hostContext]);
}
```

## Why Not Use Client Name for Features

Client name is self-reported and can be spoofed:

```typescript
// WRONG
if (hostContext.client.name === "ChatGPT") {
  // An MCP Apps host could spoof this
}

// RIGHT
if (hostContext.availableCapabilities.includes("message")) {
  // Capability is verified by the host
}
```

The host always advertises its true capabilities; spoofing one is pointless (the feature won't work anyway).

## Testing and Development

In `mcp-use dev`, the Inspector provides platform simulation:

1. Open `http://localhost:3000/mcp/inspector`
2. Click **Settings** → **CSP Mode** or **Device Simulation**
3. View's `hostContext` reflects the simulated platform

Useful for testing platform-specific UI without deploying to ChatGPT.

## Display Mode Context

Similarly, `useHostContext()` includes display-mode info:

```typescript
const {
  availableDisplayModes,       // ["inline", "fullscreen"]
  currentDisplayMode,          // current mode
  safeAreaInsets,              // safe area (notch, etc.)
  dimensions,                  // { width, height }
} = useHostContext();

useEffect(() => {
  // Respond to layout changes
  if (dimensions.width < 400) {
    // Compact layout
  }
}, [dimensions]);
```

## See Also

- `references/18-mcp-apps/05-host-capability-detection.md` — capability checking guide
- `references/18-mcp-apps/view-react/07-host-context-files-and-size.md` — full `useHostContext()` API
- `01-dual-protocol.md` — how mcp-use handles both protocols transparently
