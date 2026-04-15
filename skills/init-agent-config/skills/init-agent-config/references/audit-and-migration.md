# Audit and Migration Guide

How to audit existing repo instruction files and migrate them into an AGENTS-first hierarchy without losing signal.

## Workflow

### Phase 1: Discovery

Find the current instruction surfaces before changing anything.

```bash
find . \( -name "AGENTS.md" -o -name "CLAUDE.md" -o -name "GEMINI.md" -o -name ".cursorrules" -o -path "./.github/copilot-instructions.md" \) 2>/dev/null | sort
tree -dL 2 .
```

**What to capture:**
- root instruction files
- nested instruction files
- agent-native directories such as `.claude/`, `.cursor/`, `.github/instructions/`
- candidate `src/*` folders that should receive local `AGENTS.md` coverage

### Phase 2: Quality Assessment

Score each existing instruction file before editing it.

| Criterion | Weight | What to check |
|-----------|--------|---------------|
| Commands and workflows | 20 | Are commands verified and current? |
| Architecture clarity | 20 | Can an agent understand repo and folder boundaries? |
| Folder coverage | 15 | Do the right folders have local guidance? |
| Non-obvious patterns | 15 | Are gotchas and WHY context documented? |
| Conciseness | 15 | Is each line high-signal? |
| Actionability | 15 | Are instructions concrete and executable? |

### Grade Thresholds

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90-100 | Ready to keep or tighten only |
| B | 75-89 | Good, but missing some structure or signal |
| C | 60-74 | Functional, but too noisy or incomplete |
| D | 45-59 | Major gaps or stale guidance |
| F | <45 | Actively harmful or misleading |

### Phase 3: Report Before Updates

Always output the quality report before editing existing files.

Use this format:

```markdown
## Agent Instructions Quality Report

### Summary
- Files found: X
- Average score: X/100
- Files needing update: X

### File-by-File Assessment

#### 1. ./AGENTS.md
**Score: XX/100 (Grade: X)**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Commands and workflows | X/20 | ... |
| Architecture clarity | X/20 | ... |
| Folder coverage | X/15 | ... |
| Non-obvious patterns | X/15 | ... |
| Conciseness | X/15 | ... |
| Actionability | X/15 | ... |

**Issues:**
- ...

**Recommended changes:**
- ...
```

### Phase 4: Targeted Updates

After the report:

1. keep what is already correct
2. move universal guidance into `AGENTS.md`
3. add missing folder-level files where the tree proves they are needed
4. create or repair companion entrypoints only after the AGENTS hierarchy is stable
5. remove duplication between AGENTS and agent-native files

### Phase 5: Apply and Verify

After edits:
- re-check commands and paths
- verify folder coverage matches the tree
- confirm companion files point back to AGENTS
- summarize any remaining unknowns outside the files

## Audit Checklist

### Structural Audit

- [ ] Root `AGENTS.md` exists or is intentionally absent
- [ ] Meaningful `src/*` or app/package folders have local coverage
- [ ] Companion `CLAUDE.md` files exist where AGENTS files exist
- [ ] Files are short enough to be scanned quickly
- [ ] Child files do not repeat parent content

### Command Verification

For every documented command, check the real source:

```bash
# package.json scripts
cat package.json | jq '.scripts'

# Makefile targets
grep -E '^[A-Za-z0-9_.-]+:' Makefile

# pyproject scripts
grep -A 20 '\[project.scripts\]' pyproject.toml

# CI commands
grep -R "run:" .github/workflows
```

- [ ] Every documented command exists
- [ ] Uncertain commands are marked `[unverified]` or replaced with `See <file>`
- [ ] Folder-local files only list folder-local commands

### Signal Audit

For each line, ask:

| Question | Action |
|----------|--------|
| Can an agent infer this from code? | Remove it |
| Is it enforced by tooling? | Remove it |
| Is it generic advice? | Remove or rewrite |
| Is it really parent-level guidance? | Move it up |
| Is it only relevant inside one subtree? | Move it down |

### Migration Audit

- [ ] Shared rules are in `AGENTS.md`
- [ ] Agent-native files do not carry shared policy
- [ ] `CLAUDE.md` companions are symlinks or explicit wrapper exceptions
- [ ] No stale references to deleted or moved files remain

## Migration Guides

### From standalone `CLAUDE.md` to AGENTS-first

**When to migrate:** the repo now needs portability, folder scoping, or a second coding agent.

1. read the current `CLAUDE.md`
2. extract all shared rules into root `AGENTS.md`
3. use `tree -d .` or `tree -dL 2 .` to identify local folders that need their own `AGENTS.md`
4. create nested files for those folders
5. replace each `CLAUDE.md` with a sibling symlink to the matching `AGENTS.md`
6. move Claude-only behavior into `.claude/`

### From `.cursorrules` to AGENTS-first

1. copy universal instructions into `AGENTS.md`
2. create local AGENTS files for meaningful folders
3. move Cursor-only globs or behaviors into `.cursor/rules/*.mdc`
4. add companion `CLAUDE.md` files only if Claude support is needed

### From no agent config

1. run Wave 1 discovery
2. run Wave 2 on root candidates and meaningful `src/*` folders
3. write the AGENTS hierarchy
4. create companion entrypoints afterward

## Update Diff Format

When proposing changes before applying them, show:

````markdown
### Update: ./src/api/AGENTS.md

**Why:** The API folder has unique request-contract and test rules not captured at the repo root.

```diff
+## Local Boundaries
+- Always: update request schemas and contract tests together
+- Never: bypass the shared error formatter in `src/api/errors`
```
````

## Common Migration Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Updating `CLAUDE.md` but not `AGENTS.md` | Shared policy splits across files | Move the shared rule back into AGENTS |
| Skipping nested folder files | Local risks stay undocumented | Use Wave 2 and create the folder files |
| Creating wrapper files before AGENTS | Native file becomes source of truth | Build the AGENTS hierarchy first |
| Guessing local commands | Folder file becomes misleading | Verify or mark `[unverified]` |
| Leaving stale CLAUDE-first language | The repo still teaches the old model | Rewrite around AGENTS-first terminology |

## Verification Checklist

After migration or audit updates:

1. run every documented command you changed, if feasible
2. confirm every documented path exists
3. confirm each `CLAUDE.md` points to the right sibling `AGENTS.md` or is an explicit fallback wrapper
4. check that child files contain only folder-local content
5. ask at least one agent to summarize the root instructions and one nested folder's instructions

## Final Rule

If the audit says a file is mostly correct, tighten it. Do not rewrite it just to make it look cleaner. The goal is not prettier files. The goal is fewer agent mistakes.
