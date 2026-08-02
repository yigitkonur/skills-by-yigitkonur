# Debugging MCP Apps Widgets

*Read this when testing MCP Apps widgets, layout behavior, CSP (Content Security Policy), and runtime compatibility.*

Use the Inspector to debug a widget before you try it in a production host. The fastest loop is: connect your server, run the tool that returns the widget, inspect the widget data, then test layout, display modes, and CSP.

## Connect and run the widget tool

1. Run your mcp-use app locally:
   ```bash
   npm run dev
   ```

2. Open `http://localhost:3000/mcp/inspector` and connect to `http://localhost:3000/mcp`.

3. Open the **Tools** tab, select the tool that returns the widget, and run it with a small input.

The widget should render below the tool result. If no widget appears, check:
- `widget.name` in the server tool definition matches a folder in `resources/`
- The tool result metadata points to the widget resource
- Browser console errors from the widget iframe

## Protocol toggle

The Inspector can test MCP Apps behavior and ChatGPT Apps SDK compatibility for widgets that support both runtimes.

When the protocol toggle appears, it allows you to switch between:

| Protocol | What it tests |
| --- | --- |
| **MCP Apps** | The standard MCP Apps bridge over `postMessage`. |
| **ChatGPT Apps** | ChatGPT compatibility behavior, including Apps SDK-style host globals. |

Prefer `useWidget()` and other `mcp-use/react` hooks in widget code — they abstract over the runtime differences.

## Inspect widget data

Use the widget debug panels to confirm what the widget receives:

| Panel | What to verify |
| --- | --- |
| `props` | The structured data the widget renders. |
| `output` | The raw structured tool output, when exposed separately. |
| `metadata` | Widget-only metadata (timestamps, cache info, host hints). |
| `state` | Persisted widget state after user interactions. |
| Tool input | Arguments passed to the tool that produced the widget. |

When `props` are missing, compare the server's `outputSchema` with the widget's expected prop shape — they should describe the same fields.

## Test layout and display modes

Use the debug controls to test the widget in different contexts:

- Inline, picture-in-picture, and fullscreen display modes
- Desktop, tablet, and mobile sizing
- Touch and hover behavior
- Light and dark themes
- Locale and timezone-dependent formatting
- Safe-area insets for mobile layouts

The host may grant a different display mode than the widget requests. Read `displayMode` from `useWidget()` when the current mode matters.

## Test Content Security Policy

Test widget-declared CSP before shipping. The Inspector widget debug controls test both permissive and widget-declared CSP.

Use the widget-declared CSP mode to verify your widget works with the domains you declared. If the widget works in permissive mode but fails with widget-declared CSP, update the widget CSP configuration. See `references/18-mcp-apps/server-surface/05-csp-metadata.md` for server and widget settings.

## Use browser DevTools

Open browser DevTools while the widget renders. Console messages from the widget iframe help identify:

- Runtime errors
- Blocked requests
- CSP violations
- Missing props
- Failed tool calls

Keep console output intentional — log the minimum state needed to debug, then remove noisy logs before release.

## Test in chat

After the tool works directly, open the **Chat** tab and ask the model to use the tool.

Use chat to verify end-to-end behavior:

- The model chooses the right tool
- The tool receives valid arguments
- The model-visible text output is useful
- The widget renders with the same structured data
- Widget actions (tool calls, state updates, follow-up messages) behave as expected

Use the Tools tab again when you need to isolate whether a failure is in the tool, widget, or model behavior.

## Troubleshoot missing widgets

| Symptom | Check |
| --- | --- |
| Tool result appears, but no widget appears. | Confirm `widget.name` matches a folder under `resources/`. |
| Widget frame appears blank. | Check iframe console errors and missing required props. |
| Widget loads in permissive CSP only. | Add the required domains to widget CSP. |
| ChatGPT protocol fails, but MCP Apps works. | Check [Apps SDK compatibility](/typescript/mcp-apps/apps-sdk-compatibility). |
| A widget action fails. | Verify the tool name, arguments, auth state, and iframe console logs. |
