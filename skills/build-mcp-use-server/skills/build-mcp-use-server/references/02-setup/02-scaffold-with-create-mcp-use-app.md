# Scaffold with `create-mcp-use-app`

Use the scaffolder to get a working server with HMR, the Inspector, and example tools/resources/widgets pre-wired.

## Run

```bash
npx create-mcp-use-app@latest my-mcp-server
cd my-mcp-server
npm install
npm run dev
```

Alternative package managers:

```bash
pnpm create mcp-use-app@latest my-mcp-server
yarn create mcp-use-app@latest my-mcp-server
```

The dev server boots at `http://localhost:3000` with the Inspector at `/inspector` and the MCP endpoint at `/mcp`.

## What gets generated

The default (`starter`) template produces:

```
my-mcp-server/
├── resources/                     # React widgets (MCP Apps + ChatGPT)
│   └── product-search-result/
│       ├── widget.tsx             # Widget entry point
│       ├── components/            # Sub-components
│       └── types.ts
├── public/                        # Static assets (icons, favicon)
│   ├── icon.svg
│   └── favicon.ico
├── index.ts                       # MCP server entry point (root, not src/)
├── package.json
├── tsconfig.json
├── README.md
└── .mcp-use/                      # Auto-populated on dev/build
    └── tool-registry.d.ts
```

The entry file is `index.ts` at the project root — not `src/server.ts`. `npm run dev` resolves the entry from this default.

## What it includes out of the box

- `mcp-use`, `zod`, `@mcp-use/cli` already installed.
- A pre-configured `MCPServer` with `name`, `title`, `icons`, `websiteUrl` derived from the project name.
- Example tool and resource registrations.
- An example React widget exposed as a tool (when widgets are enabled by the template).
- HMR for tools, resources, prompts, and widgets.
- Auto-launched MCP Inspector in the browser.

## Useful flags

```bash
npx create-mcp-use-app@latest my-server --template starter
npx create-mcp-use-app@latest my-server --template mcp-apps --no-skills
```

See `03-template-flags.md` for the full template matrix.

## Where to look next

| Goal | Read |
|---|---|
| Pick a different template | `03-template-flags.md` |
| Skip scaffolder, write a stdio server | `04-manual-stdio-server.md` |
| Skip scaffolder, write an HTTP server | `05-manual-http-server.md` |
| Add MCP to an app you already own | `06-add-to-existing-app.md` |
| Wire scripts in `package.json` | `07-package-scripts.md` |
| Configure `tsconfig.json` and types | `08-tsconfig-and-types.md` |
| Write your first tool | `04-tools/01-overview.md` |
| Verify the scaffold builds | `npm run build && npx mcp-use generate-types` |
