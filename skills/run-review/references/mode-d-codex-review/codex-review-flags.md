# `codex review` flag reference

Verbatim flag table for the root-level `codex review` subcommand. Confirmed against `codex review --help` in `codex-cli 0.130.0`. Treat the live help output in the current environment as authoritative if it diverges.

## Synopsis

```
codex review [OPTIONS] [PROMPT]
```

`codex review` runs a code review **non-interactively**. It prints findings to stdout and returns. There is no resumable session; each invocation is one-shot.

## Arguments

| Argument | Meaning |
|---|---|
| `[PROMPT]` | Custom review instructions appended to codex's default review prompt. When `-` is supplied, codex reads the prompt from stdin (useful for long briefs). |

## Options

| Flag | Effect |
|---|---|
| `-c, --config <key=value>` | Override a config value that would otherwise come from `~/.codex/config.toml`. Use dotted paths (`foo.bar.baz`). The value is TOML-parsed; if parsing fails, the raw string is used. |
| `--uncommitted` | Review staged, unstaged, **and** untracked changes. |
| `--base <BRANCH>` | Review changes against the named base branch (e.g. `--base main`). |
| `--commit <SHA>` | Review the changes introduced by exactly one commit. |
| `--enable <FEATURE>` | Enable a codex feature (repeatable). Equivalent to `-c features.<name>=true`. |
| `--disable <FEATURE>` | Disable a codex feature (repeatable). Equivalent to `-c features.<name>=false`. |
| `--title <TITLE>` | Optional title displayed in the review summary header. Useful when reviewing a `--commit` or `--uncommitted` change with no PR title. |
| `-h, --help` | Print help. |

### Target selection — pick exactly one

`--uncommitted`, `--base`, and `--commit` are mutually exclusive review targets. If none is supplied, codex picks a default based on repo state (typically the branch's diff against the configured default base). For predictable behavior, always pass one of the three.

## What `codex review` does **not** accept

`codex review` (root) is **narrower** than `codex exec review`. The root form rejects all of these:

| Flag | Behavior |
|---|---|
| `--json` | rejected — root `codex review` prints human-readable findings only |
| `-o <file>` | rejected — use shell redirection (`tee`) instead |
| `-m <model>` | rejected — pin model via `-c model="<name>"` instead |
| `--dangerously-bypass-approvals-and-sandbox` | rejected — root review does not run shell commands; sandbox flags don't apply |
| `--ephemeral` | rejected — root review never persists session files |
| `--skip-git-repo-check` | rejected — root review must run inside a git work tree |

If the user needs any of those flags, route to `codex exec review` — see `codex-exec-review.md`.

## Common `-c` overrides

| Override | Effect |
|---|---|
| `-c model="o3"` | Pin a specific model for this run (replaces `-m`). |
| `-c model_reasoning_effort="high"` | Raise reasoning effort. Codex CLI default depends on profile. |
| `-c model_reasoning_effort="xhigh"` | Maximum effort; slower, deeper findings. |
| `-c sandbox_permissions='["disk-full-read-access"]'` | Pre-grant disk read for the review (TOML-parsed; quote carefully). |
| `-c features.<name>=true` / `=false` | Feature toggles; same as `--enable` / `--disable <name>`. |

`-c` values are parsed as TOML. If TOML parsing fails, codex falls back to using the raw string literally. Strings need TOML quoting (`-c model="o3"`, not `-c model=o3`).

## Invocation patterns

### Plain review against `main`

```bash
codex review --base main
```

### Review uncommitted work

```bash
codex review --uncommitted
```

### Review one commit, with a title for the summary

```bash
codex review --commit "$(git rev-parse HEAD~1)" --title "Refactor: extract auth middleware"
```

### Focus the review with a one-line prompt

```bash
codex review --base main "Focus on auth and session handling. Flag missing input validation and replay vulnerabilities."
```

### Long brief on stdin

```bash
cat <<'EOF' | codex review --base main -
Focus areas:
1. Token rotation correctness around session refresh.
2. Logout / revocation paths.
3. Any unbounded loops or O(n^2) hotspots in the new middleware.
Ignore lint-style suggestions; CI handles those.
EOF
```

### Pin model and raise effort

```bash
codex review --base main -c model="o3" -c model_reasoning_effort="high"
```

### Capture output to disk while still streaming to the terminal

```bash
mkdir -p /tmp/codex-review
ts=$(date +%Y%m%dT%H%M%SZ)
codex review --base main 2>&1 | tee "/tmp/codex-review/${ts}-review.md"
```

The skill always tees long reviews to disk so the user can scroll without losing scrollback.

## Exit codes

- `0` — review completed; findings on stdout.
- non-zero — invocation error (bad flag, target unresolvable, auth failure, codex backend error). Read stderr for the reason.

## Failure modes and recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| `error: unrecognized flag: --json` | Used `--json` on root `codex review`. | Switch to `codex exec review --json …`. |
| `error: unrecognized flag: -o` | Used `-o` on root `codex review`. | Switch to `codex exec review -o <file> …` or pipe to `tee`. |
| `error: fatal: not a git repository` | Not inside a git work tree. | `cd` into the repo root. Root `codex review` cannot use `--skip-git-repo-check`. |
| `error: BRANCH does not exist` after `--base origin/main` | The base ref is not fetched. | `git fetch origin <BRANCH>` then retry. |
| `error: unable to resolve commit SHA` after `--commit <SHA>` | SHA is short or ambiguous. | Use the full 40-char SHA from `git rev-parse <SHA>`. |
| Long pauses with no output | High reasoning effort + large diff. | Acceptable. Tee to disk and check in. Do not kill the process unless explicitly asked. |
| Auth failure (`not signed in`) | `codex login status` failing. | `codex login` interactively, or set `USE_CODEX_SKIP_CODEX_AUTH=1` when bearer-token / managed-companion / proxy auth is in use. |

## Comparison with `codex exec review`

| Feature | `codex review` (root) | `codex exec review` |
|---|---|---|
| Subcommand | top-level | nested under `exec` |
| `--json` JSONL events | no | yes |
| `-o <file>` last-message file | no | yes |
| `-m <model>` model pin | no (use `-c model="..."`) | yes |
| `--dangerously-bypass-approvals-and-sandbox` | no | yes |
| `--skip-git-repo-check` | no | yes |
| `--ephemeral` | no | yes |
| `--base <BRANCH>` | yes | yes |
| `--uncommitted` | yes | yes |
| `--commit <SHA>` | yes | yes |
| `--title <TITLE>` | yes | yes |
| `--enable` / `--disable` | yes | yes |
| `-c key=value` | yes | yes |
| Custom `[PROMPT]` positional | yes | yes (initial instructions) |
| Stdin prompt via `-` | yes | yes |

Rule of thumb: prefer root `codex review` when the user wants a human-readable second-opinion review and runs it interactively. Switch to `codex exec review` when machine-readable output, persisted last-message, model override, or a sandboxed/headless context is needed — see `codex-exec-review.md`.
