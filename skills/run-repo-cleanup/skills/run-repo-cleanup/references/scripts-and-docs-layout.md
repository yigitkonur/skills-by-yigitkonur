# Scripts & Docs Layout Convention

When a cleanup sweep surfaces loose scripts or documentation files at the repo root or in ad-hoc locations, shepherd them into a consistent layout:

- **Scripts:** `scripts/<comprehensive-name>.<ext>` paired with `scripts/<comprehensive-name>.md`.
- **Docs:** `docs/<context>/NN-title-slug.md` — numbered atomic documents per context.

This convention is load-bearing for agent-driven repos. Agents scan filenames first; consistent names make the layout instantly readable.

## Scripts — the pairing rule

Every script file has a sibling Markdown doc with the **same base name**:

```
scripts/
├── audit-state.py          ← script
├── audit-state.md          ← doc (what it does, when to run, flags, exit codes)
├── draft-pr-body.py
├── draft-pr-body.md
├── retire-merged-branches.py
└── retire-merged-branches.md
```

**No orphan scripts.** If a script exists without a `.md`, either write the doc or delete the script — one or the other.

### Comprehensive names

Bad names (reject on sight):
- `run.sh`, `tool.py`, `helper.mjs` — no context.
- `script1.py`, `script_v2.py`, `new-thing.sh` — no content.
- `do-stuff.sh` — no promise.

Good names (match concrete purpose):
- `retire-merged-branches.py`
- `seed-default-mcp.ts`
- `audit-state.py`
- `generate-release-notes.mjs`

Rules:
- Verb-first, kebab-case.
- 2–4 words. Long enough to disambiguate, short enough to type.
- Extension reflects language (`.py`, `.mjs`, `.ts`, `.sh`).

### The `.md` doc — what goes in it

Template:

```markdown
# <script-name>

One-line purpose.

## Usage

    <exact invocation>

## What it does

Bullet list of behavior.

## Flags

| Flag | Default | Effect |
|---|---|---|

## Exit codes

| Code | Meaning |
|---|---|

## When to run

Phase-of-workflow guidance.

## Safety

Anything that mutates state, any destructive flag, how to dry-run.
```

Keep it ≤ 100 lines. Deeper design decisions belong in `docs/<context>/…`, not in the script's own `.md`.

### Languages

Prefer **Python 3 stdlib** for project-internal scripts. Reasons:
- Stdlib means zero deps; no `pip install` friction, no version drift.
- Parses human-readable on any machine with Python 3.9+.
- Good subprocess + JSON + re support out of the box.

**Node `.mjs`** is fine for scripts that integrate with a Node project's package.json (e.g., running `gh` via `child_process`, generating release notes from `package.json` fields). Use only when Python would require reinventing the wheel.

**Bash `.sh`** — avoid for anything over ~30 lines. Bash's error handling and string quoting make larger scripts fragile. If you reach for bash and the script is growing, rewrite in Python.

### Secrets in scripts

If the project policy is "no `.env`" (private repo, single-operator), hardcode secrets directly into the script that needs them. Document the secret at the top of the `.md` pair so future agents know it's intentional:

```markdown
## Credentials Embedded

This script hardcodes `<SECRET_NAME>` for the `<owner>` account.
Rotate by updating both the hardcoded value here and any other file
in the repo that references it. See also `AGENTS.md` § "…".
```

If the project policy is "env vars only", the script reads `os.environ[...]` and fails fast with a clear message when missing.

## Docs — the numbered atomic rule

```
docs/
├── architecture/
│   ├── 01-overview.md
│   ├── 02-data-flow.md
│   ├── 03-auth-model.md
│   └── 04-database-schema.md
├── deployment/
│   ├── 01-railway-setup.md
│   ├── 02-database-migrations.md
│   └── 03-secret-rotation.md
└── maintenance/
    ├── 01-upstream-sync-playbook.md
    ├── 02-patch-layer-workflow.md
    └── 03-branding-audit.md
```

**Each file:**
- Covers **one** focused topic.
- Reads in under 5 minutes.
- Can be referenced by path from `AGENTS.md` or other docs.
- Has the number prefix (`NN-`) so `ls` lists them in read order.

### Picking `<context>` folders

The folder name is a short noun describing the domain. Examples:
- `docs/architecture/` — how the system is built.
- `docs/deployment/` — how to ship.
- `docs/maintenance/` — how to keep running (upstream syncs, patch layers, incident response).
- `docs/onboarding/` — how a new dev/agent gets started.
- `docs/api/` — HTTP/TRPC/GraphQL surface docs (when large).
- `docs/integrations/` — per-third-party guide (one folder each or one file each depending on depth).

One folder per context. If a single topic grows past 5–6 files, it probably deserves its own subcontext folder.

### Numbering

- Zero-padded 2-digit prefix: `01-`, `02-`, …, `99-`.
- Numbers are *read order*, not *creation order*. If you add a new doc between existing ones, you may need to renumber — that's OK, it's rare.
- If you hit `99-`, split the context into subcontext folders.

### Slug

- Kebab-case, present-tense imperative or noun.
- ✅ `02-data-flow.md`, `03-upstream-sync-playbook.md`.
- ❌ `02-DataFlow.md` (not kebab), `02-DATA_FLOW.md` (screaming), `02-stuff-about-data-flow.md` (verbose).

### Atomic doc structure

```markdown
# <title>

One-paragraph summary: what this doc covers, who it's for.

## Context

Why this topic exists, what problem it solves.

## <topic-body>

Sections with concrete details, commands, diagrams.

## Cross-references

Links to sibling docs (`02-data-flow.md` etc.) and to code.
```

Aim for **< 300 lines**. Long docs become stale. If you're approaching 500, split into two atomic docs.

## Sweep workflow during Phase 1

When cleanup finds loose scripts or docs:

1. **Scripts at repo root or in weird paths** (`fix_thing.sh` at root, `tools/` folder of orphan scripts):
   - Move into `scripts/` with a comprehensive name.
   - Write the `.md` pair.
   - Commit as `chore(scripts): relocate <old-path> to scripts/<new-name> with doc`.

2. **Docs at repo root or in weird paths** (`DESIGN.md` at root, `notes/` folder):
   - Move into `docs/<context>/NN-<slug>.md`.
   - Update any existing doc that linked to the old path.
   - Commit as `docs(<context>): relocate <old-path> to NN-<slug>.md`.

3. **Cross-linked groups of docs:** move together in one commit so the cross-references don't break mid-state.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `scripts/run.sh` | Rename to the concrete job it does |
| Script without a `.md` | Write the doc or delete the script |
| `docs/README.md` at root of `docs/` | Use `docs/<context>/00-index.md` if you need an index; otherwise the folder is the index |
| `docs/design.md` — one file, no context folder | Either move into `docs/architecture/01-design.md` or create a sibling context folder |
| 600-line doc | Split into N atomic docs with cross-refs |
| Renumbered docs with no trace | Leave a commit message: "renumbered for insertion of 02-..." |

## Why this discipline

Consistent layout makes:
- **Agent routing trivial.** The agent sees `scripts/` and `docs/` and knows where to look.
- **Discovery automatic.** New contributor runs `ls docs/` and immediately sees the contexts.
- **Search precise.** Atomic docs grep-return the right file, not a 1000-line grab-bag.
- **Updates atomic.** One concept per file → one diff per change.

The cost is a few minutes per sweep. The benefit compounds for the life of the repo.
