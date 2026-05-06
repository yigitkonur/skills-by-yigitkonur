# Shared Aliases and Tailwind

Path aliases, env files, and widget styling reuse come from the host Next.js project. Do not duplicate Next.js configuration inside `src/mcp/`.

---

## 1. Path Aliases

Define aliases once in the host app's `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

The CLI uses that project config in two places:

| Pipeline | Resolver |
|---|---|
| MCP server (`mcp-use dev` / `start`) | `tsx` with `TSX_TSCONFIG_PATH` or explicit tsx registration |
| Widget bundler (`mcp-use build` / `dev`) | Vite `resolve: { tsconfigPaths: true }` when `tsconfig.json` exists |

Result: the MCP entry can import `@/lib/server-data`, and a widget can import `@/components/card`, using the same `@/*` mapping as the Next.js app.

---

## 2. Environment Variables

When the CLI detects `next` in `package.json`, it loads this development cascade before importing the MCP entry:

```text
.env
.env.development
.env.local
.env.development.local
```

Later files override earlier files. This is implemented in the CLI's `loadNextJsEnvFiles(projectPath)`.

Do not document a production `.env.production` cascade for `mcp-use@1.26.0`; the published CLI's Next.js loader only lists the development files above.

---

## 3. Tailwind Reuse

The widget build writes a temporary stylesheet with:

```css
@import "tailwindcss";
@source "<resources-dir>";
@source "<project>/node_modules/mcp-use/**/*.{ts,tsx,js,jsx}";
@source "<project>/src";
```

It then runs Vite with `@tailwindcss/vite`, `@vitejs/plugin-react`, and Vite's tsconfig-path resolver. The official nextjs-drop-in example includes these widget build dependencies in the app:

```json
{
  "dependencies": {
    "@tailwindcss/vite": "^4.2.0",
    "@vitejs/plugin-react": "^6.0.0",
    "tailwindcss": "^4.2.0",
    "mcp-use": "workspace:*",
    "vite": "^8.0.5"
  }
}
```

---

## 4. Component Reuse

The official example proves shared component reuse with `@/components/card`:

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import React from "react";
import { z } from "zod";
import { Card } from "@/components/card";

const propSchema = z.object({
  greeting: z.string(),
  items: z.array(z.object({ id: z.number(), label: z.string() })),
});

export const widgetMetadata: WidgetMetadata = {
  description: "Renders items using a shared card component.",
  props: propSchema,
  exposeAsTool: false,
};

type ItemsProps = z.infer<typeof propSchema>;

function ItemsDisplay() {
  const { props } = useWidget<ItemsProps>();
  return (
    <Card title="Items">
      <p>{props.greeting}</p>
      <ul>
        {(props.items ?? []).map((item) => (
          <li key={item.id}>{item.label}</li>
        ))}
      </ul>
    </Card>
  );
}

export default function ItemsWidget() {
  return (
    <McpUseProvider>
      <ItemsDisplay />
    </McpUseProvider>
  );
}
```

Any component imported into a widget must be browser-safe. If it imports `server-only` or `next/headers`, the widget build fails; move that data read into an MCP tool and pass the result through `widget({ props })`.

---

## 5. What Does Not Get Inherited

| Asset | Inherited? | Notes |
|---|---|---|
| `tsconfig.json` paths | yes | server and widgets |
| Next.js dev env files | yes | server process only |
| Tailwind sources under `src/` | yes | widget build only |
| `next.config.js` rewrites / headers | no | applies to Next.js HTTP, not the MCP server |
| `middleware.ts` | no | runs in Next.js, not in the MCP transport |
| Server actions | no | call shared library code from MCP tools instead |

If you need middleware on the MCP server, use `server.use(...)` on the `MCPServer` instance; see `../08-server-config/05-middleware-and-custom-routes.md`.

---

## 6. See Also

- **What `--mcp-dir` does** → `02-mcp-dir-flag.md`
- **Why widgets can't import server-only modules** → `04-server-only-shimming.md`
- **Custom middleware and routes** → `../08-server-config/05-middleware-and-custom-routes.md`
