# AGENTS.md update — the 5-state symlink machine

After the Makefile is generated, the skill syncs only the downstream project's `## Make targets` agent-doc section as the last core step before optional CI/CD wiring. The contract is fixed: **`AGENTS.md` is the source of truth; `CLAUDE.md` is a symlink → `AGENTS.md` (or absent).** This is a deliberate convention — one place to edit, two places agents look. Five starting states cover every observed shape of the world.

This file is the only reference that reads and merges existing agent prose. Other references may still ask bounded scenario, monorepo, or CI/CD authorization questions; treat prose merging with separate care.

## The contract

| Object | What it should be after the skill runs |
|---|---|
| `AGENTS.md` | A regular file (not a symlink). Contains a `## Make targets` section accurately describing the generated Makefile. |
| `CLAUDE.md` | A relative symlink: `CLAUDE.md → AGENTS.md`. Exists only after `AGENTS.md` exists. |
| `CLAUDE.md` (absent) | Acceptable if the project predates the convention — but the skill always creates the symlink unless the user opts out. |

Boundary: `init-makefiles` updates only the `## Make targets` section and same-directory `CLAUDE.md → AGENTS.md` compatibility link. Broad AGENTS-first governance, nested folder instructions, and REVIEW.md belong to `init-agent-config`.

Why a symlink and not a copy: the user edits one file and both agent runtimes see the update. Two files drift; a symlink does not. Why `CLAUDE.md → AGENTS.md` and not the reverse: `AGENTS.md` is the cross-vendor convention (Codex, Cursor, Aider, Claude Code itself all read `AGENTS.md`), and `CLAUDE.md` is the legacy fallback.

## State detection — exact shell

The skill runs this block once at the start of the AGENTS.md step. Variables capture the state for the transition logic.

```bash
has_agents=$(test -f AGENTS.md && ! test -L AGENTS.md && echo 1 || echo 0)
has_claude=$(test -f CLAUDE.md && ! test -L CLAUDE.md && echo 1 || echo 0)
is_agents_link=$(test -L AGENTS.md && echo 1 || echo 0)
is_claude_link=$(test -L CLAUDE.md && echo 1 || echo 0)
link_target=$(readlink CLAUDE.md 2>/dev/null || true)
```

Reading the variables:

| Variable | Reads as |
|---|---|
| `has_agents=1` | `AGENTS.md` exists as a regular file (not a symlink) |
| `has_claude=1` | `CLAUDE.md` exists as a regular file (not a symlink) |
| `is_agents_link=1` | `AGENTS.md` is a symlink |
| `is_claude_link=1` | `CLAUDE.md` is a symlink |
| `link_target` | Where `CLAUDE.md` points (empty if not a symlink) |

`test -f` returns true for both regular files and symlinks-to-files. `! test -L` discriminates: regular file only.

The five states map to combinations of these flags:

| State | `has_agents` | `has_claude` | `is_claude_link` | `link_target` | Description |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 0 | (empty) | Both exist as separate files |
| 2 | 1 | 0 | 0 | (empty) | Only AGENTS.md exists |
| 3 | 0 | 1 | 0 | (empty) | Only CLAUDE.md exists |
| 4 | 0 | 0 | 0 | (empty) | Neither exists |
| 5 | 1 | 0 | 1 | `AGENTS.md` | CLAUDE.md is already a symlink |

`is_agents_link=1` is rare and treated as a degenerate case (`CLAUDE.md → AGENTS.md → ?`); see Edge cases below.

## State 1 — Both AGENTS.md and CLAUDE.md exist as separate files

Highest-friction case. The user has two real files; one or both might have content the other doesn't.

```bash
# 1. Read both, semantic diff
diff -u AGENTS.md CLAUDE.md > /tmp/agents-claude.diff || true
# 2. If contents differ, ask the user
if [ -s /tmp/agents-claude.diff ]; then
  printf "AGENTS.md and CLAUDE.md both exist with different content. Merge into AGENTS.md (Y/n)? "
  read answer
fi
# 3. Default Y → merge by appending CLAUDE.md-unique sections to AGENTS.md (or write the user's curated merge)
#    n → keep AGENTS.md as truth, drop CLAUDE.md content
# 4. Delete CLAUDE.md
rm CLAUDE.md
# 5. Create the symlink
ln -s AGENTS.md CLAUDE.md
# 6. Update the ## Make targets section in AGENTS.md (see template below)
```

The merge step is the one place a human judgment call is reasonable. The agent should:

1. Read both files in full
2. Identify sections present in CLAUDE.md but not in AGENTS.md (most common: model-specific instructions only ever added to one file)
3. Propose the merged AGENTS.md as a diff for user review (if running interactively)
4. If non-interactive, take AGENTS.md as truth, log the dropped CLAUDE.md content to the chat for the user's reference (but never as a *file* — the only persistent state is the AGENTS.md output)

If the diff is empty (`diff -u` produces no output), skip the question and proceed: just delete CLAUDE.md and create the symlink. No churn.

## State 2 — Only AGENTS.md exists

The cleanest case. The user is already on the `AGENTS.md`-as-truth convention.

```bash
# 1. Update the ## Make targets section in AGENTS.md (see template below)
# 2. Create the symlink
ln -s AGENTS.md CLAUDE.md
```

If `## Make targets` exists and is byte-identical to the template the skill would write, skip the rewrite (idempotency rule). The symlink might already exist (from a prior run) — `ln -s` will refuse with "File exists." The skill checks `is_claude_link` first; if already pointing at `AGENTS.md`, leave it. If pointing at something else, the user fixes manually (the skill won't break a user-curated symlink without consent).

## State 3 — Only CLAUDE.md exists

The legacy case. The project predates `AGENTS.md` as a convention.

```bash
# 1. Promote CLAUDE.md → AGENTS.md
mv CLAUDE.md AGENTS.md
# 2. Update the ## Make targets section
# 3. Create the symlink
ln -s AGENTS.md CLAUDE.md
```

`mv` (not `cp`) so the file's git history follows the rename — `git log --follow AGENTS.md` will show the prior history under CLAUDE.md. (Most agents and most reviewers don't pass `--follow`, but the well-behaved ones get the history.)

If `git mv` is preferred (only when working tree is clean for that file), the skill uses it. Otherwise plain `mv`.

## State 4 — Neither exists

Greenfield. Generate the file from a project-name + Make-targets template.

```bash
# 1. Detect project name (from package.json `name`, Cargo.toml `name`, or directory basename)
PROJECT=$(jq -r '.name // empty' package.json 2>/dev/null \
  || awk -F\" '/^name = / {print $2}' Cargo.toml 2>/dev/null \
  || basename "$PWD")

# 2. Write the template (see Template section)
cat > AGENTS.md <<EOT
# AGENTS.md — $PROJECT

Project agent docs. CLAUDE.md is a symlink → this file.

## Make targets
<rendered Make-targets section>
EOT

# 3. Create the symlink
ln -s AGENTS.md CLAUDE.md
```

The greenfield template is intentionally minimal — just the project banner + the `## Make targets` section. The user's actual agent prose (project context, conventions, "do this not that" rules) is added by the user later. The skill does not invent prose.

## State 5 — Symlink already exists

The skill has been here before, or the user already set up the convention. Verify and update.

```bash
# 1. Verify the link target exists
if [ "$link_target" = "AGENTS.md" ] && [ -f AGENTS.md ]; then
  : # All good — proceed to update
else
  # Pathological — link points elsewhere or to nothing
  printf "CLAUDE.md is a symlink to '%s' (not AGENTS.md). Skill can't safely change this.\n" "$link_target"
  exit 1
fi
# 2. Update the ## Make targets section in AGENTS.md
# (No symlink change needed.)
```

The check `link_target = AGENTS.md` is exact-match against the relative path. If the user has used an absolute path (`CLAUDE.md → /Users/foo/proj/AGENTS.md`), the skill refuses and tells the user to fix manually — relative symlinks travel with the repo, absolute ones don't.

## Edge cases

| Edge case | Detection | Action |
|---|---|---|
| Symlink cycle (`CLAUDE.md → AGENTS.md → CLAUDE.md`) | `is_agents_link=1` AND `readlink AGENTS.md = CLAUDE.md` | Refuse. Print the cycle and ask the user to remove both, then re-run. |
| Dangling symlink (`CLAUDE.md → AGENTS.md` but AGENTS.md doesn't exist) | `is_claude_link=1` AND `link_target=AGENTS.md` AND `! [ -f AGENTS.md ]` | Treat as State 4 — `rm CLAUDE.md` (the dangling link); generate fresh AGENTS.md; recreate the symlink. |
| Both are symlinks pointing to the same target file | `is_agents_link=1` AND `is_claude_link=1` AND `readlink AGENTS.md = readlink CLAUDE.md` | Read the target as truth. Update its `## Make targets` section. Leave both symlinks as-is. |
| `CLAUDE.md` is a symlink to a non-AGENTS.md file (e.g., `CLAUDE.md → docs/agent.md`) | `is_claude_link=1` AND `link_target != AGENTS.md` | Refuse. Tell the user the existing symlink target. Do NOT silently overwrite. |
| `AGENTS.md` is a symlink (`AGENTS.md → docs/agent.md`) | `is_agents_link=1` | Treat the link target as the source of truth. Update its `## Make targets`. The symlink shape is the user's choice; don't fight it. |
| `AGENTS.md` exists but is over 1000 lines | `wc -l < AGENTS.md` > 1000 | Ask before appending: `"AGENTS.md is N lines. The Make-targets section is ~50 lines. Append (Y/n)?"` |
| `## Make targets` section already exists and matches the template byte-for-byte | `diff` of extracted section vs rendered template is empty | Skip the rewrite. Print `"AGENTS.md unchanged"`. Idempotency rule. |
| Working tree dirty for `AGENTS.md` | `git status --porcelain AGENTS.md` non-empty | Warn before editing. The scaffold snapshot covers only manifest paths; dirty AGENTS.md prose is user work and must not be silently overwritten outside `## Make targets`. |

## The `## Make targets` section template

The skill writes (or updates) a single `## Make targets` section in AGENTS.md. The section is bracketed by the heading and the next `## ` heading (or EOF). The skill replaces only the bracketed region; surrounding prose is untouched.

```markdown
## Make targets

Generated by `init-makefiles` for scenario: **<Scenario name>**.
Regenerate via `init-makefiles` — do NOT hand-edit the Makefile.

### Local dev
- `make local` — <description>
- `make local-lan` — <description>
- `make tunnel` — <description, including "private to tailnet">

### Stop / clean
- `make stop` — kill our own dev process on $PORT
- `make clean` — `make stop` + clear build/cache

### Deploy
- `make deploy` — <provider list>
- `make verify` — HTTP-probe the deployed URL

### <Scenario-specific section>
- ...

### Knobs (env vars with defaults)
| Var | Default | Purpose |
|---|---|---|
| `PORT` | 3456 | Local dev port |
| ... | ... | ... |

### What this skill will NOT do
- Generate Funnel mappings as a side effect
- Kill foreign processes on a port
- ...
```

Section content rules:

| Subsection | Always present? | Notes |
|---|---|---|
| Header line | yes | Includes the scenario name, e.g., `Scenario A — Frontend-only` |
| Local dev | when scenario opens a port | Skip for Scenario F (build-artifact, no port) |
| Stop / clean | when port-hygiene applies | Skip for Scenario G (no local port for ship) |
| Deploy | when scenario has a deploy provider | Skip for Scenarios B, F, G |
| Scenario-specific | yes | E.g., `### Mac ship` for Scenario G; `### Supabase` for Scenario D |
| Knobs | yes | Always render the env var table |
| What this skill will NOT do | yes | Always render — the negative space is as important as the affirmative |

The lead paragraph (`Generated by init-makefiles for scenario: ...`) is the marker the skill uses to detect a prior-generated section. If the lead paragraph is present at the top of the section, the section was last written by this skill; replace it. If absent, the user wrote the `## Make targets` section by hand; require explicit replacement consent before replacing.

## Idempotency rule

The skill renders the new section into a string. It then extracts the existing `## Make targets` section from AGENTS.md (heading-to-next-heading). If the two strings are byte-identical:

```bash
# Print and exit
printf "AGENTS.md unchanged\n"
exit 0
```

No file write. No churn in `git status`. The user re-running the skill on a project that's already up-to-date sees nothing change. (`git status` after the skill is the cleanest possible signal that the skill is idempotent.)

The check is byte-identical, not semantic. Whitespace differences DO trigger a rewrite — the skill considers itself the source of truth for whitespace too, since whitespace can affect Markdown rendering in some agents' parsers. Users who hand-tune whitespace lose that on the next regen; this is a deliberate trade-off.

## "AGENTS.md too long" guard

If `wc -l < AGENTS.md` returns >1000 lines, the skill stops and asks:

```
AGENTS.md is N lines. The Make-targets section is ~50 lines. Append (Y/n)?
```

Why a guard at 1000: most repos with agent docs have AGENTS.md under 500 lines. A file over 1000 lines is either (a) auto-generated by some other tool the skill should not interfere with, or (b) a curated mega-doc the user wants intact. Asking is cheap; silent surgery on a giant file is expensive.

If the user says n, the skill skips the AGENTS.md update entirely (Makefile generation succeeded; only the agent-docs sync was deferred). The user can re-run the AGENTS.md step manually later.

## DO-NOT list

- **DO NOT delete AGENTS.md content other than the `## Make targets` section.** The skill replaces only the bracketed region between `## Make targets` and the next `## ` heading. Other sections (`## Conventions`, `## Architecture`, etc.) are user prose and are never touched.
- **DO NOT silently overwrite a separate CLAUDE.md with different content.** State 1 always asks. The default answer (Y) merges; the user can say n to keep AGENTS.md as truth, but the question is mandatory.
- **DO NOT use `cp -L` to dereference a symlink.** The contract is "CLAUDE.md is a symlink"; copying through dereferences the link and produces two diverging files. Use `ln -s` exclusively.
- **DO NOT create symlinks with relative paths beyond `AGENTS.md`.** The link target is always exactly `AGENTS.md` — same directory. No `../AGENTS.md`, no `docs/AGENTS.md`. Same-dir relative is the only portable shape.
- **DO NOT use absolute paths in the symlink target.** Absolute paths break when the repo is cloned to a different host or moved. Relative same-dir only.
- **DO NOT recreate an existing symlink that already points correctly.** Idempotency: check `readlink CLAUDE.md` first; if it equals `AGENTS.md`, do nothing. Recreating churns inode timestamps for no reason.
- **DO NOT auto-merge in State 1 without asking when contents differ.** The merge IS the user's call. The skill proposes; the user disposes.
- **DO NOT touch AGENTS.md if `## Make targets` was last hand-written by the user (no skill-generated lead paragraph).** Require explicit replacement consent before replacing user prose.
- **DO NOT proceed with the Makefile-generation step if AGENTS.md update fails.** AGENTS.md is the user's documentation contract. A wrong AGENTS.md is worse than no AGENTS.md update; halt and surface the error.
- **DO NOT include the `<Scenario name>`, `<description>`, etc., placeholder syntax in the actual rendered output.** The skill substitutes those at render time. A literal `<description>` in AGENTS.md is a bug.

## What this file does NOT cover

| Topic | Reference |
|---|---|
| The actual Makefile content (preamble, targets, helpers) | `makefile-base.md`, `makefile-frontend.md`, etc. |
| Detection of the project scenario | `scenario-detection.md` |
| Verification rungs and the post-deploy banner | `verification-ladder.md` |
| GitHub Actions wiring (separate workflow file) | `ci-cd-workflow.md` |
| Broad AGENTS hierarchy, REVIEW.md, folder-scoped guidance, or repo governance | cross-skill: `init-agent-config` |
