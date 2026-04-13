# Prompt bundles

Use this file when you need to understand prompt resolution, frontmatter, `AGENTS.md` loading, or portable handoff bundles.

## The task file is the contract

`cli-codex-subagent` is file-first. Every task or follow-up message starts from a markdown file.

The prompt file must contain:

- a non-empty markdown body
- optional frontmatter
- any reusable context as files, not inline shell arguments

## Supported frontmatter keys

These keys are currently recognized from the task file:

| Key | Meaning |
|---|---|
| `cwd` | Working directory for context discovery and runtime execution. Resolved relative to the prompt file unless absolute. |
| `label` | Human-friendly task label. |
| `model` | Requested model id. |
| `session` | Session id to reuse. |
| `effort` | Reasoning level for the turn. |
| `context_files` | List of extra context files to include. |
| `base_instructions_file` | File whose content becomes base instructions. |
| `output_schema` | Inline JSON schema or a relative `.json` file path. |

## Override order

High-level precedence:

- explicit command flags override frontmatter
- frontmatter overrides implicit defaults
- runtime config fills remaining defaults when the CLI starts or resumes the session

Important examples:

- `--model` wins over frontmatter `model`
- `--cwd` wins over frontmatter `cwd`
- `--context-file` wins over frontmatter `context_files`
- `--base-instructions-file` wins over frontmatter `base_instructions_file`
- `--output-schema` wins over frontmatter `output_schema`

## How context is resolved

For `prompt inspect`, `run`, `task start`, and `task steer`, the CLI builds a resolved prompt bundle from:

1. the prompt body
2. auto-loaded `AGENTS.md` files from the resolved cwd up to filesystem root
3. explicit `--context-file` files or frontmatter `context_files`
4. optional base instructions from `--base-instructions-file` or frontmatter

The rendered prompt appends:

- repository instructions from auto-loaded `AGENTS.md`
- additional context sections from explicit context files

Developer instructions are generated separately and also include the same `AGENTS.md` and explicit context material.

## Inspect before dispatch

Use:

```bash
cli-codex-subagent prompt inspect task.md --json
cli-codex-subagent prompt lint task.md --json
```

`prompt inspect` returns:

- `prompt`
- `promptBody`
- `renderedPrompt`
- `resolvedCwd`
- `label`
- `model`
- `session`
- `developerInstructions`
- `baseInstructions`
- `contextManifest`

## Portable bundles

Materialize a handoff bundle before execution:

```bash
cli-codex-subagent prompt inspect task.md --write-bundle ./bundle --json
```

The bundle directory contains:

- `prompt.md`
- `prompt.rendered.md`
- `context.manifest.json`
- `developer.instructions.md` when present
- `base.instructions.md` when present
- `handoff.manifest.json`

## Task artifact bundles

Started tasks write the same bundle shape into the task artifact directory. Read the paths with:

```bash
cli-codex-subagent task read tsk_123 --json
cli-codex-subagent task read tsk_123 --field artifacts.handoffManifestPath --json
```

Important task artifact fields:

- `artifacts.taskDir`
- `artifacts.promptPath`
- `artifacts.renderedPromptPath`
- `artifacts.contextManifestPath`
- `artifacts.developerInstructionsPath`
- `artifacts.baseInstructionsPath`
- `artifacts.handoffManifestPath`

## When to use a handoff bundle

Use a bundle when:

- another coding agent should continue the same task later
- you want a durable handoff with the exact rendered context
- you need to compare the original prompt body with the fully resolved prompt
- you want portable evidence of which `AGENTS.md` and context files were actually loaded
