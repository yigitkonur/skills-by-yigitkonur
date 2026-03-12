# Devin Review Specification

Complete reference for Devin Review instruction files and configuration.

---

## Instruction Files Devin Reads

Devin Review automatically ingests these files as context when analyzing PRs:

| File | Pattern | Purpose |
|---|---|---|
| `REVIEW.md` | `**/REVIEW.md` | Dedicated review guidelines (primary) |
| `AGENTS.md` | Root | Agent behavior instructions |
| `CLAUDE.md` | Root | Claude-specific coding standards |
| `CONTRIBUTING.md` | Root | Contribution workflow and standards |
| `.cursorrules` | Root | Cursor IDE rules (also read by Devin) |
| `.windsurfrules` | Root | Windsurf IDE rules |
| `.cursor/rules` | Directory | Cursor directory rules |
| `*.rules` | Any | Custom rule files |
| `*.mdc` | Any | Markdown configuration files |

Custom file patterns can be added in Settings > Review > Review Rules.

---

## REVIEW.md Format

`REVIEW.md` is pure markdown. No YAML frontmatter required. Devin parses:

- **H2/H3 headers** (`##`, `###`) for section boundaries
- **Bullet lists** for individual rules
- **Fenced code blocks** for code examples (language-tagged)
- **Bold text** for emphasis within rules

### Effective Structure

```markdown
# Review Guidelines

## Critical Areas
- [Path-specific areas needing extra scrutiny with reasoning]

## Conventions
- [Specific, measurable coding standards]

## Security
- [Security rules that should be flagged as bugs]

## Performance
- [Performance patterns to watch for]

## Patterns
### [Pattern Name]
**Good:**
\`\`\`language
// correct pattern
\`\`\`
**Bad:**
\`\`\`language
// anti-pattern
\`\`\`

## Ignore
- [Files/patterns to skip during review]

## Testing
- [Test requirements and conventions]
```

### Section Weighting

The Bug Catcher assigns different weight to each section. Place highest-weight sections first.

| Section | Weight | Merge Behavior | Classification |
|---|---|---|---|
| **Critical Areas** | Highest | Blocks merge if violated | Severe bug |
| **Security** | High | Blocks merge if violated | Severe bug |
| **Code Quality** | Medium | Reported, does not block | Non-severe bug |
| **Testing** | Medium | Reported, does not block | Non-severe bug |
| **Conventions** | Low | Reported as advisory | Informational flag |
| **Performance** | Low | Flag only with evidence | Investigate flag |

Explicit phrasing amplifies weight: "MUST" / "NEVER" → treated as higher severity than "prefer" / "consider".

### Directory-Scoped REVIEW.md

Place `REVIEW.md` in subdirectories to scope guidelines:

```
repo/
├── REVIEW.md                    # Root: applies to all PRs
├── packages/
│   ├── api/
│   │   └── REVIEW.md            # API-specific: auth, validation, error handling
│   ├── payments/
│   │   └── REVIEW.md            # Payments: PCI compliance, idempotency, audit logging
│   └── frontend/
│       └── REVIEW.md            # Frontend: accessibility, performance, component patterns
```

Subdirectory REVIEW.md files are **self-contained** — they replace the root file for their subtree. Devin uses the most specific REVIEW.md that matches a changed file's path.

### Precedence & Merge Behavior

When multiple instruction files exist, Devin resolves them by priority:

| Priority | Source | Scope |
|---|---|---|
| 1 (highest) | Scoped `REVIEW.md` | Subtree where it lives |
| 2 | Root `REVIEW.md` | Entire repo (unless scoped overrides) |
| 3 | `AGENTS.md` | Separate channel — additive, never conflicts |
| 4 (lowest) | Linter/IDE rules (`.cursorrules`, etc.) | Background signal only |

**Merge rules:**
- **Scoped is self-contained** — a subdirectory `REVIEW.md` fully replaces root for files in that subtree. No inheritance, no merging.
- **Root applies everywhere else** — any file not under a scoped `REVIEW.md` uses root rules.
- **AGENTS.md is separate** — it feeds behavioral context, not review rules. Never conflicts with `REVIEW.md`.
- **Conflict resolution** — if two scoped files could apply (nested dirs), the deepest (most specific) wins.

---

## AGENTS.md Format

`AGENTS.md` defines how Devin should behave when executing tasks (not just reviewing). Use for:

- Coding standards and architecture decisions
- Preferred libraries and patterns
- Workflow instructions (e.g., "always run tests before committing")
- File organization conventions

```markdown
# Agent Guidelines

## Architecture
- Use the repository/service/controller pattern for all API code.
- Business logic belongs in `src/services/`, not in route handlers.

## Coding Standards
- Use TypeScript strict mode. No `any` types.
- Prefer composition over inheritance.
- All async functions must use try-catch with structured error logging.

## Workflow
- Run `pnpm test` before committing any changes.
- New API endpoints require both unit tests and integration tests.
- Database schema changes must include a migration file.

## Dependencies
- Use `date-fns` for date manipulation, not `moment`.
- Use `zod` for runtime validation, not `joi`.
- Import shared utilities from `@acme/shared` — don't reimplement.
```

---

## Bug Catcher Classification

The Bug Catcher organizes findings into:

### Bugs (Actionable — should be fixed)

| Severity | Description | Example |
|---|---|---|
| **Severe** | High-confidence issues requiring immediate attention | SQL injection, auth bypass, data loss |
| **Non-severe** | Lower severity issues that should be reviewed | Missing error handling, unvalidated input, type safety |

### Flags (Informational — may or may not need action)

| Class | Description | Example |
|---|---|---|
| **Investigate** | Warrants further investigation | Unusual pattern, possible race condition |
| **Informational** | Explains behavior, no action needed | How a refactored function works, code flow explanation |

### How REVIEW.md Affects Classification

- Rules in **Critical Areas** and **Security** sections → more likely flagged as **severe bugs**
- Rules in **Conventions** → typically flagged as **non-severe bugs**
- Rules in **Performance** → typically flagged as **investigate flags**
- Rules in **Testing** → typically flagged as **informational flags**

Explicit phrasing matters: "This MUST be fixed" vs "Consider doing this" affects severity classification.

### How Rules Map to Findings

Rules flow through a pipeline before becoming review comments:

```
Rule text → Pattern match against diff → Severity assignment → Finding generated
```

**Good rules** (high signal):
- Specific: targets a concrete pattern ("Use `zod.parse()` not manual validation")
- Observable: can be verified from the diff alone
- Actionable: reviewer knows exactly what to change

**Bad rules** (noise):
- Vague: "Write clean code" — no observable pattern
- Unverifiable: "Ensure good performance" — requires runtime data
- Non-actionable: "Be careful with security" — no specific check

---

## Auto-Review Configuration

Auto-review triggers when:

- A PR is opened (non-draft)
- New commits are pushed to a PR
- A draft PR is marked as ready for review
- An enrolled user is added as a reviewer or assignee

Configuration is at Settings > Review:

- **Self-enrollment** — Any user can add themselves
- **Repository enrollment** — Admins can add repos for all-PR auto-review
- **User enrollment** — Admins can add specific GitHub usernames

Auto-Fix can be enabled to automatically suggest code fixes for detected bugs.

---

## Auto-Fix

When enabled, Devin proposes code changes alongside bug findings.

Enable via:
1. PR review settings popover (per-PR)
2. Embedded review settings
3. Settings > Customization > Pull request settings > Autofix settings

Only org admins can change this setting.

---

## CLI Usage

For local review (useful for private repos):

```bash
cd path/to/repo
npx devin-review https://github.com/owner/repo/pull/123
```

The CLI:
1. Uses local git access to fetch the PR branch
2. Creates an isolated git worktree (doesn't touch working directory)
3. Sends diff to Devin servers for analysis
4. Bug Catcher can execute read-only local commands for deeper analysis

---

## Permissions

| Action | Who |
|---|---|
| Write REVIEW.md | Anyone with repo write access |
| Self-enroll for auto-review | Any user with connected GitHub |
| Add repos for auto-review | Org admins |
| Enable auto-fix | Org admins |
| Custom review rule file patterns | Settings > Review |

---

## Error Handling

| Condition | Behavior |
|---|---|
| `REVIEW.md` not found | No custom rules applied; built-in checks only |
| Syntax errors in markdown | Best-effort parsing; malformed sections skipped |
| File exceeds 300 lines | Still parsed, but may reduce analysis quality |
| Scoped conflicts with root | Scoped wins for its subtree; root ignored there |
| References non-existent pattern | Rule applied as-is; no validation of referenced code |
| Empty section (header, no bullets) | Section skipped silently |

---

## Review Quotas & Limits

To keep reviews focused and avoid context overload:

| Limit | Value |
|---|---|
| Max rules per section | 10 |
| Max total rules | 50 |
| Max examples per section | 2–3 |
| Max ignore patterns | 20 |
| Max `REVIEW.md` length | 300 lines |

Exceeding these limits doesn't cause errors — content is still parsed — but signal quality degrades as volume increases. Prioritize high-weight sections first.
