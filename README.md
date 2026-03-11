# skills-by-yigitkonur

19 skills for AI coding agents — agent configuration, code review, design extraction, browser automation, planning, research, framework guides, SDK guides, language standards, UI component libraries, and CI/CD.

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
| **[init-agent-config](skills/init-agent-config/)** | Generates AGENTS.md (cross-agent standard, 20+ tools) and/or CLAUDE.md (Claude Code–specific) using the WHAT/WHY/HOW framework, dual-file architecture, progressive disclosure, and quality scoring. Includes 5 reference docs: best practices with scoring rubric, Claude memory hierarchy, AGENTS.md discovery spec, cross-agent compatibility matrix for 16 agents, and unified templates for 8 project types. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-agent-config
```

---

## Code Review

Skills for reviewing pull requests and setting up AI code review platform configuration.

| Skill | What it does |
|---|---|
| **[review-pr](skills/review-pr/)** | Systematic PR review using the `gh` CLI — seven-phase workflow covering context gathering, file clustering, existing comment correlation, goal validation, per-cluster review across 7 dimensions (security, correctness, data integrity, performance, API contract, maintainability, testing), cross-cutting analysis, and structured output with severity calibration. Includes 10 reference docs: review workflow, gh CLI reference, file clustering, comment correlation, review dimensions, diff analysis, output templates, anti-patterns, severity guide, and language-specific patterns. |
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

## Planning & Research

Skills that provide structured methodologies for decision-making and multi-source research.

| Skill | What it does |
|---|---|
| **[plan-work](skills/plan-work/)** | Structured planning skill for any task — intake framing, root cause analysis, option design, prioritization, systems thinking, technical strategy, communication alignment, and execution risk. Includes 10 reference docs covering 9 thinking method families and a catalog of 40+ named methods (pre-mortem, Cynefin, RICE, wardley mapping, etc.). |
| **[run-research](skills/run-research/)** | Research methodology for coding agents using the Research Powerpack MCP server — turns single-query searches into multi-source validated workflows with Google, Reddit, and page scraping. Includes 10 domain-specific reference docs: architecture, API integration, bug fixing, frontend, performance, security, testing, DevOps, and language idioms. |
| **[build-skills](skills/build-skills/)** | Skill creation methodology skill for building or redesigning Claude skills from workspace evidence, remote research, and comparison before synthesis. Use when a skill should be original, traceable, and repo-fit instead of improvised. Includes reference docs for research workflow, remote sources, comparison workflow, and source-pattern selection. |
| **[test-skill-quality](skills/test-skill-quality/)** | Derailment Testing methodology — follow a skill's workflow literally on a real task, document every friction point (P0/P1/P2) where instructions fail to specify the next action, classify root causes, apply proven fix patterns, and verify with grep-based consistency checks. Includes 5 reference docs: friction classification, root cause taxonomy, 9 fix patterns, metrics/iteration tracking, and domain adaptation guide. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/plan-work
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-skills
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/test-skill-quality
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

## Language Standards

Deep reference skills for language-level type safety, patterns, and anti-patterns.

| Skill | What it does |
|---|---|
| **[develop-typescript](skills/develop-typescript/)** | Strict TypeScript development guide covering type system patterns, anti-patterns with fixes, error handling strategies, and compiler configuration across application, library, CLI, and backend codebases. Includes 4 reference docs: anti-patterns, patterns, type-system, and strict-config. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/develop-typescript
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

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-supastarter-app
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/debug-tauri-devtools
```

---

## SDK Guides

Deep reference skills for building applications with AI platform SDKs.

| Skill | What it does |
|---|---|
| **[build-copilot-sdk-app](skills/build-copilot-sdk-app/)** | Complete developer guide for the GitHub Copilot SDK (`@github/copilot-sdk`) in TypeScript/Node.js — client setup, sessions, custom tools with Zod schemas, streaming events, permissions, hooks, custom agents, MCP servers, skills, BYOK providers, plan/autopilot/fleet modes, multi-client architectures, and Ralph loop autonomous dev patterns. Includes 10 reference docs: client/transport, sessions, tools/schemas, events/streaming, permissions, hooks, agents/MCP/skills, auth/BYOK, advanced patterns, and type reference. |

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-copilot-sdk-app
```

---

## Contributing

Want to add a new skill or improve an existing one? See **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## License

MIT
