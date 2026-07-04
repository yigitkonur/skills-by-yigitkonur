# Troubleshooting — gotchas found while verifying the Sprites backend

Real issues hit during the first end-to-end run (2026-05-28) and how the skill handles them. If you
adapt this skill to another CLI version or backend, re-check these.

## 1. macOS `tar` injects AppleDouble `._*` files → breaks vitest/rollup
**Symptom:** remote run fails with `RollupError: Parse failure: Unexpected character '\0'` on a file
like `src/._booking.test.js`. macOS `bsdtar` emits AppleDouble companion entries + `com.apple.*` xattr
pax headers for files with extended attributes; the `._*` files reach the sandbox and tools try to
parse them.
**Fix (in `lib.sh:worktree_tar`):** `COPYFILE_DISABLE=1 tar --no-mac-metadata ...`. Plus a self-heal in
`sprites.sh:sync_worktree` that deletes any stale `._*` already baked into an older golden.
**Also:** rebuild a golden if a poisoned `._*` got checkpointed into it (`sprite destroy <sprite>` →
next run re-bootstraps clean).

## 2. `sprite restore` needs `-s <sprite>`
**Symptom:** `Error: sprite name required: use -s flag or create a .sprite file`.
**Fix:** `sprite restore -s "$SP" "$cid"` — the sprite must be named even though `restore` takes a
checkpoint ID. Checkpoints are addressed by ID (e.g. `v1`), resolved from `sprite checkpoint list` by
matching the golden name stored in the `--comment`.

## 3. Command quoting lost with `"$*"` → `node -e '...'` breaks
**Symptom:** `bash: -c: line 1: syntax error near unexpected token '('` for commands containing quotes
or shell metacharacters. Joining argv with `"$*"` and re-parsing via `bash -lc` drops inner quoting.
**Fix:** `printf -v q '%q ' "$@"` then `sprite exec ... -- bash -lc "$q"` — preserves exact args while
still allowing shell operators (`&&`, `|`, globs).

## 4. Symlinked entry point can't find its own libs
**Symptom:** `~/bin/lib.sh: No such file or directory` when running via the suggested `~/bin/offload`
symlink. `dirname "${BASH_SOURCE[0]}"` returns the symlink's dir, not the script's real dir.
**Fix (in `offload.sh`):** resolve the symlink chain before computing `HERE` (readlink loop).

## 5. Cold-start / post-restore `502 bad handshake`
**Symptom:** the first `sprite exec` after create or restore fails with `websocket: bad handshake
(HTTP 502)` while the microVM is still coming up.
**Fix (in `sprites.sh:sprite_wait`):** retry `sprite exec -s "$SP" -- true` up to ~90s before doing
real work; `restore` is async ("triggers an environment restart"), so gate readiness after it too.

## 6. Noisy remote `tar` xattr warnings
**Symptom:** `tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'`
(harmless GNU-tar warnings on the remote). **Fix:** extract with `--warning=no-unknown-keyword`.

## 7. Stale files after a warm restore
A warm restore brings back the golden's `/work` (source as of checkpoint time). `sync_worktree` now
first removes everything in `$OFFLOAD_WORKDIR` **except** `node_modules`/`.venv`/`.git`, then extracts
the fresh tree — so files deleted or renamed locally don't linger remotely, while warm deps survive.

## General
- Base Sprites image is **Ubuntu** with node/npm/python/git preinstalled — the golden only needs
  `npm ci`/`pip install` baked, not the toolchain.
- A poisoned or wrong golden is always recoverable: `sprite destroy <sprite>` and re-run (re-bootstraps).
- Keep the Sprites token out of the repo — it lives in `~/.config` after `sprite` install, never in skill files.
