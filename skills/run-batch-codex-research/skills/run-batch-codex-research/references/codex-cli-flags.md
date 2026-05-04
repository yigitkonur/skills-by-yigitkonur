# Codex CLI flags — why bypass + skip-git-repo-check are required

The runner script invokes codex with two flags that look paranoid but are load-bearing for parallel fanout. This file explains why each is needed and what fails without them.

## The full invocation

```bash
command codex --dangerously-bypass-approvals-and-sandbox \
  exec --skip-git-repo-check \
  -m "$MODEL" -c model_reasoning_effort="$EFFORT" \
  -o "$answer" < "$prompt" > "$log" 2>&1
```

Each piece matters.

## Why `command codex` instead of `codex`

Many users (including the author) have a zsh function in `~/.zshrc` that wraps codex with the bypass flag:

```zsh
codex () { command codex --dangerously-bypass-approvals-and-sandbox "$@" }
```

When you type `codex exec ...` interactively in zsh, that wrapper kicks in.

**`xargs -P N -n 1 bash -c '...'` does NOT inherit the wrapper.** It spawns fresh `bash -c` subshells, which read no zsh init files. Inside those subshells, `codex` resolves to the binary at `$PATH` with no flags applied.

Using `command codex` explicitly bypasses the function lookup (in case any wrapper exists) and goes straight to the binary. It's a no-op when no wrapper exists, and a fix when one does.

## Why `--dangerously-bypass-approvals-and-sandbox`

Without it, codex in non-interactive mode will:

- Prompt for approval before running shell commands → hangs forever (no TTY).
- Refuse to write outside its sandbox → fails when `-o /path/to/answer.md` resolves outside cwd.
- Refuse to start in a non-trusted directory.

For research/generation tasks (no real shell-command tool calls — just text generation), the sandbox provides no security benefit, only friction. Bypass it.

This flag is named "dangerously" deliberately — Anthropic wants you to know you're disabling all guards. For batch *coding* runs the calculus is different (a malicious prompt could write to filesystem). For batch *research/generation*, codex only writes the answer file via `-o`; the dangers are minimal.

## Why `--skip-git-repo-check`

Codex defaults to refusing to run outside a "trusted directory" — typically a git repo. Many bulk-research workdirs are not git repos (just a folder with prompts/ and answers/), and the user has no reason to make them one.

Without this flag, you get:

```
Reading prompt from stdin...
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

— and the codex process exits non-zero. The runner reports `FAIL` for every job.

Adding `--skip-git-repo-check` tells codex "I know what I'm doing, this directory is intentional." Combine with `--dangerously-bypass-approvals-and-sandbox` and the trust check passes.

## Why model + reasoning effort are passed by config keys

```bash
-m "$MODEL" -c model_reasoning_effort="$EFFORT"
```

`-m` is a shortcut. `-c key=value` sets any TOML config override. `model_reasoning_effort` doesn't have a dedicated flag, so the `-c` form is the way. Common values: `low`, `medium`, `high`, `xhigh`. Default for batch research is `medium` — it gives strong output without burning cache budget.

Override per-batch by setting `EFFORT=high` before launching the runner.

## Why `-o` and stdin redirect work together

```bash
codex exec ... -o answers/foo.md < prompts/foo.md
```

- stdin → the prompt body, fed to codex as the user message.
- `-o file` → codex's last assistant message gets written to `file` after the run completes.

This is the cheapest way to do "one-shot prompt → file". No need for `--json` parsing, event filters, or wrapper scripts that capture output.

## Diagnosing FAILs

If many jobs FAIL with no obvious cause, read one of the per-job logs:

```bash
head -20 logs/<failed-name>.log
```

Common patterns:

| Log fragment | Cause | Fix |
|---|---|---|
| `Not inside a trusted directory` | Missing `--skip-git-repo-check` in the runner | Update `bin/run-batch.sh` |
| `Approval required` | Missing bypass flag | Same |
| `Unauthorized` / `Auth failed` | Codex not logged in | `codex login` once |
| `503 Service Unavailable` | Provider rate limit | Wait 10–15 min; rerun (skip guard re-runs only failed) |
| `tool sandbox denied` | A nested codex skill tried to write outside cwd | Bypass flag should cover this; check codex version |

If most jobs DONE but a handful FAIL transiently, just rerun the same script — the skip-existing guard will only retry the failed ones.

## Pre-flight check

Before launching a 50+ job batch, smoke-test on one prompt:

```bash
command codex --dangerously-bypass-approvals-and-sandbox exec --skip-git-repo-check \
  -m gpt-5.5 -c model_reasoning_effort=medium \
  -o /tmp/_smoke.md < prompts/$(ls prompts/ | head -1) > /tmp/_smoke.log 2>&1
echo "exit: $?"
wc -c /tmp/_smoke.md
```

If exit is 0 and `/tmp/_smoke.md` has content, the flags are correct and the runner will work. Then launch the full batch.
