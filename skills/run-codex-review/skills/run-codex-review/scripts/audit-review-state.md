# audit-review-state.py

Wraps `run-repo-cleanup/scripts/audit-state.py` and adds review-loop-specific checks. The base audit detects dirty trees, mid-op rebases, fork-safety issues; this wrapper additionally detects orphan review worktrees, stale or malformed manifests, stale round logs, and in-flight Codex jobs from a prior session.

## Usage

```bash
python3 scripts/audit-review-state.py
python3 scripts/audit-review-state.py --json
python3 scripts/audit-review-state.py --manifest /tmp/codex-review-manifest.json
python3 scripts/audit-review-state.py --rounds-dir /tmp/codex-review-rounds/
python3 scripts/audit-review-state.py --stale-minutes 60
```

## What it adds on top of `audit-state.py`

The script first invokes `audit-state.py` and prints its full output. Then it appends a "REVIEW-LOOP CHECKS" section with:

1. **Manifest status** — present / absent / malformed.
2. **Review worktrees** — every worktree whose path basename matches `<repo-name>-wt-*`.
3. **Orphan worktrees** — review worktrees on disk but **not** referenced by the manifest (debris from a prior session).
4. **Stale round logs** — files in `<rounds-dir>` whose mtime is older than `--stale-minutes` (default 60).
5. **In-flight Codex jobs** — manifest entries with `last_review_id` set and `status` not in {DONE, CAP-REACHED, BLOCKED, FAILED}.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--manifest <path>` | `/tmp/codex-review-manifest.json` | Manifest to inspect. |
| `--rounds-dir <path>` | `/tmp/codex-review-rounds/` | Round-log directory. |
| `--stale-minutes <n>` | `60` | Threshold for "stale" round logs. |
| `--json` | off | Emit JSON instead of human report. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | CLEAN. Base audit returned 0 AND no review-loop debris. |
| `1` | ACTIONABLE. Base audit returned 1 OR any review-loop debris detected. |
| `2` | Not in a git repo / fatal subprocess error. |

## When to run

- **Phase 0** — first thing, every session. Surfaces orphan state from a prior run.
- **Phase 6** — last thing, before declaring TIDY. Must exit 0.
- **Anytime suspicious** — fast read-only sanity check.

## Safety

Pure read-only. Never mutates the manifest, the worktrees, the round logs, or git state. Calls `audit-state.py` as a subprocess (also pure read).

## How it locates `audit-state.py`

The script tries, in order:

1. `<this-skill>/../run-repo-cleanup/scripts/audit-state.py` (sibling skill in same install dir).
2. `~/.agents/skills/run-repo-cleanup/scripts/audit-state.py` (default install).
3. `~/dev-test/dotfiles/agents/.agents/skills/run-repo-cleanup/scripts/audit-state.py` (dotfiles repo).

If none are found, the script continues with review-loop-only checks and prints "(audit-state.py not found — review-loop checks only)" — does not fail.

## Sample output

```
────────────────────────────────────────────────────────────────
BASE AUDIT (run-repo-cleanup/scripts/audit-state.py)
────────────────────────────────────────────────────────────────
repo:    /Users/.../myrepo
branch:  main
upstream: origin/main  (ahead 0, behind 0)

remotes:
  origin     git@github.com:you/myrepo.git
  upstream   git@github.com:them/myrepo.git

dirty files: (none — working tree is clean)
worktrees: 1 (main only)
branches: 4 local, 7 remote

→ state is CLEAN.

────────────────────────────────────────────────────────────────
REVIEW-LOOP CHECKS
────────────────────────────────────────────────────────────────
manifest:         /tmp/codex-review-manifest.json
  absent (clean — no prior session debris)
review worktrees: 0

→ CLEAN
```

When debris is present:

```
manifest:         /tmp/codex-review-manifest.json
  ⚠  malformed JSON: Expecting value: line 1 column 1 (char 0)
review worktrees: 2
  • /Users/.../myrepo-wt-feat-foo  @ feat/foo
  • /Users/.../myrepo-wt-fix-bar   @ fix/bar

⚠  ORPHAN worktrees (in fs, not in manifest): 2
  • /Users/.../myrepo-wt-feat-foo  @ feat/foo
  • /Users/.../myrepo-wt-fix-bar   @ fix/bar
    Recommend: cleanup-worktrees.py --execute (use --force-abandon if unmerged)

⚠  STALE round logs (older than threshold): 3
  • feat-foo.07.json   (240m old)
  • feat-foo.08.json   (235m old)
  • fix-bar.04.json    (180m old)

→ ACTIONABLE
```

## Recovery flow when ACTIONABLE

1. Read each warning section.
2. For orphan worktrees: `cleanup-worktrees.py --execute` (or `--force-abandon <branch>` if not merged).
3. For stale round logs: triage per `references/failure-recovery.md` "Subagent crash". Either redispatch the subagent or mark FAILED.
4. For in-flight Codex jobs: query each via `codex review --status <id>`; recover per `references/failure-recovery.md` "In-flight Codex job from prior session".
5. For malformed manifest: recover per `references/failure-recovery.md` "Manifest corruption".
6. Re-run `audit-review-state.py`. Repeat until exit 0.

## Extending

- Add a `--cleanup` flag to invoke `cleanup-worktrees.py` directly when orphans are detected. Currently the script only reports — it never mutates.
- Add a per-job query against the codex CLI to enrich the in-flight section with `running` / `completed` status.
- Add a JSON Schema validation step for the manifest (catches schema drift earlier than malformed JSON).
