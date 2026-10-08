# SKILL.md Format Specification

Complete reference for the SKILL.md file format based on the open [Agent Skills Specification](https://agentskills.io/specification).

## File requirements

- File must be named exactly `SKILL.md` (case-sensitive; `skill.md` accepted as fallback by some parsers, but `SKILL.md` is standard)
- Must be placed inside a named directory matching the skill `name`
- Frontmatter must start on line 1

## Frontmatter

YAML frontmatter is enclosed between `---` delimiters. It configures how the skill is discovered, validated, and loaded.

```yaml
---
name: my-skill-name
description: Extract PDF text, fill forms, merge files. Use when handling PDFs or document workflows.
license: MIT
compatibility: Requires Python 3.12+ and uv
metadata:
  author: example-org
  version: "1.0.0"
allowed-tools: Bash(git:*) Read
---
```

### Official Specification Field Reference (`agentskills.io`)

Only the following six fields are defined in the canonical [Agent Skills Specification](https://agentskills.io/specification):

| Field | Required | Type | Constraints | Purpose |
|---|---|---|---|---|
| `name` | **Yes** | string | 1–64 characters. Lowercase unicode letters (`a-z`), numbers (`0-9`), and hyphens (`-`) only. Must not start/end with hyphen, no consecutive hyphens (`--`). **Must match parent directory name.** | Unique identifier and slash command. |
| `description` | **Yes** | string | 1–1024 characters. Non-empty string. Avoid XML angle brackets (`<`, `>`). | Primary trigger for progressive disclosure. Describes **what** the skill does AND **when** to invoke it. |
| `license` | No | string | Short license name (e.g. `MIT`, `Apache-2.0`) or reference to bundled license file. | Licensing terms. |
| `compatibility` | No | string | 1–500 characters. | Environment requirements (target products, system packages, network access). |
| `metadata` | No | map (string: string) | Arbitrary string key-value mapping (e.g., `author`, `version`, `category`). | Client-specific or catalog metadata. Custom extensions belong here. |
| `allowed-tools` | No | string (**space-separated**) | Space-separated tool patterns, e.g. `Bash(git:*) Bash(jq:*) Read`. | Pre-approved tools the skill may run (experimental). |

> **Note on Client-Specific Extensions:**
> - Some clients support proprietary or experimental flags (e.g., `disable-model-invocation: true` in Claude Code / Cursor, or `agents/openai.yaml` in Codex).
> - These are **not** part of the official `agentskills.io` open specification. Strict specification validators (like `skills-ref validate`) will flag unrecognized top-level fields as errors (`Unexpected fields in frontmatter`).
> - For pure specification compliance and broad interoperability across all 38+ agent products (Claude Code, Cursor, Copilot, Antigravity, Windsurf), keep frontmatter restricted to the 6 official fields. Place extra metadata inside `metadata:`.

### Frontmatter Rules

1. Must start on line 1 of the file — no blank lines before `---`.
2. Must be valid YAML (parsed strictly via `strictyaml`).
3. Avoid XML angle brackets (`<`, `>`) — they can inject instructions into LLM system prompts.
4. `name` is **strictly required** and must match the directory name.
5. `description` is **strictly required** (no fallback to markdown body).
6. Unknown top-level fields trigger errors in the official `skills-ref` validator.

## Body structure

The markdown body after frontmatter contains the instructions the agent follows when the skill is activated.

### Recommended sections

```markdown
# Skill Title

Brief one-line purpose statement.

## Integration & prerequisites
Mandatory dependencies, such as companion skills (e.g. run-research).

## Core modes & decision tree
Route the agent based on the task (Discovery, Creation, Conversation-driven, Research-driven).

## Step-by-step instructions
Actionable, progressive procedures with clear validation gates.

## Available scripts
Document bundled MJS / Python scripts in scripts/ with usage examples.

## Key patterns & gotchas
Essential conventions, concrete edge cases, and pitfalls with actionable fixes.

## Reference routing
Table mapping every file in references/ to specific conditions when it must be loaded.
```

### Body guidelines

| Guideline | Rationale |
|---|---|
| Keep under 500 lines | Larger files consume excessive context budget |
| Use imperative language ("Run...", "Write...") | Clearer agent instructions than passive voice |
| Reference files via relative paths (`references/doc.md`) | Portability across environments |
| Move large docs to `references/` | Progressive disclosure — loaded only when needed |
| Bundle scripts in `scripts/` (prefer `.mjs` or `.py`) | Automate deterministic logic instead of relying on fuzzy model generation |
| Test scripts before shipping | Ensure runtime infrastructure and dependencies execute cleanly |

## Progressive disclosure architecture

Agents manage context through progressive disclosure:

1. **Discovery (Startup)**: Only `name` and `description` are loaded (~100 tokens per skill) into the system prompt or agent catalog.
2. **Activation (On Demand)**: When a user query matches the skill's description or when manually invoked, the full `SKILL.md` body is loaded (<5,000 tokens recommended).
3. **Deep Reference & Scripts (As Needed)**: Additional documentation in `references/` or executables in `scripts/` are only read or executed when explicitly required by the workflow.

## Validation with `skills-ref`

Validate any skill against the official open specification using the reference validator:

```bash
skills-ref validate ./my-skill
```
