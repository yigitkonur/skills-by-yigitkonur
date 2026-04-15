# Runtime config

Use this file when you need to understand how `codex-worker` inherits Codex runtime defaults and how explicit flags interact with them.

## Default source

The CLI asks the Codex runtime for config defaults through `config/read`, which usually reflects `~/.codex/config.toml`.

Relevant runtime defaults currently include:

- `model`
- `model_provider`
- `approval_policy`
- `sandbox_mode`
- `service_tier`
- `personality`

## What the CLI inherits

When starting or resuming sessions, the CLI carries through runtime defaults for:

- model provider
- approval policy
- sandbox mode
- service tier
- personality

This is why a working local Codex config matters. The CLI is a shell around the Codex runtime, not a separate model client.

## Override rules

### Task and prompt control

Explicit CLI flags override defaults for:

- `--cwd` — working directory
- `--model` — model selection
- `--effort` — reasoning effort level (low, medium, high)
- `--label` — task label
- `--plan` / `--skip-plan` — planning behavior

### Session reuse

When you reuse a session via `--session <threadId>`:

- the existing session pins the underlying thread and cwd
- the CLI resumes that thread before starting the new turn
- a new `--model` can only apply when the resumed turn supports it and the runtime accepts it
- `task steer` keeps the anchor session and uses the terminal task as the continuation point

Use session reuse deliberately. It is good for continuity, but it also carries context forward.

## Practical recommendations

- Put stable environment defaults in `~/.codex/config.toml`
- Put task-specific differences in CLI flags
- Do not hardcode provider credentials or personal secrets into prompt files

## Example config shape

These are common settings the CLI can inherit:

```toml
model = "gpt-5.4"
model_provider = "codex-lb"
approval_policy = "never"
sandbox_mode = "danger-full-access"
service_tier = "fast"
personality = "pragmatic"
```

Keep provider-specific secrets in the normal Codex config or environment, not in task files.
