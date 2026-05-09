# codex-flags.sh

Sourced helper. Single source of truth for the codex spawn flags every runner uses.

## Inputs (env)

| Var | Default | Effect |
|---|---|---|
| `ORCHESTRATE_CODEX_MODEL` | `gpt-5.5` | Override the pinned model |
| `ORCHESTRATE_CODEX_EFFORT` | `xhigh` | Override the pinned `model_reasoning_effort` |

## Outputs (exported)

| Var | Type | Value |
|---|---|---|
| `CODEX_MODEL` | string | resolved model name |
| `CODEX_EFFORT` | string | resolved effort name |
| `CODEX_FLAGS` | array | `--dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -m "$CODEX_MODEL" -c "model_reasoning_effort=$CODEX_EFFORT"` |
| `CODEX_REVIEW_FLAGS` | array | `-c "model_reasoning_effort=$CODEX_EFFORT"` — narrow safety rail for the **bare `codex review`** root subcommand only. See subcommand surface table below. |

## Subcommand flag surface (codex-cli 0.130)

| Subcommand | Accepts `${CODEX_FLAGS[@]}`? | Notes |
|---|---|---|
| `codex exec` | yes | The default surface; every runner uses this. |
| `codex exec review` | **yes** | Same flag surface as `codex exec`: `--dangerously-bypass-approvals-and-sandbox`, `--skip-git-repo-check`, `-m`, `--json`, `-o`, `--ephemeral` all accepted. `run-review.sh` expands `${CODEX_FLAGS[@]}` here. |
| `codex exec resume` | yes | Same surface as `codex exec`. |
| `codex review` (root) | **no** | Narrower: rejects `--skip-git-repo-check`, `-o`, `--json`, `-m`, `--dangerously-bypass-approvals-and-sandbox`. Only `-c key=value` is accepted. Use `${CODEX_REVIEW_FLAGS[@]}` if a runner ever needs to call this. The skill avoids it (no `--json` means no machine-readable findings). |

The earlier doc revision claimed `codex exec review` had a narrower surface than `codex exec`. That was wrong; codex-cli 0.130 makes them equivalent. `CODEX_REVIEW_FLAGS` exists for the bare `codex review` invocation, not for `codex exec review`.

## Usage

```bash
. "$(dirname "$0")/codex-flags.sh"
codex exec "${CODEX_FLAGS[@]}" --json -o "$out" "$prompt"
codex exec review "${CODEX_FLAGS[@]}" --json -o "$out" "$prompt"   # same surface
# Bare codex review (rare; skill does not use this path):
codex review "${CODEX_REVIEW_FLAGS[@]}" "$prompt"
```

## Behavior

- Idempotent: sourcing twice is a no-op (`ORCHESTRATE_CODEX_FLAGS_LOADED=1` guard).
- Returns 0 on success.
- Pure side-effect-free except for variable export.

## Why an array, not a string

Codex flag values like `model_reasoning_effort=xhigh` contain `=` and need word-boundary safety under `set -u` and `bash -c` subshells. String-split-into-argv loses that. Always expand as `"${CODEX_FLAGS[@]}"`.

## Why hard-coded model + effort

The skill is opinionated. The user opts in to bypass + xhigh + gpt-5.5 when invoking the skill. Per-spawn overrides are a foot-gun (silent semantic drift); per-session overrides via env vars are documented in `references/universal/codex-flags.md`.
