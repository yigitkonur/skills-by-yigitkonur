# Runtime config

Use this file when you need to understand how `cli-codex-subagent` inherits Codex runtime defaults and how explicit flags interact with them.

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
- approval policy, unless an explicit CLI approval policy is set
- sandbox mode
- service tier
- personality

This is why a working local Codex config matters. The CLI is a shell around the Codex runtime, not a separate model client.

## Override rules

### Task and prompt resolution

Explicit CLI flags beat prompt frontmatter for:

- `cwd`
- `label`
- `model`
- `session`
- `effort`
- `context-file`
- `base-instructions-file`
- `output-schema`

### Runtime behavior

- explicit `--approval-policy` beats runtime `approval_policy`
- `--auto-approve` is shorthand for `--approval-policy never`
- if you do not pass `--model` and the prompt file does not set `model`, the runtime default model decides the session start

## Session reuse nuance

When you reuse a session:

- the existing session pins the underlying thread and cwd
- the CLI resumes that thread before starting the new turn
- a new `--model` can only apply when the resumed turn supports it and the runtime accepts it
- `task steer` keeps the anchor session and uses the terminal task as the continuation point

Use session reuse deliberately. It is good for continuity, but it also carries context and approvals forward.

## Practical recommendations

- Put stable environment defaults in `~/.codex/config.toml`
- Put task-specific differences in prompt frontmatter or CLI flags
- Use `session create` when you want to freeze cwd/model context before dispatching multiple related tasks
- Do not hardcode provider credentials or personal secrets into prompt bundles

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
