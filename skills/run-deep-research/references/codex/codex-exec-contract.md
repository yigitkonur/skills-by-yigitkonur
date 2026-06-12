# Codex Exec Contract

The codex CLI surface this skill depends on, per-flag rationale, JSON
event handling, MCP-active fallback, model and effort overrides.

This file is the canonical reference for **how a single codex job is
invoked**. It does not cover wave choreography (see
`wave-dispatch.md`) or prompt body shape (see
`codex-prompt-skeleton.md`).

## Required CLI version

The skill assumes `codex-cli 0.130.0` or later. Verify before
dispatching the first wave:

```bash
codex --version
```

The flags below are confirmed against `codex exec --help` for the
0.130.0 build. If a flag is rejected, the local CLI is too old —
upgrade rather than working around.

## Canonical invocation

Every per-job spawn uses this exact shape:

```bash
timeout "${USE_CODEX_TIMEOUT:-1500}" \
  codex exec \
    --dangerously-bypass-approvals-and-sandbox \
    --skip-git-repo-check \
    -m "${USE_CODEX_CODEX_MODEL:-gpt-5.5}" \
    -c model_reasoning_effort=<low|medium|high> \
    --json \
    -o <corpus-root>/<final-answer-path> \
    -C <corpus-root> \
    < <workdir>/prompts/<wave>/<slug>.md \
    > <workdir>/logs/<wave>/<slug>.jsonl \
    2> <workdir>/logs/<wave>/<slug>.stderr
```

The `< prompt > jsonl 2> stderr` redirection shape is identical for every
job; only the prompt path, output path, working directory, and effort
level change.

## Flag-by-flag rationale

| Flag | Rationale |
|---|---|
| `--dangerously-bypass-approvals-and-sandbox` | The sanctioned mode for codex orchestration. Downgrades to `-s read-only` or `-s workspace-write` silently block on network calls (web research) — codex hangs, the runner sees no progress, retries land in the same hang. The skill is built on bypass; downgrades change semantics. |
| `--skip-git-repo-check` | The corpus directory is usually not a git repo. Without this flag, codex refuses to start. |
| `-m <model>` | Default `gpt-5.5`. Override via env `USE_CODEX_CODEX_MODEL` for cost / capability trade-offs. Mid-run model changes invalidate the run; pick once. |
| `-c model_reasoning_effort=<low\|medium\|high>` | The first-class wave-level lever — see `effort-routing.md`. Mid-wave changes invalidate the wave's audit. |
| `--json` | Emits JSONL events to stdout. Captured to `<workdir>/logs/<wave>/<slug>.jsonl` for forensics; not parsed as the source of truth. |
| `-o <path>` | The final-answer file. **This is the canonical output.** Trust it over the JSONL stream — when MCP is active, JSON events can drop while the `-o` write still completes. |
| `-C <corpus-root>` | Codex's working directory. Set to the corpus root so codex's filesystem reads and writes use relative paths inside the corpus. |
| stdin (prompt redirected from `<workdir>/prompts/<wave>/<slug>.md`) | Never use the positional `[PROMPT]` argument for per-job dispatch — stdin redirection is shell-quoting-safe and reproducible. |
| `timeout 1500` | 25-minute wall-clock cap per job. Hung codex processes land in `failed` rather than stalling the pool's slot. Override via env `USE_CODEX_TIMEOUT`. |

Forbidden — do not substitute:

- `--full-auto` (deprecated)
- `-a` other than `never`
- `-s read-only` / `-s workspace-write` (block on web/network — corpus jobs need to read the web)
- `--ignore-rules`, `--ignore-user-config` (only when explicitly debugging codex itself)

## Effort flag passing

The effort flag is the per-wave dispatch lever:

```bash
EFFORT=high  # picked from Phase 0's effort plan
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  -m gpt-5.5 \
  -c "model_reasoning_effort=${EFFORT}" \
  --json -o <out> -C <root> < <prompt>
```

Always quote the `-c` value when interpolating an env var; codex's TOML
parsing is strict and an unquoted `high` is treated as a bareword
identifier.

For the per-wave effort-selection rules and concrete examples, see
`effort-routing.md`.

## JSON event handling — log, do not parse-as-truth

`--json` emits a JSONL stream (one event per line) to stdout. The events
include:

- `turn.started`, `turn.completed`
- `tool.call`, `tool.result`
- `agent.message`
- terminal events

Capture the stream to `<workdir>/logs/<wave>/<slug>.jsonl` for forensics.
**Do not gate `done` on a JSON event.** The runner's contract is:

1. Codex exits non-zero → `failed`.
2. Codex exits zero AND `-o` file is empty → `failed` (`last_error="empty_answer"`).
3. Codex exits zero AND `-o` file is non-empty → atomic rename `-o.tmp` → `-o`; write `status/<slug>.status = "done"`.

The JSONL is a Monitor input (for a TUI tail), not a state machine. When
MCP is active, JSON events sometimes drop entirely while the `-o` write
still completes; trusting the file over the events is the correct call.

## MCP-active fallback

If codex is invoked from inside an MCP-active session and the JSONL
stream goes silent while the process is still alive, the `-o` file
remains canonical. The runner's `done` gate is `exit-0 AND -o-non-empty`,
which survives MCP-induced event drop. Record an advisory
`last_error="json_event_dropped"` in the manifest but do not auto-fail.

## Auth gate — interpret, don't trust the headline

`codex login status` is the operator's pre-flight gate but its output
is misleading on proxy / managed-companion / bearer-token / ephemeral CI
setups. "Not logged in" from `codex login status` does not mean the API
is unreachable; it only means `~/.codex/auth.json` is absent.

If the machine is on a proxy or managed setup (check
`~/.codex/config.toml` for non-default `base_url`, or just ask the
operator once), set `USE_CODEX_SKIP_CODEX_AUTH=1` and run this smoke
test before dispatching any real wave:

```bash
mkdir -p /tmp/codex-smoke-work
rm -f /tmp/codex-smoke-work/lorem.txt /tmp/codex-smoke.md
USE_CODEX_SKIP_CODEX_AUTH=1 codex exec \
  --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
  -m gpt-5.5 -c model_reasoning_effort=high \
  --json -o /tmp/codex-smoke.md -C /tmp/codex-smoke-work \
  "Count 1 to 10 on one line then write a 3-line lorem ipsum to lorem.txt in the current working directory. Confirm both done in one sentence."
test -s /tmp/codex-smoke-work/lorem.txt && test -s /tmp/codex-smoke.md && echo "auth OK"
```

If both files are non-empty, the proxy is wired and you can dispatch
the real fleet. If the smoke fails with an auth/credentials error,
*then* ask the operator to fix auth before continuing.

Skipping the smoke test is the canonical failure mode that wastes a
full wave's API budget on entries that all fail at the runner-spawn
auth handshake.

## Model overrides

Override the default model via env (recorded in `run.json` so re-runs
replay the same choice):

```bash
USE_CODEX_CODEX_MODEL=gpt-5.4 codex exec ...
```

Mid-run model swaps invalidate the run's audit (per-wave outputs from
different models are not directly comparable). Pick the model at Phase
0 and keep it.

## Timeout overrides

Override the per-job timeout via env:

```bash
USE_CODEX_TIMEOUT=2400 codex exec ...
```

The default of 1500s (25 min) covers most per-entity research jobs.
Raise it only for genuinely heavy synthesis waves (Wave 3 cross-axis
comparison over 20+ entities); never lower it without a measured
reason — short timeouts produce false `failed` rows on legitimate
work.

## Detached vs. foreground

For test / debug, you may run a single codex job in the foreground:

```bash
USE_CODEX_RUNNER_FOREGROUND=1 codex exec ...
```

For production wave dispatch, every job runs detached (background)
via the wave-dispatch loop. See `wave-dispatch.md` for the bounded
worker-pool shape.

## Cross-skill anchor: broader codex orchestration

The codex executor here is the **research-specific lens** on codex
orchestration. For the broader codex framework — exec/batch/single/
review/rescue modes, manifest contract, Monitor wiring, rescue and
re-attach mechanics — refer the user to the codex orchestration skills in
the [secondary pack](https://github.com/yigitkonur/skills-by-yigitkonur-secondary).
Those generalize beyond the corpus-research use case; the pattern here is
narrower and folder-tree-shaped.
