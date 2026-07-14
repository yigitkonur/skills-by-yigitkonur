# Next.js Drop-In Overview

Colocate an MCP server inside an existing Next.js app: same repo, same `@/*` aliases, same shared components, and the same development env files. Your Next.js routes keep working; `mcp-use dev`, `mcp-use build`, or `mcp-use start` runs the MCP server beside them.

---

## What the Drop-In Is

A `@mcp-use/cli` mode triggered by `--mcp-dir <dir>`. In `mcp-use@1.26.0` this tells the CLI to:

- Auto-discover the MCP entry inside `<dir>`.
- Look for widgets in `<dir>/resources/` unless `--widgets-dir` overrides it.
- Use the host project's `tsconfig.json` for path aliases.
- Build widgets with Vite's `resolve.tsconfigPaths` when a project `tsconfig.json` exists.
- Mirror Next.js development env files into `process.env`.
- Shim `server-only`, `client-only`, `next/cache`, `next/headers`, `next/navigation`, and `next/server` when `next` is present in `package.json`.

---

## Why It Exists

Three problems show up when an MCP server lives inside a Next.js project:

1. **Path aliases.** `@/lib/server-data` resolves through Next.js's `tsconfig.json` paths. The MCP entry and widget build need the same resolution.
2. **Server-runtime modules.** Shared helpers may import `server-only` and `next/headers`; those imports are not usable in a plain Node process unless the CLI shim layer is active.
3. **Env vars.** `.env`, `.env.development`, `.env.local`, and `.env.development.local` are loaded before the server entry runs.

The drop-in handles those automatically when the CLI detects a Next.js project.

---

## Project Layout

```text
my-next-app/
├── package.json
├── tsconfig.json            # "@/*": ["./src/*"]
├── next.config.js
├── src/
│   ├── app/                 # Next.js routes
│   ├── components/          # Shared React components
│   ├── lib/                 # Shared server code imported by tools
│   └── mcp/
│       ├── index.ts         # MCP server entry
│       └── resources/       # Widgets rendered in MCP clients
│           └── items-widget/
│               └── widget.tsx
```

Run the MCP process on a different port from `next dev`:

```bash
mcp-use dev --mcp-dir src/mcp --port 3001
```

---

## Quick Start

In an existing Next.js app with a `src/` layout:

1. **Add MCP-side dependencies.**
   ```bash
   npm install mcp-use zod
   npm install -D @mcp-use/cli
   ```

2. **Create `src/mcp/index.ts`.**
   ```typescript
   import { MCPServer, text } from "mcp-use/server";
   import { z } from "zod";
   import { getGreeting } from "@/lib/server-data";

   const server = new MCPServer({
     name: "nextjs-drop-in-example",
     version: "1.0.0",
   });

   server.tool(
     {
       name: "greet",
       schema: z.object({ name: z.string() }),
     },
     async ({ name }) => text(await getGreeting(name)),
   );

   await server.listen();
   ```

3. **Add scripts to `package.json`.**
   ```json
   {
     "scripts": {
       "dev": "next dev",
       "mcp:dev": "mcp-use dev --mcp-dir src/mcp --port 3001",
       "mcp:build": "mcp-use build --mcp-dir src/mcp",
       "mcp:start": "mcp-use start --mcp-dir src/mcp --port 3001"
     }
   }
   ```

4. **Run both processes.** Use two terminals or a process runner.

---

## Requirements

- A project-root `package.json` with `next` in `dependencies` or `devDependencies`.
- A project-root `tsconfig.json` with the aliases your app uses.
- Widget dependencies resolvable from the project. The official example uses `tailwindcss`, `@tailwindcss/vite`, `@vitejs/plugin-react`, `vite`, `react`, and `react-dom`.

---

## Cluster Map

- **`02-mcp-dir-flag.md`** — what `--mcp-dir` does, entry-file discovery order, and `--entry` / `--widgets-dir` overrides.
- **`03-shared-aliases-and-tailwind.md`** — how `tsconfig` paths, env files, and widget styling are reused.
- **`04-server-only-shimming.md`** — what gets shimmed, what fails loudly, and the widget build-time guardrail.
- **`05-deploying-as-vercel-route.md`** — deployment options and stateless handler considerations.

---

**Canonical doc:** https://manufact.com/docs/typescript/server/nextjs-drop-in
