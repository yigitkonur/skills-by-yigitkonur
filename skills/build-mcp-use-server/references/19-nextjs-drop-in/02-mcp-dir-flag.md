# `--mcp-dir` Flag

`--mcp-dir <dir>` is the flag that enables the Next.js drop-in layout. It tells `@mcp-use/cli` where the MCP entry lives and where widget resources live by default.

---

## Where the Flag Works

`@mcp-use/cli@3.1.2` registers `--mcp-dir` on `dev`, `build`, and `start`:

```bash
mcp-use dev   --mcp-dir src/mcp --port 3001
mcp-use build --mcp-dir src/mcp
mcp-use start --mcp-dir src/mcp --port 3001
```

Use the same `--mcp-dir` value across build and start so the build manifest and source entry agree.

---

## Drop-In Flags

| Flag | Purpose |
|---|---|
| `--mcp-dir <dir>` | Folder holding the MCP entry plus `resources/`. Example: `src/mcp`. |
| `--entry <file>` | Explicit entry file relative to project root. Overrides `--mcp-dir` discovery. |
| `--widgets-dir <dir>` | Widgets directory. Defaults to `<mcp-dir>/resources`. |

---

## Entry File Discovery

In `--mcp-dir` mode, `dev` and `build` discover the first existing file in this order:

1. `<mcp-dir>/index.ts`
2. `<mcp-dir>/index.tsx`
3. `<mcp-dir>/server.ts`
4. `<mcp-dir>/server.tsx`

Use `--entry <file>` to override discovery:

```bash
mcp-use dev --mcp-dir src/mcp --entry src/mcp/server.ts
```

`mcp-use start --mcp-dir` can run a source TypeScript entry recorded by `mcp-use build`; when no manifest entry exists it also checks source and `dist/` candidates under the MCP directory.

---

## Where the MCP Code Lives

The canonical convention:

```text
src/mcp/
├── index.ts              # MCP entry; registers tools, calls server.listen()
└── resources/            # Widgets auto-discovered by build/dev
    └── items-widget/
        └── widget.tsx
```

The entry can import shared app code through the host alias:

```typescript
import { MCPServer, text, widget } from "mcp-use/server";
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

await server.listen();
```

---

## Why a Separate `--mcp-dir`?

1. **Disambiguation.** The CLI needs to know which files are the MCP entry and widgets instead of treating the whole Next.js project as the server.
2. **Build hygiene.** In `--mcp-dir` mode, `mcp-use build` skips the standalone esbuild transpile step and records the source entry for `tsx` at start time.

You can put the MCP folder anywhere as long as you pass the same path consistently.

---

## Custom Widget Directory

If widgets live somewhere other than `<mcp-dir>/resources/`:

```bash
mcp-use dev --mcp-dir src/mcp --widgets-dir src/widgets
```

Widget folder names become widget IDs. A widget at `src/widgets/items-widget/widget.tsx` is referenced as `widget: { name: "items-widget" }`.

---

## See Also

- **Why aliases work without configuration** → `03-shared-aliases-and-tailwind.md`
- **What the CLI auto-shims for `next/*`** → `04-server-only-shimming.md`
- **Standalone CLI usage** → `../03-cli/01-overview.md`
