# `resources/` Folder Conventions

mcp-use auto-discovers widgets from the `resources/` directory at startup. Convention beats configuration: name a directory, drop a `widget.tsx` in it, and the widget is registered.

## Layout

```
my-mcp-app/
├── resources/
│   ├── weather-display/
│   │   ├── widget.tsx              ← entry point (default + widgetMetadata)
│   │   └── components/
│   │       └── WeatherCard.tsx
│   └── product-search/
│       ├── widget.tsx
│       ├── components/
│       │   ├── ProductCard.tsx
│       │   └── Carousel.tsx
│       └── types.ts
├── public/                          ← static assets, served at /mcp-use/public/...
│   └── images/logo.png
├── src/
│   ├── server.ts
│   └── tools/
│       └── weather.ts
├── package.json
└── tsconfig.json
```

## Auto-discovery rules

| Rule | What it means |
|---|---|
| Directory name = widget name | `resources/weather-display/` is the `weather-display` widget. Reference it by that name in `widget.name` on tools. |
| `widget.tsx` is required | Other files in the directory are imported by `widget.tsx` but not auto-registered. |
| Each `widget.tsx` exports `default` (component) and `widgetMetadata` | Without both, registration fails at build time. |
| Nested directories are fine | `components/`, `hooks/`, `types.ts` — anything `widget.tsx` imports. |
| `resources/` must be in `tsconfig.json` `include` | Otherwise types aren't generated. |

## Minimum `widget.tsx`

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propSchema = z.object({ city: z.string(), temperature: z.number() });

export const widgetMetadata: WidgetMetadata = {
  description: "Displays current weather",
  props: propSchema,
};

type Props = z.infer<typeof propSchema>;

const WeatherDisplay: React.FC = () => {
  const { props, isPending } = useWidget<Props>();
  if (isPending) return <div>Loading...</div>;
  return <div>{props.city}: {props.temperature}°C</div>;
};

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <WeatherDisplay />
    </McpUseProvider>
  );
}
```

## Linking widgets to tools

Tools reference widgets by directory name:

```typescript
server.tool(
  {
    name: "get-weather",
    schema: z.object({ city: z.string() }),
    widget: { name: "weather-display" },   // ← directory name
  },
  async ({ city }) => {
    const data = await fetchWeather(city);
    return widget({ props: { city, ...data }, output: text(`...`) });
  }
);
```

If the name doesn't match a discovered directory, mcp-use fails fast at startup with the list of known widget names.

## Overriding auto-discovery with `server.uiResource`

You'd override when:

- You need a non-React HTML widget (no `widget.tsx`).
- You want a custom `htmlTemplate` different from the default.
- You're shipping a `rawHtml` or `remoteDom` resource.

```typescript
server.uiResource({
  type: "mcpApps",
  name: "static-widget",
  htmlTemplate: `<!DOCTYPE html>...`,
  metadata: { /* ... */ },
});
```

When both an auto-discovered `resources/static-widget/widget.tsx` **and** a manual `server.uiResource({ name: "static-widget" })` exist for the same name, the manual registration wins — useful for staging custom builds.

## Public assets

Files under `public/` are served at `${baseUrl}/mcp-use/public/<path>`. Reference them in widgets via the `<Image />` component (path resolution honors `MCPServer({ baseUrl })` / `MCP_URL`):

```tsx
import { Image } from "mcp-use/react";

<Image src="/images/logo.png" alt="Logo" />
```

See `04-baseurl-and-asset-serving.md` for resolution rules.

## What lives where

| Concern | Location |
|---|---|
| Widget React component | `resources/<name>/widget.tsx` (default export) |
| Widget metadata (CSP, props schema, description) | `resources/<name>/widget.tsx` (`widgetMetadata` named export) |
| Helper components | `resources/<name>/components/` (anywhere `widget.tsx` imports) |
| Tool that returns the widget | `src/tools/*.ts` |
| Static assets used by the widget | `public/` |
| Server entry point | `src/server.ts` |

## Anti-patterns

- **Widget logic in `src/`** — Tooling auto-discovers from `resources/`. Putting widget code under `src/` won't register it.
- **Multiple widgets per directory** — One `widget.tsx` per directory. Need two? Make two directories.
- **Importing `useWidget` in non-widget files** — Allowed for helper components if they're rendered inside a widget tree, but never call `useWidget` outside of a `McpUseProvider`.
- **Hardcoded paths in the iframe HTML** — Use `MCP_URL` / `<Image />` so deployments work.
