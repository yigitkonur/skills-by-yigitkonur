# The `to-delete/` Folder Pattern

**Rule: never `rm` a file you didn't create in this session. Move it to `to-delete/` instead.**

## Why

Deleting files an agent is uncertain about is a one-way action. Moving them to `to-delete/` is reversible, invisible (the folder is gitignored), and gives the owner a place to audit what was swept up.

This matters most with:
- AI agent session artifacts (`.continues-handoff.md`, `.claude-session*`, `.cursor-session*`, `.aider*`).
- Scratch scripts from prior exploration (`scratch/`, `debug-*.sh`, `one-off-test.py`).
- Orphan docs (`TODO.md`, `NOTES.md`, old `README.v2.md`).
- Binary artifacts of unknown origin.
- Anything you can't confidently say "this belongs in this repo".

## Setup (one-time per repo)

```bash
python3 scripts/init-to-delete.py
```

The script:
1. Creates `to-delete/` at the repo root if missing.
2. Adds a `.gitkeep` inside so the folder can exist without any files (git doesn't track empty dirs).
3. Appends `to-delete/` to `.gitignore` if not already there.
4. Appends the recommended AI-artifact / secrets / scratch patterns if not already there (see below).
5. Idempotent — safe to run repeatedly.

See `scripts/init-to-delete.md`.

## Recommended `.gitignore` additions

The script adds these if missing (grouped under a `# Added by run-repo-cleanup init-to-delete.py` header for auditability):

```gitignore
# to-delete/ sweep folder — never tracked, used for quarantine before real deletion
to-delete/

# Secrets (never tracked)
.env
.env.local
.env.*.local
*.pem
*.p12
id_rsa
id_rsa.pub
*.key
credentials.json
service-account.json

# AI agent session artifacts
.continues-handoff.md
.claude-session*
.cursor-session*
.aider*
.design-soul/
derailment-notes/
derail-notes/
derail-results/

# Editor scratch
.vscode/settings.local.json
.idea/workspace.xml
*.swp
*.swo
.DS_Store
Thumbs.db

# Local-only test / debug output
scratch/
tmp/
*.log
```

The entries are safe defaults. If your repo already has some of these with different variants, the script leaves existing entries alone and only appends missing ones.

## What to move into `to-delete/`

During Phase 1 diff-walk, for every file you encounter:

1. If you can name the concern it belongs to → commit it.
2. If it looks like AI session scratch, editor scratch, or orphan debug artifact → **move to `to-delete/`**.
3. If you genuinely can't tell → **move to `to-delete/`** and note it in the Phase 5 PR body so the owner reviews.

```bash
mv <file-or-dir> to-delete/
```

Multiple files at once (preserving relative structure):

```bash
mkdir -p to-delete/scratch
mv scratch/debug-*.sh to-delete/scratch/
```

## What NOT to move

- Files that belong to the feature you're working on — commit them.
- Files that are tracked in git already. If it's `git ls-files`-visible, it's NOT a candidate for `to-delete/` without a proper `git rm` commit. Move only untracked files.
- The `.gitignore` itself.
- `AGENTS.md`, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `LICENSE`, `package.json`, `pyproject.toml`. These are always load-bearing.

## Flushing `to-delete/`

`to-delete/` is not a garbage folder — it's a quarantine. The owner reviews it periodically:

```bash
# Review contents
ls -la to-delete/
find to-delete/ -type f | head -20

# For each, decide: promote back OR actually delete
mv to-delete/<path>/scratch-X ./<original-location>/   # promote
rm -rf to-delete/<path-to-actually-delete>              # real delete
```

Or bulk-delete when confident everything in `to-delete/` is actually trash:

```bash
rm -rf to-delete/* to-delete/.[!.]*
```

The folder itself stays (with `.gitkeep`) so future sweeps have a home.

## Reporting on `to-delete/` in the PR body

When Phase 1 moved files into `to-delete/`, the Phase 4 PR body must mention it:

> **Files moved to `to-delete/`**
>
> The following uncertain files were moved to `to-delete/` (gitignored) for owner review:
> - `scratch/old-debug-prompt.txt` — looked like AI session scratch.
> - `.continues-handoff.md` — agent session artifact.
> - `TODO.v2.md` — unclear if this is the current TODO or an old one.
>
> No files were deleted. Review `to-delete/` locally and delete or promote as appropriate.

That gives the owner a clean, reversible audit trail.

## Special case: tracked files of uncertain value

If a file is already tracked and you think it shouldn't be:

1. **Do NOT `git rm`** in a cleanup PR unless the owner asked for it.
2. Instead, open a **separate PR** that just deletes the file with a rationale in the PR body. The reviewer then decides.

Mixing "delete this uncertain thing" with other changes hides the decision in a large diff. Keep it its own PR.

## Why not just delete outright?

Three reasons:

1. **AI agents are overconfident.** Anything an agent confidently identifies as "not needed" is wrong ~5–10% of the time. On a large enough sweep that's a data-loss incident.
2. **`to-delete/` is free.** A gitignored folder costs zero runtime and zero review time.
3. **The owner's mental model > the agent's.** A file the agent thinks is scratch may be the owner's permanent note. Let them decide.

## Common mistakes

| Mistake | Fix |
|---|---|
| `rm -rf scratch/` | `mv scratch to-delete/scratch` |
| Forgetting to gitignore `to-delete/` | Run `init-to-delete.py` |
| Committing `to-delete/` | The folder is ignored; if it appears in `git status`, the ignore is missing |
| Treating `to-delete/` as eventually-to-delete | It's reviewed, not auto-flushed |
| Moving tracked files into `to-delete/` without `git rm` | Use `git rm` + commit for tracked files |
| Flushing `to-delete/` yourself without owner review | Don't. The owner flushes |

## The mindset

`to-delete/` is the cheapest-possible insurance against agent overconfidence. Move, don't delete. The owner decides.
