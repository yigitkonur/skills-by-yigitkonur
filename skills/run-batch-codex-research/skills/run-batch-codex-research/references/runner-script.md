# Anatomy of run-batch.sh

The runner is intentionally small (under 60 lines). This file explains why each piece is the way it is, so you can modify it confidently.

## The full flow

```
find prompts/*.md -print0
  |
  xargs -0 -n 1 -P $JOBS bash -c 'run_one "$0"'
  |
  for each prompt:
    if answers/<name>.md is non-empty:  echo "SKIP <name>"
    else:
      echo "START <name>"
      codex exec ... -o answers/<name>.md < prompt > logs/<name>.log
      if exit 0:  echo "DONE <name>"
      else:       echo "FAIL <name> (...)"
```

The runner's stdout is a structured event log: `START`, `DONE`, `FAIL`, `SKIP`, then `--- all jobs finished ---`. That's the contract Monitor consumes.

## Why xargs and not GNU parallel

| | xargs -P | GNU parallel |
|---|---|---|
| Available | Yes (POSIX, ships with macOS/Linux) | Often missing on minimal images |
| Concurrency cap | `-P N` | `-j N` |
| NUL-safe filenames | `-0` | Yes (default) |
| Output ordering | Interleaved | Optional `--keep-order` |
| Citation banner | None | `--citation` nag |

xargs is enough. No reason to add a dependency.

## Why -n 1 (one prompt per bash invocation)

Without `-n 1`, xargs batches as many filenames as fit in a single command line, then invokes the function once with all of them as arguments. That breaks the "one event per state transition" promise — start/done would interleave per-batch instead of per-prompt.

`-n 1` ensures every invocation handles exactly one prompt, producing exactly one START and one DONE/FAIL/SKIP line.

## Why the `-print0 | xargs -0` pair

If any prompt filename contains spaces, newlines, or unusual characters, the default whitespace-separated xargs input breaks. `-print0`/`-0` uses NUL bytes as separators, which can never appear in filenames.

In practice, the rendering script sanitises slugs to `[a-zA-Z0-9._-]` so spaces won't appear. But the NUL-safe pair costs nothing and survives if a user pre-creates prompt files with weird names.

## Why `bash -c 'run_one "$0"'`

xargs invokes a child process per chunk. The child needs to be `bash` (so we can use `function` and `export -f`). The argument convention `bash -c 'COMMAND' "$0_value"` makes `$0` inside the command resolve to the filename — that's the cleanest way to pass the file as `$1` of the function call.

We `export -f run_one` and the env vars (`MODEL`, `EFFORT`, `ANSWERS`, `LOGS`) so the function and its environment are available inside each subshell.

## The skip-existing guard

```bash
if [ -s "$answer" ]; then
  echo "SKIP  $name (answer already exists)"
  return 0
fi
```

`[ -s file ]` = "file exists and is non-empty." This is the entire idempotency mechanism. It costs one stat() per prompt, runs at the start of `run_one`, and means:

- Reruns of the same workdir only process unfinished prompts.
- Crashes mid-batch don't lose completed work — relaunching skips finished ones.
- Adding a new prompt later is just `render-prompts.sh` then rerun the runner.

Empty answer files (zero bytes) re-run automatically. This handles the case where codex started but failed to write any output.

## Env vars and how to override them

```bash
JOBS=10 MODEL=gpt-5.5 EFFORT=medium ./run-batch.sh
```

| Var | Default | When to change |
|---|---|---|
| `JOBS` | `10` | 5 if your provider rate-limits you; 20 if you've measured headroom. Don't go above 20 without thinking. |
| `MODEL` | `gpt-5.5` | The model id codex passes through. Set to whatever your codex provider supports. |
| `EFFORT` | `medium` | `low` for simple lookups; `high` for deep reasoning; `xhigh` only if you have time and budget. |
| `PROMPTS` | `./prompts` | Override if your prompts live elsewhere. |
| `ANSWERS` | `./answers` | Same. |
| `LOGS` | `./logs` | Same. |

## Exit codes

The runner itself always exits 0 even if individual jobs failed — failures are surfaced via FAIL lines in the runner log, not via an aggregate exit code. This is intentional: the runner's job is to produce the event stream, not to gate downstream tooling on per-job results.

If you need a hard fail on any FAIL, post-process the runner log:

```bash
if grep -q '^FAIL ' logs/_runner.log; then
  echo "Some jobs failed" >&2
  exit 1
fi
```

## Common modifications

- **Different LLM CLI.** Replace the `codex exec` invocation with whatever your CLI is. Keep the stdin-redirect + `-o`-style output-file pattern if available; otherwise capture stdout to a temp file and `mv` it to `$answer` only on success.
- **Per-prompt model overrides.** Embed model hints in the prompt filename (`gpt-5.5__foo.md` vs `haiku__bar.md`) and parse the prefix in `run_one`. Most users don't need this.
- **Cooldown between jobs.** Add a `sleep` inside `run_one` to throttle. Better: lower `JOBS` instead — sleep doesn't help when 10 are concurrent anyway.

## What NOT to add

- A retry loop inside `run_one` — retries belong outside the runner (move answer aside, rerun the script). See `retry-strategy.md`.
- An aggregate "wait for all" hook — xargs already does this, the script blocks until the last job exits.
- A progress bar — Monitor is the progress bar, and rendering one inside the runner conflicts with the structured event stream.
- A "verify size" check inside `run_one` — the audit is a separate pass, intentionally. Mixing them invites premature retries on cold starts.
