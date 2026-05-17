# Package Scripts

The canonical script set for an `mcp-use` server. Keep names stable across templates so CI, deploy hooks, and skill instructions all agree.

## Canonical `scripts` block

```json
{
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "deploy": "mcp-use deploy",
    "generate-types": "mcp-use generate-types",
    "typecheck": "tsc --noEmit"
  }
}
```

Pass an entry file when the entry isn't `index.ts` at the project root:

```json
{
  "scripts": {
    "dev": "mcp-use dev src/server.ts",
    "generate-types": "mcp-use generate-types --server src/server.ts"
  }
}
```

## What each script does

| Script | Wraps | Effect |
|---|---|---|
| `dev` | `mcp-use dev` | TypeScript watch + widget HMR + Inspector at `/inspector`, MCP at `/mcp`. Auto-runs `generate-types`. |
| `build` | `mcp-use build` | Compiles TS, bundles widgets, emits `dist/` and `dist/mcp-use.json` manifest. |
| `start` | `mcp-use start` | Runs the built server from `dist/`. Reads `dist/mcp-use.json` for the entry. |
| `deploy` | `mcp-use deploy` | Ships the build to Manufact Cloud (requires `mcp-use login`). |
| `generate-types` | `mcp-use generate-types` | Regenerates `.mcp-use/tool-registry.d.ts` from Zod tool schemas. |
| `typecheck` | `tsc --noEmit` | Pure type-checking. Safe to run in CI without producing artifacts. |

Detailed flags for each command live in `03-cli/`.

## Why the script names matter

| Name | Used by |
|---|---|
| `dev` | Inspector docs, README, all skill examples assume `npm run dev`. |
| `build` | `mcp-use deploy` and `mcp-use start` both expect `dist/` produced by `build`. |
| `start` | `mcp-use deploy` runs `start` on the cloud runner. |
| `deploy` | Stable name for the cloud deploy entry point. |
| `generate-types` | Skill snippets, CI checks, `useCallTool` typed-hook flow. |

Renaming any of these breaks tooling and other docs that reference them. Use the canonical names.

## Optional helpers

| Script | When to add |
|---|---|
| `lint` | Project uses ESLint / Biome. |
| `clean` | `rimraf dist .mcp-use/tool-registry.d.ts` for fresh rebuilds. |
| `dev:tunnel` | `mcp-use dev --tunnel` for ChatGPT widget testing. |

Avoid duplicating the canonical names with prefixes (`run-dev`, `mcp:dev`) — prefer the bare canonical script names.

## CI shape

```bash
npm ci
npm run typecheck
npm run build
npm run generate-types -- --server src/server.ts
```

`generate-types` runs implicitly during `mcp-use dev`, but in CI run it explicitly to fail loudly when schemas drift.

## See also

- `08-tsconfig-and-types.md` — `tsconfig` settings and where `tool-registry.d.ts` lives.
- `03-cli/` — full per-command CLI reference.
- `25-deploy/` — `deploy` flags and cloud-side behavior.
