# redistribute-commits.py

Phase 1 helper. For a branch with commits that mix concerns (different domains in one commit), produce a split plan and — in `--execute` mode — drive `git rebase -i` programmatically to split each mixed commit into per-domain conventional commits, with a safety backup ref so any failure can be recovered.

## Usage

```bash
# Dry-run: see the proposed split plan
python3 scripts/redistribute-commits.py --branch feat/foo --base main

# Execute: create backup ref, drive interactive rebase
python3 scripts/redistribute-commits.py --branch feat/foo --base main --execute

# Override published-commit refusal (rare; usually wrong)
python3 scripts/redistribute-commits.py --branch feat/foo --base main --execute --allow-published
```

## Heuristic — what "mixed concerns" means

For each commit in `<base>..<branch>`, the script reads the file list and groups by **domain**:

| Path pattern | Domain | Conv-commit type |
|---|---|---|
| `src/<a>/<b>/...` | `src/<a>/<b>` | `feat` |
| `packages/<x>/...` | `packages/<x>` | `feat` |
| `scripts/...`, `bin/...` | `scripts` | `chore` |
| `docs/...`, `*.md` | `docs` | `docs` |
| `test/...`, `*_test.py`, `*.test.ts`, `*.spec.ts` | `tests` | `test` |
| `locales/...`, `i18n/...` | `i18n` | `chore` |
| `.github/...` | `ci` | `ci` |
| `Makefile`, `package.json`, `*.lock`, `*.toml`, `*.yaml` | `build` | `build` |
| anything else | top-level dir | `chore` |

If a single commit's files span **2 or more domains**, the commit is flagged for splitting into N sub-commits, one per domain.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--branch <b>` | required | Branch to inspect / split. |
| `--base <ref>` | `main` | Base ref for the diff range (`<base>..<branch>`). |
| `--execute` | off (dry-run) | Actually split via interactive rebase. |
| `--allow-published` | off | Allow rewriting commits already on `origin/<branch>` (DANGEROUS — requires force-push). |
| `--backup-prefix <p>` | `backup/codex-review/` | Prefix for the safety backup ref. |
| `--json` | off | Emit machine-readable JSON. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No commits need splitting / split succeeded. |
| `1` | Dry-run with actionable splits printed. |
| `2` | Refused due to safety check (published commits without `--allow-published`) or fatal. |
| `3` | Rebase failed mid-flight; aborted and restored from backup ref. |

## Mechanics — execute mode

1. **Backup**: `git branch --force <backup-prefix><branch-slug>/<utc-timestamp> <branch>` — the safety net. Recover with `git reset --hard <backup-ref>` if anything goes wrong.
2. **Checkout** `<branch>` (rebase requires the branch to be checked out).
3. **Sequence editor**: write a temp Python script that rewrites the rebase-todo to mark every split-target commit's `pick` as `edit`. Set `GIT_SEQUENCE_EDITOR=python3 <temp-script>` and `GIT_EDITOR=true`.
4. **Start rebase**: `git rebase -i <base>` — pauses at the first `edit` stop.
5. **Per stop**:
   - Read the stopped SHA from `.git/rebase-merge/stopped-sha`.
   - Look up the plan entry for that SHA.
   - `git reset HEAD~` (un-applies the commit, leaves changes in the index).
   - For each domain group: `git add <files>` + `git commit -m '<emoji> <type>(<scope>): split from <short-sha>'`.
   - `git rebase --continue`.
6. **Loop** until `is_rebase_in_progress()` returns false.
7. **Failure handling**: any `git` command that fails triggers `git rebase --abort` + `git reset --hard <backup-ref>` + exit 3.
8. **Safety bound**: max iterations = `len(target_shas) + 5`. Prevents infinite loops if the rebase state is unexpected.

## Refusal: published commits

If any commit in the split-target list also exists on `origin/<branch>`, `--execute` is refused unless `--allow-published` is set. Rewriting published history requires force-push, which:

- Invalidates inline review attribution (Codex sees a different SHA).
- Breaks the round-log → review-id mapping in the manifest.
- Loses other people's work if they have the branch checked out.

**Preferred alternative for published commits**: use the cherry-pick-into-new-branch pattern from `references/commit-redistribution.md`. The original branch stays untouched.

## Subject convention

Auto-generated subjects: `<emoji> <type>(<scope>): split from <short-sha>`.

Examples:
- `✨ feat(src/features/foo): split from a1b2c3d4`
- `📝 docs(docs): split from a1b2c3d4`
- `🔧 chore(scripts): split from a1b2c3d4`

These are **placeholders**. After the split, refine each commit's subject with `git commit --amend` BEFORE pushing — the placeholder is meaningful for grouping, but ships poorly. Refinement is part of Phase 1's diff-walk discipline.

## Sample dry-run output

```
branch:    feat/lockdown
base:      main
commits:   2
needs split: 1 of 2

1. a1b2c3d4ef  ✨ feat(wope-lockdown): brand + behavior lockdown layer ⚠ MIXED
   files: 21, domains: ['src/features/Onboarding', 'src/features/ChatInput', 'docs', 'i18n']
   proposed split into 4 commits:
     - [feat(src/features/Onboarding)] 6 files
       subject: ✨ feat(src/features/Onboarding): split from a1b2c3d4
       • src/features/Onboarding/Classic/index.tsx
       • src/features/Onboarding/types.ts
       … and 4 more
     - [feat(src/features/ChatInput)] 8 files
       subject: ✨ feat(src/features/ChatInput): split from a1b2c3d4
       …
     - [docs(docs)] 5 files
       subject: 📝 docs(docs): split from a1b2c3d4
       …
     - [chore(i18n)] 2 files
       subject: 🔧 chore(i18n): split from a1b2c3d4
       …

2. f5e6d7c8aa  📝 docs(wope): document lockdown layer in AGENTS.md
   files: 9, domains: ['docs']

→ 1 commit(s) flagged for split. Re-run with --execute to perform the split.
```

## Recovery

If `--execute` exits with code 3, the script has already run `git rebase --abort` + `git reset --hard <backup-ref>`. The branch is back at the pre-split HEAD. Re-read the plan, decide whether to:

- Retry the split (perhaps with a refined `--branch` selection).
- Skip splitting and accept Codex flagging branch structure as a major item later.
- Cherry-pick into new branches manually instead.

The backup ref persists. Find it with:

```bash
git for-each-ref --format='%(refname:short)' 'refs/heads/backup/codex-review/<branch>/*'
```

Manual recovery (if the script's auto-restore failed for any reason):

```bash
git rebase --abort 2>/dev/null
git checkout <branch>
git reset --hard backup/codex-review/<branch>/<timestamp>
```

## When to run

- **Phase 1**, after the dirty-tree diff-walk and before Phase 2 (`spawn-review-worktrees.py`).
- Per branch that has multiple commits or large mixed commits. Skip branches with only one coherent commit.

## When NOT to run

- After Phase 2 has spawned worktrees or Phase 3 has started reviews. Mid-loop redistribution invalidates the round-log → review-id continuity.
- On commits that have been reviewed by Codex already (the review references the SHA you'd be deleting).
- When the cognitive cost of refining the auto-generated subjects exceeds the benefit of granular history.

## Safety properties

- **Backup ref is always created first.** No execute-mode failure can lose work that was on the branch before the run.
- **Refusal-by-default for published commits.** The script will not silently rewrite shared history.
- **Failure aborts and restores.** A failed rebase mid-flight does not leave the branch in a half-rebased state.
- **Max iterations cap.** A pathological rebase loop self-terminates with abort + restore.
- **Editor sandboxing.** `GIT_EDITOR=true` prevents any unintended editor invocation from blocking on `stdin`.

## Limitations

- The domain heuristic is path-based, not semantic. A commit that genuinely needs splitting along a non-path boundary (e.g. "extract this helper that lives in the same file as the feature") will be flagged as not-needing-split — manual splitting is still the right answer there.
- Auto-generated subjects are placeholders. Refine before pushing.
- Conflicts during rebase auto-abort. Manual rebase + manual splitting is the fallback for tangled history.
- Does not handle merge commits. The `--no-merges` filter on `git log` excludes them; merge commits are left alone.

## Extending

- Add `--per-commit-plan <json>` to consume a hand-written split plan (overrides the heuristic).
- Add `--interactive` to ask the user for subject refinement at each stop.
- Add `--by-prefix <regex>` to group files by a non-path-based pattern (e.g. test files vs production files when both live in `src/`).
