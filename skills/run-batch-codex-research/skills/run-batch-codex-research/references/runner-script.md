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
| Available | Ships with macOS/BSD and Linux out of the box (`-P`/`-0` are GNU/BSD extensions, not strict POSIX) | Often missing on minimal images |
| Concurrency cap | `-P N` | `-j N` |
| NUL-safe filenames | `-0` | `--null` / `-0` (newline-delimited by default) |
| Output ordering | Interleaved | Optional `--keep-order` |
| Citation banner | None | `--citation` nag |

xargs is enough. No reason to add a dependency.

## Why -n 1 (one prompt per bash invocation)

Our invocation is `bash -c 'run_one "$0"'` — only `$0` is consumed. Without `-n 1`, xargs would pack as many filenames as fit on the command line into a single `bash -c` call, where filenames 2..N land in `$1`, `$2`, … and `run_one "$0"` simply ignores them. The result: prompts get **silently dropped**, not "batched".

`-n 1` forces xargs to invoke `bash -c` once per filename, so every prompt runs exactly once and emits exactly one START and one DONE/FAIL/SKIP line.

## Why the `-print0 | xargs -0` pair

If any prompt filename contains spaces, newlines, or unusual characters, the default whitespace-separated xargs input breaks. `-print0`/`-0` uses NUL bytes as separators, which can never appear in filenames.

In practice, the rendering script sanitises slugs to `[a-zA-Z0-9._-]` so spaces won't appear. The NUL-safe pair costs nothing and survives if a user pre-creates prompt files with weird names — but note that the structured event protocol downstream (`DONE <name>` etc.) is still whitespace-delimited, and the watcher `sizeof()` helper rejects names outside `[A-Za-z0-9._-]`. **If you hand-author prompt files, keep filenames within that charset** or the watcher will report `0 bytes` for files it cannot safely look up.

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

The runner exits 0 on a successful pass even if individual jobs FAIL — per-job failures are surfaced via FAIL lines in the runner log, not via an aggregate exit code. This is intentional: the runner's job is to produce the event stream, not to gate downstream tooling on per-job results.

The runner exits 1 only on configuration errors detected before fanout (e.g. missing `PROMPTS` directory, no `*.md` prompts present). Those cases print `FATAL …` to stderr and skip the `--- all jobs finished ---` sentinel — no Monitor watcher will mistake them for a clean run.

If you need a hard fail on any per-job FAIL, post-process the runner log:

```bash
if grep -q '^FAIL ' logs/_runner.log; then
  echo "Some jobs failed" >&2
  exit 1
fi
```

## Common modifications

- **Different LLM CLI.** Replace the `codex exec` invocation with whatever your CLI is. The runner already does atomic writes via `$tmp` → `mv $tmp $answer` on success, so a CLI that produces output via stdout is fine — pipe to `$tmp` instead of using `-o`. Keep the rule: never write directly to `$answer`, or a partial-then-fail will poison the next idempotent rerun.
- **Per-prompt model overrides.** Embed model hints in the prompt filename (`gpt-5.5__foo.md` vs `haiku__bar.md`) and parse the prefix in `run_one`. Most users don't need this.
- **Cooldown between jobs.** Add a `sleep` inside `run_one` to throttle. Better: lower `JOBS` instead — sleep doesn't help when 10 are concurrent anyway.

## What NOT to add

- A retry loop inside `run_one` — retries belong outside the runner (move answer aside, rerun the script). See `retry-strategy.md`.
- An aggregate "wait for all" hook — xargs already does this, the script blocks until the last job exits.
- A progress bar — Monitor is the progress bar, and rendering one inside the runner conflicts with the structured event stream.
- A "verify size" check inside `run_one` — the audit is a separate pass, intentionally. Mixing them invites premature retries on cold starts.
