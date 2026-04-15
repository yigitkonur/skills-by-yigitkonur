# Agent Entrypoints, Review Context, and Cross-Agent Compatibility

How AGENTS-first repositories expose the same instruction hierarchy to agent-native loaders and review adapters without creating competing sources of truth.

## Core Model

`AGENTS.md` is the source of truth for agent behavior. `REVIEW.md` is the source of truth for review standards. Agent-native entrypoints and review adapters are companions, not peers.

Default order:
1. discover the repo
2. write the root and folder `AGENTS.md` hierarchy
3. create companion `CLAUDE.md` / `GEMINI.md` entrypoints
4. write the repo-grounded `REVIEW.md` layer
5. generate platform-native review adapters from that completed context

## Support Matrix

| Agent | Reads root `AGENTS.md` | Reads nested `AGENTS.md` | Native file | Recommended role |
|------|-------------------------|--------------------------|-------------|------------------|
| Codex CLI | Yes | Yes | `AGENTS.md` | Primary shared consumer |
| Cursor | Yes | Yes | `.cursor/rules/*.mdc` | Reads AGENTS directly, add `.mdc` only for Cursor-only behavior |
| VS Code Copilot | Yes | Yes | `.github/copilot-instructions.md` | Shared rules stay in AGENTS |
| Claude Code | Through `CLAUDE.md` | Through nested `CLAUDE.md` companions | `CLAUDE.md` + `.claude/` | Mirror each AGENTS file with a companion entrypoint |
| Gemini CLI | Yes | Root-first | `GEMINI.md` | Shared rules in AGENTS, Gemini-only notes in `GEMINI.md` |
| Aider | Yes | Root-first | `.aider.conf.yml` | Configure `read: AGENTS.md` |
| Windsurf | Yes | Root-first | `.windsurfrules` | Keep native file minimal and pointer-oriented |
| Root-only agents | Yes | No | Agent-specific | Depend on a strong root AGENTS file |

## Default Entrypoint Strategy

| Agent | Primary file | Default strategy in this skill |
|------|--------------|--------------------------------|
| Claude Code | `CLAUDE.md` | Symlink to sibling `AGENTS.md` |
| Gemini CLI | `GEMINI.md` | Small pointer or agent-only delta that points back to `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` | Pointer to `AGENTS.md` plus scoped files only if needed |
| Cursor | `.cursor/rules/*.mdc` | Use only for Cursor-only behavior; shared rules stay in `AGENTS.md` |
| Aider | `.aider.conf.yml` | Configure `read: AGENTS.md` |
| Windsurf | `.windsurfrules` | Condensed pointer or summary when native file is required |

## Core Standardization Pair

Every finished repo should leave this skill with these two surfaces:

| File | Purpose |
|------|---------|
| `AGENTS.md` | How agents should work, where code belongs, what boundaries exist |
| `REVIEW.md` | What diffs should be flagged, protected, or held to a higher bar |

Keep them complementary:
- `AGENTS.md` tells the agent how to operate
- `REVIEW.md` tells the reviewer what to scrutinize
- neither file should become a duplicate of the other

## Configurable Native Review Adapters

These are final-stage adapters generated from the completed `AGENTS.md` + `REVIEW.md` pair.

| Platform | Native files | Use them for | Keep out of them | Key gotcha |
|----------|--------------|--------------|------------------|------------|
| Copilot | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` | Copilot review guidance and scoped review rules | Shared repo-wide coding policy that belongs in `AGENTS.md` | Copilot reads instruction files from the base branch, not the PR branch |
| Devin | `REVIEW.md` plus optional scoped `REVIEW.md` and existing `AGENTS.md` | Bug Catcher diff criteria and scoped review surfaces | Duplicated review rules in `AGENTS.md` | Avoid relying on undocumented precedence for overlapping scoped files |
| Greptile | `.greptile/config.json` plus optional `rules.md`, `files.json` | Review configuration, prose rules, scoped context files | Shared coding-agent policy that belongs in `AGENTS.md` | Greptile reads config from the source branch, not the base branch |

## Final-Step Question

After the AGENTS hierarchy and `REVIEW.md` layer are done, ask one concise question:

`The AGENTS.md and REVIEW.md hierarchy is complete. Which native review adapters should also be generated for this repo: Copilot, Devin, Greptile, or none?`

Use that answer to decide whether to stop or generate adapters in this same workflow.

## Claude Code: Symlink-First Policy

For every finalized `AGENTS.md`, create the matching companion file:

```bash
ln -s AGENTS.md CLAUDE.md
```

For nested folders:

```bash
cd src/api
ln -s AGENTS.md CLAUDE.md
```

This skill treats the sibling symlink as the default Claude compatibility policy because it keeps `AGENTS.md` authoritative and eliminates drift.

## When the Symlink Cannot Be Used

Use the fallback wrapper only when the target environment cannot preserve symlinks:

```markdown
@AGENTS.md
```

If you have to use the wrapper:
- keep it one line unless the user explicitly wants more
- call out the reason in your response
- do not let the wrapper grow into a second instruction document

## Where Claude-Only Behavior Belongs

Keep Claude-specific features in `.claude/`, not in the symlinked `CLAUDE.md`.

| Need | Put it here | Why |
|------|-------------|-----|
| Path-scoped Claude rules | `.claude/rules/` | Claude loads them natively without duplicating AGENTS content |
| Custom slash commands | `.claude/commands/` | Native feature, not shared policy |
| Named agents | `.claude/agents/` | Claude-only orchestration surface |
| Hooks and permissions | `.claude/settings.json` | Operational config, not portable instruction text |
| Team-wide project rules | `AGENTS.md` | Shared by all coding agents |

**Rule:** if a line applies to more than Claude, it does not belong in `CLAUDE.md`.

## Other Agent Entrypoints

### GitHub Copilot

Use `.github/copilot-instructions.md` plus scoped `.github/instructions/*.instructions.md` as the Copilot translation of the completed review context.

Brief setup map:
- enable Copilot code review in repository or organization GitHub settings before expecting the files to matter
- keep universal rules in `AGENTS.md`
- keep repo review standards grounded in `REVIEW.md`
- keep each Copilot instruction file under the platform limit
- remember that Copilot review uses the base branch version of the instruction files

Minimal pointer example:

```markdown
See AGENTS.md for shared repository instructions.
Keep this file limited to Copilot-only behavior.
```

Generate these files only if the user explicitly chose Copilot at the final stage.

### Devin

Devin uses the same split as this skill:
- `REVIEW.md` for Bug Catcher review criteria
- `AGENTS.md` for coding behavior, architecture, workflow, and testing expectations

Brief setup map:
- prefer `REVIEW.md` only unless coding behavior guidance is also needed
- keep review criteria out of `AGENTS.md`
- verify with a test PR or `npx devin-review`
- avoid contradictions across multiple scoped `REVIEW.md` or `AGENTS.md` files

Generate extra Devin-specific review surfaces only if the user explicitly chose Devin at the final stage.

### Gemini CLI

Use `GEMINI.md` only for Gemini-only behavior. Shared rules still live in `AGENTS.md`.

Example:

```markdown
# Gemini Notes

See `AGENTS.md` for shared project instructions.
Only add Gemini-specific execution notes here if they are genuinely unique.
```

### Greptile

Use `.greptile/config.json` as the primary Greptile translation of the completed review context, with optional `rules.md` and `files.json` when repo evidence justifies them.

Brief setup map:
- install the Greptile GitHub app or GitLab webhook before expecting repo config to run
- prefer the `.greptile/` directory over legacy `greptile.json`
- keep `scope` as an array and `ignorePatterns` as a newline-separated string
- add context files only when they materially improve review quality
- remember Greptile reads config from the source branch

Generate these files only if the user explicitly chose Greptile at the final stage.

### Cursor

Cursor reads `AGENTS.md` directly. Use `.cursor/rules/*.mdc` only for Cursor-specific globs, not for shared project rules.

### Aider

Configure the read list rather than duplicating instructions:

```yaml
read:
  - AGENTS.md
```

## Decision Table: Where an Instruction Belongs

| Instruction type | Destination |
|------------------|-------------|
| Shared project command or convention | `AGENTS.md` |
| Repo-wide diff-review rule | `REVIEW.md` |
| Folder-specific workflow | Folder-local `AGENTS.md` |
| Folder-specific diff-review rule | Scoped `REVIEW.md` |
| Claude-only path rule | `.claude/rules/*.md` |
| Claude-only command or agent profile | `.claude/commands/` or `.claude/agents/` |
| Copilot-only scoped behavior | `.github/instructions/*.instructions.md` |
| Gemini-only runtime note | `GEMINI.md` |
| Personal override | Gitignored local file, not shared config |

## Universal vs Agent-Specific Content

### Safe in AGENTS

- verified commands
- architecture boundaries
- folder-local risks
- repo-wide conventions
- Always/Ask/Never rules
- non-obvious WHY context

### Safe in REVIEW

- diff-review criteria
- high-risk change patterns
- boundaries that should trigger findings
- ignore patterns for generated or irrelevant files
- testing or validation expectations that matter during review

### Keep out of AGENTS

- Claude path-scoped rules
- Claude slash commands and agents
- Cursor glob rules
- Copilot scoped instruction files
- Gemini-only runtime behavior
- Aider read-list configuration

### Keep out of REVIEW

- generic coding advice
- linter-enforced style rules
- agent workflow instructions that belong in AGENTS
- platform-native syntax that belongs in adapters

## Recommended Layouts

### Single project

```text
repo/
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── GEMINI.md
└── .github/
    └── copilot-instructions.md
```

### Large `src/` tree

```text
repo/
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
└── src/
    ├── api/
    │   ├── AGENTS.md
    │   └── CLAUDE.md -> AGENTS.md
    ├── web/
    │   ├── AGENTS.md
    │   └── CLAUDE.md -> AGENTS.md
    └── jobs/
        ├── AGENTS.md
        └── CLAUDE.md -> AGENTS.md
```

### Monorepo

```text
repo/
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── apps/
│   ├── web/
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md -> AGENTS.md
│   └── api/
│       ├── AGENTS.md
│       └── CLAUDE.md -> AGENTS.md
└── packages/
    └── shared/
        ├── AGENTS.md
        └── CLAUDE.md -> AGENTS.md
```

## Strategy by Team Shape

### Single-agent team

If the user explicitly wants one agent only, that agent's native file can be enough. This skill still prefers AGENTS-first unless the user asks for a single-agent exception.

### Multi-agent team

1. use AGENTS as the shared source of truth
2. create local AGENTS files for meaningful folders
3. mirror each finalized AGENTS file with a sibling `CLAUDE.md` companion
4. add native files only for genuinely agent-specific behavior
5. keep personal overrides gitignored

### Root-only agent consumers

Because some agents do not read nested files, the root `AGENTS.md` still needs:
- verified repo-wide commands
- top-level architecture
- shared boundaries
- a concise map of the folders that have stronger local rules

## Migration Patterns

### From standalone `CLAUDE.md`

1. extract shared instructions into root `AGENTS.md`
2. create local `AGENTS.md` files where the architecture needs them
3. replace `CLAUDE.md` with a sibling symlink to `AGENTS.md`
4. move Claude-only behavior into `.claude/`

### From `.cursorrules`

1. copy universal content into `AGENTS.md`
2. move Cursor-only globs and behavior into `.cursor/rules/*.mdc`
3. create companion `CLAUDE.md` files only if Claude support is needed

### From no config

1. run Wave 1 exploration
2. run Wave 2 on meaningful folders
3. write root and folder AGENTS files
4. add companion entrypoints afterward

## Verification

```bash
# Find companion files
find . -name CLAUDE.md -o -name GEMINI.md -o -path './.github/copilot-instructions.md'

# Check which Claude files are symlinks
find . -type l -name CLAUDE.md -print

# Check for adjacent native review surfaces
find . \( -path './.github/copilot-instructions.md' -o -name 'REVIEW.md' -o -path './.greptile/config.json' \) 2>/dev/null
```

Then verify in the target agent:
- ask Claude Code to summarize its instructions in one nested folder
- ask a second agent to summarize the root instructions
- confirm both responses reflect the same AGENTS hierarchy

Use at least two agents when validating a shared setup. One should read nested files and one can be root-only.

If the user later opts into review adapters, validate those adapter files against the completed `REVIEW.md` rather than reopening the AGENTS authoring pass.

## Real-World Examples

### Example 1: Claude + Codex on an app repo

```text
AGENTS.md
CLAUDE.md -> AGENTS.md
src/api/AGENTS.md
src/api/CLAUDE.md -> AGENTS.md
src/web/AGENTS.md
src/web/CLAUDE.md -> AGENTS.md
```

Codex reads the root and nested AGENTS files directly. Claude follows the mirrored companions. Both agents converge on the same instruction hierarchy.

### Example 2: Open-source repo with mixed contributors

```text
AGENTS.md
src/cli/AGENTS.md
src/core/AGENTS.md
```

Keep the root file strong enough for root-only tools. Add native companion files only if contributors actually use those agents.

### Example 3: Enterprise monorepo

```text
AGENTS.md
CLAUDE.md -> AGENTS.md
apps/web/AGENTS.md
apps/web/CLAUDE.md -> AGENTS.md
apps/api/AGENTS.md
apps/api/CLAUDE.md -> AGENTS.md
.github/copilot-instructions.md
.claude/rules/
```

AGENTS stays authoritative. Copilot and Claude each get only the native extras they need.

## Common Gotchas

| Gotcha | Why it bites | Fix |
|--------|-------------|-----|
| Writing `CLAUDE.md` first | Claude becomes the real source of truth | Write `AGENTS.md` first, then mirror it |
| Skipping `REVIEW.md` because no PR tool is installed | The repo loses its review standards layer | Always write the generic review context anyway |
| Adding shared rules to `CLAUDE.md` | Other agents never see them | Move them into `AGENTS.md` |
| Using wrapper text as a second policy file | Shared rules drift | Keep wrapper one line or use the symlink |
| Keeping Claude-only notes in AGENTS | Pollutes portable instructions | Move them into `.claude/` |
| Forgetting nested companions | Claude misses folder-local rules | Mirror each finalized nested `AGENTS.md` with a sibling `CLAUDE.md` |
| Root file is too weak for root-only agents | Too much was pushed into nested files | Restore repo-wide commands, architecture, and boundaries to root |
| REVIEW duplicates AGENTS | The two files compete instead of complementing | Keep operating guidance in AGENTS and diff scrutiny in REVIEW |
| Native files duplicate AGENTS content | Shared policy drifts by tool | Point back to AGENTS and keep only agent-specific deltas |
| Copilot rules authored on a feature branch | The PR review ignores them | Merge the instruction changes to the base branch first |
| Devin `REVIEW.md` and `AGENTS.md` say the same thing | Devin reads both and review noise increases | Keep review criteria in `REVIEW.md`, coding behavior in `AGENTS.md` |
| Greptile config uses the wrong field shapes | The config silently misbehaves | Keep `scope` as arrays and `ignorePatterns` as a newline string |
| Asking about review adapters too early | The main task gets derailed before AGENTS and REVIEW are done | Ask only at the final configurable step |

## Out-of-Scope Exception

A standalone, Claude-only `CLAUDE.md` may still be valid when the user explicitly wants a Claude-only setup and portability does not matter. That is not the default operating model for this skill. This skill assumes AGENTS-first unless the user says otherwise.
