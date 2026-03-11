---
name: init-agent-config
description: Use skill if you are generating, auditing, or migrating repo-grounded AGENTS.md and CLAUDE.md files, especially for dual-file setups, multi-agent compatibility, or converting existing agent config.
---

# Init Agent Config

Generate agent configuration that reflects the actual repository, not a generic template. Use `AGENTS.md` for universal cross-agent guidance. Use `CLAUDE.md` for Claude Code memory and Claude-only features. When both are needed, `AGENTS.md` is the shared source of truth and `CLAUDE.md` stays thin.

## Use this skill for

- creating new `AGENTS.md` and/or `CLAUDE.md` from repo evidence
- tightening noisy or stale agent config
- migrating standalone `CLAUDE.md` into a dual-file setup
- extracting universal project rules from `.cursorrules`, `copilot-instructions.md`, or other agent config
- designing repo-level plus monorepo/package-level instruction boundaries

## Do not use this skill for

- `.github/copilot-instructions.md` or `*.instructions.md` review config → use `init-copilot-review`
- `REVIEW.md` or Devin-specific review setup → use `init-devin-review`
- Greptile config setup → use `init-greptile-review`
- writing generic "AI coding guidelines" without inspecting a real repository

## Non-negotiables

- Inspect the repository before drafting anything.
- Verify commands and paths against real files; never invent them.
- Keep universal guidance in `AGENTS.md`. Keep Claude-only syntax and features out of `AGENTS.md`.
- Complement existing config; do not blindly replace it.
- Preserve existing `Always`, `Ask`, `Never`, `WARNING`, `CRITICAL`, and `DO NOT` rules unless the repo proves they are obsolete.
- Prefer high-signal directives over long prose. If a line would not prevent a mistake, cut it.

## Anti-derail guardrails

- If the draft starts to read like a generic style guide, stop and replace broad advice with repo-specific facts or remove it.
- Do not create shared defaults in `AGENTS.override.md` or `CLAUDE.local.md`; those are override/personal layers.
- Do not invent `.claude/`, `agent_docs/`, or nested `AGENTS.md` structure without a concrete repo need.
- If the correct agent surface is unclear, default to the smallest verified setup and explain the tradeoff instead of emitting speculative extra files.
- If existing config is already mostly correct, switch from rewrite mode to audit/tighten mode.

## Workflow

### 1) Scope the request first

Classify the job before reading deeply:

| Request type | What to produce |
|-------------|-----------------|
| New setup | Fresh `AGENTS.md`, `CLAUDE.md`, or both |
| Audit | Findings + targeted edits, not a full rewrite by default |
| Migration | Preserve valid rules, convert format, remove duplication |
| Extension | Add missing file(s) or Claude-specific structure without rewriting universal content |

Then determine the agent surface actually in use. Quick existence checks (`ls` for `AGENTS.md`, `CLAUDE.md`, `.cursorrules`) count as scoping, not deep reading — do these before consulting the table below.

| Team/tool reality | Default output |
|------------------|----------------|
| Claude Code only | Standalone `CLAUDE.md` |
| One non-Claude agent, or future portability matters | `AGENTS.md` |
| Claude Code + any other agent | `AGENTS.md` + thin `CLAUDE.md` wrapper |
| Existing `AGENTS.md`, now adding Claude-only features | Keep `AGENTS.md` authoritative; add `CLAUDE.md` and `.claude/` only if needed |
| Existing standalone `CLAUDE.md`, now adding other agents | Extract universal content into `AGENTS.md`, reduce `CLAUDE.md` to a thin wrapper |
| Unknown / open-source project | `AGENTS.md` + thin `CLAUDE.md` wrapper (maximum portability) |

If you cannot determine which agents the team uses (common for open-source repos), default to maximum portability with the dual-file pattern.

If the user mentions another agent-specific file (`.cursorrules`, `GEMINI.md`, `.github/copilot-instructions.md`, etc.), treat it as input to mine rules from unless they explicitly want that format as output.

### 2) Inspect the repository before drafting

Read only enough to ground the config, in this order:

1. **Existing agent and contributor docs** — extract rules to preserve
   - `AGENTS.md`, `AGENTS.override.md`
   - `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`, `.claude/settings.json`
   - `.cursorrules`, `.windsurfrules`, `GEMINI.md`
   - `.github/copilot-instructions.md`
   - `README.md`, `CONTRIBUTING.md`

2. **Command sources** — extract dev/test/build/lint commands
   - `package.json` scripts
   - `Makefile` / `Justfile`
   - `pyproject.toml`
   - `Cargo.toml`, `.cargo/config.toml`
   - CI workflows in `.github/workflows/`

3. **Repo structure and tech-stack anchors** — identify non-obvious layout and tech choices
   - framework/tool configs (`tsconfig.json`, `next.config.*`, `go.mod`, `docker-compose.yml`, workspace manifests)
   - monorepo layout, package/service boundaries, non-standard directories

4. **Code-level evidence for non-obvious rules** — verify conventions agents cannot infer
   - validate only conventions agents would not reliably infer on their own
   - capture WHY when the repo encodes an intentional trade-off

**When to stop inspecting:** Once you can fill in all Commands entries, identify non-obvious conventions agents would get wrong, and note architecture boundaries (if any). If uncertain whether a convention is "non-obvious," include it and trim in step 7.

**Recovery rules**
- If a command is not verified, write `See [file]` or `Test: [not configured]`.
- If an existing config file is mostly good, switch from rewrite mode to audit/tighten mode.
- If repo facts conflict across files, prefer the stricter or more current source and call out the conflict.

### 3) Choose the file strategy deliberately

Use the simplest setup that matches the repo:

- **Standalone `CLAUDE.md`** when the team uses Claude Code only, or Claude-specific imports/rules are the real center of gravity.
- **`AGENTS.md` only** when shared, agent-agnostic instructions are enough.
- **Dual-file pattern** when the repo needs both portability and Claude-specific features.

Dual-file rule:

1. Put all universal instructions in `AGENTS.md`.
2. Keep `CLAUDE.md` thin:
   ```markdown
   @AGENTS.md

   ## Claude-Specific
   - Add only Claude-only features or memory notes here
   - (If path-scoped rules are needed) See `.claude/rules/`
   ```
3. Do not copy `AGENTS.md` content into `CLAUDE.md`.

Monorepo rule (skip for single-package projects):

- Root file = universal repo-wide guidance
- Nested `AGENTS.md` or `.claude/rules/` = package/path-specific rules
- Never dump every package-specific rule into the root file

### 4) Draft only high-signal instructions

Use the **WHAT / WHY / HOW** filter:

| Layer | Include |
|------|---------|
| WHAT | Non-obvious tech choices, architecture boundaries, unusual paths |
| WHY | Reasoning that stops agents from "fixing" intentional decisions |
| HOW | Verified commands and exact workflows that must be followed |

Every generated file should strongly prefer:

- imperative voice: `Use pnpm`, `Run tests before commit`
- measurable rules: `Never edit existing migrations`
- project-specific boundaries: `Always`, `Ask`, `Never`
- non-obvious context over generic advice

Cut aggressively:

- linter/formatter rules already enforced by tooling
- obvious facts the agent can infer from code
- copied `README.md` content
- exhaustive file trees or dependency lists
- motivational filler like `write clean code`

**When to add sections beyond templates:** add a dedicated section when 3+ related non-obvious facts need grouping. If only 1–2 facts, merge them into Conventions instead.

Cutting means removing from the root config file. If cut content is occasionally useful, reference it as a supplemental doc pointer instead of inlining.

### 5) Control scope and disclosure

Root config files should contain only instructions needed in most sessions.

Use progressive disclosure only when it improves signal:

- `AGENTS.md` → universal shared guidance, with pointer references only
- `CLAUDE.md` → may use `@import` or `.claude/rules/`
- nested `AGENTS.md` → package/service-specific rules
- `.claude/rules/` → path-scoped Claude-only rules

Do not create extra support files just because the platform allows them. Add `@import` files, `.claude/rules/`, or `agent_docs/` only when the repo is complex enough to justify them and the content can stay lean.

### 6) Audit or migrate without losing signal

> For new setups, verify the format rules below apply to your draft, then proceed to step 7.

When auditing or migrating:

- preserve valid warning/boundary rules from the current files
- separate **universal** content from **agent-specific** content
- rewrite vague suggestions as direct instructions or remove them
- remove duplication between `AGENTS.md` and `CLAUDE.md`
- keep format rules strict:
  - `AGENTS.md` = plain markdown only, no frontmatter, no `@import`
  - `CLAUDE.md` = Claude-only memory, imports, `.claude/` references allowed

If the input is noisy, extract only the lines that would cause a real mistake if missing.

### 7) Validate before finalizing

Check all of the following:

- commands and paths are verified against repo files
- instructions document non-obvious repo reality, not framework defaults
- `AGENTS.md` contains only universal content
- `CLAUDE.md` contains only Claude-specific additions beyond shared guidance
- no duplicated content across both files
- file sizes stay lean
  - root `AGENTS.md`: ideally <80 lines
  - thin `CLAUDE.md`: ideally <20 lines
  - standalone `CLAUDE.md`: ideally <60 lines
- unresolved unknowns are called out in your response to the user (not in the generated files)

**If a check fails:**
- Over target size → trim low-signal lines, or split into nested files for monorepos
- Commands unverified → use `See [file]` or `Test: [not configured]` syntax
- Content duplicated → move it to `AGENTS.md` and keep `CLAUDE.md` as a thin wrapper

## Do this, not that

| Do this | Not that |
|--------|----------|
| Ground every rule in repo evidence | Paste a generic best-practices template |
| Verify commands in manifests, makefiles, or CI | Invent `test`, `lint`, or `build` commands |
| Put shared rules in `AGENTS.md` | Put Claude-only `@import` or `.claude` syntax in `AGENTS.md` |
| Use `CLAUDE.md` as a thin wrapper when both files exist | Duplicate the same content in both files |
| Preserve existing warning/boundary rules during migration | Drop `Never` / `CRITICAL` rules because they feel repetitive |
| Use nested files or scoped rules for monorepos | Stuff every package-specific rule into the root file |
| Point to existing docs for bulky detail | Copy `README.md` or API docs into agent config |
| Use templates only after repo inspection | Fill a template before you know the repo shape |
| Route tool-specific review setup to the matching `init-*` skill | Force this skill to own Copilot/Devin/Greptile review configs |

## Reference routing

Read the smallest reference set that unblocks the current decision:

| Need | Reference |
|-----|-----------|
| High-signal writing, WHAT/WHY/HOW, dual-file guidance | `references/writing-guidelines.md` |
| `AGENTS.md` format, nesting, size limits, compatibility with non-Claude agents | `references/agents-md-format.md` |
| `CLAUDE.md` imports, memory hierarchy, path-scoped rules, `.claude/` structure | `references/claude-md-format.md` |
| Cross-agent support matrix and wrapper strategy | `references/cross-agent-compat.md` |
| Auditing existing files or migrating from another format | `references/audit-and-migration.md` |
| Project-type starter structures after repo inspection | `references/project-templates.md` |

Start with one or two references. Suggested starting points: **new setups** → writing-guidelines.md + project-templates.md; **audits** → audit-and-migration.md; **dual-file decisions** → agents-md-format.md + claude-md-format.md. Expand only if the current task truly needs more detail.

## Final output expectations

When you generate or revise files, provide:

1. the chosen file strategy and why it fits this repo
2. a file tree of created/updated files
3. the actual file contents or precise edits
4. any remaining unknowns or follow-up checks
5. for audits, a concise score or findings summary
