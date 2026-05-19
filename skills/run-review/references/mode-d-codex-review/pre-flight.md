# Mode D pre-flight checks

Run these before composing the `codex review` invocation. Each check is one shell command; one line of failure recovery per check.

## Required pre-flight checks

### 1. `codex` binary present

```bash
command -v codex
```

Expected: prints a path. If empty: install codex CLI before proceeding; do not improvise.

### 2. Version is `0.130.0` or newer

```bash
codex --version
```

The Mode D flag table is verified against `codex-cli 0.130.0`. Older versions may not accept `--enable`, `--disable`, `--commit`, or the bare `[PROMPT]` argument.

If older: capture the live `codex review --help` and re-derive the flag set from that output before invoking.

### 3. Inside a git work tree

```bash
git rev-parse --is-inside-work-tree
```

Expected: `true`. Root `codex review` cannot use `--skip-git-repo-check` — if you're outside a git repo, either `cd` into one or switch to `codex exec review --skip-git-repo-check`.

### 4. Base branch exists (if `--base <BRANCH>` is the target)

```bash
git rev-parse --verify "$BRANCH"
```

If the ref is missing locally but tracked on `origin`:

```bash
git fetch origin "$BRANCH:refs/remotes/origin/$BRANCH"
```

Then re-run.

### 5. Commit SHA resolvable (if `--commit <SHA>` is the target)

```bash
git rev-parse --verify "$SHA"
```

Use the full 40-char SHA from this command to avoid ambiguity. Codex may reject shortened SHAs that match more than one commit.

### 6. Working tree state (if `--uncommitted` is the target)

```bash
git status --short
```

`--uncommitted` reviews staged + unstaged + untracked files. Confirm the tree actually has uncommitted changes (a clean tree under `--uncommitted` produces an empty review).

### 7. Codex auth

```bash
codex login status
```

Expected: a logged-in status line. If `Not logged in` AND the environment uses bearer-token / managed-companion / proxy auth:

```bash
export USE_CODEX_SKIP_CODEX_AUTH=1
```

This env var is honored by the pack's codex bootstrap and skips the hard-gate. Document the bypass when reporting back to the user.

If `Not logged in` AND no proxy / token is in play, run `codex login` interactively before invoking review.

## Optional pre-flight checks

### Disk space for long captures

If teeing review output to disk:

```bash
df -h /tmp
```

Codex review output for a large diff can run into hundreds of KB; ensure /tmp has room before kicking off.

### Confirm output directory

```bash
mkdir -p /tmp/codex-review
```

Done early so the `tee` target exists when the invocation runs.

## When a pre-flight check fails

Stop. Report the failed check to the user in one line. Do **not** silently degrade — for example:

- do not switch to `codex exec` without telling the user when the base flag failed,
- do not skip auth and `--dangerously-bypass-approvals-and-sandbox` your way around it,
- do not change `--commit` to `--uncommitted` because the SHA didn't resolve.

The user picked the target; the skill verifies and reports — it does not improvise.

## Pre-flight script (paste-ready)

```bash
#!/usr/bin/env bash
set -euo pipefail

# Mode D pre-flight. Adjust TARGET_KIND and TARGET_VALUE before running.
TARGET_KIND="${1:-base}"        # base | uncommitted | commit
TARGET_VALUE="${2:-main}"        # branch name | (ignored for uncommitted) | full SHA

command -v codex >/dev/null || { echo "FAIL: codex not on PATH"; exit 1; }
codex --version || { echo "FAIL: codex --version errored"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null || { echo "FAIL: not in a git work tree"; exit 1; }

case "$TARGET_KIND" in
  base)
    git rev-parse --verify "$TARGET_VALUE" >/dev/null \
      || { echo "FAIL: base branch $TARGET_VALUE not resolvable; fetch first"; exit 1; }
    ;;
  uncommitted)
    if [[ -z "$(git status --short)" ]]; then
      echo "WARN: --uncommitted target but working tree is clean — review will be empty"
    fi
    ;;
  commit)
    git rev-parse --verify "$TARGET_VALUE" >/dev/null \
      || { echo "FAIL: commit SHA $TARGET_VALUE not resolvable"; exit 1; }
    ;;
  *)
    echo "FAIL: unknown TARGET_KIND $TARGET_KIND"; exit 1 ;;
esac

if ! codex login status >/dev/null 2>&1; then
  if [[ "${USE_CODEX_SKIP_CODEX_AUTH:-0}" != "1" ]]; then
    echo "FAIL: codex login status failed and USE_CODEX_SKIP_CODEX_AUTH!=1"
    exit 1
  fi
fi

echo "PASS: pre-flight clean for codex review --$TARGET_KIND $TARGET_VALUE"
```

Run it once before composing the actual `codex review` invocation. The skill never bundles this as an executable script — it is a paste-ready snippet because the exact set of checks varies by target.
