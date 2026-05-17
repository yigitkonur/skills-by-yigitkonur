# init-to-delete.py

Idempotently sets up the `to-delete/` quarantine pattern in the current repo:

1. Creates `to-delete/` at the repo root (with `.gitkeep` so git tracks the empty dir).
2. Appends `to-delete/` to `.gitignore` if not present.
3. Appends recommended patterns (secrets, AI artifacts, editor scratch, test/debug outputs) to `.gitignore` if not present.

Safe to run repeatedly — the script only adds what's missing.

## Usage

```bash
python3 scripts/init-to-delete.py                  # apply
python3 scripts/init-to-delete.py --dry-run        # preview
python3 scripts/init-to-delete.py --print-patterns # print the recommended patterns
```

## What the patterns cover

```
# to-delete/ sweep folder
to-delete/

# Secrets
.env, .env.local, .env.*.local
*.pem, *.p12, id_rsa, id_rsa.pub, *.key
credentials.json, service-account.json

# AI agent session artifacts
.continues-handoff.md
.claude-session*, .cursor-session*, .aider*
.design-soul/, derailment-notes/, derail-notes/, derail-results/

# Editor scratch
.vscode/settings.local.json, .idea/workspace.xml
*.swp, *.swo, .DS_Store, Thumbs.db

# Local-only test / debug output
scratch/, tmp/, *.log
```

The full list lives in the script's `PATTERNS` constant. Run `--print-patterns` to see it without modifying the repo.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--dry-run` | off | Print actions that would be taken, without changing anything. |
| `--print-patterns` | off | Print the pattern list and exit. No filesystem access. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK — changes applied, nothing to do, or `--print-patterns` completed. |
| 2 | Not inside a git repository. |

## How it modifies `.gitignore`

Appends a clearly-labelled block:

```
# ━━ Added by run-repo-cleanup init-to-delete.py ━━
<all patterns>
# ━━ end run-repo-cleanup ━━
```

If you later run the script again and some patterns are already present (from the block OR from elsewhere in `.gitignore`), it only appends the missing ones — but as a fresh block. That's intentional: each run leaves a clear audit trail of what was added when.

After running, if you want to consolidate into a single block, delete the duplicates manually. The script will not do this automatically (it's safer to leave duplicates than to incorrectly merge).

## When to run

- **Phase 0**, on any repo that doesn't have a `to-delete/` folder yet.
- **New repo setup**, as part of the fork-safety checklist (see `references/fork-safety.md`).

## Safety

Creates files (`.gitkeep`, appends to `.gitignore`). Never deletes anything.

Running on a repo that already has all the patterns is a no-op: the script reports "Nothing to do" and exits 0.

If you want to inspect the patterns before applying, use `--print-patterns` or `--dry-run`. Both leave the repo untouched.

## Extending

If your project has additional patterns to ignore (common in specific frameworks — e.g. `.next/`, `.nuxt/`, `target/`, `vendor/`), add them to the `PATTERNS` list in the script. Keep the categorization comments (`# Secrets`, `# Editor scratch`, etc.) so the `.gitignore` stays readable.
