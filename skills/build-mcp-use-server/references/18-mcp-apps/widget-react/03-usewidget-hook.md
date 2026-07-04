# `useWidget()` — The Primary Widget Hook

Single source of truth for everything a widget needs from the host: server-computed props, persisted state, theme, display mode, streaming progress, and the actions to call back into the host.

```typescript
import { useWidget } from "mcp-use/react";

const result = useWidget<TProps, TState, TOutput, TMetadata, TToolInput>(defaultProps);
```

## Type parameters

All optional, in package order:

```typescript
useWidget<
  TProps      = UnknownObject, // Shape of `props`
  TState      = UnknownObject, // Shape of persisted widget state
  TOutput     = UnknownObject, // Shape of `output`
  TMetadata   = UnknownObject, // Shape of `_meta`
  TToolInput  = UnknownObject  // Complete tool-call arguments
>(defaultProps?: TProps): UseWidgetResult<TProps, TState, TOutput, TMetadata, TToolInput>;
```

## Return value — full property reference

### Core data

| Property | Type | Description |
|---|---|---|
| `props` | `Partial<TProps>` while pending, `TProps` when complete | Merged from `defaultProps`, complete `toolInput`, and `structuredContent` overlay. `{}` if no data is available. |
| `toolInput` | `TToolInput` | Complete tool-call arguments the LLM sent. Defaults to `{}` before they arrive. |
| `isPending` | `boolean` | `true` while the tool executes on the server. |
| `output` | `TOutput \| null` | Structured tool output delivered to the widget (`structuredContent`, or parsed object fallback). |
| `metadata` | `TMetadata \| null` | Response metadata (the `_meta` field). |

### Persistent state

| Property | Type | Description |
|---|---|---|
| `state` | `TState \| null` | Persisted widget state. Survives reloads and follow-up tool calls. |
| `setState` | `(state: TState \| ((prev: TState \| null) => TState)) => Promise<void>` | Update persisted state. Async — awaits host acknowledgement. |

See `09-state-persistence.md` for the persistence contract.

### Display

| Property | Type | Description |
|---|---|---|
| `theme` | `"light" \| "dark"` | Current host theme. Default `"light"`. |
| `displayMode` | `"inline" \| "pip" \| "fullscreen"` | Current display mode. Default `"inline"`. |
| `requestDisplayMode` | `(mode: DisplayMode) => Promise<{ mode: DisplayMode }>` | Ask the host to change mode. May resolve to a different mode if the host declined. |
| `safeArea` | `{ insets: { top: number; bottom: number; left: number; right: number } }` | Safe-area insets for mobile. Default zero on all sides. |
| `maxHeight` | `number` | Maximum height available in pixels. Default `600`. |
| `maxWidth` | `number \| undefined` | Maximum width available. MCP Apps only — `undefined` in ChatGPT. |

See `10-display-modes.md` and `11-host-context.md`.

### Streaming

| Property | Type | Description |
|---|---|---|
| `isStreaming` | `boolean` | `true` while the LLM is streaming tool arguments. Always `false` in ChatGPT Apps SDK. |
| `partialToolInput` | `Partial<TToolInput> \| null` | Growing partial tool args during streaming. `null` before streaming starts and in ChatGPT Apps SDK. |

See `../streaming-tool-props/01-overview.md` for the full streaming pattern.

### Actions

| Method | Signature | Description |
|---|---|---|
| `callTool` | `(name: string, args: Record<string, unknown>) => Promise<CallToolResponse>` | Call any registered MCP tool. Type-safe alternative: `useCallTool` (`04-usecalltool-hook.md`). |
| `sendFollowUpMessage` | `(content: string \| MessageContentBlock[]) => Promise<void>` | Push a follow-up message into the conversation. See `12-followup-messages.md`. |
| `openExternal` | `(href: string) => void` | Open a URL in the host's browser, escaping the iframe. See `13-open-external.md`. |

Height reporting is handled by `<McpUseProvider autoSize>` in `mcp-use@1.26.0`; `useWidget()` does not expose a `notifyIntrinsicHeight` method. See `14-notify-intrinsic-height.md`.

### Environment

| Property | Type | Description |
|---|---|---|
| `locale` | `string` | BCP 47 locale (default `"en"`). |
| `timeZone` | `string` | IANA timezone (e.g. `"America/New_York"`). |
| `mcp_url` | `string` | MCP server base URL — useful for fetches to your own server's public endpoints. |
| `userAgent` | `{ device: { type: string }; capabilities: { hover: boolean; touch: boolean } }` | Device hints. Default `{ device: { type: "desktop" }, capabilities: { hover: true, touch: false } }`. |
| `hostInfo` | `{ name: string; version: string } \| undefined` | Host identity from the SEP-1865 `ui/initialize` handshake. MCP Apps only — `undefined` in ChatGPT. |
| `hostCapabilities` | `Record<string, unknown> \| undefined` | Host-advertised capabilities (SEP-1865). MCP Apps only — `undefined` in ChatGPT. |
| `isAvailable` | `boolean` | `true` when the provider is connected and ready. |

## Default values (before host attaches)

| Field | Default |
|---|---|
| `theme` | `"light"` |
| `displayMode` | `"inline"` |
| `safeArea` | `{ insets: { top: 0, bottom: 0, left: 0, right: 0 } }` |
| `maxHeight` | `600` |
| `userAgent` | `{ device: { type: "desktop" }, capabilities: { hover: true, touch: false } }` |
| `locale` | `"en"` |
| `timeZone` | Browser `Intl` timezone, or `"UTC"` server-side |
| `mcp_url` | `""` |
| `props` | `{}` |
| `toolInput` | `{}` |
| `output` | `null` |
| `metadata` | `null` |
| `state` | `null` |

## Lifecycle

1. **First render** — `isPending = true`, `props = {}`, `output`/`metadata` = `null`. Render a loading state.
2. **(Optional) Streaming phase** — `isStreaming = true`, `partialToolInput` updates incrementally.
3. **Tool complete** — `isPending = false`; `props`, `output`, `metadata` populated.

```tsx
const MyWidget: React.FC = () => {
  const { props, isPending } = useWidget<MyWidgetProps>();
  if (isPending) return <LoadingSpinner />;
  return <div>{props.city} — {props.temperature}°C</div>;
};
```

## Discipline rules

- **Never accept React props on a widget root component.** Children read from `useWidget()` only — props come from the host, not the parent. `<MyWidget city={x} />` is wrong.
- **Type the parameters you use** when any of them are non-trivial. Remember the order is `props`, `state`, `output`, `metadata`, `toolInput`.
- **Treat `props` as `Partial<TProps>`** — every field can be `undefined` while `isPending` or during streaming.
- **Read `state` defensively** — null until the user has set it once.

## Convenience hooks

If a component only needs one slice of `useWidget`, the convenience hooks reduce noise:

| Hook | Returns |
|---|---|
| `useWidgetProps<T>()` | Just `props`. |
| `useWidgetTheme()` | Just `theme`. |
| `useWidgetState<T>(initial?)` | `[state, setState]` tuple. In `1.26.0`, the initial seed auto-persists only when ChatGPT's `window.openai.setWidgetState` is available; still handle `null`. |

```tsx
import { useWidgetProps, useWidgetTheme, useWidgetState } from "mcp-use/react";

const props = useWidgetProps<{ city: string }>();
const theme = useWidgetTheme();
const [prefs, setPrefs] = useWidgetState<{ unit: "c" | "f" }>({ unit: "c" });
```

## Composite example

```tsx
import { useWidget } from "mcp-use/react";

interface ProductProps { productId: string; name: string; price: number }
interface ProductOutput { reviews: Array<{ rating: number; comment: string }> }
interface ProductState { favorites: string[] }

const ProductWidget: React.FC = () => {
  const {
    props, output, state, setState,
    theme, displayMode, safeArea,
    callTool, sendFollowUpMessage, openExternal,
    requestDisplayMode,
    isAvailable,
  } = useWidget<ProductProps, ProductState, ProductOutput, {}, ProductProps>();

  const addFavorite = async () => {
    await setState((prev) => ({ favorites: [...(prev?.favorites ?? []), props.productId!] }));
  };

  return (
    <div data-theme={theme}>
      <h1>{props.name}</h1>
      <p>${props.price}</p>
      <button onClick={addFavorite}>Add to Favorites</button>
      <button onClick={() => callTool("get-product-reviews", { productId: props.productId })}>
        Get Reviews
      </button>
    </div>
  );
};
```

The hook abstracts over the runtime — same code runs in MCP Apps clients (JSON-RPC over `postMessage`, SEP-1865 bridge) and ChatGPT Apps SDK (`window.openai`). The only difference at runtime is which fields are populated; the hook's surface is identical.
