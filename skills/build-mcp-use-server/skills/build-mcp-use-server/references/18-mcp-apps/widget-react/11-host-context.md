# Host Context — `theme`, `locale`, `timeZone`, `safeArea`, `userAgent`, `maxHeight`

Read-only signals from the host that drive layout and formatting decisions. All come from `useWidget()`.

## Reference

| Field | Type | Default | Description |
|---|---|---|---|
| `theme` | `"light" \| "dark"` | `"light"` | Host theme. Auto-syncs through `<ThemeProvider>` (07). |
| `locale` | `string` | `"en"` | BCP 47 locale (e.g. `"en-US"`, `"de-DE"`). |
| `timeZone` | `string` | browser `Intl` timezone, or `"UTC"` server-side | IANA timezone (e.g. `"America/New_York"`). |
| `safeArea` | `{ insets: { top: number; right: number; bottom: number; left: number } }` | all zero | Safe-area insets in pixels. Mobile only. |
| `userAgent` | `{ device: { type: "mobile" \| "tablet" \| "desktop" \| "unknown" }, capabilities: { hover: boolean; touch: boolean } }` | desktop defaults | Device hints. |
| `maxHeight` | `number` | `600` | Max height in pixels available to the widget. |
| `maxWidth` | `number \| undefined` | undefined | Max width. MCP Apps only — `undefined` in ChatGPT. |

## When values update

| Field | Updates on |
|---|---|
| `theme` | Host theme change (system or user toggle). |
| `locale` / `timeZone` | Rare — usually stable for the session. |
| `safeArea` | Device rotation, virtual keyboard show/hide. |
| `userAgent` | Stable for the session. |
| `maxHeight` / `maxWidth` | Display mode change, viewport resize. |

`useWidget` re-renders whenever any of these change.

## Use them

### Locale-aware formatting

```tsx
const { locale, timeZone } = useWidget();

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale, { timeZone, dateStyle: "medium", timeStyle: "short" })
    .format(new Date(iso));

const formatPrice = (cents: number) =>
  new Intl.NumberFormat(locale, { style: "currency", currency: "USD" })
    .format(cents / 100);
```

### Safe-area-aware layout

```tsx
const { safeArea } = useWidget();

<div
  style={{
    paddingTop: safeArea.insets.top,
    paddingBottom: safeArea.insets.bottom,
    paddingLeft: safeArea.insets.left,
    paddingRight: safeArea.insets.right,
  }}
>
  ...
</div>
```

### Touch-vs-hover affordances

```tsx
const { userAgent } = useWidget();

const isTouch = userAgent.capabilities.touch;
const buttonClass = isTouch ? "p-3 min-h-[44px]" : "p-1 hover:bg-gray-100";
```

`44px` minimum is the standard touch target.

### Constrain to `maxHeight`

```tsx
const { maxHeight } = useWidget();

<div style={{ maxHeight, overflowY: "auto" }}>...</div>
```

This is especially important when not using `autoSize` on `<McpUseProvider>` — without auto-sizing, you must keep the widget within the host's allotted height.

## Theme — read once, branch sparingly

```tsx
const { theme } = useWidget();
const isDark = theme === "dark";
```

Prefer Tailwind's `dark:` variant over manual branching. The `<ThemeProvider>` already sets the `dark` class on `<html>`, so `dark:bg-gray-900` works without referencing `theme` directly. Only branch on `theme` for inline styles or non-Tailwind libraries.

## Defaults are conservative

When the host hasn't connected yet (`isAvailable` is false), values default to the safest assumptions: `light`, desktop, English, browser timezone, no insets, 600px height. Render against the defaults without crashing — your widget should look acceptable even before the runtime attaches.
