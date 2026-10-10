# Version Drift Policy

*Read this before editing examples, command docs, or migration guidance, and whenever the user's installed versions differ from what this skill assumes.*

## What this skill is grounded in

This skill documents **mcp-use v2** — the stable production line published on npm `latest` — verified against these exact upstream artifacts:

| Artifact | Version | Facts verified against |
|---|---|---|
| `mcp-use` | `2.8.2` (`latest` tag) | shipped `.d.ts` type contracts and runtime source (Node >= 22.22.2) |
| `@mcp-use/cli` | `4.3.2` (`latest` tag) | shipped package + command dispatch source |
| `create-mcp-use-app` | `2.0.10` (`latest` tag) | shipped templates |
| `@openai/apps-sdk-ui` | `0.2.2` (`latest` tag) | official design system, 29+ Radix components, Tailwind 4 tokens |
| `@mcp-use/inspector` | `20.3.18` (`latest` tag) | official inspector runtime |
| npm `v1-legacy` tag | `1.34.8` (maintenance) | v1 legacy maintenance only |

`npm install mcp-use` installs **v2** (`latest`). v1 is legacy maintenance (`v1-legacy` tag). `@mcp-use/react` is not an npm package — React hooks ship inside `mcp-use` at the `mcp-use/react` subpath. All ChatGPT apps require `@openai/apps-sdk-ui` by default for UI compliance. Node.js engine requirement is **>= 22.22.2**.

## Precedence when sources disagree

1. The **installed package's `.d.ts`** under the project's `node_modules` — always wins.
2. Installed binary help: `npx @mcp-use/cli --help`, `mcp-use <command> --help`.
3. This skill's references.
4. Published docs (docs.mcp-use.com) — official documentation for v2.

Core framework invariants in `2.8.1`:

- **Stateless core:** v2 is stateless per request. Cross-request state uses `requestState` or an external store.
- **Skills over MCP (SEP-2640):** Conventional `skills/` directory discovery and `MCPServer({ skills: true | false | { directory } })`.
- **Mixed Authentication (v2.7.0):** `mixedAuth: true` on `MCPServer` enables public discovery and per-tool `securitySchemes` (`noauth` vs `oauth2`).
- **Interactive Elicitation:** `ctx.elicit()` was removed in v2.4.3 (#2409); elicitation is handled via returning `inputRequired({ inputRequests: { [key]: inputRequired.elicit(...) } })`, and reading subsequent responses with `inputResponse(ctx.inputResponses, key)` and `acceptedContent()`.
- **ChatGPT Extensions (v2.8.0):** Typed `view.entrypoints` (`global`, `thread`, `file`), native `server.settings()`, and `tool.icons`.
- **Cancellation:** `ToolCancelledError` from `mcp-use/react` is raised when the host aborts tool execution.

## Detecting drift in a real project

Run `scripts/check-mcp-use-version.sh` (usage: `scripts/check-mcp-use-version.sh.md`). It reports installed vs dist-tag versions and classifies the installed `mcp-use` package as v1 or v2 by its `package.json` exports map:

- A `"./server"` export key present → **v1 package**. Route through `references/28-migration/02-v1-to-v2-overview.md` before applying any other reference.
- ESM-only (`"type": "module"`) with a root `MCPServer` export and no `"./server"` key → **v2 package**. Apply this skill directly.

The same signal, read from source instead of imports: a `views/` directory or `mcp-use/oauth/*` imports in the project are v2-only conventions and are further evidence (not the primary check) that a project targets v2.
