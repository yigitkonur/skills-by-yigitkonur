# skills-by-yigitkonur

Skills for AI coding agents — review, research, UI/UX audit, MCP & framework builders, browser/device automation, design extraction, config files, publish. One combined pack, **45 skills**, organized under the 12-verb naming registry (see [NAMING.md](NAMING.md)).

> Previously split into a main pack and a `-secondary` b-side. **They're now merged here** — one repo, one install surface. The old secondary repo is archived and redirects here.

## Install

Two ways to install. **Both read from this one repo** — pick whichever fits your workflow.

### 1. As Claude Code plugins (easy install / uninstall via `/plugin`)

Add the marketplace once:

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
```

Then install exactly what you want — a single skill, a themed bundle, or everything — and remove it just as easily:

```
/plugin install run-review@yigitkonur         # one skill
/plugin install yk-mcp@yigitkonur             # a themed bundle
/plugin install yk-everything@yigitkonur      # the whole pack
/plugin uninstall run-review@yigitkonur       # gone
```

Browse and toggle every plugin interactively with `/plugin`. Each **per-skill** plugin is named after the skill (`<skill-name>@yigitkonur`); **bundles** are the `yk-*` names in the table below.

### 2. With the `skills` CLI

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur                      # full pack
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>  # single skill
```

Per-skill one-liners live in each skill's `INSTALL.md`.

---

## Bundles

Themed groups for one-shot installs. Every skill also installs individually — see the sections below.

| Bundle | Skills | Install |
|---|---|---|
| **yk-everything** | all 45 | `/plugin install yk-everything@yigitkonur` |
| **yk-review** | review, codex-review-loop, completion audit, runtime debug | `/plugin install yk-review@yigitkonur` |
| **yk-frontend** | url→next.js, design.md, UI/UX/Laws-of-UX audits | `/plugin install yk-frontend@yigitkonur` |
| **yk-mcp** | build/audit/test/convert MCP servers, clients, CLIs | `/plugin install yk-mcp@yigitkonur` |
| **yk-build** | chrome, effect-ts, kernel, langchain, macos, raycast, tinacms | `/plugin install yk-build@yigitkonur` |
| **yk-research** | research, deep-research, github-scout, bulk-search (+ researcher agents) | `/plugin install yk-research@yigitkonur` |
| **yk-automation** | agent-browser, android control, tailscale funnel | `/plugin install yk-automation@yigitkonur` |
| **yk-config** | AGENTS/CLAUDE/REVIEW files, drift audit, Makefiles | `/plugin install yk-config@yigitkonur` |
| **yk-ops** | railway, repo-cleanup, babysitter, linear, offload, vercel, npm publish | `/plugin install yk-ops@yigitkonur` |
| **yk-skills** | build-skill, derailment stress-test | `/plugin install yk-skills@yigitkonur` |

---

## 🏗️ Build apps & frameworks

Write application code with a specific framework or SDK.

- **[build-chrome-extension](skills/build-chrome-extension/)** — Chrome MV3: manifest v3, service_worker, content_scripts, popup, side_panel, declarativeNetRequest, Web Store packaging.
- **[build-effect-ts-v3](skills/build-effect-ts-v3/)** — Effect-TS v3: `Effect.gen`, `Layer`, `Schema`, typed errors, fibers, `Stream`.
- **[build-kernel-ts-sdk](skills/build-kernel-ts-sdk/)** — Kernel SDK (`@onkernel/sdk`): browsers, Apps, profiles, Managed Auth, pools, Playwright/CDP wiring.
- **[build-langchain-ts-app](skills/build-langchain-ts-app/)** — LangChain.js: agents, tool-calling, RAG retrievers, structured output, streaming, LangGraph `StateGraph`.
- **[build-macos-app](skills/build-macos-app/)** — SwiftUI/AppKit: HIG, Liquid Glass, snapshot validation, SwiftLint hooks, Convex+Clerk sync.
- **[build-raycast-script-command](skills/build-raycast-script-command/)** — Raycast Script Commands (`.sh`/`.py` with `@raycast.*` metadata): fields, modes, arguments, discovery.
- **[build-tinacms-nextjs](skills/build-tinacms-nextjs/)** — TinaCMS + Next.js App Router: `tina/config.ts`, MDX/git content, schema modeling, `useTina` visual editing, deploys.

`/plugin install yk-build@yigitkonur`

---

## 🔌 MCP & agent interfaces

Build, test, convert, and audit MCP servers, clients, and agent-facing CLIs.

- **[build-mcp-server-sdk-v1](skills/build-mcp-server-sdk-v1/)** — MCP server on `@modelcontextprotocol/sdk` v1.x: single-package, Zod, `McpServer`.
- **[build-mcp-server-sdk-v2](skills/build-mcp-server-sdk-v2/)** — MCP server on `@modelcontextprotocol/server` v2 alpha: split packages, `registerTool`, `ctx.mcpReq`.
- **[build-mcp-use-server](skills/build-mcp-use-server/)** — mcp-use/server: `server.tool`, response helpers, `ctx.auth`, sessions, transports, widgets, Inspector, deploy.
- **[build-mcp-use-client](skills/build-mcp-use-client/)** — mcp-use client: `MCPClient`, `MCPSession`, `useMcp`, `mcp-use/react`, browser transport.
- **[build-mcp-use-agent](skills/build-mcp-use-agent/)** — mcp-use `MCPAgent`: LLM picks & orchestrates MCP tools via `run`, `stream`, `streamEvents`.
- **[build-clean-mcp-architecture](skills/build-clean-mcp-architecture/)** — Clean Architecture layer boundaries for TypeScript mcp-use/server code, import direction, dependency-cruiser gates.
- **[convert-mcp-sdk-v1-to-v2](skills/convert-mcp-sdk-v1-to-v2/)** — Port a v1 MCP server to the v2 split-package SDK: package renames, `ServerContext`, Zod v4.
- **[test-by-mcpc-cli](skills/test-by-mcpc-cli/)** — Drive the `mcpc` CLI (0.2.x) to test/debug/smoke-check an MCP server over stdio or Streamable HTTP.
- **[audit-agentic-mcp](skills/audit-agentic-mcp/)** — Audit an MCP server for agent-readiness, or design a new one before code: framework, security, context posture.
- **[audit-agentic-cli](skills/audit-agentic-cli/)** — Audit/design a CLI for agent consumption: stable JSON, exit codes, non-interactive flags, repair loops.

`/plugin install yk-mcp@yigitkonur`

---

## ⚙️ Config & instruction files

Generate or refresh config / instruction files that another tool consumes.

- **[init-agent-config](skills/init-agent-config/)** — AGENTS.md / CLAUDE.md / REVIEW.md hierarchies; folder-scoped guidance; native review adapters.
- **[init-makefiles](skills/init-makefiles/)** — Scaffold safe scenario Makefiles (local dev, tunnels, deploys, R2 sync, Supabase, Railway, Vercel, Mac shipping).
- **[update-agent-config](skills/update-agent-config/)** — Audit AGENTS.md / CLAUDE.md / REVIEW.md for drift after refactors; refresh refs, recount frequency tables, fill gap folders.

`/plugin install yk-config@yigitkonur`

---

## 🎨 Frontend rebuild & audit

Rebuild a live site, extract its design, or audit a running UI/UX.

- **[convert-url-to-nextjs](skills/convert-url-to-nextjs/)** — Rebuild a deployed site AS-IS pixel-faithful as a Next.js project from a live URL — the "we lost the frontend repo" recovery. L0+L1 crawl + back-to-back agent-browser verification.
- **[create-design-md](skills/create-design-md/)** — Produce a `design.md` spec (Google Labs DESIGN.md) plus per-asset `references/` tree from a live URL, codebase, or HTML snapshot.
- **[audit-ux-laws](skills/audit-ux-laws/)** — Audit UI against the 30 Laws of UX (Fitts's, Hick's, Miller's, Jakob's, Gestalt, choice overload, cognitive load) with CRITICAL/MINOR severity and code fixes.
- **[audit-ui-and-save-files](skills/audit-ui-and-save-files/)** — Visual UI audit across pages/viewports with browser screenshots, per-bug findings to `css-issues/[YY-MM-DD]/...`, ending with an approval-gated fix-subagent plan.
- **[audit-ux-and-save-files](skills/audit-ux-and-save-files/)** — Usability audit from real personas walking their journeys, per-issue findings to `ux-findings/[YY-MM-DD]/...`, ending with a prioritized recommendations report (reports, does not fix).

`/plugin install yk-frontend@yigitkonur`

---

## 📝 Review & debug

Evaluate a change for merge-readiness, triage feedback, verify "done", and chase runtime bugs.

- **[run-review](skills/run-review/)** — One entry point, four modes: (A) do a PR/branch review, (B) open your branch as a self-review PR, (C) triage received feedback, (D) delegate to `codex review`.
- **[run-codex-review-loop](skills/run-codex-review-loop/)** — Native `codex exec review` across multiple branches; compare findings; rescue a saved branch-review loop.
- **[audit-completion](skills/audit-completion/)** — Audit task / session / plan / branch completion claims with evidence; remediate to terminal status.
- **[debug-runtime](skills/debug-runtime/)** — Language-agnostic systematic debugging: four phases + Iron Law, for reproducible bugs and repeated failed fixes.

`/plugin install yk-review@yigitkonur`

---

## 🔬 Research & discovery

Answer questions and find things with current web evidence. Bundles the `internet-researcher-*` subagents.

- **[run-research](skills/run-research/)** — One technical question, current web + Reddit practitioner evidence, source-backed synthesis, optionally fanned across subagents.
- **[run-deep-research](skills/run-deep-research/)** — Wave-based corpus research over 5+ entities or a market/category; evidence persisted to disk; Claude subagents or `codex exec` executors.
- **[run-github-scout](skills/run-github-scout/)** — Adaptive GitHub repo discovery, shortlisting for a concrete need, OSS comparison with repo evidence.
- **[search-it-bulk-by-codex](skills/search-it-bulk-by-codex/)** — Many small Codex-native web searches through `codex exec` with per-question, parseable answer files.

`/plugin install yk-research@yigitkonur`

---

## 🤖 Live automation

Drive a browser, a phone, or a public tunnel during the session.

- **[run-agent-browser](skills/run-agent-browser/)** — agent-browser CLI: `@ref` snapshots, sessions, forms, extraction, screenshots, headed/stealth, provider runs.
- **[mobilerun-control](skills/mobilerun-control/)** — Drive a connected Android phone via the mobilerun CLI: tap/type/swipe/read by box-center, deterministic multi-step on-device tasks.
- **[run-tailscale-funnel](skills/run-tailscale-funnel/)** — Expose a local HTTP server at a public `.ts.net` URL via Tailscale Funnel for browser navigation, mobile testing, webhooks, demos.

`/plugin install yk-automation@yigitkonur`

---

## 🚀 Ops & release

Deploy, maintain, offload, and publish.

- **[run-railway](skills/run-railway/)** — Railway CLI: deploys, logs, env vars, link, ssh, db shells, scaling, installed-vs-docs version-drift routing.
- **[run-repo-cleanup](skills/run-repo-cleanup/)** — Finish a project: review + merge every live branch and worktree into main locally (no PRs), retire dangling branches, sweep junk to a gitignored trash.
- **[run-babysitter](skills/run-babysitter/)** — Autonomous per-repo maintenance loop: triage commits + issues + persistent memory, file one deduplicated GitHub issue per cycle.
- **[run-linear-cli](skills/run-linear-cli/)** — Drive the linear-cli binary: LIN- IDs, linear.app URLs, bulk creation, lifecycle, search, git/PR loops.
- **[offload-run](skills/offload-run/)** — Run npm/pnpm install, tests, builds, tsc, eslint, pytest, or a dev server in a remote Sprites cloud sandbox instead of locally.
- **[vercel-local-prebuild](skills/vercel-local-prebuild/)** — Convert Vercel projects to local `vercel build` + `vercel deploy --prebuilt` to save build minutes.
- **[publish-npm-package](skills/publish-npm-package/)** — npm releases via GitHub Actions: trusted publishing, `NPM_TOKEN`, provenance, semantic-release, changesets, release-please.

`/plugin install yk-ops@yigitkonur`

---

## 🧩 Skill authoring

Build and harden skills themselves.

- **[build-skill](skills/build-skill/)** — Create/redesign/merge a Claude skill with evidence-based research and comparison before writing SKILL.md.
- **[audit-skill-by-derailment](skills/audit-skill-by-derailment/)** — Stress-test an existing SKILL.md by running a fresh subagent on a real task and editing the skill where the trace shows friction.

`/plugin install yk-skills@yigitkonur`

---

## Notes

- Each installed skill adds to the context window. Install only what you need — that's why the pack ships as per-skill plugins and small bundles, not one monolith.
- The plugin path and the `skills` CLI path read the same `skills/` files; the plugin marketplace is defined in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json), regenerated by `python3 scripts/gen-marketplace.py`.
- For the verb taxonomy and naming conventions, read [NAMING.md](NAMING.md).
- For the canonical skill structure and contribution checklist, read [CONTRIBUTING.md](CONTRIBUTING.md).
- The spec this pack follows: [agentskills.io/specification](https://agentskills.io/specification). Plugin/marketplace docs: [code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).
- If you see duplicate skill triggers, that's a known Claude Code issue ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills must use a verb from the [12-verb registry](NAMING.md), pass `python3 scripts/validate-skills.py`, and be added to the marketplace via `python3 scripts/gen-marketplace.py`.

## License

MIT
