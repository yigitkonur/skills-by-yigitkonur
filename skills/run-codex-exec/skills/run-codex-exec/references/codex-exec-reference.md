# Codex CLI Reference (codex exec)

Focused on the flags that matter for programmatic orchestration. For the full surface run `codex exec --help`.

Tested against `codex-cli 0.121.0`.

## Basic invocation

```bash
codex exec [OPTIONS] [PROMPT]
```

Prompt can be passed as an argument (short) or via stdin (long multi-line). If both are provided, stdin is appended as a `<stdin>` block.

## The flags the wrapper uses

| Flag | What it does | Why it matters |
|---|---|---|
| `--full-auto` | Sets sandbox to `workspace-write` and auto-approves edits + reads + bash within the cwd | Required for non-interactive automation; without this the agent will prompt for permission on every edit |
| `-m, --model <id>` | Model selection | `gpt-5.4` is the current default; `gpt-5` / `o3` also valid |
| `-c <key=value>` | Override a config value from `~/.codex/config.toml` | Used for `-c model_reasoning_effort=high` / `xhigh` / `medium` / `low` |
| `-C, --cd <DIR>` | Set agent's working root | Alternative to `cd` before launching; explicit is safer |
| `--skip-git-repo-check` | Allow running outside a git repo | Needed when working in a temp dir; never needed for worktrees |

## Reasoning effort trade-off

From `~/.codex/config.toml` override via `-c model_reasoning_effort=<level>`:

| Level | Typical tokens | Reliability | Use when |
|---|---|---|---|
| `low` | ~15k | ~100% completion | 1-3 mechanical commands, file ops, simple patches |
| `medium` | 30k-60k | 80%+ | Multi-step coding, refactoring, straightforward features |
| `high` | 60k-110k | 50-70% | Multi-file changes requiring reasoning across modules |
| `xhigh` | 80k-150k | 30-50% | Deep architectural work, paired plans, complex migrations |

**Counter-intuitive rule:** higher reasoning ≠ better outputs. A task that fits in `medium`'s budget will complete more reliably at `medium` than at `high`. At `xhigh` the agent often exhausts its reasoning budget on the plan before writing any code.

**Default to `high`** for shipping-level plans (not `xhigh`). The 10-30 point reliability gap is worth accepting some nuance loss.

## Sandbox modes

From `-s, --sandbox <mode>`:

| Mode | Permissions |
|---|---|
| `read-only` | No edits, no commands, only reads. For inspection tasks. |
| `workspace-write` | Edit + run commands + read. **This is what `--full-auto` sets.** |
| `danger-full-access` | No sandbox. Not needed for orchestration. |

`--full-auto` is the happy path. Use it and stop thinking about sandboxes.

## Reading stdin

If you pass `-` as the prompt argument, codex reads instructions from stdin. Useful for passing multi-line prompts without shell escape hell:

```bash
codex exec --full-auto -m gpt-5.4 - <<'PROMPT'
Your multi-line prompt here.
Notice the quoted heredoc marker prevents shell expansion.
PROMPT
```

The wrapper uses the argument form because its prompts come through via `"$3"` quoting.

## Useful non-flag behaviors

- **`--output-last-message <FILE>`** — writes the agent's last message to a file. Useful when you want the agent's summary without parsing its full stdout.
- **`--json`** — emits events as JSONL. Useful for programmatic parsing. Wrapper doesn't use this; stdout lines are fine for grep.
- **`--ephemeral`** — don't persist session files. Use for one-shot runs where resume isn't needed.
- **`--color never`** — strip ANSI codes. Useful when piping to log files (wrapper's `tee` already does this cleanly with color on, but some tools prefer never).

## Auth

Configured via `~/.codex/config.toml` or the companion app. Check status:

```bash
node "$(find ~/.claude/plugins -name codex-companion.mjs 2>/dev/null | head -1)" setup --json
```

Or in plain codex:
```bash
codex --version        # just confirms install
# Auth status is visible in `~/.codex/config.toml` + app-server logs
```

If `auth.loggedIn` is false, run `codex login` once interactively.

## Things NOT to do in the wrapper

- **Don't pass `--dangerously-bypass-approvals-and-sandbox`.** `--full-auto` is sufficient. The dangerous flag removes all guardrails.
- **Don't use `-s read-only` for work that should produce edits.** The agent will try and fail silently.
- **Don't set `model_reasoning_effort=xhigh` by default.** Reliability drops faster than output quality improves.
- **Don't combine `--json` with `| tee`.** Binary output corrupted by tee reconfiguring the stdout. Use `--json > file` instead.

## Rate-limit behavior

Codex's backend (OpenAI infrastructure) enforces per-account rate limits. When you exceed them, `codex exec` exits with:

```
ERROR: unexpected status 503 Service Unavailable: Rate limit exceeded. Try again in ~806s
```

Observed reset windows (trust the `Try again in <N>s` value from the error, not the averages):
- **~13 minutes** after a burst of ~10 parallel high-reasoning dispatches on a mostly-fresh quota.
- **~45 minutes** on a quota already depleted by a long session earlier the same day.
- Occasionally much shorter (~5 min) for very small bursts.

No reliable way to pre-check — just try and handle the 503. The wrapper's post-verify will show `no changes` and `exit=1` when this happens.

## Performance tips

- `gpt-5.4 medium reasoning` on a focused prompt ≈ 300-600 seconds for a small-medium plan.
- `gpt-5.4 high reasoning` on a focused prompt ≈ 500-900 seconds.
- `gpt-5.4 xhigh reasoning` with a dense prompt ≈ 1500-2500 seconds. Don't use unless you have to.
- Paired plans (two related plans in one worktree) double the runtime predictably.

Budget ~1 hour end-to-end for a wave of 6 plans at `high`. Budget ~2 hours at `xhigh`.
