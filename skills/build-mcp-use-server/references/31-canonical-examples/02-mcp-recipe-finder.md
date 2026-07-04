# Canonical: `mcp-use/mcp-recipe-finder`

**URL:** https://github.com/mcp-use/mcp-recipe-finder
**Hosted demo:** https://bold-tree-1fe79.run.mcp-use.com/mcp

The schema and middleware reference. The cleanest example of complex Zod schemas, MCP-protocol middleware, prompt registration, completable arguments, and tool annotations — in one server.

## Foundational

One of the three repos to read first. Where `01-mcp-widget-gallery.md` covers widget *shapes*, this one covers *server-side mechanics*.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (top, `server.use(...)` blocks) | HTTP-layer logging middleware (Hono) |
| `index.ts` (`server.use("mcp:tools/call", ...)`) | MCP-operation middleware that wraps every tool call |
| `index.ts` (`recipes` array) | Realistic data shape used across every tool |
| `index.ts` (`search-recipes`, `get-recipe` tool definitions) | Cuisine / dietary / difficulty enums, optional filters, `completable` |
| `index.ts` (resource and prompt registrations) | Recipe catalog as a resource and meal-planning prompt |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| Hono request log: `server.use(async (c, next) => { ... })` | Top of `index.ts` |
| MCP-op middleware: `server.use("mcp:tools/call", async (ctx, next) => { ... })` | Top of `index.ts` |
| Discriminated-enum filters in Zod schemas | `search-recipes` schema |
| `completable(schema, fn)` for argument autocomplete | Recipe-name and ingredient inputs |
| Tool annotations (`readOnlyHint`, `destructiveHint`) | Tool registration objects |
| Prompts: `server.prompt({...}, async (args) => ({ messages: [...] }))` | Meal-planning prompt |
| Resources: `server.resource({...}, async () => ...)` | Recipe catalog |
| `mix(...)` to combine multiple content types in one response | Detail tools |

## Clusters this complements

- `../04-tools/` — tool registration, annotations, completable
- `../06-resources/` — resource registration
- `../07-prompts/` — prompt registration
- `../17-advanced/` — Hono middleware passthrough
- `../15-logging/` — what the middleware is logging

## When to study this repo

- You need a non-trivial Zod schema example (multiple optional filters, enum unions, defaults).
- You are about to add tool annotations and want to see them in context.
- You want to see HTTP-layer and MCP-op middleware side by side.
- You are adding `completable` arguments and need an end-to-end example.

## Local run

```bash
gh repo clone mcp-use/mcp-recipe-finder
cd mcp-recipe-finder
npm install
npm run dev
```
