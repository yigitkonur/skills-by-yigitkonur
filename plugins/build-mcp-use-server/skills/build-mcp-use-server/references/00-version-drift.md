# Version Drift Policy

*Read this before editing examples, command docs, or migration guidance, and whenever the user's installed versions differ from what this skill assumes.*

## What this skill is grounded in

This skill documents **mcp-use v2** — the `beta` npm dist-tag line — verified against these exact artifacts (as of 2026-08-02):

| Artifact | Version | Facts verified against |
|---|---|---|
| `mcp-use` | `2.0.0-beta.66` (`beta` tag) | shipped `.d.ts` type contracts |
| `@mcp-use/cli` | `4.0.0-beta.15` (`beta` tag) | shipped package + command dispatch source |
| `create-mcp-use-app` | `2.0.0-beta.14` (`beta` tag) | shipped templates |
| `@mcp-use/inspector` | `20.0.0-beta.58` | inspector docs |
| npm `latest` tag | `1.34.x` — this is **v1**, not what this skill teaches | v1 docs (used in migration references only) |

`npm install mcp-use` without a tag installs **v1**. v2 requires the `beta` tag (or an exact 2.x version). `@mcp-use/react` is not an npm package — react hooks ship inside `mcp-use` at the `mcp-use/react` subpath.

## Precedence when sources disagree

1. The **installed package's `.d.ts`** under the project's `node_modules` — always wins.
2. Installed binary help: `npx @mcp-use/cli --help`, `mcp-use <command> --help`.
3. This skill's references.
4. Published docs (docs.mcp-use.com) — they mix v1 and v2 pages and can lag or lead the shipped beta.

Known documented-but-not-shipped surfaces in `2.0.0-beta.66` (docs describe them; the package does not export them):

- Session stores (`InMemorySessionStore`, `RedisSessionStore`, filesystem storage) — v2 is stateless; see `references/10-sessions/01-overview-stateless-truth.md`.
- Parts of the elicitation helper surface — see `references/12-elicitation/01-overview.md` for what beta.66 actually ships.

## Detecting drift in a real project

Run `scripts/check-mcp-use-version.sh` (usage: `scripts/check-mcp-use-version.sh.md`). It reports installed vs dist-tag versions and classifies the project as v1 or v2 by import shape:

- `from "mcp-use/server"` anywhere → **v1 project**. Route through `references/28-migration/02-v1-to-v2-overview.md` before applying any other reference.
- Root `MCPServer` import, `views/` directory, `mcp-use/oauth/*` imports → **v2 project**. Apply this skill directly.

## When the user's beta is newer than beta.66

Beta releases move fast. If an API in this skill fails to typecheck against the user's installed version, trust the installed `.d.ts`, note the drift in your report, and prefer the nearest equivalent API. Do not silently substitute v1 APIs — v1 and v2 do not mix.
