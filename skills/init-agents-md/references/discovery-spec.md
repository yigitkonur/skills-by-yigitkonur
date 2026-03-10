# AGENTS.md Discovery Specification

How AI coding agents discover, load, and merge AGENTS.md files. Based on the official AGENTS.md standard and Codex CLI implementation.

## Format

- **Plain markdown.** No required fields, no YAML frontmatter, no special syntax.
- Any headings and structure work. Agents parse the raw text.
- No `@import` syntax (that is a CLAUDE.md feature).
- No file size enforcement by format — but Codex CLI enforces `project_doc_max_bytes`.

## Discovery Algorithm (Codex CLI)

Codex builds an instruction chain once per session:

### Step 1: Global Scope

Check `~/.codex/` for:
1. `AGENTS.override.md` (if exists and non-empty) → use it
2. Else `AGENTS.md` (if exists and non-empty) → use it

At most one file at this level.

### Step 2: Project Scope

Starting at the project root (typically git root), walk down the directory tree to the current working directory. At each directory, check in order:

1. `AGENTS.override.md`
2. `AGENTS.md`
3. Any name in `project_doc_fallback_filenames`

Include at most one file per directory (the first non-empty found).

### Step 3: Merge

Concatenate all discovered files from root → leaf, separated by blank lines. Files closer to the current directory appear later and **override** earlier content.

### Step 4: Size Limit

Stop adding files when combined size reaches `project_doc_max_bytes` (default: 32,768 bytes / 32 KiB).

Empty files are skipped entirely.

## Override Mechanism

`AGENTS.override.md` takes precedence over `AGENTS.md` in the same directory.

When both exist in a directory, only `AGENTS.override.md` is read. The base `AGENTS.md` is ignored for that directory level.

**Use cases for overrides:**
- Temporary instructions during a migration
- Environment-specific rules (staging vs production)
- Quick experiments without modifying the shared file

Remove the override file to restore shared guidance.

## Configuration (Codex CLI)

Settings in `~/.codex/config.toml`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `project_doc_max_bytes` | 32768 | Maximum combined instruction size |
| `project_doc_fallback_filenames` | `[]` | Alternate filenames to check |

### Fallback Filenames

```toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
```

Check order per directory: `AGENTS.override.md` → `AGENTS.md` → fallback filenames in order.

## General Agent Discovery (Non-Codex)

Most agents follow a simpler model:

1. Look for `AGENTS.md` at the repository root
2. Read it as context before starting work
3. Explicit user prompts override file content

For monorepos, some agents (Codex, Cursor, VS Code) check for nested files. Others only read the root file. When in doubt, keep the root file comprehensive.

## Monorepo Hierarchy Example

```
repo/
├── AGENTS.md                          # Global project instructions
├── services/
│   ├── payments/
│   │   ├── AGENTS.md                  # Payment service specifics
│   │   └── AGENTS.override.md        # Temporary migration rules
│   └── auth/
│       └── AGENTS.md                  # Auth service specifics
└── packages/
    └── shared/
        └── AGENTS.md                  # Shared library rules
```

**What Codex loads when working in `services/payments/`:**
1. `~/.codex/AGENTS.md` (global)
2. `repo/AGENTS.md` (root)
3. `repo/services/payments/AGENTS.override.md` (nearest — override wins)

**Combined: root instructions + payment override.** The base `services/payments/AGENTS.md` is skipped because the override exists.

## Verification

After creating or editing AGENTS.md files, verify the discovery chain:

```bash
# Codex: ask it to summarize loaded instructions
codex --ask-for-approval never "Summarize the current instructions."

# Codex: check from a subdirectory
codex --cd services/payments --ask-for-approval never "List the instruction sources you loaded."
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| No guidance loaded | File is empty or not at project root | Ensure file has content; check `codex status` for workspace root |
| Wrong instructions | Override file in parent directory | Search upward for `AGENTS.override.md` files |
| Fallback names ignored | Not listed in config | Add to `project_doc_fallback_filenames` and restart Codex |
| Content truncated | Combined size exceeds 32 KiB | Raise `project_doc_max_bytes` or split across nested directories |
| Instructions from wrong level | Global file overriding project | Check `~/.codex/AGENTS.md` for conflicting content |
