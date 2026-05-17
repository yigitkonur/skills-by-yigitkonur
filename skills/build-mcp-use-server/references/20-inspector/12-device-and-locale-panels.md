# Device and Locale Panels

When a widget is rendered, the Inspector exposes panels for simulating the host environment: device type, locale, time zone, safe-area insets, capabilities, display mode, and props. Use these to test responsive behavior, internationalization, and CSS safe-area handling without leaving the browser.

## Device Emulation

Switch viewport and capability presets.

| Device | Viewport | Capabilities |
|---|---|---|
| **Desktop** | Large | Hover supported, no touch |
| **Mobile** | Small | Touch supported, no hover |
| **Tablet** | Medium | Both touch and hover |

The selected device updates `window.openai.userAgent`:

```ts
{ device: { type: 'mobile' }, capabilities: { hover: false, touch: true } }
```

Widgets reading `userAgent.device.type` should adapt layout and input affordances. Widgets using `useWidget()` from `mcp-use/react` receive `userAgent` in the same result object.

## Locale Selector

Drives `window.openai.locale` (and the equivalent `useWidget` field). Pick from 100+ locales — `en-US`, `es-ES`, `ja-JP`, `de-DE`, `fr-FR`, `ar-SA`, etc.

Verify:

- Date / number / currency formatting via `Intl.*` APIs picks up the new locale.
- Translated strings (i18n catalogs) re-render.
- Right-to-left layouts render correctly for `ar-*`, `he-*`, `fa-*`.

## Timezone Selector

**MCP Apps protocol only.** Drives `timeZone` in the `useWidget` context.

Use to validate:

- `Intl.DateTimeFormat({ timeZone })` output.
- "Today" / "Yesterday" relative-date logic across DST boundaries.
- Calendar / scheduler widgets that pin events to user TZ.

## Capabilities

Toggle individual capabilities independent of the Device preset.

| Capability | Effect |
|---|---|
| **Touch** | Enables touch event simulation (e.g. `touchstart`, `touchend`) |
| **Hover** | Enables hover state detection (e.g. `:hover` styles, `mouseenter`) |

Useful for hybrid devices (tablets with mice, foldables) or for confirming that a widget gracefully handles `hover: false`.

## Safe Area Insets

Configure CSS `env(safe-area-inset-*)` values used to lay out around notches, status bars, home indicators, and display cutouts.

| Inset | Models |
|---|---|
| **Top** | Notch / status bar |
| **Bottom** | Home indicator |
| **Left** / **Right** | Display cutouts (foldables, edge displays) |

Updates `window.openai.safeArea` and `useWidget`'s `safeArea`:

```ts
{ insets: { top: 44, bottom: 34, left: 0, right: 0 } }
```

Test that:

- Sticky headers respect `top` inset.
- Bottom-pinned action bars respect `bottom` inset.
- Padding scales — content does not bleed under the notch.

## Display Mode Controls

| Mode | Behavior | How to enter |
|---|---|---|
| **Inline** | Embedded in result panel. Default. | Default state |
| **Picture-in-Picture** | Floating, draggable, resizable | Click PiP button; or widget calls `requestDisplayMode({ mode: 'pip' })` |
| **Fullscreen** | Full browser window | Click fullscreen button; or `requestDisplayMode({ mode: 'fullscreen' })` |

`window.openai.displayMode` reflects the current mode. The `openai:set_globals` event fires on each transition.

Test that:

- Layout reflows when the container size changes.
- `notifyIntrinsicHeight` is honored in inline mode and capped in fullscreen / pip.
- `Esc` exits fullscreen cleanly.

## Theme

Theme follows the Inspector theme automatically. There is no separate theme picker for widgets — toggle the Inspector theme to flip widget `theme` between `"light"` and `"dark"`.

Validate that:

- Tokens / CSS variables react to `theme` updates.
- Component contrasts work in both themes.

## Props Management

For widgets that take props (via `structuredContent`), the panel offers:

| Action | Purpose |
|---|---|
| **Use Tool Input** | Use the current tool call's arguments as widget props |
| **Select Preset** | Load a previously saved prop set |
| **Create Preset** | Save the current props for reuse |
| **Edit Props** | Manually edit JSON values in place |

Use presets to maintain a small library of representative inputs (empty state, loading state, error state, large dataset) and switch quickly between them.

## Combined widget testing recipe

For a production-bound widget:

1. **Desktop / `en-US` / America/Los_Angeles** — baseline. Verify default render.
2. **Mobile / no hover / touch** — confirm tap targets, scroll behavior.
3. **Tablet / both capabilities** — confirm hover affordances coexist with touch.
4. **`ja-JP` / Asia/Tokyo** — verify CJK layout and timezone-aware dates.
5. **`ar-SA`** — verify RTL layout.
6. **Safe area `{ top: 44, bottom: 34 }`** — verify mobile chrome.
7. **Switch through inline / pip / fullscreen** — verify reflow.
8. **Pair with Protocol Toggle and CSP Mode** — see `11-protocol-toggle-and-csp-mode.md`.

## See also

- `09-debugging-chatgpt-apps.md` — full `window.openai` API reference.
- `11-protocol-toggle-and-csp-mode.md` — protocol switching and CSP enforcement.
- `../18-mcp-apps/server-surface/` — server-side widget setup.
- `../18-mcp-apps/widget-react/` — widget hooks and components.
