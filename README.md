# skills-by-yigitkonur

42 skills for AI coding agents — agent configuration, code review, design extraction, browser automation, multi-agent orchestration, planning, research, project execution, SEO & marketing, framework guides, SDK guides, language standards, UI component libraries, CI/CD, OpenClaw platform, and skill research.

## Install the full pack

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## Install a single skill

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

Use the canonical `skills/<skill-name>` path for single-skill installs. It installs exactly one skill and keeps future updates tied to the same canonical skill path.

Examples:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-skills
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-playwright
```

## How discovery works

Each skill uses its `SKILL.md` frontmatter description as a trigger. Install the full pack when you want broad coverage, or install a single skill from the `skills/` subdirectory when you want a narrower setup.

---

## Agent Configuration

Skills that generate project-level instruction files (`CLAUDE.md`, `AGENTS.md`) so AI coding agents understand your codebase from the first session.

| Skill | What it does |
|---|---|
| **[init-agent-config](skills/init-agent-config/)** | Generates AGENTS.md (cross-agent standard, 20+ tools) and/or CLAUDE.md (Claude Code–specific) using the WHAT/WHY/HOW framework, dual-file architecture, progressive disclosure, and quality scoring. Includes 7 reference docs: best practices with scoring rubric, Claude memory hierarchy, AGENTS.md discovery spec, cross-agent compatibility matrix for 16 agents, unified templates for 10 project types, and steering experiences from derailment testing. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-agent-config
```

---

## Code Review

Skills for reviewing pull requests and setting up AI code review platform configuration.

| Skill | What it does |
|---|---|
| **[review-pr](skills/review-pr/)** | Systematic PR review using the `gh` CLI — eight-phase workflow covering context gathering, file clustering, existing comment correlation, goal validation, per-cluster review across 7 dimensions (security, correctness, data integrity, performance, API contract, maintainability, testing), cross-cutting analysis, and structured output with severity calibration. Includes 17 reference docs: review workflow, gh CLI reference, file clustering, comment correlation, review dimensions, diff analysis, output templates, anti-patterns, severity guide, language-specific patterns, security review, performance review, bug patterns, cross-cutting analysis, large PR strategy, automation, and communication. |
| **[init-greptile-review](skills/init-greptile-review/)** | Generates `.greptile/config.json`, `rules.md`, and `files.json` with semantic rules scoped to your repo's actual architecture — not linter-level checks, but cross-file implications that require LLM understanding. Includes 3 reference docs covering the full config spec, 11 example scenarios (TypeScript, Python, Go, Rust, Tauri, MCP, Next.js), and an anti-patterns/troubleshooting guide. |
| **[init-devin-review](skills/init-devin-review/)** | Generates `REVIEW.md` and `AGENTS.md` for Devin's Bug Catcher by exploring your repo structure, tech stack, and pain points, then producing prioritized review rules with code examples. Includes 2 reference docs: the full instruction file spec and 8 complete scenario templates (API, dashboard, Tauri, MCP, monorepo). |
| **[init-copilot-review](skills/init-copilot-review/)** | Generates a root `copilot-instructions.md` plus path-scoped `*.instructions.md` micro-files that stay within Copilot's 4,000-character processing limit. Includes 6 reference docs covering setup and format, rule-writing quality (SMSA), scoping and targeting, troubleshooting, scenario templates, and a micro-library of 50+ reusable rule blocks. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/review-pr
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-greptile-review
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-devin-review
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-copilot-review
```

---

## Design Extraction

Skills that forensically parse real CSS/JS from existing sites and produce structured design documentation or buildable projects.

| Skill | What it does |
|---|---|
| **[extract-saas-design](skills/extract-saas-design/)** | Extracts the complete visual DNA from any SaaS dashboard or admin panel codebase — every token, component state, animation keyframe, and responsive breakpoint — into structured documentation that lets a builder recreate the exact look-and-feel without copying source. Includes 6 reference docs: component/system templates, dashboard patterns catalog, foundations and components agent guides, and a quality checklist. |
| **[convert-snapshot-nextjs](skills/convert-snapshot-nextjs/)** | Converts browser "Save As" HTML snapshots into buildable Next.js App Router projects with zero third-party dependencies — self-hosted fonts, images, icons, and a Tailwind config grounded on real extracted CSS values (no approximations, no guessing). Includes 6 reference docs: foundations/sections agent guides, section/system templates, website patterns catalog, and a quality checklist. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/extract-saas-design
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/convert-snapshot-nextjs
```

---

## Browser Automation

Skills for automating browser interactions — navigation, form filling, screenshots, data extraction, and web app testing.

| Skill | What it does |
|---|---|
| **[run-agent-browser](skills/run-agent-browser/)** | Automates browser tasks using the Browserbase agent CLI — navigation, form filling, screenshots, data extraction, and web app testing through a snapshot-and-interact loop with element refs. |
| **[run-playwright](skills/run-playwright/)** | Reliable operational guide for `@anthropic-ai/playwright-cli` grounded in installed-CLI behavior — chrome bootstrap, observe-act proof loops, form/upload verification, tab/session coordination, console/network artifacts, visual checks, and advanced `run-code` recipes. Includes 7 reference docs: command reference, session/tab management, forms/data, visual testing, debugging, async/advanced recipes, and orchestrator guide. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-agent-browser
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-playwright
```

---

## Multi-Agent Orchestration

Skills for coordinating multiple AI coding agents across terminals — launching, messaging, transcript sharing, and multi-agent workflow patterns.

| Skill | What it does |
|---|---|
| **[run-hcom-agents](skills/run-hcom-agents/)** | Orchestrates multiple AI coding agents via hcom — launching headless Claude and Codex agents, messaging between them, reading transcripts, and applying tested multi-agent patterns (worker-reviewer loops, ensemble consensus, cascade pipelines, cross-tool collaboration). Includes 12 reference docs: delivery pipeline, CLI reference, 6 tested script patterns with real event JSON, advanced patterns from 35-repo research, cross-tool details, and gotchas. |
| **[build-hcom-systems](skills/build-hcom-systems/)** | Builds applications and automation systems on top of hcom as the multi-agent communication backbone — designing agent topologies, understanding hcom internals (SQLite schema, hook system, PTY terminal management, MQTT relay, event subscriptions, bootstrap injection), creating custom workflow scripts, and integrating hcom into CI/CD pipelines. Includes 11 reference docs: core architecture, scripting engine, config system, TUI, hooks, relay, PTY, events, tool integration, bootstrap, and 35-repo multi-agent research. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-hcom-agents
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-hcom-systems
```

---

## Planning & Research

Skills that provide structured methodologies for decision-making and multi-source research.

| Skill | What it does |
|---|---|
| **[plan-work](skills/plan-work/)** | Structured planning skill for any task — intake framing, root cause analysis, option design, prioritization, systems thinking, technical strategy, communication alignment, and execution risk. Includes 17 reference docs covering 9 thinking method families and a catalog of 40+ named methods (pre-mortem, Cynefin, RICE, wardley mapping, etc.). |
| **[run-research](skills/run-research/)** | Research methodology for coding agents using the Research Powerpack MCP server — turns single-query searches into multi-source validated workflows with Google, Reddit, and page scraping. Includes 10 domain-specific reference docs: architecture, API integration, bug fixing, frontend, performance, security, testing, DevOps, and language idioms. |
| **[build-skills](skills/build-skills/)** | Skill creation methodology skill for building or redesigning Claude skills from workspace evidence, remote research, and comparison before synthesis. Use when a skill should be original, traceable, and repo-fit instead of improvised. Includes reference docs for research workflow, remote sources, comparison workflow, and source-pattern selection. |
| **[enhance-skill-by-derailment](skills/enhance-skill-by-derailment/)** | Tests a skill's instructional quality by following its workflow literally on a real task — when instructions fail to guide the next action, diagnoses the root cause (missing instruction, wrong instruction, missing reference) and fixes SKILL.md and references/ directly. No synthetic report files. Includes 5 reference docs: friction classification, root cause taxonomy, 9 fix patterns, metrics/iteration tracking, and domain adaptation guide. |
| **[plan-issue-tree](skills/plan-issue-tree/)** | Creates maximalist GitHub Issue trees with sub-issue nesting (up to 8 levels), wave-based execution order, labels, and agent-ready bodies following the subagent prompt protocol — asks brainstorming questions first, then generates bottom-up issue hierarchies with BSV Definition of Done criteria, mandatory pre-creation body size validation (60K threshold), bidirectional cross-linking verification, and dependency wiring via GraphQL. Includes 5 reference docs (question bank, issue body template, label schema, body size validation, cross-linking patterns) and 3 scripts (label setup, sub-issue linking, recursive tree reader). |
| **[run-issue-plan](skills/run-issue-plan/)** | Executes project plans stored as GitHub Issue trees by recursively reading the hierarchy, dispatching subagents wave-by-wave via the Agent tool, verifying BSV completion criteria, and tracking progress with status labels and issue comments. Includes pre-dispatch validation, tool-agnostic prompt generation, partial wave failure handling with recovery patterns, and state recovery from GitHub labels. Includes 4 reference docs (subagent dispatch template, wave execution patterns, generic prompt patterns, partial wave handling) and 1 script (recursive tree reader). |
| **[plan-prd](skills/plan-prd/)** | Structured PRD (Product Requirements Document) creation — five-phase workflow covering mandatory discovery with relentless interviewing, codebase-grounded analysis, 10-section AI-agent-actionable template with measurable acceptance criteria, quality validation, issue body size management with split strategies, and optional vertical-slice decomposition. Includes 10 reference docs: elicitation questions, format decision guide, PRD template, decomposition guide, issue size management, quality checklist, acceptance criteria guide, anti-patterns, worked example, and requirements quality calibration. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/plan-work
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-skills
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/enhance-skill-by-derailment
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/plan-issue-tree
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-issue-plan
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/plan-prd
```

---

## SEO & Marketing

Skills for running SEO analysis workflows using MCP-powered marketing tool suites.

| Skill | What it does |
|---|---|
| **[run-seo-analysis](skills/run-seo-analysis/)** | Operational workflow guide for the MCP Marketers server's 32 SEO tools — routes agents through site audits, keyword research, backlink analysis, competitor intelligence, SERP analysis, rank tracking, content optimization, AI presence monitoring, local SEO, ASO, e-commerce SEO, and trend analysis with cost-aware tool chaining. Includes 16 reference docs: 12 workflow guides (site-audit, keyword-research, competitor-analysis, backlink-analysis, serp-analysis, rank-tracking, content-optimization, ai-presence, local-seo, aso, ecommerce-seo, trends-analysis) and 4 guides (tool-selection-matrix, cost-optimization, seo-domain-knowledge, parameter-guide). |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-seo-analysis
```

---

## CI/CD

Skills for automating package publishing, release workflows, and continuous deployment pipelines.

| Skill | What it does |
|---|---|
| **[publish-npm-package](skills/publish-npm-package/)** | Automates npm package publishing via GitHub Actions — covers OIDC and token authentication, semantic-release/changesets/release-please version strategies, provenance attestation, and copy-paste workflow templates for all combinations. Includes 3 reference docs: auth methods, version tools comparison, and complete workflow templates. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/publish-npm-package
```

---

## Standards & Optimization

Deep reference skills for language-level type safety, patterns, anti-patterns, and system-specific optimization.

| Skill | What it does |
|---|---|
| **[optimize-mcp-server](skills/optimize-mcp-server/)** | Exploration-first optimization skill for any MCP server — explores the codebase, diagnoses issues across 15 quality dimensions, presents findings with severity and options, and applies approved changes with verification steps. 113 patterns, 7 decision trees, framework-agnostic (FastMCP, mcp-use, official SDK, any framework). Includes 22 reference files. |
| **[test-by-mcpc-cli](skills/test-by-mcpc-cli/)** | Test and debug any MCP server using the Apify `mcpc` CLI — covers stdio, HTTP stateless (SSE), and HTTP stateful (streamable HTTP) transports with session management, tool discovery, schema validation, async tasks, proxy sandboxing, auth precedence, pagination, and automated test scripts. Includes 30 reference docs across guides, patterns, commands, examples, and troubleshooting. |
| **[develop-typescript](skills/develop-typescript/)** | Strict TypeScript development guide covering type system patterns, anti-patterns with fixes, error handling strategies, and compiler configuration across application, library, CLI, and backend codebases. Includes 4 reference docs: anti-patterns, patterns, type-system, and strict-config. |
| **[develop-clean-architecture](skills/develop-clean-architecture/)** | Clean Architecture, DDD tactical patterns, and Hexagonal Architecture for TypeScript — dependency direction, entity design with `#` private fields and create/reconstitute factories, use case isolation, CQRS, domain events, composition roots, and strict TypeScript enforcement. 76 rules across 11 categories with mode-based workflow (designing, reviewing, implementing, refactoring). Includes 78 reference docs: dependency rules, entity/aggregate/value-object patterns, use case ports, clean code fundamentals, component cohesion, TypeScript strictness and LSP performance, architecture patterns (CQRS, events, vertical slices), boundary definitions, adapter patterns, framework isolation, testing pyramid, and decision tables. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/optimize-mcp-server
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/test-by-mcpc-cli
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/develop-typescript
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/develop-clean-architecture
```

---

## UI Component Libraries

Skills for building interfaces with component library ecosystems and their MCP tooling.

| Skill | What it does |
|---|---|
| **[build-daisyui-mcp](skills/build-daisyui-mcp/)** | Operational guide for the daisyui-blueprint MCP server — two MCP tools, 500+ component snippets, Figma design extraction, 7 conversion workflows (Figma, screenshot, Bootstrap, Tailwind, theme), CSS-only interaction patterns, and daisyUI v5 class reference. Includes 17 reference docs across tool API, component catalog, themes, workflows, and conversion prompts. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-daisyui-mcp
```

---

## Framework Guides

Deep reference skills for specific frameworks and tools.

| Skill | What it does |
|---|---|
| **[build-supastarter-app](skills/build-supastarter-app/)** | Comprehensive developer guide for the SupaStarter Next.js SaaS boilerplate — monorepo architecture, App Router layout chains, oRPC API patterns, Better Auth, Prisma, Stripe payments, organizations, mail, i18n, S3 storage, UI conventions, analytics, and deployment. Includes 93 reference docs organized across 20 domains with cheatsheets for commands, env vars, file locations, and imports. |
| **[debug-tauri-devtools](skills/debug-tauri-devtools/)** | CrabNebula DevTools integration for debugging Tauri v2 apps — gives AI agents visibility into the Rust side with console logs, tracing spans, IPC call timings, live config inspection, and frontend source browsing. Includes 5 reference docs: architecture deep-dive, IPC span anatomy, integration patterns, tab reference, and common debugging scenarios. |
| **[convert-vue-nextjs](skills/convert-vue-nextjs/)** | Converts Vue 2/3 and Nuxt codebases to Next.js App Router — component mapping (directives, slots, emits, v-model), state migration (Pinia/Vuex to Zustand/Context), routing conversion, SSR/data-fetching patterns, coexistence architectures (proxy/Web Components/micro-frontends), and testing strategy. Includes 12 reference docs: component mapping, state management, routing, SSR/data fetching, advanced patterns, migration workflow, package mapping, migration strategies, assessment checklist, coexistence patterns, testing strategy, and pitfalls. |
| **[build-chrome-extension](skills/build-chrome-extension/)** | Production-grade Chrome extension development with Manifest V3 — service worker persistence patterns, content script injection (ISOLATED/MAIN worlds), type-safe messaging and storage, popup/sidepanel/options UI, framework comparison (WXT/Plasmo/CRXJS/vanilla), testing with Playwright/Puppeteer, and Chrome Web Store publishing. Includes 13 reference docs: manifest V3 spec, permissions risk matrix, MV2-to-MV3 migration, messaging, storage, 12 core Chrome APIs, service worker patterns, content scripts, UI surfaces, framework comparison, testing guide, debugging, and Web Store publishing. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-supastarter-app
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/debug-tauri-devtools
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/convert-vue-nextjs
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-chrome-extension
```

---

## SDK Guides

Deep reference skills for building applications with AI platform SDKs.

| Skill | What it does |
|---|---|
| **[build-copilot-sdk-app](skills/build-copilot-sdk-app/)** | Complete developer guide for the GitHub Copilot SDK (`@github/copilot-sdk`) in TypeScript/Node.js — client setup, sessions, custom tools with Zod schemas, streaming events, permissions, hooks, custom agents, MCP servers, skills, BYOK providers, plan/autopilot/fleet modes, multi-client architectures, and Ralph loop autonomous dev patterns. Includes 17 reference docs: client/transport, sessions, tools/schemas, events/streaming, permissions, hooks, agents/MCP/skills, auth/BYOK, advanced patterns, and type reference. |
| **[build-mcp-use-server](skills/build-mcp-use-server/)** | Production-grade MCP server development with the `mcp-use` TypeScript library — MCPServer constructor, tool registration with Zod schemas, response helpers (`text()`, `object()`, `error()`), resources, prompts, transport selection (stdio/httpStream/SSE), OAuth providers (Auth0, WorkOS, Supabase), session management, middleware, elicitation, sampling, notifications, and deployment. Includes 13 reference docs: quick-start, tools/schemas, resources/prompts, transports, authentication, advanced features, testing/debugging, production patterns, deployment, anti-patterns, server recipes, project templates, and common errors. |
| **[build-mcp-use-client](skills/build-mcp-use-client/)** | Production-grade MCP client development with the `mcp-use` TypeScript library — MCPClient constructor, MCPSession for tool calling/resources/prompts, HTTP and STDIO transports, environment-specific entry points (Node/Browser/React/CLI), sampling callbacks, elicitation with form/URL modes and helpers, completion autocomplete, notifications, OAuth authentication, React hooks (useMcp/McpClientProvider/useMcpClient/useMcpServer), code mode with VM/E2B executors, and server manager configuration. Includes 20 reference docs: quick-start, client configuration, environments, tools, resources, prompts, CLI reference, sampling, elicitation, completion, notifications and logging, authentication, server manager, code mode, React integration, production patterns, anti-patterns, client recipes, project templates, and common errors. |
| **[build-mcp-use-agent](skills/build-mcp-use-agent/)** | Production-grade AI agent development with the `mcp-use` TypeScript library — MCPAgent constructor, explicit and simplified initialization modes, LLM integration (OpenAI, Anthropic, Google, Groq), streaming (stream/streamEvents/prettyStreamEvents), structured output with Zod schemas, memory management, server manager for multi-server routing, Langfuse observability, and production deployment. Includes 14 reference docs: quick-start, agent configuration, LLM integration, streaming, memory management, server manager, structured output, observability, advanced patterns, production patterns, anti-patterns, agent recipes, integration recipes, and common errors. |
| **[build-mcp-use-apps-widgets](skills/build-mcp-use-apps-widgets/)** | Interactive MCP App development with the `mcp-use` TypeScript library — widget-based applications that render UI inside ChatGPT, Claude, Goose, and other MCP hosts. Covers tool-to-widget binding, useWidget/useCallTool hooks, streaming preview, display modes, theming, CSP configuration, McpUseProvider, persistent widget state, follow-up messages, dual-protocol ChatGPT support, and deployment. Includes 25 reference docs: quick-start, widgets and UI, widget components, streaming preview, ChatGPT apps flow, tools/schemas, response helpers, authentication, session management, deployment, anti-patterns, MCP apps patterns, widget recipes, server recipes, project templates, and common errors. |
| **[build-langchain-ts-app](skills/build-langchain-ts-app/)** | LangChain.js v1 and LangGraph.js in TypeScript — createAgent, LCEL composition, StateGraph workflows, tool calling with Zod, structured output, streaming (8 modes), middleware (14 built-in), RAG pipelines, memory/persistence, multi-agent patterns, MCP integration, human-in-the-loop, and deployment. Includes 22 reference docs: agents, models, providers, tools, structured output, streaming, memory (checkpointers + stores), middleware (catalog + patterns), MCP, HITL, multi-agent, RAG, LangGraph (core + execution), knowledge agents, deployment (local + production), observability (tracing + evaluation), and common errors. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-copilot-sdk-app
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-server
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-client
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-agent
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-apps-widgets
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-langchain-ts-app
```

---

## OpenClaw Platform

Skills for building on the OpenClaw open-source AI agent runtime — skill authoring, plugin development, agent configuration, multi-agent orchestration, workflow automation, and production deployment.

| Skill | What it does |
|---|---|
| **[build-openclaw-skill](skills/build-openclaw-skill/)** | Creates custom OpenClaw skills — SKILL.md format, YAML frontmatter, metadata gating with bins/env/config requirements, reference file organization, skill testing, and ClawHub publishing. Includes 5 reference docs: format spec, metadata gating, reference organization, testing methodology, and ClawHub publishing. |
| **[build-openclaw-plugin](skills/build-openclaw-plugin/)** | Builds OpenClaw plugins — plugin manifests (`openclaw.plugin.json`), tool registration with typed definitions, channel/model-provider/speech/image-generator setup, skill bundling, tool profiles (full/coding/messaging/minimal), and allow/deny restrictions. Includes 6 reference docs: plugin manifest, tool registration, channel/provider setup, plugin lifecycle, tool profiles, and plugin skills bundling. |
| **[init-openclaw-agent](skills/init-openclaw-agent/)** | Configures OpenClaw agent workspaces — IDENTITY.md authoring, tool profile selection across 4 presets, allow/deny list rules with group shortcuts, skills loading with precedence and extra dirs, memory configuration, and security hardening with exec approvals and sandbox isolation. Includes 5 reference docs: agent identity, tool profiles, tool restrictions, skills loading, and security patterns. |
| **[run-openclaw-agents](skills/run-openclaw-agents/)** | Orchestrates OpenClaw multi-agent systems — session lifecycle management, sub-agent spawning with scoped tool profiles, ACP routing for specialized coordination, cross-agent messaging, and risk classification across 11 orchestration tools. Includes 5 reference docs: session management, sub-agent patterns, ACP routing, messaging patterns, and risk/security. |
| **[build-openclaw-workflow](skills/build-openclaw-workflow/)** | Builds OpenClaw automation workflows — Lobster typed workflows with resumable approvals, cron scheduled jobs with safety rules, LLM task chains for structured output, browser automation via built-in Chromium, and gateway/exec management. Includes 5 reference docs: Lobster workflows, cron scheduling, LLM task chains, browser automation, and gateway/exec. |
| **[run-openclaw-deploy](skills/run-openclaw-deploy/)** | Deploys OpenClaw to production — Docker/Podman/Nix/Ansible container setup, VPS provisioning, security hardening (exec approvals, tool restrictions, sandbox isolation), gateway management with 5+ messaging channels, monitoring with health checks and cost tracking, and backup/restore. Includes 5 reference docs: container setup, security hardening, gateway management, monitoring/ops, and container patterns. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-openclaw-skill
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-openclaw-plugin
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-openclaw-agent
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-openclaw-agents
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-openclaw-workflow
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-openclaw-deploy
```

---

## Skill Research & Discovery

Skills for searching, discovering, and downloading AI coding skills from the playbooks.com registry.

| Skill | What it does |
|---|---|
| **[use-skill-dl-util](skills/use-skill-dl-util/)** | Drives the skill-dl CLI (v1.3.0) for searching and downloading AI skills — Serper-powered Google search across playbooks.com, keyword ranking, batch downloads with repo-level parallelism, corpus inspection, and pipe-friendly workflows. Includes reference docs: search strategies, download patterns, and corpus inspection. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/use-skill-dl-util
```

---

## Contributing

Want to add a new skill or improve an existing one? See **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## License

MIT
