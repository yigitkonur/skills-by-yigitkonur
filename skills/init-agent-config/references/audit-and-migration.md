# Audit and Migration Guide

How to audit existing agent configuration files for quality, and how to migrate between formats.

## Quality Scoring Rubric

Rate any agent config file (CLAUDE.md, AGENTS.md, .cursorrules) on these dimensions:

| Dimension | Weight | What to Check |
|-----------|--------|---------------|
| **Commands accuracy** | 25% | All documented commands verified against package.json / Makefile / CI. No invented commands. |
| **Architecture documentation** | 25% | Non-obvious boundaries, data flow, service ownership documented. Not duplicating README. |
| **Non-obvious patterns** | 20% | Documents what agents cannot infer: why decisions were made, hidden gotchas, non-standard paths. |
| **Conciseness** | 15% | No bloat, no filler, no linter-enforced rules. Every line passes the litmus test. |
| **Actionability** | 15% | Instructions are directives, not suggestions. Agent can execute without ambiguity. |

### Grade Thresholds

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90–100 | Production-ready, minimal iteration needed |
| B | 75–89 | Good, 1–2 areas to tighten |
| C | 60–74 | Functional but noisy or missing key sections |
| D | 45–59 | Significant gaps or stale content |
| F | < 45 | Actively harmful — incorrect commands, misleading architecture |

### Scoring Each Dimension (0–5)

**Commands accuracy (25%):**
- 5: All commands verified, tested, and current
- 4: Commands verified but 1–2 minor gaps
- 3: Most commands correct but some unverified
- 2: Several commands incorrect or missing
- 1: Commands mostly invented or stale
- 0: No commands section

**Architecture documentation (25%):**
- 5: Non-obvious decisions documented with WHY context
- 4: Key decisions documented but missing some reasoning
- 3: Architecture described but mostly restating the obvious
- 2: Minimal architecture context
- 1: Copy of README or generic description
- 0: No architecture section

**Non-obvious patterns (20%):**
- 5: Gotchas, edge cases, and conventions that prevent real mistakes
- 4: Most non-obvious patterns covered
- 3: Some useful patterns but misses key ones
- 2: Few patterns, mostly obvious
- 1: Generic advice not specific to project
- 0: No patterns documented

**Conciseness (15%):**
- 5: Every line passes the "would removing this cause a mistake?" test
- 4: 1–2 lines of bloat
- 3: ~20% noise (linter rules, obvious facts)
- 2: ~40% noise
- 1: ~60% noise, config is more noise than signal
- 0: Wall of text, mostly useless

**Actionability (15%):**
- 5: All instructions are specific, measurable directives
- 4: Most instructions are directives, 1–2 suggestions
- 3: Mix of directives and vague suggestions
- 2: Mostly suggestions and aspirational statements
- 1: Generic advice ("write clean code")
- 0: No actionable instructions

## Audit Checklist

### Phase 1: Structural Audit

- [ ] File exists at correct location (project root or `.claude/CLAUDE.md`)
- [ ] File is under target line count (see sizing table)
- [ ] Clear markdown structure with headers and bullet lists
- [ ] No paragraphs of prose — only structured instructions
- [ ] Commands section present and appears first or second

### Phase 2: Command Verification

For every command documented in the config file:

```bash
# Check against package.json scripts
cat package.json | jq '.scripts'

# Check against Makefile targets
grep -E '^[a-zA-Z_-]+:' Makefile

# Check against pyproject.toml scripts
grep -A 20 '\[project.scripts\]' pyproject.toml

# Check against CI config
cat .github/workflows/*.yml | grep -E 'run:'

# Check against Cargo.toml aliases
grep -A 10 '\[alias\]' .cargo/config.toml
```

- [ ] Every documented command exists in actual config
- [ ] No commands are invented or assumed
- [ ] Uncertain commands say `"See [file]"` instead of guessing

### Phase 3: Signal Quality Audit

For each line, apply these checks:

| Check | Action if True |
|-------|---------------|
| Agent can infer this from reading code | Remove |
| Linter/formatter enforces this | Remove |
| This is a standard convention for the framework | Remove |
| This duplicates README content | Remove or reference README |
| This is a suggestion, not a directive | Rewrite as directive or remove |
| This is generic advice applicable to any project | Remove |

### Phase 4: Content Completeness

- [ ] Non-obvious tech stack choices documented
- [ ] Architecture boundaries and data flow documented
- [ ] Boundaries section with Always/Ask/Never rules
- [ ] WHY context for non-obvious decisions
- [ ] Troubleshooting for common gotchas

### Phase 5: Format-Specific Checks

**AGENTS.md-specific:**
- [ ] Plain markdown only — no `@import`, no YAML frontmatter
- [ ] Under 32 KiB combined across all nested files
- [ ] Boundaries section uses Always/Ask/Never format
- [ ] Nested files do not repeat root-level instructions

**CLAUDE.md-specific:**
- [ ] Any `@import` paths resolve to real files
- [ ] Progressive disclosure files referenced from root
- [ ] `.claude/rules/` files have valid `paths:` frontmatter
- [ ] Thin wrapper pattern: no duplicated content from AGENTS.md

### Phase 6: Cross-Check

- [ ] No secrets or credentials in config files
- [ ] No stale paths, dead links, or outdated versions
- [ ] Conventions match actual code patterns (grep for counter-examples)
- [ ] No linter-enforced rules repeated

## Audit Output Template

```markdown
## Agent Config Audit: [Project Name]

**File:** CLAUDE.md / AGENTS.md
**Lines:** NN
**Date:** YYYY-MM-DD

### Scores

| Dimension | Score (0–5) | Notes |
|-----------|-------------|-------|
| Commands accuracy | X/5 | [specific notes] |
| Architecture docs | X/5 | [specific notes] |
| Non-obvious patterns | X/5 | [specific notes] |
| Conciseness | X/5 | [specific notes] |
| Actionability | X/5 | [specific notes] |
| **Weighted Total** | **XX/100** | **Grade: X** |

### Issues Found

1. [Issue description + fix]
2. [Issue description + fix]

### Recommended Changes

1. [Change + rationale]
2. [Change + rationale]
```

## Migration Guides

### From `.cursorrules` to AGENTS.md

**When to migrate:** Team uses multiple AI agents or wants cross-agent compatibility.

**Steps:**

1. **Read existing `.cursorrules`**
   ```bash
   cat .cursorrules
   ```

2. **Extract universal content**
   - Copy all project description, commands, conventions, and boundaries
   - These are agent-agnostic and belong in AGENTS.md

3. **Identify Cursor-specific content**
   - Look for Cursor-specific syntax, references to Cursor features
   - These stay in `.cursor/rules/*.mdc` files

4. **Create AGENTS.md**
   - Write extracted universal content in AGENTS.md format
   - Add Boundaries section with Always/Ask/Never pattern

5. **Create Cursor-specific rules**
   ```
   .cursor/
   └── rules/
       └── general.mdc    # Cursor-only settings with globs
   ```

6. **Clean up**
   - Remove `.cursorrules` or reduce to a minimal pointer
   - `.cursorrules` is deprecated but still read for backwards compatibility

7. **Verify** — test with both Cursor and at least one other agent

### From Standalone `CLAUDE.md` to Dual-File Pattern

**When to migrate:** Team adds a second AI agent (Cursor, Codex, Gemini, etc.).

**Steps:**

1. **Read existing `CLAUDE.md`**
   ```bash
   cat CLAUDE.md
   ```

2. **Separate content by type**

   | Content Type | Destination |
   |-------------|-------------|
   | Project description, commands, conventions | `AGENTS.md` |
   | `@import` lines | Remove from AGENTS.md, keep in CLAUDE.md |
   | `.claude/rules/` references | Keep in CLAUDE.md only |
   | Hooks, commands, agents references | Keep in CLAUDE.md only |
   | Claude-specific preferences | Keep in CLAUDE.md only |

3. **Create AGENTS.md** with universal content (inline everything — no imports)

4. **Replace CLAUDE.md** with thin wrapper:
   ```markdown
   @AGENTS.md

   ## Claude-Specific
   - [Claude-only features]
   - See `.claude/rules/` for path-scoped rules
   ```

5. **Verify** — no content duplication between files

### From `copilot-instructions.md` to AGENTS.md

**Steps:**

1. Copy content from `.github/copilot-instructions.md` to `AGENTS.md`
2. Remove any Copilot-specific references
3. Replace `.github/copilot-instructions.md` with pointer: `"See AGENTS.md"`
4. Move Copilot-specific instructions to `.github/instructions/*.instructions.md`

### From No Agent Config (New Setup)

**Steps:**

1. **Explore the repository** (Phase 1 of the skill workflow)
2. **Pick a template** from `references/project-templates.md`
3. **Fill in project-specific details**
4. **Verify every command** against actual config files
5. **Trim ruthlessly** — remove anything the agent can infer
6. **Test with your agent** — ask it to summarize its instructions

## Common Migration Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Copy-pasting entire `.cursorrules` into AGENTS.md | Includes Cursor-specific syntax | Extract only universal content |
| Keeping `@import` in AGENTS.md | Not supported — AGENTS.md is plain markdown | Inline all referenced content |
| Duplicating content in both files | Wastes context budget | Thin wrapper pattern — import, don't copy |
| Not verifying commands post-migration | Commands may not match new format | Run every command and confirm success |
| Adding YAML frontmatter to AGENTS.md | Not supported by the format | Remove frontmatter, use plain markdown |
| Losing boundary rules during migration | Critical warnings dropped | Scan for Never/Always/WARNING markers |

## Verification Checklist (Post-Migration)

After any migration:

1. **Run every documented command** and confirm it succeeds
2. **Confirm documented paths exist** (`ls src/api/` etc.)
3. **Confirm conventions match actual code** (grep for counter-examples)
4. **Confirm no linter-enforced rules** are repeated
5. **Test with each agent** the team uses:
   ```bash
   [agent] "What project conventions should you follow?"
   ```
6. **Check file sizes** against targets
7. **Confirm no content duplication** between AGENTS.md and agent-specific files

## Common Audit Pitfalls

| Pitfall | What happens | Prevention |
|---------|-------------|------------|
| Rewriting a mostly-good config from scratch | Loses existing signal, introduces new errors | Switch to audit/tighten mode -- edit, don't replace |
| Auditing a greenfield project | Wastes time looking for nonexistent config | Skip audit step (Step 6) for new setups |
| Fixing style without fixing substance | Config looks better but still has wrong commands | Always verify commands first -- style is secondary |
| Scoring without evidence | "Looks good" is not a score | Use the rubric dimensions with specific examples |
| Missing AGENTS.md vs CLAUDE.md separation | Universal content stuck in CLAUDE.md | Check every line: is this Claude-specific or universal? |
| Preserving stale boundary rules | `Never` rules that no longer apply to the codebase | Verify each boundary rule against current code |

## Example Audit Score Calculation

Given a project with this existing AGENTS.md:

```
Commands accuracy:    4/5 (one command uses wrong flag)
Architecture docs:    3/5 (key boundaries documented but missing WHY)
Non-obvious patterns: 2/5 (mostly restates what is obvious from code)
Conciseness:          4/5 (short, but includes a few linter-duplicated rules)
Actionability:        3/5 (some suggestions instead of directives)
```

**Score calculation:**
- Commands: 4/5 x 25% x 100 = 20.0
- Architecture: 3/5 x 25% x 100 = 15.0
- Patterns: 2/5 x 20% x 100 = 8.0
- Conciseness: 4/5 x 15% x 100 = 12.0
- Actionability: 3/5 x 15% x 100 = 9.0
- **Total: 64.0 / 100 = Grade C**

**Findings summary:**
- Fix the wrong command flag (Commands -> 5)
- Add WHY context for architecture decisions (Architecture -> 4)
- Remove obvious patterns, add non-obvious ones (Patterns -> 3)
- Remove linter-duplicated rules (Conciseness -> 5)
- Convert suggestions to directives (Actionability -> 4)
- **Projected score after fixes: 84 = Grade B**
