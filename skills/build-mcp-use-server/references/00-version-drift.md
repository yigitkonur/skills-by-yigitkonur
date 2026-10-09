# Version Drift Policy

*Read this before editing examples, command docs, or migration guidance, and whenever the user's installed versions differ from what this skill assumes.*

## What this skill is grounded in

This skill documents **mcp-use v2** — the stable production line published on npm `latest` — verified against these exact upstream artifacts:

| Artifact | Version | Facts verified against |
|---|---|---|
| `mcp-use` | `2.8.1` (`latest` tag) | shipped `.d.ts` type contracts and runtime source |
| `@mcp-use/cli` | `4.3.1` (`latest` tag) | shipped package + command dispatch source |
| `create-mcp-use-app` | `2.0.10` (`latest` tag) | shipped templates |
| `@mcp-use/inspector` | `20.3.17` (`latest` tag) | official inspector runtime |
| npm `legacy-v1` tag | `1.34.6` (maintenance) | v1 legacy maintenance only |

`npm install mcp-use` installs **v2** (`latest`). v1 is legacy maintenance (`legacy-v1` tag). `@mcp-use/react` is not an npm package — React hooks ship inside `mcp-use` at the `mcp-use/react` subpath.

## Precedence when sources disagree

1. The **installed package's `.d.ts`** under the project's `node_modules` — always wins.
2. Installed binary help: `npx @mcp-use/cli --help`, `mcp-use <command> --help`.
3. This skill's references.
4. Published docs (docs.mcp-use.com) — official documentation for v2.

Core framework invariants in `2.8.1`:

- **Stateless core:** v2 is stateless per request. Cross-request state uses `requestState` or an external store.
- **Skills over MCP (SEP-2640):** Conventional `skills/` directory discovery and `MCPServer({ skills: true | false | { directory } })`.
- **Mixed Authentication (v2.7.0):** `mixedAuth: true` on `MCPServer` enables public discovery and per-tool `securitySchemes` (`noauth` vs `oauth2`).
- **Interactive Elicitation:** `ctx.elicit(key, message, schemaOrUrl)` is a first-class convenience method alongside `inputRequired()`, `inputResponse()`, and `acceptedContent()`.
- **ChatGPT Extensions (v2.8.0):** Typed `view.entrypoints` (`global`, `thread`, `file`), native `server.settings()`, and `tool.icons`.
- **Cancellation:** `ToolCancelledError` from `mcp-use/react` is raised when the host aborts tool execution.

## Detecting drift in a real project

Run `scripts/check-mcp-use-version.sh` (usage: `scripts/check-mcp-use-version.sh.md`). It reports installed vs dist-tag versions and classifies the installed `mcp-use` package as v1 or v2 by its `package.json` exports map:

- A `"./server"` export key present → **v1 package**. Route through `references/28-migration/02-v1-to-v2-overview.md` before applying any other reference.
- ESM-only (`"type": "module"`) with a root `MCPServer` export and no `"./server"` key → **v2 package**. Apply this skill directly.

The same signal, read from source instead of imports: a `views/` directory or `mcp-use/oauth/*` imports in the project are v2-only conventions and are further evidence (not the primary check) that a project targets v2.
