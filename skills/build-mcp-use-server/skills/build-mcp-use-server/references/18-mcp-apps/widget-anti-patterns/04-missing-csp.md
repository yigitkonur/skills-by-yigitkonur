# Anti-Pattern: Missing CSP Declarations

Production hosts run widgets in a sandboxed iframe with a strict Content-Security-Policy. Any external network call — image, font, script, fetch — needs explicit allowlisting via `widgetMetadata.metadata.csp`. Skip it and the widget silently fails the moment it leaves your dev host.

## What goes wrong

```tsx
// BAD — no CSP. Works in dev, fails in production.
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: z.object({ city: z.string() }),
  // CSP missing
};

function WidgetContent() {
  // This image silently fails to load in production
  return <img src="https://openweathermap.org/img/wn/01d.png" alt="" />;
}
```

Symptoms:

- Images render in dev, broken in production
- `fetch()` from inside the widget hangs or errors with `Refused to connect to ...`
- DevTools console shows `Refused to load the image because it violates the following Content Security Policy directive: img-src ...`
- Inline `<style>` or `<script>` blocks throw `Refused to apply inline style`

## Declare every external domain

The three CSP keys cover the main directives:

| Key | Maps to | Use for |
|---|---|---|
| `connectDomains` | `connect-src` | `fetch`, `WebSocket`, `XHR` |
| `resourceDomains` | resource-loading directives | Images, scripts, stylesheets, fonts |
| `scriptDirectives` | `script-src` | Remote scripts (rare; widgets ship JS at build time) |

```tsx
// GOOD — every external origin declared
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: z.object({ city: z.string(), iconCode: z.string() }),
  metadata: {
    csp: {
      resourceDomains: ["https://openweathermap.org"],
    },
    prefersBorder: true,
  },
};
```

## What "every domain" means

- Only include origins the widget iframe touches. Server-side `fetch()` calls do not need widget CSP entries.
- Origins, not URLs. `https://cdn.example.com`, not `https://cdn.example.com/v2/`.
- Subdomains are not wildcarded by default. List `https://api.foo.com` and `https://cdn.foo.com` separately if you use both.
- `data:` URIs (inline images) are allowed by default. You do not need to whitelist `data:`.
- `https:` everywhere. Plain `http:` will be blocked by mixed-content rules in most hosts.

## Audit checklist

Before shipping, search the widget for every external string and confirm it has a matching CSP entry:

```bash
# Find candidate origins inside the widget folder
grep -RhE "https?://[a-zA-Z0-9.-]+" resources/my-widget/ | grep -oE "https?://[a-zA-Z0-9.-]+" | sort -u
```

Each unique origin must appear in either `connectDomains` or `resourceDomains` of `widgetMetadata.metadata.csp`.

## Inline style and script

Tailwind-built CSS and the bundled widget JS ship inline by default and are not affected by CSP `style-src` / `script-src` — the host pre-allows the widget bundle. You only need `scriptDirectives` if you load remote scripts at runtime, which you should not be doing.

If you absolutely must inline a `<style>` block at runtime, prefer adding the styles to the widget's CSS-in-JS layer rather than emitting raw `<style>` — runtime inline styles trigger CSP violations even in dev.

## Severity

High. CSP violations are silent in production until a user notices. Every widget that touches external network must declare its domains. Make this part of the PR checklist.
