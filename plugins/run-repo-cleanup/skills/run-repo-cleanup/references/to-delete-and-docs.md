# `to-delete/` Trash + Docs Consolidation

**Rule: nothing non-essential stays in the working tree, and nothing gets `rm`'d. Everything non-essential moves to a gitignored `to-delete/`; everything doc-like consolidates into a gitignored `docs/`.**

Be aggressive. Moving is reversible — both folders are gitignored, so a wrong move costs nothing and the owner can promote anything back. The bar is high: *if a file isn't needed to run, build, or understand the project, it goes.*

## What stays (the keep-list)

At the repo root, keep:
- `README*` — the entry point.
- `AGENTS.md`, `CLAUDE.md` — agent instructions.
- `LICENSE*`, `CONTRIBUTING*`, `CODE_OF_CONDUCT*` — project governance.
- Everything required to **run or build**: source dirs (`src/`, `lib/`, `app/`, …), `package.json` + lockfiles, `pyproject.toml`, `Makefile`, `Dockerfile`, `tsconfig.json`, CI config (`.github/`), `.gitignore`, etc.

Doc **folders** (`docs/`, `agent-docs/`, `documentation/`) may stay — but they get **consolidated into a single `docs/`** (see below).

## What moves to `to-delete/` (sweep-eligible — be aggressive)

Everything else, **including hidden files and folders**:
- **AI/agent session artifacts:** `.continues-handoff.md`, `*.claude-session*`, `.cursor-session*`, `.aider*`, `.design-soul/`, `derailment-notes/`, `derail-*`, handoff notes, "what I did" summaries.
- **Scratch + one-offs:** `scratch/`, `tmp/`, `debug-*.sh`, `one-off-*.py`, `test-*.js` left at root, throwaway scripts.
- **Stray plans / notes:** `TODO.md`, `NOTES.md`, `PLAN.md`, `IDEAS.md`, `*.plan.md`, anything that's a working note rather than project doc.
- **Secrets that slipped in:** `.env`, `.env.*`, `*.pem`, `id_rsa*`, `*.key`, `credentials.json`, `service-account.json` — move them out of the tree *and* ensure they're gitignored.
- **Unknown binaries / build debris** not produced by the build: stray `.zip`, `.log`, `.sqlite`, dumps.

When in doubt, the script **lists** the file rather than moving it, and you decide. But default aggressive: the cost of moving something that turns out essential is one `mv` back.

## Docs consolidation — always one `docs/`

Multiple doc locations are confusing. Unify them:
1. All doc-like content — stray root `*.md` (outside the keep-list), `agent-docs/`, `documentation/`, `notes/` that are real docs — moves **into a single `docs/`** folder.
2. If several doc folders exist, they merge into one `docs/` (preserve subpaths to avoid name collisions, e.g. `docs/agent-docs/…`).
3. `docs/` is then **gitignored** too. The reasoning: in a finished-cleanup state the human wants docs available locally for reference but not cluttering version control / not committed as project surface. (If a project genuinely ships its docs — a docs site, published API reference — that's an `AGENTS.md`/repo-convention override; keep `docs/` tracked in that case.)

## `.gitignore` management

Before moving anything, the sweep ensures `.gitignore` contains, under an auditable header:

```gitignore
# Added by run-repo-cleanup sweep-artifacts.py
to-delete/
docs/

# Secrets (never tracked)
.env
.env.*
*.pem
id_rsa
id_rsa.pub
*.key
credentials.json
service-account.json

# AI agent session artifacts
*.claude-session*
.cursor-session*
.aider*
.continues-handoff.md
.design-soul/
derailment-notes/
```

Idempotent — patterns already present are not duplicated. Adding the ignore *before* moving means the moved files disappear from `git status` immediately instead of showing as deletions.

## Flushing `to-delete/`

This skill never empties `to-delete/`. The owner reviews it later and either promotes files back or deletes for real:

```bash
ls -la to-delete/        # review what got swept
rm -rf to-delete/        # when you're sure nothing in there matters
```

That deliberate, human `rm` is the only real deletion in the whole flow.
