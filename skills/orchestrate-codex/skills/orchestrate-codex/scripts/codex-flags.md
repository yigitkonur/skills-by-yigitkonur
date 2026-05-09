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
| `CODEX_REVIEW_FLAGS` | array | alias of `CODEX_FLAGS`. Review mode uses `codex exec review`, which accepts the full policy flag set in codex-cli 0.130.0. |

## Usage

```bash
. "$(dirname "$0")/codex-flags.sh"
codex exec "${CODEX_FLAGS[@]}" --json -o "$out" "$prompt"
```

## Behavior

- Idempotent: sourcing twice is a no-op (`ORCHESTRATE_CODEX_FLAGS_LOADED=1` guard).
- Returns 0 on success.
- Pure side-effect-free except for variable export.

## Why an array, not a string

Codex flag values like `model_reasoning_effort=xhigh` contain `=` and need word-boundary safety under `set -u` and `bash -c` subshells. String-split-into-argv loses that. Always expand as `"${CODEX_FLAGS[@]}"`.

## Why hard-coded model + effort

The skill is opinionated. The user opts in to bypass + xhigh + gpt-5.5 when invoking the skill. Per-spawn overrides are a foot-gun (silent semantic drift); per-session overrides via env vars are documented in `references/universal/codex-flags.md`.
