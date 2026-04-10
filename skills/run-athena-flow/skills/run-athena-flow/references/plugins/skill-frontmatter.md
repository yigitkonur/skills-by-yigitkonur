# Skill Frontmatter Reference

Each `skills/<name>/SKILL.md` in a plugin uses YAML frontmatter to define the skill's metadata and behavior.

## Full Example

```yaml
---
name: add-e2e-tests
description: Full pipeline orchestrator for adding Playwright E2E tests
user-invocable: true
argument-hint: "<url> <feature>"
allowed-tools:
  - Read
  - Bash
  - Write
  - Glob
  - Grep
---
```

## Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | Slash command name (`add-e2e-tests` → `/add-e2e-tests`) |
| `description` | string | Yes | — | Shown in `/help` output |
| `user-invocable` | boolean | No | `false` | If `true`, appears as a user-visible slash command |
| `argument-hint` | string | No | — | Argument description shown in help (e.g., `"<url> <feature>"`) |
| `allowed-tools` | string[] | No | — | Tools this skill can use |

## The Skill Body

Everything below the `---` closing delimiter is the prompt template. It's injected as the user message when the skill is invoked.

### `$ARGUMENTS` Placeholder

Use `$ARGUMENTS` in the skill body to interpolate user input:

```markdown
---
name: analyze-deps
user-invocable: true
argument-hint: "[path]"
---

Analyze dependencies at: $ARGUMENTS
```

When the user types `/analyze-deps ./src`, `$ARGUMENTS` becomes `./src`.

## Visibility Rules

- `user-invocable: true` — Appears as a slash command in `/help` and can be typed by the user
- `user-invocable: false` (or omitted) — Loaded into the system but not visible as a command. Useful for workflow-invoked skills that shouldn't be called directly

## Skill Loading Process

1. Athena scans `skills/*/SKILL.md` in each plugin directory
2. Parses YAML frontmatter using a YAML parser
3. Reads the body text below the frontmatter
4. Creates a `ParsedSkill` object with frontmatter fields and body
5. For `user-invocable: true` skills, creates a `PromptCommand` in the command registry
6. `$ARGUMENTS` is replaced at invocation time with the user's input

## Naming Conventions

- Skill names should be kebab-case: `add-e2e-tests`, `analyze-test-codebase`
- The name becomes the slash command: `name: analyze-deps` → `/analyze-deps`
- Keep names short but descriptive
- Avoid generic names that might conflict with built-in commands

## Built-in Slash Commands

These are registered by Athena and cannot be overridden by plugin skills:

| Command | Aliases |
|---------|---------|
| `/help` | `/h`, `/?` |
| `/clear` | `/cls` |
| `/quit` | `/q`, `/exit` |
| `/stats` | `/s` |
| `/context` | `/ctx` |
| `/sessions` | — |
| `/tasks` | `/todo` |
| `/setup` | — |
| `/telemetry` | — |
| `/workflow` | — |
