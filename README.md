# skills-by-yigitkonur

skills for ai coding agents — one pack, **47 skills** + the internet-researcher agents. review, research, writing, ui/ux audit, mcp & framework builders, frontend/backend testing, browser/device/terminal automation, config files, publish. install what you need, skip the rest. no monolith.

> used to be two repos (a main pack + a `-secondary` b-side). they're one now. the old secondary repo is gone — everything lives here.

## install

three ways in. Codex and Claude Code both get the complete 47-skill pack.

### as claude code plugins (the good way — toggle on/off via `/plugin`)

add the marketplace once:

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
```

then grab exactly what you want — one skill, a themed bundle, the researcher agents, or everything — and drop it just as fast:

```
/plugin install run-review@yigitkonur          # one skill
/plugin install yk-mcp@yigitkonur              # a themed bundle
/plugin install yk-researchers@yigitkonur      # just the internet-researcher agents
/plugin install yk-everything@yigitkonur       # the whole thing
/plugin uninstall run-review@yigitkonur        # gone
```

installed ≠ enabled. `/plugin` lets you flip stuff on and off without reinstalling — enable what you're working with, mute the rest so it doesn't eat your context. per-skill plugins are named after the skill (`<skill>@yigitkonur`); bundles are the `yk-*` names below.

### as a codex plugin

add the marketplace once:

```bash
codex plugin marketplace add yigitkonur/skills-by-yigitkonur
```

then open `/plugins` in Codex and install the skill you need, such as `run-review@yigitkonur`; `skills-by-yigitkonur@yigitkonur` installs the full pack.

Codex offers the same per-skill choice: install `run-review@yigitkonur`, `build-mcp-server-sdk-v2@yigitkonur`, or any other skill directly from `/plugins`. `skills-by-yigitkonur@yigitkonur` remains the all-pack option for existing users. Codex packages are generated under `plugins/`, so each install is self-contained; Claude Code also offers its themed `yk-*` bundles.

### with the `skills` cli

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur                      # full pack
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>  # single skill
```

per-skill one-liners live in each Claude-compatible skill's `README.md`; Codex-only skills document the Codex all-pack install instead.

### staying fresh

every push to `main` auto-bumps the version, so `/plugin marketplace update` always pulls the latest skills and agents. you don't chase releases — they chase you.

---

## bundles

Claude Code themed groups for one-shot installs. every Claude-compatible skill also installs on its own; Codex-only skills are listed separately below.

| bundle | what's in it | install |
|---|---|---|
| **yk-everything** | all 47 skills + researcher agents | `/plugin install yk-everything@yigitkonur` |
| **yk-researchers** | internet-researcher agents only, no skills | `/plugin install yk-researchers@yigitkonur` |
| **yk-review** | review, codex review loops, completion audit | `/plugin install yk-review@yigitkonur` |
| **yk-frontend** | url→next.js, ui/ux/laws-of-ux audits | `/plugin install yk-frontend@yigitkonur` |
| **yk-mcp** | build/audit/test/convert mcp servers, clients, clis | `/plugin install yk-mcp@yigitkonur` |
| **yk-testing** | TestSprite frontend/browser and backend API verification | `/plugin install yk-testing@yigitkonur` |
| **yk-build** | chrome, cloudflare email, effect-ts, kernel, langchain, licenseseat, raycast, sentry, tinacms | `/plugin install yk-build@yigitkonur` |
| **yk-research** | research, deep-research, github-scout (+ agents) | `/plugin install yk-research@yigitkonur` |
| **yk-automation** | herdr terminal/agent control, browser automation, ios/android testing | `/plugin install yk-automation@yigitkonur` |
| **yk-config** | agents/claude/review files, drift audit, makefiles | `/plugin install yk-config@yigitkonur` |
| **yk-ops** | railway, coolify-cloud deploy, ci/cd optimization, repo-cleanup, npm publish | `/plugin install yk-ops@yigitkonur` |
| **yk-skills** | build-skill, derailment stress-test | `/plugin install yk-skills@yigitkonur` |
| **yk-writing** | multilingual natural-writing diagnosis, rewrite, and publication review | `/plugin install yk-writing@yigitkonur` |

---

## 🏗️ build apps & frameworks

write app code against a specific framework or sdk.

- **[build-chrome-extension](skills/build-chrome-extension/)** — chrome mv3: manifest v3, service_worker, content_scripts, popup, side_panel, declarativenetrequest, web store packaging.
- **[build-cloudflare-email-sending](skills/build-cloudflare-email-sending/)** — cloudflare email service: `send_email` worker binding, wrangler domain onboarding, migrate from resend/ses/postmark, replace supabase auth's mailer.
- **[build-effect-ts-v3](skills/build-effect-ts-v3/)** — effect-ts v3: `Effect.gen`, `Layer`, `Schema`, typed errors, fibers, `Stream`.
- **[build-kernel-ts-sdk](skills/build-kernel-ts-sdk/)** — kernel sdk (`@onkernel/sdk`): browsers, apps, profiles, managed auth, pools, playwright/cdp.
- **[build-langchain-ts-app](skills/build-langchain-ts-app/)** — langchain.js: agents, tool-calling, rag retrievers, structured output, streaming, langgraph.
- **[build-licenseseat-swift](skills/build-licenseseat-swift/)** — licenseseat swift sdk on macos: source-verified api surface (readme snippets that don't compile), two-singleton trap, `.pending` activation trap, offline grace, seats, hardened licensemanager blueprint.
- **[build-raycast-script-command](skills/build-raycast-script-command/)** — raycast script commands (`.sh`/`.py` with `@raycast.*` header): fields, modes, arguments, discovery.
- **[build-sentry-macos-swift](skills/build-sentry-macos-swift/)** — sentry-cocoa on macOS/swift: explore-repo → support matrix → deep integration (crash, nsexception, breadcrumbs, tags, scope, tracing, release health, dSYM, privacy scrubbing).
- **[build-tinacms-nextjs](skills/build-tinacms-nextjs/)** — tinacms + next.js app router: `tina/config.ts`, mdx/git content, schema modeling, `useTina` visual editing.

`/plugin install yk-build@yigitkonur`

---

## 🔌 mcp & agent interfaces

build, test, convert, and audit mcp servers, clients, and agent-facing clis.

- **[build-mcp-server-sdk-v1](skills/build-mcp-server-sdk-v1/)** — mcp server on `@modelcontextprotocol/sdk` v1.x: single-package, zod, `McpServer`.
- **[build-mcp-server-sdk-v2](skills/build-mcp-server-sdk-v2/)** — mcp server on `@modelcontextprotocol/server` v2 alpha: split packages, `registerTool`, `ctx.mcpReq`.
- **[build-mcp-use-server](skills/build-mcp-use-server/)** — mcp-use v2: `MCPServer` tools, views (MCP Apps), oauth providers, streamable HTTP, deploys, v1 migration.
- **[build-mcp-use-client](skills/build-mcp-use-client/)** — mcp-use client: `MCPClient`, `MCPSession`, `useMcp`, `mcp-use/react`, browser transport.
- **[build-mcp-use-agent](skills/build-mcp-use-agent/)** — mcp-use `MCPAgent`: an llm picks & orchestrates mcp tools via `run`, `stream`, `streamEvents`.
- **[build-clean-mcp-architecture](skills/build-clean-mcp-architecture/)** — clean architecture layer boundaries for typescript mcp-use/server code, import direction, dependency-cruiser gates.
- **[convert-mcp-sdk-v1-to-v2](skills/convert-mcp-sdk-v1-to-v2/)** — port a v1 mcp server to the v2 split-package sdk: package renames, `ServerContext`, zod v4.
- **[test-by-mcpc-cli](skills/test-by-mcpc-cli/)** — drive the `mcpc` cli (0.6.x) to test/debug/smoke-check an mcp server over stdio or streamable http.
- **[audit-agentic-mcp](skills/audit-agentic-mcp/)** — audit an mcp server for agent-readiness, or design a new one before code: framework, security, context posture.
- **[audit-agentic-cli](skills/audit-agentic-cli/)** — audit/design a cli for agent consumption: stable json, exit codes, non-interactive flags, repair loops.

`/plugin install yk-mcp@yigitkonur`

---

## 🧪 frontend & backend testing

author, run, diagnose, and release-gate deployed browser and API tests.

- **[run-testsprite-backend](skills/run-testsprite-backend/)** — TestSprite backend API tests with secure, revision-pinned release proof.
- **[run-testsprite-frontend](skills/run-testsprite-frontend/)** — TestSprite browser tests via public CLI or localhost MCP.

`/plugin install yk-testing@yigitkonur`

---

## ⚙️ config & instruction files

generate or refresh the config / instruction files another tool reads.

- **[init-agent-config](skills/init-agent-config/)** — agents.md / claude.md / review.md hierarchies; folder-scoped guidance; native review adapters.
- **[init-jean-json](skills/init-jean-json/)** — onboard a repo to jean: author jean.json + .worktreeinclude, prove them in a throwaway worktree, document in agents.md, retire test worktrees.
- **[init-makefiles](skills/init-makefiles/)** — scaffold safe scenario makefiles (local dev, tunnels, deploys, r2 sync, supabase, railway, vercel, mac shipping).
- **[update-agent-config](skills/update-agent-config/)** — audit agents.md / claude.md / review.md for drift after refactors; refresh refs, recount tables, map folder coverage, fill only invariant-dense gap folders.

`/plugin install yk-config@yigitkonur`

---

## 🎨 frontend rebuild & audit

rebuild a live site, rip its design, or audit a running ui/ux.

- **[convert-url-to-nextjs](skills/convert-url-to-nextjs/)** — rebuild a deployed site as-is pixel-faithful as a next.js project from a live url — the "we lost the frontend repo" recovery. l0+l1 crawl + back-to-back agent-browser verification.
- **[audit-ux-laws](skills/audit-ux-laws/)** — audit ui against the 30 laws of ux (fitts's, hick's, miller's, jakob's, gestalt, choice overload, cognitive load) with critical/minor severity + code fixes.
- **[audit-ui-and-save-files](skills/audit-ui-and-save-files/)** — visual ui audit across pages/viewports with browser screenshots, per-bug findings to `css-issues/[yy-mm-dd]/...`, ending with an approval-gated fix-subagent plan.
- **[audit-ux-and-save-files](skills/audit-ux-and-save-files/)** — usability audit from real personas walking their journeys, per-issue findings to `ux-findings/[yy-mm-dd]/...`, ending with a prioritized recommendations report (reports, doesn't fix).

`/plugin install yk-frontend@yigitkonur`

---

## 📝 review & completion

judge a change for merge-readiness, triage feedback, and verify "done".

- **[run-review](skills/run-review/)** — one entry point, four modes: (a) do a pr/branch review, (b) open your branch as a self-review pr, (c) triage received feedback, (d) delegate to `codex review`.
- **[run-codex-review-loop](skills/run-codex-review-loop/)** — multi-lens or multi-branch codex review loops; independently verify findings and optionally fix confirmed issues in isolated worktrees until convergence.
- **[audit-completion](skills/audit-completion/)** — audit task / session / plan / branch completion claims with evidence; remediate to terminal status.

`/plugin install yk-review@yigitkonur`

---

## 🔬 research & discovery

answer questions and find things with real web evidence. ships the `internet-researcher-*` subagents.

- **[run-research](skills/run-research/)** — one technical question, current web + reddit practitioner evidence, source-backed synthesis, optionally fanned across subagents.
- **[run-deep-research](skills/run-deep-research/)** — wave-based corpus research over 5+ entities or a market/category; evidence persisted to disk; claude subagents or `codex exec` executors.
- **[run-github-scout](skills/run-github-scout/)** — adaptive github repo discovery, shortlisting for a concrete need, oss comparison with repo evidence.

`/plugin install yk-research@yigitkonur` · agents only: `/plugin install yk-researchers@yigitkonur`

---

## 🤖 live automation

drive a browser, a phone, or a terminal workspace mid-session.

- **[herdr](skills/herdr/)** — control herdr panes, tabs, workspaces, worktrees, commands, and coding agents without stealing focus.
- **[run-agent-browser](skills/run-agent-browser/)** — agent-browser cli: `@ref` snapshots, sessions, forms, extraction, screenshots, headed/stealth, provider runs.
- **[run-agent-device](skills/run-agent-device/)** — agent-device cli for ios app testing: settle-first snapshot/press/fill loop, evidence capture, cross-layer bug triage, runtime-freshness + fresh-state discipline, fix-and-retest.
- **[mobilerun-control](skills/mobilerun-control/)** — drive a connected android phone via the mobilerun cli: tap/type/swipe/read by box-center, deterministic multi-step on-device tasks.

`/plugin install yk-automation@yigitkonur`

---

## 🚀 ops & release

deploy, maintain, offload, publish.

- **[run-railway](skills/run-railway/)** — railway cli: deploys, logs, env vars, link, ssh, db shells, scaling, installed-vs-docs version-drift routing.
- **[deploy-coolify-cloud](skills/deploy-coolify-cloud/)** — deploy/update docker-compose services on coolify cloud via the api: verified create/patch/urls-domain/env-var contracts, base64 compose, custom domains + TLS, cross-service networking, and box-level deploy verification.
- **[ci-cd-optimize](skills/ci-cd-optimize/)** — diagnose or optimize slow CI/CD by measured bottleneck — GitHub Actions, GitLab CI, CircleCI, Buildkite, monorepos, Docker builds, runner queues, deployment paths, and Swift/Xcode CI — while preserving required checks, cache correctness, and exact-artifact verification.
- **[run-repo-cleanup](skills/run-repo-cleanup/)** — finish a project: review + merge every live branch and worktree into main locally (no prs), retire dangling branches, sweep junk to a gitignored trash.
- **[publish-npm-package](skills/publish-npm-package/)** — npm releases via github actions: trusted publishing, `NPM_TOKEN`, provenance, semantic-release, changesets, release-please.

`/plugin install yk-ops@yigitkonur`

---

## ✍️ writing & editing

rewrite supplied content for real readers while preserving evidence, locale, and document structure.

- **[convert-to-natural-writing](skills/convert-to-natural-writing/)** — diagnose, rewrite, and publication-review robotic, generic, or AI-sounding multilingual copy in plain text, Markdown, MDX, or HTML; preserves claims and structure without detector theater or invented personality.

`/plugin install yk-writing@yigitkonur`

---

## 🧩 skill authoring

build and harden skills themselves.

- **[build-skill](skills/build-skill/)** — create/redesign/merge a skill with evidence-based research and comparison before writing skill.md.
- **[audit-skill-by-derailment](skills/audit-skill-by-derailment/)** — stress-test an existing skill.md by running a fresh subagent on a real task and editing the skill where the trace shows friction.

`/plugin install yk-skills@yigitkonur`

---

## notes

- every enabled skill costs context. that's the whole point of shipping per-skill Codex and Claude plugins, plus small Claude bundles, instead of one blob — enable what you use.
- the plugin paths and the `skills` cli read the canonical `skills/` files. generated metadata lives in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json), [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json), [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json), and the self-contained Codex packages in [`plugins/`](plugins/); the version comes from [`VERSION`](VERSION) and ci bumps it on every push to `main`.
- naming/taxonomy → [NAMING.md](NAMING.md). structure + contribution checklist → [CONTRIBUTING.md](CONTRIBUTING.md).
- spec: [agentskills.io/specification](https://agentskills.io/specification). plugin/marketplace docs: [code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).
- duplicate skill triggers? known claude code thing ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## contributing

see [CONTRIBUTING.md](CONTRIBUTING.md). new skills use a verb from the [12-verb registry](NAMING.md), pass `python3 scripts/validate-skills.py`, and land in the marketplace via `python3 scripts/gen-marketplace.py`.

## license

mit
