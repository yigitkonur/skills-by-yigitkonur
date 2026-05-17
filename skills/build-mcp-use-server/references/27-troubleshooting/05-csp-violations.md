# CSP Violations

Reading the browser console violation, mapping it to a `widgetMetadata.metadata.csp` field, and verifying with the Inspector's CSP mode.

---

## 1. The shape of a CSP violation in the console

Browser DevTools (Chrome/Edge example):

```
Refused to connect to 'https://api.example.com/data' because it violates
the following Content Security Policy directive: "connect-src 'self' https://your-server.com".
```

Three things to extract:

1. **The action that was blocked** — `connect`, `script`, `style`, `img`, `frame`, `font`.
2. **The directive that blocked it** — `connect-src`, `script-src`, etc.
3. **The blocked origin** — `https://api.example.com` in this example.

---

## 2. Map the directive to the widget metadata field

mcp-use translates camelCase widget metadata fields into CSP directives in the iframe:

| CSP directive       | `widgetMetadata.metadata.csp.*` field | Use for                                    |
|---------------------|---------------------------------------|--------------------------------------------|
| `connect-src`       | `connectDomains`                      | `fetch`, `XMLHttpRequest`, `WebSocket`, EventSource. |
| `script-src`        | `resourceDomains`                     | External JS bundles, CDN scripts.          |
| `style-src`         | `resourceDomains`                     | External CSS.                              |
| `img-src`           | `resourceDomains`                     | Images served from external origins.       |
| `font-src`          | `resourceDomains`                     | External fonts.                            |
| `frame-src`         | `frameDomains`                        | Embedded iframes (YouTube, Stripe, etc.).  |
| `base-uri`          | `baseUriDomains`                      | The widget's `<base href>`.                |

If the violation says `connect-src`, you fix it in `connectDomains`. If it says `script-src`, you fix it in `resourceDomains`. The mapping is strict — `connectDomains` won't unblock a script load.

---

## 3. Add the origin to the widget metadata

When registering the widget resource:

```typescript
server.resource({
  name: "my-widget",
  uri: "ui://widget/my-widget.html",
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      resourceDomains: ["https://cdn.example.com"],
      frameDomains: ["https://www.youtube.com"],
      baseUriDomains: ["https://app.example.com"],
    },
  },
}, async () => readFile("./resources/my-widget.html"));
```

After redeploy, the iframe's CSP meta tag includes the new origin.

---

## 4. Auto-injected origins (since v1.16.1)

mcp-use automatically adds:

- The MCP server's own origin to `connectDomains` and `resourceDomains` (so the widget can call back to the server).
- The request origin (from `X-Forwarded-Host` or `Host`) when behind a proxy (since v1.16.0).

You don't need to declare your own server domain. You **do** need to declare every external origin the widget touches.

---

## 5. The Inspector's CSP mode

The Inspector has a "CSP mode" toggle that simulates the production iframe sandbox. Without it, the Inspector renders the widget in a permissive iframe and you won't see violations until production.

- **Toggle on** → simulates the real CSP. Violations show in the browser console exactly as they will in production.
- **Toggle off** → permissive — useful only for "is the widget even rendering?" checks.

Always run with CSP mode on before declaring a widget ready. See `../20-inspector/11-protocol-toggle-and-csp-mode.md` for the toggle's location and behavior.

---

## 6. Common patterns

| Widget needs to ...                       | Add to                |
|-------------------------------------------|-----------------------|
| Call your own MCP server (`/mcp`)         | Auto-injected. Nothing. |
| Call a public API (e.g. `api.openai.com`) | `connectDomains`      |
| Load Tailwind from a CDN                  | `resourceDomains`     |
| Embed a YouTube video                     | `frameDomains`        |
| Use Google Fonts                          | `resourceDomains` (for `fonts.googleapis.com` and `fonts.gstatic.com`) |
| Load Stripe Elements                      | `resourceDomains` and `frameDomains` |
| Make WebSocket calls                      | `connectDomains` (with `wss://`) |

---

## 7. Inline scripts and styles

By default, the iframe sandbox forbids inline `<script>` and inline event handlers. If you've copy-pasted HTML with `<script>console.log(...)</script>` or `onclick="..."`, the browser will block it.

**Fix:** Move scripts to an external file in the widget's bundle, or use React event handlers (which compile down without inline attributes).

`unsafe-inline` is **not** an option in production widgets — mcp-use does not expose a knob to enable it.

---

## 8. After every CSP fix

1. Rebuild: `npm run build`.
2. Redeploy if testing live.
3. Hard refresh in the Inspector (or any host) — iframes are cached aggressively.
4. Re-check console — confirm zero violations before shipping.

---

For broader widget rendering troubleshooting (blank, plain HTML, missing provider), see `04-widget-rendering-issues.md`. For widget anti-patterns, see `18-mcp-apps/widget-anti-patterns/`.
