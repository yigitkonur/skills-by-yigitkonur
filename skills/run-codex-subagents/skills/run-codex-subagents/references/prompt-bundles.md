# Prompt bundles

Use this file when you need to understand how `codex-worker` handles prompt files and follow-up prompts.

## The prompt file is the contract

`codex-worker` is file-first. `run`, `send`, `turn start`, and `turn steer` all start from a Markdown file.

Each prompt file should define:
- the objective
- the relevant files
- constraints
- verification
- the expected deliverable

## How the CLI handles prompt files

The CLI reads the Markdown file content and sends that content to the Codex runtime.

Important behavior:
- the CLI does **not** parse frontmatter
- the runtime handles `AGENTS.md` discovery
- continuation happens by thread id, not by a separate `session` layer

## Working directory

Use `--cwd` on `run` when the thread should start somewhere other than the current shell directory:

```bash
codex-worker run task.md --cwd /abs/project
```

## Continuation patterns

Friendly continuation:

```bash
codex-worker send <thread-id> followup.md
```

Explicit turn continuation:

```bash
codex-worker turn steer <thread-id> <turn-id> followup.md
```

Use `thread resume` when you need to reconnect to the underlying runtime thread before more protocol-first operations.
