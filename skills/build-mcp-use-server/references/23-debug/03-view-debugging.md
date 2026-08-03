# View Debugging

*Read this when a view (MCP App) is not rendering, shows blank, or interactive features fail.*

## Inspector View Preview

The easiest way to test a view rendering:

1. Open `http://localhost:3000/mcp/inspector`
2. Go to **Tools** tab
3. Call a tool that returns a `view: { name: "my-view" }`
4. Inspector shows the rendered view inline
5. Click **Debug Panels** (above output) to see:
   - **props**: Structured data the view receives (this is the tool result's `structuredContent`, typed by the tool's `outputSchema`)
   - **output**: Raw tool result
   - **metadata**: Timestamps, cache, host hints
   - **state**: View state after interactions

If the view doesn't appear:
- Check **props** panel — are the props being sent?
- Open browser DevTools (F12) → **Console** — are there errors in the iframe?
- Check tool `view.name` matches folder name in `views/`

## Browser DevTools

Open DevTools **Console** tab while the view renders:

```javascript
// Errors appear in console from the view iframe
// Common errors:
"CSP violation: script from https://cdn.example.com blocked"
"Failed to parse module: unexpected token"
"Cannot find module 'react'"
```

For CSP violations, see references/18-mcp-apps/server-surface/05-csp-metadata.md.

## Protocol Toggle (MCP Apps vs ChatGPT Apps)

In Inspector with a view visible:
1. Look for **Protocol** toggle (appears when the view supports both runtimes)
2. Toggle between **MCP Apps** and **ChatGPT Apps**
3. Different rendering behavior confirms dual-protocol support

Use this to verify the view works in both MCP and ChatGPT contexts.

## CSP Mode Testing

Some views declare restrictive CSP metadata. Inspector can test both permissive and declared CSP:

1. Tool returns a view with `view: { csp: { connectDomains: ["api.example.com"] } }`
2. Inspector shows two renderings:
   - **Permissive CSP**: View works with no restrictions (baseline test)
   - **Declared CSP**: View with specified CSP applied (production test)
3. If the view fails only in declared CSP, the CSP config is too restrictive

Fix by:
- Adding domains to `connectDomains`, `resourceDomains`, `frameDomains`, `baseUriDomains`
- Or loosening CSP if safe (e.g., `connectDomains: ["*"]` for public APIs)

See references/18-mcp-apps/server-surface/05-csp-metadata.md for CSP fields.

## Screenshot Command

Capture a view as PNG (useful for CI/CD verification). Tool arguments are trailing positional `key=value` / `key:=<json>` pairs — or a single JSON object — not a flag:

```bash
mcp-use screenshot \
  --mcp http://localhost:3000/mcp \
  --tool my-tool \
  param=value \
  --output my-view.png \
  --width 1200 \
  --height 800 \
  --device-scale-factor 2 \
  --theme dark
```

Or with a saved server (from `mcp-use client connect`) and JSON arguments:

```bash
mcp-use screenshot --server my-local --tool my-tool '{"param":"value"}' --json
```

Source options (exactly one required):
- `--server <name>`: Use a server saved by `mcp-use client`
- `--mcp <url>`: Connect directly to an HTTP(S) MCP endpoint (pair with `-H/--header` for auth; incompatible with `--server`)

Capture options:
- `--tool <name>`: View-backed tool to call (required)
- `--output <path>`: Output PNG path (default: timestamped view name)
- `--width <px>`: Host/view width (default 768, matching an OpenAI inline MCP App container)
- `--height <px>`: Host viewport height for responsive layout (default 720); the PNG is cropped to the view's rendered bounds
- `--device-scale-factor <n>`: Pixel density, greater than 0 and at most 4 (default 1)
- `--theme light|dark`: Host theme (default light)
- `--wait-for <selector>`: Wait for a selector before capture
- `--delay <ms>`: Additional delay after readiness (default 0)
- `--timeout <ms>`: Tool/browser timeout (default 30000)
- `--inspector <url>`: Use an existing Inspector origin instead of spawning a packaged one
- `--cdp-url <url>`: Use an existing Chrome DevTools endpoint instead of launching Chrome
- `--json`: Emit one machine-readable result or error; never prompt

There is no `--arguments` flag — passing a bare JSON object or `key=value` pairs after `--tool <name>` is the only way to supply tool arguments.

Result: PNG file of the rendered view at the specified size/theme.

## Display Modes

Inspector tests different display modes (device sizes, themes):

1. View preview shows **display modes** dropdown
2. Select:
   - **Inline**: View in normal flow (default)
   - **Picture-in-Picture**: Floating view overlay
   - **Fullscreen**: View takes entire viewport
3. Select device size: **Desktop**, **Tablet**, **Mobile**
4. Select theme: **Light**, **Dark**
5. Select locale/timezone: Affects date/time formatting

Verify view layout works in all modes before shipping. Only display modes listed in the view's `viewConfig.displayModes` are actually offered to the host — see references/18-mcp-apps/server-surface/03-viewconfig.md.

## Testing View State

Interact with the view in Inspector:
1. Call the tool that returns a view
2. Click buttons, fill forms in the view
3. **Debug Panels** → **state** tab shows persisted view state
4. Verify state matches expected shape

If view state resets unexpectedly:
- Check `<ThemeProvider>` wraps the component at the root (see references/18-mcp-apps/view-react/01-setup-and-providers.md)
- Verify state is managed by `useViewState()` or `useState()` — there is no `useWidget()` hook in v2

## Checking View Props

Tool handler returns a view with props — `structuredContent` on the tool result **is** the props object directly, typed by the tool's `outputSchema`; do not nest it under a `props` key:

```typescript
server.tool(
  { name: "my-tool", /* ..., outputSchema: ... */ view: { name: "my-view" } },
  async (args) => ({
    content: [...],
    structuredContent: { title: "Hello", items: [...] },
  })
);
```

In Inspector:
- **Debug Panels** → **props** shows: `{ title: "Hello", items: [...] }`
- Verify the shape matches the tool's `outputSchema` and what `views/my-view/view.tsx` reads via `useToolContext()`
- If props don't match schema, the view renders an error (see browser console)

## Hot Reload Issues

After editing `views/my-view/view.tsx`:
- Run `npm run dev` — HMR should reload the view automatically
- If not:
  - Refresh browser tab
  - Check build output for TypeScript errors
  - Restart `npm run dev`

If HMR breaks during edit:
- Verify import statements are correct (TypeScript compilation pass 1)
- Restart dev server to rebuild views

## View Asset URLs

A view accesses images, stylesheets, JS libraries:

```typescript
export default function MyView() {
  return (
    <img src="./my-icon.svg" />  // Relative path OK in dev
  );
}
```

In dev, relative paths work. In production, ensure:
- `MCP_URL` and `MCP_ASSETS_URL` are set at build time
- Assets are in `.mcp-use/build/views/my-view/`
- Deployed platform serves assets correctly (see references/25-deploy/platforms/10-runtime-patterns.md)

If the deployed view shows 404 on images:
- Check `MCP_ASSETS_URL` was set during build
- Verify static binding is configured correctly for your platform

