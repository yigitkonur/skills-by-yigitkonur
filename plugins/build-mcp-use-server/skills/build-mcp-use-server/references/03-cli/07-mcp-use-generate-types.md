# `mcp-use generate-types`

Regenerates `.mcp-use/tool-registry.d.ts` from your tool Zod schemas. Auto-runs during `mcp-use dev`; run manually for CI, after pulling schema changes, or to debug type drift.

## Usage

```bash
mcp-use generate-types [options]
```

## Flags

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--server <file>` | Server entry file | `index.ts` |

## What it does

1. Loads the server entry file.
2. Reads `server.registrations.tools`.
3. Converts tool Zod schemas to TypeScript types.
4. Writes `.mcp-use/tool-registry.d.ts`.

## Output consumers

| Consumer | What it gains |
|---|---|
| Widget code calling `useCallTool("foo")` from `mcp-use/react` | Typed args + return values for tool `foo` |
| `generateHelpers<ToolRegistry>()` | Per-tool typed hooks |
| Editor IntelliSense in widget files | Auto-completion on tool names and arg shapes |

## Typed hook wiring

```tsx
import { generateHelpers } from "mcp-use/react";
import type { ToolRegistry } from "../.mcp-use/tool-registry";

const { useCallTool } = generateHelpers<ToolRegistry>();
```

For the full widget side, route to `../18-mcp-apps/`.

## Sync checklist

1. Edit a Zod schema.
2. `server.listen()` in development regenerates automatically — or run `mcp-use generate-types` manually.
3. Restart the editor TS server if widget hooks still show stale types.

## Required `tsconfig.json` include

```json
{
  "include": ["index.ts", "src/**/*", "resources/**/*", ".mcp-use/**/*"]
}
```

Without `.mcp-use/**/*`, the generated types are invisible to TypeScript. See `../02-setup/08-tsconfig-and-types.md`.

## Examples

```bash
mcp-use generate-types
mcp-use generate-types -p ./packages/api
mcp-use generate-types --server src/server.ts
```

## When to run manually

| Trigger | Action |
|---|---|
| CI pipeline | Run as a step before `tsc --noEmit` to catch schema drift |
| After `git pull` brings new schemas | Run before opening the project in editor |
| Widget hooks show `any` | Run; if still `any`, check `--server` matches actual entry |
| Renamed a tool | Run; old entries disappear when the registry file is regenerated |

## Anti-pattern

Excluding `.mcp-use/` from `tsconfig.json` and then wondering why widget hooks lack types. Add the path; don't paper over the absence with manual `as any` casts.

## See also

- `../02-setup/08-tsconfig-and-types.md` — required include path
- `../04-tools/03-zod-schemas.md` — schema patterns the generator handles
- `04-mcp-use-build.md` — production build also regenerates types unless `--no-typecheck`
