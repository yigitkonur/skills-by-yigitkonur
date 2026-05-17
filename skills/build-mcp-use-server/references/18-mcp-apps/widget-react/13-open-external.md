# `openExternal(href)` — Open URLs Outside the Iframe

Routes a URL through the host's browser instead of trying to navigate the widget's own iframe.

```typescript
const { openExternal } = useWidget();

openExternal("https://example.com/details/123");
```

## Why not `<a href="...">` or `window.open()`

The widget runs inside a sandboxed iframe with strict CSP. Plain anchors and `window.open` are routinely blocked or open inside the iframe, breaking back navigation and leaving the user stranded.

`openExternal` delegates to the host runtime, which:

- ChatGPT Apps SDK: calls `window.openai.openExternal({ href })`.
- MCP Apps: sends `ui/open-link` to the host.

The host opens the URL in the user's default browser (or its own browser tab), outside the iframe.

## Signature

```typescript
openExternal(href: string): void;
```

Synchronous fire-and-forget. Returns nothing. If the runtime API is missing, `useWidget().openExternal` throws; host policy denials are host-specific.

## Use it

```tsx
import { useWidget } from "mcp-use/react";

const LinkRow: React.FC = () => {
  const { props, openExternal } =
    useWidget<{ url: string; title: string }>();

  return (
    <button onClick={() => openExternal(props.url!)}>
      Open {props.title} →
    </button>
  );
};
```

## CSP implications

`openExternal` is **not** subject to the iframe's CSP `connect-src` or `navigate-to` rules — the host opens the URL, not the iframe. This is the exact reason the API exists. You do **not** need to add domains opened via `openExternal` to `widgetMetadata.metadata.csp.connectDomains`.

In contrast, fetches to that same domain (`fetch("https://example.com")`) **do** require the domain in `connectDomains`.

## URL hygiene

The package hook does not validate or normalize the string before passing it to the host. Validate URLs before calling it:

- Prefer absolute `https://` URLs.
- Resolve relative paths yourself before passing `href`.
- Reject user-controlled URLs that are not on an allow-list.
- Never pass `javascript:` or other executable schemes.

## Anti-patterns

- Calling `openExternal` from `useEffect` on mount — opens an unsolicited tab.
- Concatenating user-controlled values without validation — host trusts your URL string. Validate the href is on an allow-list before opening.
- Using `<a href={url} target="_blank">` — works inconsistently; `openExternal` is the correct API.
