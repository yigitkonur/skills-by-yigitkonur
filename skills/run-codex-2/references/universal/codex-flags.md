# Codex CLI flags the skill uses

Authoritative for codex-cli **0.130.0** and later (verified during this pass). Verify with `codex --help`, `codex exec --help`, `codex exec review --help`, and `codex review --help`. The skill's `scripts/codex-flags.sh` is the single source of truth for the flag arrays every runner uses; if you find yourself typing `--dangerously-bypass-approvals-and-sandbox` inside a runner, source the helper instead.

## Contents

- The hard-wired set (every direct `codex exec` spawn)
- Per-spawn additions
- Forbidden flags
- Per-session overrides
- Model alias
- Subcommand surfaces
- JSONL event types (with `--json`)
- MCP-active dropout — known issue
- Verify before assuming
- What this file is not

## The hard-wired set (every direct `codex exec` spawn)

```bash
. scripts/codex-flags.sh
codex exec "${CODEX_FLAGS[@]}" --json -o <answer-file> -C <cwd> "<prompt>"
```

`CODEX_FLAGS` expands to:

| Flag | Why hard-wired |
|---|---|
| `--dangerously-bypass-approvals-and-sandbox` | Never inherit user-config in subshells. `xargs bash -c` loses zsh function wrappers; explicit-per-spawn is the only durable form. |
| `--skip-git-repo-check` | Required outside a git repo (batch mode); harmless inside one. Required in `xargs bash -c` subshells where the trusted-dir check fails for spawned processes. |
| `-m gpt-5.5` | Pinned model. The skill is opinionated. Bumping is a one-line edit in `codex-flags.sh`. |
| `-c model_reasoning_effort=xhigh` | Pinned effort. Same rationale. |

### Sandbox semantics: network egress

With `--dangerously-bypass-approvals-and-sandbox` (the skill's default, hard-wired into `CODEX_FLAGS`), codex has **full filesystem write access AND full network egress** inside the spawned process. Outbound HTTP is allowed: codex can hit package registries, CVE databases, web search endpoints, vendor APIs, and arbitrary URLs that its tools call. This is what makes use cases like CVE lookup, dependency-vulnerability scanning, web fetches inside research prompts, and registry-version checks work end-to-end without per-call approval prompts. Without the bypass flag, the default sandbox is `read-only`: no filesystem writes, no network. Other discrete sandbox modes (`-s read-only`, `-s workspace-write`) are forbidden by this skill (see "Forbidden flags" below) — they downgrade the bypass policy and silently change semantics. Cross-link: the approval-policy table is in this file's "Forbidden flags" section; the sandbox-mode discussion is in the same section.

### Two review surfaces — different flag sets

Codex exposes review through two distinct entry points and they accept different flags. This is the most common source of confusion.

**`codex exec review` (the surface this skill drives, non-interactive):** accepts the **full** `CODEX_FLAGS` array plus `--json`, `-o`, `--ephemeral`, `--ignore-rules`, `--ignore-user-config`. It is `codex exec` with `review` as the action verb — the parent's flag surface is reused. The `run-review.sh` runner sources `codex-flags.sh` and passes `${CODEX_FLAGS[@]}` directly.

**`codex review` (root command, interactive TUI):** has a much narrower flag surface. This is the only place `CODEX_REVIEW_FLAGS` matters as a safety rail — a thin set the skill exports for the rare case an operator drops out of the orchestrator and wants to launch the TUI manually with the same effort/model policy:

| Flag | Why included in `CODEX_REVIEW_FLAGS` |
|---|---|
| `-c model_reasoning_effort=xhigh` | Review benefits from deep reasoning. The TUI reads model from config; effort can still be overridden. |

Always pass `--json` to `codex exec review` for machine-readable findings. The skill never invokes `codex review` (root) programmatically — it is interactive-only by design.

## Per-spawn additions

These vary by mode; spelled out per mode in the spine and per-mode references:

| Flag | Mode | Why |
|---|---|---|
| `--json` | exec, batch, single, review | JSONL events to stdout. Pair with `-o` for MCP-active dropout fallback. |
| `-o <file>` / `--output-last-message <file>` | exec, batch, single, review | Final-message or findings file. The skill reads this as truth for "did codex produce output." Pair with `--json` always. |
| `-C <dir>` / `--cd <dir>` | exec, single, review | Pin the worktree (or current cwd) for the spawned codex. Defaults to the spawning shell's cwd; explicit is safer in xargs subshells. |
| `--add-dir <path>` | rare | When the worktree needs codex to write to a path outside it (e.g. a shared monorepo build cache). Prefer this over downgrading to `danger-full-access`'s effective scope. |
| `--ephemeral` | batch only (optional) | Skips writing session files to disk. Useful for one-shot batch jobs that won't be resumed. **Forbidden** for review and rescue (kills resume capability). |

## Forbidden flags

| Flag | Why forbidden |
|---|---|
| `--full-auto` | Deprecated and removed in codex 0.129.0. Use `--dangerously-bypass-approvals-and-sandbox` plus `--sandbox <mode>`. |
| `-a on-failure` | Deprecated. Behaviorally similar to `on-request` for our purposes; explicit `never` is the policy. |
| `-a untrusted` / `-a on-request` | Would block fleet flow. Every spawn must run unattended. |
| `-s read-only` / `-s workspace-write` | Defeats the bypass policy. The skill is opinionated; downgrades silently change semantics. |
| `--ignore-rules` | The skill's policy is carried by the bypass + explicit flags; ignoring user `.rules` files is overreach. |
| `--ignore-user-config` | Same; user config is a useful audit signal. We don't suppress it. |
| `--remote <ADDR>` | The skill drives local codex only. Remote app-server is out of scope. |
| `--search` | TUI-only flag. Non-interactive runs use codex's tool-calling for search. |

## Per-session overrides

The user may override model and effort once per session:

```bash
USE_CODEX_CODEX_MODEL=gpt-5.6 \
USE_CODEX_CODEX_EFFORT=high \
node scripts/run-codex-2.mjs exec --tasks tasks.json
```

The override is captured in `manifest.policy.overrides` so rescue replays the same policy. Documented as advisory, not blocking — the skill assumes `gpt-5.5 + xhigh + bypass` is what the user wants in 95% of cases.

## Model alias

The `codex-companion.mjs` dispatcher recognizes one alias: `spark` → `gpt-5.3-codex-spark`. The skill does not surface this alias; if you want spark, pass `USE_CODEX_CODEX_MODEL=gpt-5.3-codex-spark` directly.

## Subcommand surfaces

| Subcommand | Use case |
|---|---|
| `codex exec` | The main spawn surface. Used by all modes except review. |
| `codex exec review` | The non-interactive review surface. Used by review mode workers. |
| `codex exec resume --last [PROMPT]` | Resume the most recent session in cwd. Used by rescue mode for single-task continuation. |
| `codex exec resume <SESSION_ID> [PROMPT]` | Resume a specific session by id. Used by rescue when the manifest has the session id. |
| `codex review` (root) | Interactive TUI review. **Not used by the skill** — that's interactive. The skill calls `codex exec review`. |
| `codex login status` | Auth probe. Pre-flight uses this to detect unauthenticated runs. |
| `codex resume` (root) | Interactive picker. Not used. |

## JSONL event types (with `--json`)

See `references/universal/json-streaming.md` for the full event dictionary. The summary:

| Event | Fields | Skill uses it for |
|---|---|---|
| `thread.started` | `thread_id` | Captured into `manifest.entries[i].codex_thread_id` for rescue resume. |
| `turn.started` | `{}` | Monitor "thinking" timer start. |
| `item.started` (`command_execution`) | `command` | Filter emits `[CMD>]`. |
| `item.completed` (`command_execution`) | `command, exit_code, aggregated_output` | Filter emits `[CMD✓]` / `[CMD✗]`. |
| `item.completed` (`reasoning`) | `text` | Filter emits `[THINK]` (first line only). |
| `item.completed` (`agent_message, phase=final_answer`) | `text` | Terminal success signal. The runner reads this as "the task spoke." |
| `item.started/completed` (`file_change`) | `changes:[{path,...}]` | Monitor counts touched files. |
| `turn.completed` | `usage:{input_tokens, cached_input_tokens, output_tokens}` | Monitor records token spend. |
| `error` | `message` | Filter emits `[ERR]`. Failure signal. |

## MCP-active dropout — known issue

When the user has MCP servers configured (`~/.codex/config.toml` `mcp_servers` table populated), `codex exec --json` may silently drop events from stdout. Tracked upstream as [#15451](https://github.com/openai/codex/issues/15451). The mitigation is unconditional: **always pair `--json` with `-o <file>`**.

If the JSONL stream loses the `agent_message phase=final_answer` event but `-o` shows the answer file is non-empty, the runner marks the entry `done` with advisory `last_error="json_event_dropped"`. Audit-fleet-state surfaces these so a human can confirm the output is what was expected.

## Verify before assuming

When in doubt, run `--help` against the actual binary the user has:

```bash
codex --version
codex exec --help
codex exec review --help
codex exec resume --help
codex review --help
```

If the binary disagrees with this document, the binary wins. File an issue against the skill (or the plan) so this reference can be bumped.

## What this file is not

- A general codex tutorial. The codex docs are upstream; this file is the skill's policy.
- A list of every codex flag. Only the flags the skill touches.
- An override-everything menu. Most flags are pinned by design.
