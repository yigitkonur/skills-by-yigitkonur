# Changelog Pointer

The Inspector ships frequently — protocol fixes, OAuth refinements, embed-mode improvements, and dual-protocol widget polish all land on regular minor and patch versions. Always read the canonical changelog before pinning or upgrading.

**Canonical changelog:** [https://manufact.com/docs/inspector/changelog](https://manufact.com/docs/inspector/changelog)

> Source note: the canonical changelog currently tops out at Inspector `v3.0.2`, while `mcp-use@1.26.0` depends on `@mcp-use/inspector` `4.0.0`; treat the package dependency as the install-time source of truth until the changelog catches up.

## Recent versions at a glance

| Version | Theme |
|---|---|
| `v4.0.0` | Published Inspector package paired with `mcp-use` v1.26.0; changelog entry not yet present in the canonical page. |
| `v3.0.2` | E2E coverage update for command-palette Settings. Paired with `mcp-use` v1.25.2. |
| `v3.0.1` | OAuth single-tab redirect, embedded `ChatTab` UI fixes, Hono duck-type detection in `mountInspector`. Paired with `mcp-use` v1.25.1. |
| `v3.0.0` | Inline elicitation in chat thread; rich link previews. Paired with `mcp-use` v1.25.0. |
| `v2.2.0` | First-party LLM providers (Anthropic / OpenAI / Google) — chat no longer depends on LangChain. Copy / Export Chat. Hosted free-tier chat. |
| `v2.1.0` | Theme toggle in MCP Apps debug toolbar; navbar / settings UX rework. |
| `v2.0.0` | Subpath-aware OAuth callbacks for `/inspector` mounts; tab persistence after reload. Paired with `mcp-use` v1.24.0. |

Older versions are listed in full on the canonical page.

## Where to look first

- **OAuth bugs after upgrade** — check `v3.0.1` and `v2.0.0` notes; both touched OAuth flow.
- **Embedded-mode regressions** — `v3.0.1` fixed several `ChatTab` embed leaks.
- **Hono `mountInspector` crashes** — `v3.0.1` switched to duck-typed framework detection.
- **Chat-related changes** — `v2.2.0` rewrote the chat path.
- **Mounted at `/inspector` and OAuth redirects fail** — `v2.0.0` fix.

## Pin strategy

The Inspector tracks `mcp-use` peer-dep versions tightly, but package numbers do not always match. Pin both packages explicitly in `package.json`, then verify `mcp-use`'s `package.json` dependency and the canonical changelog when bumping either. Use `npm outdated mcp-use @mcp-use/inspector` plus the canonical doc to time upgrades.
