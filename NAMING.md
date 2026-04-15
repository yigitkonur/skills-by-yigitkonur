# Naming Standard

This repo is a **single skills pack**. Every skill name starts with a verb prefix that signals its primary function.

## The Rule

Every skill directory, `SKILL.md` frontmatter `name`, and README label must:
- Start with a verb prefix from the table below
- Use `kebab-case`
- Be short, stable, and install-path-friendly
- Match exactly across directory name, frontmatter `name`, and README label

## Verb-First Naming

Every skill name follows the pattern **`verb-object`** where:
- **verb** — a single English verb from the prefix registry that tells the user *what the skill does* at a glance
- **object** — a short noun phrase that tells the user *what it acts on* (`pr`, `typescript`, `npm-package`, `tauri-devtools`)

The verb is the most important word in the name. A user scanning a list of 50 skills should be able to filter by verb alone: "I want to build something" → look at `build-*`, "I need to set something up" → look at `init-*`.

### Why verb-first

- **Sortable** — `ls skills/` groups skills by action, not by technology
- **Predictable** — a new contributor can guess the right prefix without reading this file
- **Disambiguating** — the verb separates skills that touch the same technology but serve different purposes (e.g., `build-mcp-use-server` vs `optimize-mcp-server` vs `debug-mcp-server`)

## Prefix Registry

Each prefix has a **definition**, a **boundary** (what falls outside it), and **disambiguation rules** against the prefixes it's most often confused with.

### `build-`

**Definition:** Create, scaffold, author, or extend a project, application, or artifact using a specific framework, SDK, or tool. The skill teaches the agent how to produce working code within that ecosystem.

**Boundary:** The output is *new or modified source code* in the user's project. If the skill doesn't produce code that ships in the user's repo, it's not `build-`.

**Use when:** The agent writes application code, scaffolds a project, or extends a codebase using a framework/SDK/library.
**Not when:** The agent generates config files for a third-party platform (`init-`), runs an external tool (`run-`), or reviews existing code (`review-`).

**Disambiguation:**
- `build-` vs `init-` — `build-` produces application code; `init-` produces config/instruction files for external tools
- `build-` vs `convert-` — `build-` starts from requirements; `convert-` starts from an existing artifact in a different format
- `build-` vs `develop-` — `build-` is framework-specific ("build a Supastarter app"); `develop-` is language-level ("write TypeScript correctly")

**Current skills:** `build-chrome-extension`, `build-convex-clerk-swiftui`, `build-copilot-sdk-app`, `build-daisyui-mcp`, `build-hcom-systems`, `build-langchain-ts-app`, `build-mcp-use-agent`, `build-mcp-use-apps-widgets`, `build-mcp-use-client`, `build-mcp-use-server`, `build-openclaw-plugin`, `build-openclaw-skill`, `build-openclaw-workflow`, `build-raycast-script-command`, `build-skills`, `build-supastarter-app`

---

### `convert-`

**Definition:** Transform an existing artifact from one format, framework, or representation into another. The input is a concrete source (file, snapshot, export); the output is a functionally equivalent artifact in the target format.

**Boundary:** There must be a *source artifact* that the skill reads and a *target format* it produces. If the skill creates something from scratch, it's `build-`, not `convert-`.

**Use when:** The agent takes an existing file/snapshot/export and produces a new project or file in a different format.
**Not when:** The agent writes code from requirements (`build-`), or extracts documentation without producing a buildable artifact (`extract-`).

**Disambiguation:**
- `convert-` vs `build-` — `convert-` requires an existing source artifact; `build-` starts from requirements or a blank slate
- `convert-` vs `extract-` — `convert-` produces a *buildable project*; `extract-` produces *documentation or structured data*

**Current skills:** `convert-snapshot-nextjs`, `convert-vue-nextjs`

---

### `debug-`

**Definition:** Inspect, diagnose, or troubleshoot a running or built application using a specific debugging tool or observability platform. The skill teaches the agent how to use the tool to find and understand problems.

**Boundary:** The skill connects the agent to a *diagnostic tool*. If the agent is fixing code directly without a diagnostic tool, that's normal coding, not a skill. If the agent is running a test suite, that's `test-`.

**Use when:** The agent uses a dedicated debugging/observability tool (DevTools, profilers, tracers) to investigate issues.
**Not when:** The agent runs a test suite (`test-`), reviews code for issues (`review-`), or writes code to fix a known bug (`build-`).

**Disambiguation:**
- `debug-` vs `test-` — `debug-` uses diagnostic tools to investigate unknowns; `test-` runs a verification suite against known expectations
- `debug-` vs `review-` — `debug-` is live inspection of a running/built app; `review-` is static analysis of source diffs

**Current skills:** `debug-tauri-devtools`

---

### `develop-`

**Definition:** Apply language-level standards, type system patterns, idioms, and anti-patterns when writing or reviewing code in a specific programming language. The skill is about *how to write the language correctly*, not about any particular framework.

**Boundary:** Scoped to *language-level* concerns — type safety, compiler config, idiomatic patterns. Framework-specific guidance belongs under `build-`.

**Use when:** The agent writes, reviews, or refactors code and needs language-level quality standards (strict types, anti-patterns, compiler flags).
**Not when:** The agent works within a specific framework (`build-`), or reviews a PR as a whole (`review-`).

**Disambiguation:**
- `develop-` vs `build-` — `develop-` is language-wide ("TypeScript strict mode everywhere"); `build-` is framework-specific ("build a Next.js app with Supastarter")
- `develop-` vs `review-` — `develop-` provides standards to apply *while writing*; `review-` evaluates *already-written* code in a PR context

**Current skills:** `develop-clean-architecture`, `develop-macos-hig`, `develop-macos-liquid-glass`, `develop-typescript`

---

### `extract-`

**Definition:** Forensically analyze an existing codebase, design, or system and produce structured documentation that captures its visual DNA, architecture, or patterns — without producing a buildable project.

**Boundary:** The output is *documentation or structured data*, not runnable code. If the output is a buildable project, it's `convert-`.

**Use when:** The agent reads source code/CSS/assets and produces design tokens, component catalogs, or architecture docs.
**Not when:** The agent produces a buildable project from the source (`convert-`), or writes new application code (`build-`).

**Disambiguation:**
- `extract-` vs `convert-` — `extract-` produces documentation; `convert-` produces a buildable project
- `extract-` vs `review-` — `extract-` documents the *design system*; `review-` evaluates *code quality*

**Current skills:** `extract-saas-design`

---

### `enhance-`

**Definition:** Test and improve the instructional quality of an existing skill, prompt, or agent artifact by running it through real-world usage, analyzing failure points, and applying targeted fixes.

**Boundary:** The skill improves *instruction quality* through empirical testing. If the skill creates something new from scratch, it's `build-`. If it audits code, it's `review-` or `optimize-`.

**Use when:** The agent improves a skill's SKILL.md by running it, reading the execution trace, and fixing instruction gaps. Or when the agent restructures a prompt for better LLM performance.
**Not when:** The agent creates a skill from scratch (`build-skills`), reviews code (`review-`), or runs verification tests (`test-`).

**Disambiguation:**
- `enhance-` vs `build-` — `enhance-` improves an existing artifact's quality; `build-` creates from scratch
- `enhance-` vs `optimize-` — `enhance-` focuses on instructional/prompt quality; `optimize-` focuses on system performance
- `enhance-` vs `test-` — `enhance-` includes the fix step; `test-` only verifies

**Current skills:** `enhance-prompt`, `enhance-skill-by-derailment`

---

### `init-`

**Definition:** Generate configuration, instruction, or setup files that a third-party tool or platform reads. The skill analyzes the user's repo and produces tailored config files — not application code.

**Boundary:** The output is *config/instruction files consumed by an external tool* (Greptile, Devin, Copilot, Claude). If the output is application code, it's `build-`.

**Use when:** The agent generates `.greptile/config.json`, `REVIEW.md`, `copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`, or similar tool-consumed files.
**Not when:** The agent writes application code (`build-`), or runs the tool after setup (`run-`).

**Disambiguation:**
- `init-` vs `build-` — `init-` produces config for external tools; `build-` produces application code
- `init-` vs `run-` — `init-` generates files once; `run-` executes a tool repeatedly during a session
- Multiple related surfaces for one configuration problem can be combined into one skill (e.g. `init-agent-config` can own `AGENTS.md`, `REVIEW.md`, and native review adapters for one repo)

**Current skills:** `init-agent-config`, `init-openclaw-agent`

---

### `optimize-`

**Definition:** Evaluate and enhance an existing system's quality, performance, or adherence to best practices. The skill audits what exists and recommends specific improvements — it does not build from scratch.

**Boundary:** The agent *evaluates and improves* an existing system. If the agent creates a new system, it's `build-`. If the agent applies language-level standards, it's `develop-`.

**Use when:** The agent audits an existing server/application against quality patterns and recommends/applies specific optimizations.
**Not when:** The agent builds from scratch (`build-`), applies language-level patterns (`develop-`), or reviews a PR (`review-`).

**Disambiguation:**
- `optimize-` vs `build-` — `optimize-` improves existing code; `build-` creates new code
- `optimize-` vs `review-` — `optimize-` actively applies improvements; `review-` only evaluates
- `optimize-` vs `develop-` — `optimize-` is system-specific (MCP servers); `develop-` is language-wide (TypeScript)

**Current skills:** `optimize-mcp-server`

---

### `plan-`

**Definition:** Apply structured decision-making, prioritization, or problem-framing methodologies before taking action. The skill provides thinking frameworks, not code.

**Boundary:** The output is a *decision, plan, or analysis* — not code or config. If the skill produces files, it's a different prefix.

**Use when:** The agent needs to frame a problem, compare options, prioritize work, or apply a named methodology (pre-mortem, RICE, Cynefin).
**Not when:** The agent writes code (`build-`), generates config (`init-`), or researches external information (`run-`).

**Disambiguation:**
- `plan-` vs `run-` — `plan-` is internal reasoning with structured methods; `run-research` is external information gathering via APIs and web scraping

**Current skills:** *(none currently — prefix reserved for future use)*

---

### `publish-`

**Definition:** Automate package publishing, release workflows, and CI/CD pipelines. The skill produces deployment configuration — GitHub Actions workflows, release scripts, and authentication setup.

**Boundary:** Scoped to *release and publishing automation*. General CI/CD that doesn't publish a package (like running tests in CI) is not `publish-`.

**Use when:** The agent sets up automated publishing to a package registry (npm, PyPI) or creates release workflows.
**Not when:** The agent writes application code (`build-`), or generates non-CI config files (`init-`).

**Disambiguation:**
- `publish-` vs `init-` — `publish-` produces CI/CD workflows for releasing packages; `init-` produces config for development tools
- `publish-` vs `build-` — `publish-` automates the release pipeline; `build-` writes the application being released

**Current skills:** `publish-npm-package`

---

### `review-`

**Definition:** Evaluate existing code for correctness, security, performance, and quality. The skill provides a systematic methodology for assessing code that has already been written — in a PR, a file, or a codebase.

**Boundary:** The agent *reads and evaluates* existing code. If the agent *writes* new code, it's `build-` or `develop-`. If the agent *generates review config* for a platform, it's `init-`.

**Use when:** The agent reviews a pull request, audits a codebase, or checks code against quality dimensions.
**Not when:** The agent generates review rules for a platform (`init-`), applies language standards while writing new code (`develop-`), or debugs a running app (`debug-`).

**Disambiguation:**
- `review-` vs `init-` — `review-` *performs* the review; `init-` *configures* a review platform
- `review-` vs `develop-` — `review-` evaluates after the fact; `develop-` guides while writing
- `review-` vs `debug-` — `review-` is static analysis of source; `debug-` is live inspection of runtime

**Current skills:** `review-pr`

---

### `run-`

**Definition:** Execute an external CLI tool, browser automation framework, or multi-source workflow as part of the agent's task. The skill teaches the agent the correct command sequences, interaction patterns, and output handling for a specific tool.

**Boundary:** The agent *drives an external tool* during the session. If the tool runs once to generate files and then the agent is done, consider `init-` or `publish-`.

**Use when:** The agent operates a browser (Playwright, Browserbase), queries external APIs (Google, Reddit), or executes a CLI tool that requires multi-step interaction.
**Not when:** The agent generates static config (`init-`), writes application code (`build-`), or uses a diagnostic tool to investigate bugs (`debug-`).

**Disambiguation:**
- `run-` vs `debug-` — `run-` drives a tool for a productive task; `debug-` drives a tool for diagnosis
- `run-` vs `init-` — `run-` is an ongoing session with the tool; `init-` is a one-time generation
- `run-` vs `test-` — `run-` drives any external tool; `test-` specifically runs verification/validation suites

**Current skills:** `run-agent-browser`, `run-athena-flow`, `run-github-scout`, `run-hcom-agents`, `run-issue-tree`, `run-openclaw-agents`, `run-openclaw-deploy`, `run-playwright`, `run-research`

---

### `test-`

**Definition:** Validate, verify, or run QA checks against a server, API, protocol implementation, or codebase. The skill defines what to test, how to test it, and how to interpret results.

**Boundary:** The agent *runs a verification suite* with pass/fail expectations. If the agent is investigating an unknown problem, it's `debug-`. If the agent is driving a tool for a non-verification purpose, it's `run-`.

**Use when:** The agent tests an MCP server against a protocol spec, runs an API compatibility suite, or validates a build artifact.
**Not when:** The agent investigates an unknown bug (`debug-`), reviews source code (`review-`), or drives a browser for data extraction (`run-`).

**Disambiguation:**
- `test-` vs `debug-` — `test-` checks against known expectations; `debug-` investigates unknowns
- `test-` vs `run-` — `test-` is specifically about verification; `run-` is about general tool execution
- `test-` vs `review-` — `test-` runs the code and checks output; `review-` reads the code and checks quality

**Current skills:** `test-by-mcpc-cli`, `test-macos-snapshots`

---

### `use-`

**Definition:** Drive a specific CLI utility to accomplish a targeted workflow. The skill teaches the agent the correct commands, flags, and patterns for a particular utility.

**Boundary:** Scoped to a *single CLI utility* with a focused workflow. If the tool is a browser or multi-step external API, prefer `run-`. If the tool generates config once, prefer `init-`.

**Use when:** The agent operates a single CLI utility for a specific task (downloading skills, formatting files, etc.).
**Not when:** The agent drives a browser or multi-step API workflow (`run-`), generates config files (`init-`), or runs verification suites (`test-`).

**Disambiguation:**
- `use-` vs `run-` — `use-` is a single-utility focused workflow; `run-` is broader external tool/API orchestration
- `use-` vs `init-` — `use-` executes the tool repeatedly; `init-` generates files once

**Current skills:** *(none currently — prefix reserved for future use)*

---

## Choosing a Prefix — Decision Tree

```
What does the skill primarily do?
│
├─ Writes application code using a framework/SDK?
│  └─► build-
│
├─ Transforms an existing artifact into a different format?
│  └─► convert-
│
├─ Uses a diagnostic tool to investigate runtime behavior?
│  └─► debug-
│
├─ Applies language-level patterns and standards while coding?
│  └─► develop-
│
├─ Tests and improves instructional quality of a skill or prompt?
│  └─► enhance-
│
├─ Reads a codebase and produces design documentation?
│  └─► extract-
│
├─ Generates config/instruction files for an external tool?
│  └─► init-
│
├─ Evaluates and enhances an existing system's quality?
│  └─► optimize-
│
├─ Applies structured thinking methods to frame a decision?
│  └─► plan-
│
├─ Automates package releasing and CI/CD publishing?
│  └─► publish-
│
├─ Evaluates existing code for quality, security, correctness?
│  └─► review-
│
├─ Drives an external CLI tool or API for a productive task?
│  └─► run-
│
├─ Runs verification/validation checks with pass/fail criteria?
│  └─► test-
│
├─ Drives a single CLI utility for a focused workflow?
│  └─► use-
│
└─ None of the above?
   └─► Propose a new prefix (see "Adding a New Verb Prefix")
```

## Object Naming

The object part (everything after the verb prefix) follows these rules:

1. **Name the thing acted on**, not the skill's internal technique — `build-supastarter-app` not `build-with-orpc-and-prisma`
2. **Use the ecosystem's own name** when one exists — `daisyui-mcp` not `component-library-server`
3. **Keep it short** — 2-3 words max after the verb: `run-playwright`, `init-agent-config`, `review-pr`
4. **Avoid generic suffixes** — no `-guide`, `-helper`, `-util`, `-tool`, `-v2`, `-final`
5. **Avoid redundancy with the verb** — `test-mcp-server` not `test-mcp-server-tests`
6. **Prefer specificity** — `publish-npm-package` not `publish-package` (which registry?)

## Canonical Rules

### 1) Directory name
- Must start with a verb prefix from the registry above
- Use short, stable, install-path-friendly `kebab-case`
- Prefer the name users would actually type in an install command
- Avoid suffixes like `-guide`, `-migrate`, `-v2`, or `-final`

### 2) `SKILL.md` frontmatter `name`
- Must exactly match the directory name
- No aliases, no legacy names

### 3) README label
- Must exactly match the directory name and frontmatter `name`
- If the displayed name differs from the install path, the repo becomes harder to scan and trust

### 4) Cross-skill references
- Always use canonical repo-local names

### 5) Description standard
Every skill description is canonical metadata, not body copy.

Required format:
- Start with `Use skill if you are`
- 30 words or fewer
- Describe when the skill should trigger, not what the body contains
- Use concrete user intent, tools, file patterns, or workflows when helpful
- Stay specific enough to avoid overlap with nearby skills

Good:
- `Use skill if you are setting up GitHub Copilot review behavior with copilot-instructions.md or scoped *.instructions.md files for repo-specific pull request review.`
- `Use skill if you are converting saved HTML snapshots into buildable Next.js pages with self-hosted assets and extracted styles.`

Weak:
- `Best MCP skill ever.`
- `Research guide.`
- `Mandatory for all work.`

## Naming Anti-Patterns

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| No verb prefix (`agent-browser`) | Can't scan by action; breaks sort order | `run-agent-browser` |
| Noun-first (`typescript-develop`) | Verb-first is the convention; noun-first hides the action | `develop-typescript` |
| Generic suffix (`mcp-guide`, `pr-helper`) | Adds noise, implies the skill is advisory instead of operational | `build-mcp-sdk-server`, `review-pr` |
| Version suffix (`snapshot-nextjs-v2`) | Versions belong in git history, not in names | `convert-snapshot-nextjs` |
| Marketing name as primary ID (`soul`, `powerpack`) | Cute names don't sort or predict; use them in the SKILL.md title if desired | Use the verb-object pattern for the directory name |
| Mismatched names across files | Directory says `snapshot-to-nextjs`, frontmatter says `convert-snapshot-nextjs` | Pick one canonical name and use it everywhere |
| Overly broad object (`build-app`, `run-tool`) | Doesn't tell the user *which* app or *which* tool | `build-supastarter-app`, `run-playwright` |

## Adding a New Verb Prefix

If none of the existing prefixes fit:
1. Check whether an existing prefix can stretch to cover the use case
2. If not, propose the new prefix in a PR with at least one concrete skill example
3. Keep the prefix to a single common English verb
4. Write the full prefix entry: definition, boundary, use/not-use, disambiguation, and at least one current skill

## Migration Rule

When renaming a published skill:
1. Rename the directory
2. Update frontmatter `name` to match
3. Update frontmatter `description` to current standard
4. Update README label and install commands
5. Update NAMING.md canonical list
6. Update all cross-skill references

## Current Canonical Skill Names

- `build-chrome-extension`
- `build-convex-clerk-swiftui`
- `build-copilot-sdk-app`
- `build-daisyui-mcp`
- `build-hcom-systems`
- `build-langchain-ts-app`
- `build-mcp-use-agent`
- `build-mcp-use-apps-widgets`
- `build-mcp-use-client`
- `build-mcp-use-server`
- `build-openclaw-plugin`
- `build-openclaw-skill`
- `build-openclaw-workflow`
- `build-raycast-script-command`
- `build-skills`
- `build-supastarter-app`
- `convert-snapshot-nextjs`
- `convert-vue-nextjs`
- `debug-tauri-devtools`
- `develop-clean-architecture`
- `develop-macos-hig`
- `develop-macos-liquid-glass`
- `develop-typescript`
- `enhance-prompt`
- `enhance-skill-by-derailment`
- `extract-saas-design`
- `init-agent-config`
- `init-openclaw-agent`
- `optimize-mcp-server`
- `publish-npm-package`
- `review-pr`
- `run-agent-browser`
- `run-athena-flow`
- `run-github-scout`
- `run-hcom-agents`
- `run-issue-tree`
- `run-openclaw-agents`
- `run-openclaw-deploy`
- `run-playwright`
- `run-research`
- `test-by-mcpc-cli`
- `test-macos-snapshots`
