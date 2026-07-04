# Dual-Protocol via `type: "mcpApps"`

The recommendation in two words: **always use `mcpApps`**. One widget code path, two protocols supported, runtime detection handled by `useWidget`.

## The recommendation

```typescript
server.uiResource({
  type: "mcpApps",   // not "appsSdk"
  name: "...",
  htmlTemplate: `...`,
  metadata: { /* unified */ },
});
```

| Type | ChatGPT | MCP Apps clients | Status |
|---|---|---|---|
| `mcpApps` | Yes | Yes | **Recommended** |
| `appsSdk` | Yes | No | **Legacy** |

## Why this works

`mcpApps` registrations generate both metadata payloads from one widget definition:

| Variant | Resource / metadata shape | Metadata namespace | CSP keys |
|---|---|---|---|
| MCP Apps | registered `mcpApps` UI resource | `_meta.ui.*` | camelCase |
| ChatGPT | generated Apps SDK tool/resource metadata | `_meta["openai/*"]` | snake_case |

ChatGPT uses the generated `openai/*` metadata; Claude/Goose/MCP Inspector use the `mcp-app` profile and camelCase metadata.

See `03-skybridge-mime.md` for the MIME/metadata details and `04-csp-format-differences.md` for the CSP conversion.

## Runtime detection in the widget

Inside the iframe, `useWidget` detects which host loaded it:

```typescript
const isChatGPT = typeof window !== "undefined" && "openai" in window;
const isMcpApps = typeof window !== "undefined" && window.parent !== window;
```

It then picks the correct bridge:

- **ChatGPT** → uses `window.openai.*` for `callTool`, `setState`, `sendFollowUpMessage`, theme, etc.
- **MCP Apps** → uses JSON-RPC over `postMessage` for the same operations.

Your widget code does not branch. See `07-runtime-detection.md`.

## What goes in the unified `metadata`

```typescript
metadata: {
  // Shared — used by both protocols
  csp: {
    connectDomains: [...],
    resourceDomains: [...],
    redirectDomains: [...], // ChatGPT-specific
  },
  prefersBorder: true,
  invoking: "Loading...",
  invoked: "Ready",

  // MCP Apps specific (ignored by ChatGPT)
  autoResize: true,

  // ChatGPT specific (ignored by MCP Apps clients)
  widgetDescription: "Special description for ChatGPT",
  domain: "https://chatgpt.com",
  widgetAccessible: true,
  locale: "en-US",
}
```

Adapters transform the supported unified fields to protocol-specific metadata. Keep ChatGPT-only CSP options under `metadata.csp`.

## Writing once, shipping twice — full example

```typescript
// resources/weather-display/widget.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propSchema = z.object({
  city: z.string(),
  temperature: z.number(),
  conditions: z.string(),
});

export const widgetMetadata: WidgetMetadata = {
  description: "Display weather information",
  props: propSchema,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      scriptDirectives: ["'unsafe-eval'"],
    },
    prefersBorder: true,
    autoResize: true,
    widgetDescription: "Interactive weather card",  // ChatGPT-only field; MCP Apps ignores
  },
};

const WeatherDisplay: React.FC = () => {
  const { props, isPending, theme } = useWidget<z.infer<typeof propSchema>>();
  // identical code in both hosts
  if (isPending) return <Spinner />;
  return <WeatherCard {...props} dark={theme === "dark"} />;
};

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <WeatherDisplay />
    </McpUseProvider>
  );
}
```

The same component runs in ChatGPT and Claude unchanged.

## Don't dual-register

Do **not** register the same widget under both `type: "mcpApps"` and `type: "appsSdk"`. `mcpApps` already covers ChatGPT. Dual registration duplicates the resource and confuses tool wiring.

## When you'd ever pick `appsSdk`

You wouldn't, for new code. Existing `appsSdk` registrations should migrate — see `06-deprecation-of-appssdk.md` and `../../28-migration/04-appssdk-to-mcpapps.md`.

The only reason to keep `appsSdk` is staged rollout: keep the legacy registration live while you test the `mcpApps` variant, then delete the legacy once verified.
