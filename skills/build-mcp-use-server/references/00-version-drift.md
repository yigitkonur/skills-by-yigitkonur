# Version Drift Policy

Use this before editing version-sensitive references, CLI command docs, package examples, protocol dates, Inspector notes, or migration claims.

## Source order

Prefer sources in this order when docs disagree:

1. Local `package.json` declarations and lockfile.
2. Installed package declarations under `node_modules`, especially `mcp-use`, `@mcp-use/cli`, `@mcp-use/react`, and `@mcp-use/inspector`.
3. Installed binary help: `mcp-use --help`, `mcp-use <command> --help`, `npx @mcp-use/cli --help`.
4. Package metadata: `npm view mcp-use version`, `npm view @mcp-use/cli version`, `npm view @mcp-use/react version`.
5. Official docs and changelogs.

Package declarations and installed binary help beat stale docs. Official docs still matter for intent and migration notes, but do not override a verified installed API surface.

## Required checks before changing examples

```bash
npm view mcp-use version
npm view @mcp-use/cli version
npm view @mcp-use/react version
npm ls mcp-use @mcp-use/cli @mcp-use/react zod typescript
mcp-use --help
```

If `node_modules` exists, inspect declarations before editing API claims:

```bash
rg "export .*MCPServer|listen\\(|getHandler\\(|proxy\\(" node_modules/mcp-use -g '*.d.ts'
rg "program\\.command|\\.command\\(" node_modules/@mcp-use/cli -g '*.js' -g '*.cjs' -g '*.mjs'
```

## Grep before one-off edits

Never update a single version-specific reference in isolation. First grep for the same value across this skill:

```bash
rg "1\\.26\\.0|3\\.1\\.2|2025-11-25|v1\\.25|@mcp-use/cli" references SKILL.md
```

Update every affected claim or leave a local source note explaining why the claim intentionally differs.

## Tombstone policy

Keep tombstones for non-shipped commands until the installed CLI proves the command exists:

- `03-cli/09-mcp-use-introspect.md`
- `03-cli/10-mcp-use-serve.md`
- `03-cli/11-mcp-use-generate-docs.md`

Do not expand tombstones into fake command docs. Before removing one, verify:

```bash
mcp-use --help
mcp-use introspect --help
mcp-use serve --help
mcp-use generate-docs --help
```

If a future CLI ships one of these commands, update the overview, the tombstone file, every workflow that avoided it, and this policy in the same commit.

## Review posture

- Mark claims grounded in installed package declarations as package-verified.
- Mark claims grounded only in docs as docs-verified and re-check them during maintenance.
- Do not infer a version fix from memory. Verify with package metadata or installed declarations first.
- Prefer `latest` in greenfield package examples unless a version pin is required to document a known behavior.
