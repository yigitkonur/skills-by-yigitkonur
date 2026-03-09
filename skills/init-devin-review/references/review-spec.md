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

The Bug Catcher treats content near the top of the file with higher priority. Recommended order:

1. Critical Areas / Security (highest priority — flags these as severe bugs)
2. Conventions (core rules — flags violations as non-severe bugs)
3. Performance (medium priority — typically flagged as investigate)
4. Patterns with code examples (used for pattern matching)
5. Ignore (noise reduction)
6. Testing (lower priority — informational flags)

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

Subdirectory REVIEW.md files **complement** the root file — they don't replace it. Devin reads all applicable REVIEW.md files for a given changed file.

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
