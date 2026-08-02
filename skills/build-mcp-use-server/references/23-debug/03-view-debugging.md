# View Debugging

*Read this when a view (MCP App) is not rendering, shows blank, or interactive features fail.*

## Inspector Widget Preview

The easiest way to test a view rendering:

1. Open `http://localhost:3000/mcp/inspector`
2. Go to **Tools** tab
3. Call a tool that returns a `widget: { name: "my-view" }`
4. Inspector shows the rendered widget inline
5. Click **Debug Panels** (above output) to see:
   - **props**: Structured data the widget receives
   - **output**: Raw tool result
   - **metadata**: Timestamps, cache, host hints
   - **state**: Widget state after interactions

If widget doesn't appear:
- Check **props** panel — are the props being sent?
- Open browser DevTools (F12) → **Console** — are there errors in the iframe?
- Check tool `widget.name` matches folder name in `resources/`

## Browser DevTools

Open DevTools **Console** tab while widget renders:

```javascript
// Errors appear in console from widget iframe
// Common errors:
"CSP violation: script from https://cdn.example.com blocked"
"Failed to parse module: unexpected token"
"Cannot find module 'react'"
```

For CSP violations, see resources/18-mcp-apps/server-surface/05-csp-metadata.md.

## Protocol Toggle (MCP Apps vs ChatGPT Apps)

In Inspector with a widget visible:
1. Look for **Protocol** toggle (appears when widget supports both runtimes)
2. Toggle between **MCP Apps** and **ChatGPT Apps**
3. Different rendering behavior confirms dual-protocol support

Use this to verify widget works in both MCP and ChatGPT contexts.

## CSP Mode Testing

Some widgets declare restrictive CSP headers. Inspector can test both permissive and declared CSP:

1. Tool returns widget with `view: { csp: { connectDomains: ["api.example.com"] } }`
2. Inspector shows two renderings:
   - **Permissive CSP**: Widget works with no restrictions (baseline test)
   - **Declared CSP**: Widget with specified CSP applied (production test)
3. If widget fails only in declared CSP, CSP config is too restrictive

Fix by:
- Adding domains to `connectDomains`, `resourceDomains`, `frameDomains`, `baseUriDomains`
- Or loosening CSP if safe (e.g., `connectDomains: ["*"]` for public APIs)

See references/18-mcp-apps/server-surface/05-csp-metadata.md for CSP fields.

## Screenshot Command

Capture a view as PNG (useful for CI/CD verification):

```bash
mcp-use screenshot \
  --mcp http://localhost:3000/mcp \
  --tool my-tool \
  --arguments '{"param":"value"}' \
  --output my-view.png \
  --width 1200 \
  --height 800 \
  --device-scale-factor 2 \
  --theme dark
```

Options:
- `--device-scale-factor 2`: Retina-like scaling (for mobile testing)
- `--theme dark|light`: Apply theme before rendering
- `--wait-for <selector>`: Wait for element to appear (e.g., `--wait-for .chart-loaded`)
- `--delay <ms>`: Wait N milliseconds before screenshot
- `--timeout <ms>`: Fail if screenshot takes >N ms (default 30000)

Result: PNG file of the rendered widget at the specified size/theme.

## Display Modes

Inspector tests different display modes (device sizes, themes):

1. Widget preview shows **display modes** dropdown
2. Select:
   - **Inline**: Widget in normal flow (default)
   - **Picture-in-Picture**: Floating widget overlay
   - **Fullscreen**: Widget takes entire viewport
3. Select device size: **Desktop**, **Tablet**, **Mobile**
4. Select theme: **Light**, **Dark**
5. Select locale/timezone: Affects date/time formatting

Verify widget layout works in all modes before shipping.

## Testing Widget State

Interact with the widget in Inspector:
1. Call tool that returns widget
2. Click buttons, fill forms in the widget
3. **Debug Panels** → **state** tab shows persisted widget state
4. Verify state matches expected shape

If widget state resets unexpectedly:
- Check `<McpUseProvider autoSize>` is wrapping the component (see references/18-mcp-apps/view-react/01-setup-and-providers.md)
- Verify state is managed by `useWidget()` or `useState()`

## Checking View Props

Tool handler returns view with props:

```typescript
server.tool(
  { name: "my-tool", ..., widget: { name: "my-view" } },
  async (args) => ({
    content: [...],
    structuredContent: {
      props: { title: "Hello", items: [...] }
    }
  })
);
```

In Inspector:
- **Debug Panels** → **props** shows: `{ title: "Hello", items: [...] }`
- Verify prop types match widget schema (in `resources/my-view/widget.tsx` → `widgetMetadata.props`)
- If props don't match schema, widget renders error (see browser console)

## Hot Reload Issues

After editing `resources/my-view/widget.tsx`:
- Run `npm run dev` — HMR should reload widget automatically
- If not:
  - Refresh browser tab
  - Check build output for TypeScript errors
  - Restart `npm run dev`

If HMR breaks during edit:
- Verify import statements are correct (TypeScript compilation pass 1)
- Restart dev server to rebuild views

## View Asset URLs

Widget accesses images, stylesheets, JS libraries:

```typescript
export default function MyWidget() {
  return (
    <img src="./my-icon.svg" />  // Relative path OK in dev
  );
}
```

In dev, relative paths work. In production, ensure:
- `MCP_URL` and `MCP_ASSETS_URL` are set at build time
- Assets are in `.mcp-use/build/views/my-view/`
- Deployed platform serves assets correctly (see references/25-deploy/platforms/10-runtime-patterns.md)

If deployed widget shows 404 on images:
- Check MCP_ASSETS_URL was set during build
- Verify static binding is configured correctly for your platform

