# `server-only` and `next/*` Shimming

The CLI shims Next.js server-runtime modules so MCP tools can import shared `src/lib/*` helpers. Widgets are different: they run in a browser iframe and are blocked from importing those modules at build time.

---

## 1. The Problem

The official drop-in example has shared server code like this:

```typescript
import "server-only";
import { headers } from "next/headers";

export async function getGreeting(name: string): Promise<string> {
  const h = await headers();
  const ua = h.get("user-agent") ?? "unknown";
  return `Hello, ${name}! (ua: ${ua})`;
}
```

Without shims, importing that helper from a plain MCP server process can fail before the tool runs.

---

## 2. What the Drop-In Shims

When the CLI detects `next` in the host `package.json`, it installs runtime shims for these exact specifiers:

| Module | Stub behavior |
|---|---|
| `server-only` | No-op module. |
| `client-only` | No-op module. |
| `next/cache` | `revalidatePath()` and `revalidateTag()` no-op; `unstable_cache(fn)` returns `fn`; `unstable_noStore()`, `unstable_cacheLife()`, and `unstable_cacheTag()` no-op. |
| `next/headers` | `headers()` returns empty `Headers`; `cookies()` returns an empty cookie store; `draftMode()` returns disabled state. |
| `next/navigation` | `redirect()`, `permanentRedirect()`, and `notFound()` throw outside Next.js. |
| `next/server` | Minimal `NextResponse`, `NextRequest`, and `userAgent()` stubs. |

Shims run on both module sides:

- ESM: via Node `module.register()` through `next-shims-register.mjs`.
- CJS: via a `Module._resolveFilename` patch in `next-shims-cjs.cjs`.

---

## 3. Tool Import Pattern

Read server-only data in the MCP tool, then return it through a normal helper:

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
import { getGreeting } from "@/lib/server-data";

const server = new MCPServer({ name: "nextjs-drop-in-example", version: "1.0.0" });

server.tool(
  {
    name: "greet",
    schema: z.object({ name: z.string() }),
  },
  async ({ name }) => text(await getGreeting(name)),
);
```

The shimmed `headers()` is empty in the MCP process, so shared helpers must handle missing request metadata.

---

## 4. What Fails Loudly

`redirect()`, `permanentRedirect()`, and `notFound()` still throw. Do not reuse Next.js route helpers that redirect or render a Next.js response from inside MCP tools unless the tool catches and translates that failure.

Preferred split:

| Code path | Allowed imports |
|---|---|
| Next.js route/page helpers | Full Next.js runtime APIs. |
| Shared library helpers called by MCP tools | Data access and pure logic; tolerate empty `headers()` / `cookies()`. |
| Widgets | Browser-safe React only; no `server-only` or `next/*` server modules. |

---

## 5. Widget Build-Time Guard

The widget build rejects the same server-runtime specifiers:

```text
Widget "items-widget" imports "next/headers" (...), which is a Next.js server-only module.
Widgets run in a browser iframe and cannot use server APIs.

To fix:
  - Remove the import from the widget or any transitive module.
  - Read the data inside an MCP tool and pass it through widget props.
```

This guard is implemented as a Vite plugin named `mcp-use-widget-server-only-guard`.

---

## 6. Read on Server, Pass via Props

```typescript
import { MCPServer, widget } from "mcp-use/server";
import { z } from "zod";
import { getGreeting, sampleItems } from "@/lib/server-data";

const server = new MCPServer({ name: "nextjs-drop-in-example", version: "1.0.0" });

server.tool(
  {
    name: "show-items",
    schema: z.object({ name: z.string().default("world") }),
    widget: { name: "items-widget" },
  },
  async ({ name }) =>
    widget({
      props: {
        greeting: await getGreeting(name),
        items: sampleItems,
      },
      message: `Rendered ${sampleItems.length} items for ${name}.`,
    }),
);
```

Widgets receive `props` with `useWidget()` and stay browser-only.

---

## 7. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Calling `redirect()` from an MCP tool | Throws outside Next.js | Return `error()` or branch before calling the redirecting helper |
| Importing a server-only module from a widget | Build fails | Move the read into the MCP tool |
| Treating shimmed `cookies()` as a real request cookie jar | The shim is empty | Use OAuth-backed `ctx.auth` for verified identity |
| Writing local shim files for `next/*` | Duplicates CLI behavior | Let `@mcp-use/cli` install its shims |

---

## 8. See Also

- **OAuth identity (`ctx.auth`) instead of cookies** → `../11-auth/01-overview-decision-matrix.md`
- **Aliases that make shared imports work** → `03-shared-aliases-and-tailwind.md`
- **Per-call client info** → `../16-client-introspection/01-overview.md`
