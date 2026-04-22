# Runtime config

Use this file when you need to understand how `codex-worker` inherits Codex runtime defaults and how explicit flags interact with them.

## Default source

`codex-worker` relies on the installed Codex runtime and the active `CODEX_HOME` / `CODEX_HOME_DIRS` configuration.

Relevant runtime defaults include:
- model
- model provider
- approval policy
- sandbox mode

## What the CLI inherits

When starting or resuming threads, the worker carries through runtime defaults for:
- provider selection
- sandbox behavior
- approval behavior

## Explicit overrides

Common CLI overrides in the released surface:
- `run --cwd <dir>`
- `run --model <id>`
- `run --timeout <ms>`
- `thread start --developer-instructions <text>`
- `thread start --base-instructions <text>`

## Continuation and reuse

There is no `--session` flag in the released CLI.

Reuse happens through:
- `send <thread-id> <message.md>`
- `thread resume <thread-id>`
- `turn steer <thread-id> <turn-id> <prompt.md>`

These commands keep the existing thread context instead of creating a fresh thread.

## Recommendations

- Put stable environment defaults in Codex config
- Put task-specific differences in CLI flags or the prompt file
- Keep provider secrets in Codex config or environment, not inside prompt files
