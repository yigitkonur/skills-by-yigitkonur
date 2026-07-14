# skills-by-yigitkonur

skills for ai coding agents — one pack, **48 skills** + the internet-researcher agents. review, research, ui/ux audit, mcp & framework builders, backend api testing, browser/device automation, config files, publish. install what you need, skip the rest. no monolith.

> used to be two repos (a main pack + a `-secondary` b-side). they're one now. the old secondary repo is gone — everything lives here.

## install

three ways in. Codex gets the complete 48-skill pack; Claude Code gets 47 Claude-compatible skills and intentionally excludes the Codex-only Jean orchestrator.

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

then open `/plugins` in Codex and install `skills-by-yigitkonur@yigitkonur`.

Codex consumes this repo as one polished all-pack plugin from the repo root. Claude Code gets fine-grained per-skill and themed bundle plugins because its marketplace supports per-entry skill allowlists; Codex gets the full pack through `.codex-plugin/plugin.json` pointing at `./skills/`.

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
| **yk-everything** | all 47 Claude-compatible skills + researcher agents | `/plugin install yk-everything@yigitkonur` |
| **yk-researchers** | internet-researcher agents only, no skills | `/plugin install yk-researchers@yigitkonur` |
| **yk-review** | review, codex-review-loop, codex adversarial loop, completion audit, runtime debug | `/plugin install yk-review@yigitkonur` |
| **yk-frontend** | url→next.js, ui/ux/laws-of-ux audits | `/plugin install yk-frontend@yigitkonur` |
| **yk-mcp** | build/audit/test/convert mcp servers, clients, clis | `/plugin install yk-mcp@yigitkonur` |
| **yk-testing** | deep TestSprite backend API verification against deployed services | `/plugin install yk-testing@yigitkonur` |
| **yk-build** | chrome, cloudflare email, effect-ts, kernel, langchain, licenseseat, raycast, sentry, tinacms | `/plugin install yk-build@yigitkonur` |
| **yk-research** | research, deep-research, github-scout, bulk-search (+ agents) | `/plugin install yk-research@yigitkonur` |
| **yk-automation** | agent-browser, android control, tailscale funnel | `/plugin install yk-automation@yigitkonur` |
| **yk-config** | agents/claude/review files, drift audit, makefiles | `/plugin install yk-config@yigitkonur` |
| **yk-ops** | railway, coolify-cloud deploy, repo-cleanup, npm publish | `/plugin install yk-ops@yigitkonur` |
| **yk-skills** | build-skill, derailment stress-test | `/plugin install yk-skills@yigitkonur` |
| **yk-delivery** | scored alignment, spec corpus, waved orchestration for big initiatives | `/plugin install yk-delivery@yigitkonur` |

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
- **[build-mcp-use-server](skills/build-mcp-use-server/)** — mcp-use/server: `server.tool`, response helpers, `ctx.auth`, sessions, transports, widgets, inspector, deploy.
- **[build-mcp-use-client](skills/build-mcp-use-client/)** — mcp-use client: `MCPClient`, `MCPSession`, `useMcp`, `mcp-use/react`, browser transport.
- **[build-mcp-use-agent](skills/build-mcp-use-agent/)** — mcp-use `MCPAgent`: an llm picks & orchestrates mcp tools via `run`, `stream`, `streamEvents`.
- **[build-clean-mcp-architecture](skills/build-clean-mcp-architecture/)** — clean architecture layer boundaries for typescript mcp-use/server code, import direction, dependency-cruiser gates.
- **[convert-mcp-sdk-v1-to-v2](skills/convert-mcp-sdk-v1-to-v2/)** — port a v1 mcp server to the v2 split-package sdk: package renames, `ServerContext`, zod v4.
- **[test-by-mcpc-cli](skills/test-by-mcpc-cli/)** — drive the `mcpc` cli (0.2.x) to test/debug/smoke-check an mcp server over stdio or streamable http.
- **[audit-agentic-mcp](skills/audit-agentic-mcp/)** — audit an mcp server for agent-readiness, or design a new one before code: framework, security, context posture.
- **[audit-agentic-cli](skills/audit-agentic-cli/)** — audit/design a cli for agent consumption: stable json, exit codes, non-interactive flags, repair loops.

`/plugin install yk-mcp@yigitkonur`

---

## 🧪 backend api testing

author, run, diagnose, and release-gate real deployed api tests.

- **[run-testsprite-backend](skills/run-testsprite-backend/)** — repo-first TestSprite backend workflow: managed credentials, semantic Python assertions, streaming/data-flow coverage, immutable failure artifacts, fix loops, and exact-revision release proof.

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

## 📝 review & debug

judge a change for merge-readiness, triage feedback, verify "done", and chase runtime bugs.

- **[run-review](skills/run-review/)** — one entry point, four modes: (a) do a pr/branch review, (b) open your branch as a self-review pr, (c) triage received feedback, (d) delegate to `codex review`.
- **[run-codex-review-loop](skills/run-codex-review-loop/)** — native `codex exec review` across multiple branches; compare findings; rescue a saved branch-review loop.
- **[run-codex-adversarial-loop](skills/run-codex-adversarial-loop/)** — fan out parallel codex adversarial reviews across derived lenses, independently verify every finding, fix confirmed issues in grouped worktrees, loop until clean.
- **[audit-completion](skills/audit-completion/)** — audit task / session / plan / branch completion claims with evidence; remediate to terminal status.
- **[debug-runtime](skills/debug-runtime/)** — language-agnostic systematic debugging: four phases + iron law, for reproducible bugs and repeated failed fixes.

`/plugin install yk-review@yigitkonur`

---

## 🔬 research & discovery

answer questions and find things with real web evidence. ships the `internet-researcher-*` subagents.

- **[run-research](skills/run-research/)** — one technical question, current web + reddit practitioner evidence, source-backed synthesis, optionally fanned across subagents.
- **[run-deep-research](skills/run-deep-research/)** — wave-based corpus research over 5+ entities or a market/category; evidence persisted to disk; claude subagents or `codex exec` executors.
- **[run-github-scout](skills/run-github-scout/)** — adaptive github repo discovery, shortlisting for a concrete need, oss comparison with repo evidence.
- **[search-it-bulk-by-codex](skills/search-it-bulk-by-codex/)** — many small codex-native web searches through `codex exec` with per-question, parseable answer files.

`/plugin install yk-research@yigitkonur` · agents only: `/plugin install yk-researchers@yigitkonur`

---

## 🤖 live automation

drive a browser, a phone, or a public tunnel mid-session.

- **[run-agent-browser](skills/run-agent-browser/)** — agent-browser cli: `@ref` snapshots, sessions, forms, extraction, screenshots, headed/stealth, provider runs.
- **[mobilerun-control](skills/mobilerun-control/)** — drive a connected android phone via the mobilerun cli: tap/type/swipe/read by box-center, deterministic multi-step on-device tasks.
- **[run-tailscale-funnel](skills/run-tailscale-funnel/)** — expose a local http server at a public `.ts.net` url via tailscale funnel for browser nav, mobile testing, webhooks, demos.

`/plugin install yk-automation@yigitkonur`

---

## 🧠 codex-only

skills that depend on Codex desktop/runtime capabilities. these are included in the Codex all-pack plugin and intentionally excluded from every Claude Code plugin and bundle.

- **[orchestrate-projects-by-jean](skills/orchestrate-projects-by-jean/)** — supervise existing jean coding agents through mcp + computer use, bounded watchers, exact-state recovery, and completion gates.

install `skills-by-yigitkonur@yigitkonur` from `/plugins` in Codex.

---

## 🚀 ops & release

deploy, maintain, offload, publish.

- **[run-railway](skills/run-railway/)** — railway cli: deploys, logs, env vars, link, ssh, db shells, scaling, installed-vs-docs version-drift routing.
- **[deploy-coolify-cloud](skills/deploy-coolify-cloud/)** — deploy/update docker-compose services on coolify cloud via the api: verified create/patch/urls-domain/env-var contracts, base64 compose, custom domains + TLS, cross-service networking, and box-level deploy verification.
- **[run-repo-cleanup](skills/run-repo-cleanup/)** — finish a project: review + merge every live branch and worktree into main locally (no prs), retire dangling branches, sweep junk to a gitignored trash.
- **[publish-npm-package](skills/publish-npm-package/)** — npm releases via github actions: trusted publishing, `NPM_TOKEN`, provenance, semantic-release, changesets, release-please.

`/plugin install yk-ops@yigitkonur`

---

## 🧩 skill authoring

build and harden skills themselves.

- **[build-skill](skills/build-skill/)** — create/redesign/merge a skill with evidence-based research and comparison before writing skill.md.
- **[audit-skill-by-derailment](skills/audit-skill-by-derailment/)** — stress-test an existing skill.md by running a fresh subagent on a real task and editing the skill where the trace shows friction.

`/plugin install yk-skills@yigitkonur`

---

## 🧭 aligned delivery

drive a large, ambiguous initiative front-to-back: scored question alignment, then a spec corpus, then waved subagent orchestration.

- **[run-aligned-delivery](skills/run-aligned-delivery/)** — scored multi-round question alignment, then a filename-state spec corpus, then waved subagent orchestration — for a large or ambiguous initiative.

`/plugin install yk-delivery@yigitkonur`

---

## notes

- every enabled skill costs context. that's the whole point of shipping per-skill Claude plugins and small Claude bundles instead of one blob — enable what you use.
- the plugin paths and the `skills` cli read the same `skills/` files. generated metadata lives in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json), [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json), and [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json); the version comes from [`VERSION`](VERSION) and ci bumps it on every push to `main`.
- naming/taxonomy → [NAMING.md](NAMING.md). structure + contribution checklist → [CONTRIBUTING.md](CONTRIBUTING.md).
- spec: [agentskills.io/specification](https://agentskills.io/specification). plugin/marketplace docs: [code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).
- duplicate skill triggers? known claude code thing ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## contributing

see [CONTRIBUTING.md](CONTRIBUTING.md). new skills use a verb from the [12-verb registry](NAMING.md), pass `python3 scripts/validate-skills.py`, and land in the marketplace via `python3 scripts/gen-marketplace.py`.

## license

mit
