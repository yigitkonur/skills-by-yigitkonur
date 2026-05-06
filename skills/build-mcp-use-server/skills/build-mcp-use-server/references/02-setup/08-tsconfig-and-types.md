# `tsconfig.json` and Generated Types

The TypeScript settings that keep `mcp-use/server` ESM resolution working, plus the workflow for the auto-generated tool registry.

## Required `compilerOptions`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*", ".mcp-use/**/*"]
}
```

`module: NodeNext` / `moduleResolution: NodeNext` is also valid and works on modern Node.

## Why each option matters

| Option | Reason |
|---|---|
| `target: ES2022` | Top-level `await`, class fields, native error causes. |
| `module: Node16` (or `NodeNext`) | Honours `mcp-use`'s package `exports` map; `CommonJS` cannot resolve `mcp-use/server`. |
| `moduleResolution: Node16` | Same — ESM-aware resolution. |
| `strict: true` | Prevents `any` leaks in tool args; tool handlers stay type-safe. |
| `esModuleInterop: true` | Cleaner default-import syntax for CJS deps. |
| `skipLibCheck: true` | Skips `node_modules` types — speeds compile, avoids upstream type clashes. |
| `resolveJsonModule: true` | Lets you `import pkg from "../package.json"`. |

Project root (scaffolded) projects use `index.ts` at the root, not `src/index.ts`. Adjust `include`:

```json
{
  "include": ["index.ts", "resources/**/*", ".mcp-use/**/*"]
}
```

## With React widgets

Widgets need JSX support and the `resources/` folder included:

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "lib": ["ES2022", "DOM", "DOM.Iterable"]
  },
  "include": ["index.ts", "src/**/*", "resources/**/*", ".mcp-use/**/*"]
}
```

## Generated types — `.mcp-use/tool-registry.d.ts`

`mcp-use generate-types` scans tool registrations, converts Zod schemas to TypeScript types, and writes:

```
.mcp-use/
└── tool-registry.d.ts
```

This file powers:

| Consumer | What it gets |
|---|---|
| Widget code calling `useCallTool("foo")` | Argument types and return types inferred from the tool's Zod schema. |
| `generateHelpers<ToolRegistry>()` from `mcp-use/react` | Typed hooks per tool. |
| Editor IntelliSense in widget files | Auto-completion on tool names, args, results. |

`mcp-use dev` regenerates types automatically on schema changes. Run the command manually for CI or after pulling schema changes:

```bash
npx mcp-use generate-types
npx mcp-use generate-types --server src/server.ts   # custom entry
```

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot find module 'mcp-use/server'` | `moduleResolution` not `Node16`/`NodeNext` | Update `tsconfig.json`. |
| `SyntaxError: Unexpected token 'export'` at runtime | Missing `"type": "module"` in `package.json` | Add it. |
| Widget hooks have `any` for tool args | `.mcp-use/` excluded or types not generated | Run `mcp-use generate-types`; ensure `include` covers `.mcp-use/**/*`. |
| Type generation never updates | Server entry mismatch | Pass `--server <file>` matching the actual entry. |

## When to regenerate

| Event | Action |
|---|---|
| Edited a tool's Zod schema | Auto in dev; run `generate-types` manually in CI. |
| Renamed a tool | Same as above. |
| Added a new tool | Same as above. |
| Pulled new schemas from main | Run `generate-types` before `tsc --noEmit`. |
| Widget hooks show stale types | Run `generate-types` and restart the editor TS server. |

## See also

- `03-cli/07-mcp-use-generate-types.md` — full CLI flag reference.
- `04-tools/03-zod-schemas.md` — schema patterns the generator understands.
