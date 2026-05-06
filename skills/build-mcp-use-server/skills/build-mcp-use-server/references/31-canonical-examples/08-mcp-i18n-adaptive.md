# Canonical: `mcp-use/mcp-i18n-adaptive`

**URL:** https://github.com/mcp-use/mcp-i18n-adaptive

The client-introspection reference. A widget that adapts both layout (column count derived from `maxWidth`) and formatting (`Intl.NumberFormat`, `Intl.DateTimeFormat`) based on `useWidget`-provided host context. A companion `detect-caller` tool exposes the same context as JSON for non-widget clients.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`show-context` tool) | Sample data the widget formats — numbers, dates, greeting |
| `index.ts` (`detect-caller` tool) | `ctx.client.user()` and `ctx.client.info()` — the server-side mirror of what the widget sees |
| `resources/context-display/widget.tsx` | All the `useWidget` context fields used live: `locale`, `timeZone`, `userAgent`, `safeArea`, `maxWidth`, `maxHeight`, `hostInfo`, `hostCapabilities`, `theme`, `displayMode` |
| `resources/context-display/types.ts` | Minimal `propSchema` — most context comes from the host, not the props |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| Adaptive grid via `maxWidth` thresholds | `cols = useMemo(() => maxWidth < 400 ? 1 : maxWidth < 800 ? 2 : 3, [maxWidth])` |
| `Intl.NumberFormat(locale)` driven by `useWidget` `locale` | `formattedNumbers` `useMemo` |
| `Intl.DateTimeFormat(locale, { timeZone })` driven by both `locale` and `timeZone` | `formattedDates` `useMemo` |
| Safe-area inset visualization — `safeArea.insets.{top,right,bottom,left}` | `SafeAreaBox` |
| Host user-agent context display | `User Agent` section |
| `hostInfo`, `hostCapabilities` — display the calling client's identity | `Host` card |
| Server-side parity via `ctx.client.user()` and `ctx.client.info()` | `detect-caller` tool |

## Clusters this complements

- `../16-client-introspection/` — every field surfaced via `useWidget`
- `../18-mcp-apps/widget-react/` — `useWidget` reference
- `../30-workflows/15-i18n-adaptive-widget.md` — workflow derived from this repo

## When to study this repo

- Your widget targets phones, tablets, and desktop and needs different layouts in each.
- You are formatting numbers, currency, dates, or relative times and want to honour the user's locale.
- You need iOS safe-area awareness inside a widget container.
- You want the server to recognise which client is calling so it can vary the response.

## Local run

```bash
gh repo clone mcp-use/mcp-i18n-adaptive
cd mcp-i18n-adaptive
npm install
npm run dev
# Resize the Inspector window — the widget reflows live.
```
