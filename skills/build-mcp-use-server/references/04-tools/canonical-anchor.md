# Canonical Anchor — `mcp-use/mcp-recipe-finder`

Reference repo for tool registration, Zod schemas, widgets, resources, prompts, middleware, and `outputSchema` examples.

**Repo:** [github.com/mcp-use/mcp-recipe-finder](https://github.com/mcp-use/mcp-recipe-finder)

## Why this one

It exercises the exact surfaces this cluster covers:

- Multiple tools registered with `server.tool(...)`.
- Zod schemas with `.describe()`, `.optional()`, `.default()`, and enums.
- Widget-returning tools that use `widget({ props, output })`.
- A tool that declares `outputSchema`.
- Resource templates with `callbacks.complete`.
- Prompt schemas using `completable()`.

## Load-bearing files

| File | What to look at |
|---|---|
| `index.ts` | Server construction, middleware, tool/resource/prompt registration, Zod schemas, `widget()`, `outputSchema`, `completable()`, and startup. |
| `resources/styles.css` | Shared widget styling for the `recipe-card` resource. |
| `public/icon.svg` | Static asset referenced by server icons. |
| `package.json` | Dependency and script baseline for an official mcp-use example app. |

## Patterns it demonstrates

- **Widget tool shape.** `search-recipes` pairs a Zod input schema with `widget` registration metadata and returns `widget({ props, output: text(...) })`.
- **Typed output caveat.** `get-recipe` declares `outputSchema`, but the handler returns text/markdown without structured output; use package runtime source, not this example, for `outputSchema` enforcement claims.
- **Completion routing.** `recipe_by_id` uses `callbacks.complete`; prompt schemas use `completable()`.

## How to read it

1. Open `index.ts` first — get the full server shape.
2. Read `search-recipes` for schema + widget registration + `widget()` response.
3. Read `get-recipe` for the declared `outputSchema` caveat.
4. Read `recipe_by_id` and `meal-plan` for `callbacks.complete` and `completable()` usage.

Do not copy this repo wholesale. Use it as evidence for how the patterns in this cluster compose into a real server.
