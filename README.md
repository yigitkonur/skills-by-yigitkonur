# skills-by-yigitkonur

16 skills for AI coding agents — code review setup, design extraction, MCP tooling, browser automation, planning, research, framework guides, and language standards.

## Install the full pack

```bash
npx skills add yigitkonur/skills-by-yigitkonur
```

## Install a single skill

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

Examples:

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/skill-builder
npx skills add yigitkonur/skills-by-yigitkonur/skills/research-powerpack
npx skills add yigitkonur/skills-by-yigitkonur/skills/playwright-cli
```

## How discovery works

Each skill uses its `SKILL.md` frontmatter description as a trigger. Install the full pack when you want broad coverage, or install a single skill from the `skills/` subdirectory when you want a narrower setup.

---

## Code Review Setup

Skills that analyze your repo and generate review configuration files for AI code review platforms.

| Skill | What it does |
|---|---|
| **[greptile-config](skills/greptile-config/)** | Generates `.greptile/config.json`, `rules.md`, and `files.json` with semantic rules scoped to your repo's actual architecture — not linter-level checks, but cross-file implications that require LLM understanding. Includes 3 reference docs covering the full config spec, 11 example scenarios (TypeScript, Python, Go, Rust, Tauri, MCP, Next.js), and an anti-patterns/troubleshooting guide. |
| **[devin-review-init](skills/devin-review-init/)** | Generates `REVIEW.md` and `AGENTS.md` for Devin's Bug Catcher by exploring your repo structure, tech stack, and pain points, then producing prioritized review rules with code examples. Includes 2 reference docs: the full instruction file spec and 8 complete scenario templates (API, dashboard, Tauri, MCP, monorepo). |
| **[copilot-review-init](skills/copilot-review-init/)** | Generates a root `copilot-instructions.md` plus path-scoped `*.instructions.md` micro-files that stay within Copilot's 4,000-character processing limit. Includes 4 reference docs: instruction spec, micro-library of 50+ reusable rule blocks, 10 scenario templates, and an anti-patterns guide. |

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/greptile-config
npx skills add yigitkonur/skills-by-yigitkonur/skills/devin-review-init
npx skills add yigitkonur/skills-by-yigitkonur/skills/copilot-review-init
```

---

## Design Extraction

Skills that forensically parse real CSS/JS from existing sites and produce structured design documentation or buildable projects.

| Skill | What it does |
|---|---|
| **[design-soul-saas](skills/design-soul-saas/)** | Extracts the complete visual DNA from any SaaS dashboard or admin panel codebase — every token, component state, animation keyframe, and responsive breakpoint — into structured documentation that lets a builder recreate the exact look-and-feel without copying source. Includes 6 reference docs: component/system templates, dashboard patterns catalog, foundations and components agent guides, and a quality checklist. |
| **[snapshot-to-nextjs](skills/snapshot-to-nextjs/)** | Converts browser "Save As" HTML snapshots into buildable Next.js App Router projects with zero third-party dependencies — self-hosted fonts, images, icons, and a Tailwind config grounded on real extracted CSS values (no approximations, no guessing). Includes 6 reference docs: foundations/sections agent guides, section/system templates, website patterns catalog, and a quality checklist. |

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/design-soul-saas
npx skills add yigitkonur/skills-by-yigitkonur/skills/snapshot-to-nextjs
```

---

## MCP Tooling

Skills for building, testing, debugging, and reviewing MCP (Model Context Protocol) servers and clients.

| Skill | What it does |
|---|---|
| **[mcp-server-tester](skills/mcp-server-tester/)** | Tests MCP servers through two modes: protocol-level verification across 19 checks (transport, schema, errors, timeouts), and LLM-powered end-to-end testing with domain-adaptive business case generation. Includes 6 reference docs: basic/LLM test guides, Inspector API reference, provider patterns, business cases, and troubleshooting. |
| **[test-mcp-by-cli](skills/test-mcp-by-cli/)** | Behavior-verified guide for testing MCP servers with `philschmid/mcp-cli` v0.3.0 — 8-phase verification, config and JSON argument patterns, raw `call` response parsing with `jq`, and troubleshooting for daemon, auth, and argument failures. Includes 4 reference docs: testing flow, configuration and arguments, output/debugging/chaining, and errors/recovery. |
| **[mcp-apps-builder](skills/mcp-apps-builder/)** | Reference for building MCP apps with the mcp-use framework — server creation, tool/resource/prompt handlers, widget system, authentication (Supabase/WorkOS/custom), and deployment. Includes 16 reference docs across foundations, server patterns, widget guides, and auth providers. |
| **[mcp-use-code-review](skills/mcp-use-code-review/)** | Code review skill for Python apps using the `mcp-use` pip package — catches the 6 most common AI-agent derailment patterns: leaked connections, missing timeouts, improper error handling, session lifecycle bugs, namespace collisions, and auth misuse. Includes 10 reference docs covering async lifecycle, tools deep-dive, LangChain bridge, server config, deployment, and migration from the TypeScript SDK. |

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/mcp-server-tester
npx skills add yigitkonur/skills-by-yigitkonur/skills/test-mcp-by-cli
npx skills add yigitkonur/skills-by-yigitkonur/skills/mcp-apps-builder
npx skills add yigitkonur/skills-by-yigitkonur/skills/mcp-use-code-review
```

---

## Browser Automation

| Skill | What it does |
|---|---|
| **[playwright-cli](skills/playwright-cli/)** | Reliable operational guide for `@anthropic-ai/playwright-cli` grounded in installed-CLI behavior — chrome bootstrap, observe-act proof loops, form/upload verification, tab/session coordination, console/network artifacts, visual checks, and advanced `run-code` recipes. Includes 7 reference docs: command reference, session/tab management, forms/data, visual testing, debugging, async/advanced recipes, and orchestrator guide. |

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/playwright-cli
```

---

## Planning & Research

Skills that provide structured methodologies for decision-making and multi-source research.

| Skill | What it does |
|---|---|
| **[planning](skills/planning/)** | Structured planning skill for any task — intake framing, root cause analysis, option design, prioritization, systems thinking, technical strategy, communication alignment, and execution risk. Includes 10 reference docs covering 9 thinking method families and a catalog of 40+ named methods (pre-mortem, Cynefin, RICE, wardley mapping, etc.). |
| **[research-powerpack](skills/research-powerpack/)** | Research methodology for coding agents using the Research Powerpack MCP server — turns single-query searches into multi-source validated workflows with Google, Reddit, and page scraping. Includes 10 domain-specific reference docs: architecture, API integration, bug fixing, frontend, performance, security, testing, DevOps, and language idioms. |
| **[skill-builder](skills/skill-builder/)** | Skill creation methodology skill for building or redesigning Claude skills from workspace evidence, remote research, and comparison before synthesis. Use when a skill should be original, traceable, and repo-fit instead of improvised. Includes reference docs for research workflow, remote sources, comparison workflow, and source-pattern selection. |

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/planning
npx skills add yigitkonur/skills-by-yigitkonur/skills/research-powerpack
npx skills add yigitkonur/skills-by-yigitkonur/skills/skill-builder
```

---

## Language Standards

Deep reference skills for language-level type safety, patterns, and anti-patterns.

| Skill | What it does |
|---|---|
| **[typescript](skills/typescript/)** | Strict TypeScript development guide covering type system patterns, anti-patterns with fixes, error handling strategies, and compiler configuration across application, library, CLI, and backend codebases. Includes 4 reference docs: anti-patterns, patterns, type-system, and strict-config. |

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/typescript
```

---

## Framework Guides

Deep reference skills for specific frameworks and tools.

| Skill | What it does |
|---|---|
| **[supastarter](skills/supastarter/)** | Comprehensive developer guide for the SupaStarter Next.js SaaS boilerplate — monorepo architecture, App Router layout chains, oRPC API patterns, Better Auth, Prisma, Stripe payments, organizations, mail, i18n, S3 storage, UI conventions, analytics, and deployment. Includes 93 reference docs organized across 20 domains with cheatsheets for commands, env vars, file locations, and imports. |
| **[tauri-devtools](skills/tauri-devtools/)** | CrabNebula DevTools integration for debugging Tauri v2 apps — gives AI agents visibility into the Rust side with console logs, tracing spans, IPC call timings, live config inspection, and frontend source browsing. Includes 5 reference docs: architecture deep-dive, IPC span anatomy, integration patterns, tab reference, and common debugging scenarios. |

```bash
npx skills add yigitkonur/skills-by-yigitkonur/skills/supastarter
npx skills add yigitkonur/skills-by-yigitkonur/skills/tauri-devtools
```

---

## Contributing

Want to add a new skill or improve an existing one? See **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## License

MIT
