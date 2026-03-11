# Setup and Format Specification

Complete reference for setting up GitHub Copilot code review instruction files, enabling the feature, and understanding the file format specification.

## Table of Contents

1. [Enabling Copilot Code Review](#enabling-copilot-code-review)
2. [File Types and Locations](#file-types-and-locations)
3. [copilot-instructions.md Format](#copilot-instructionsmd-format)
4. [*.instructions.md Format](#instructionsmd-format)
5. [Character and Length Limits](#character-and-length-limits)
6. [Configuration Levels](#configuration-levels)
7. [Automatic vs Manual Reviews](#automatic-vs-manual-reviews)
8. [Base Branch Behavior](#base-branch-behavior)
9. [Review Type and Limitations](#review-type-and-limitations)
10. [Quick Setup Checklist](#quick-setup-checklist)

---

## Enabling Copilot Code Review

### Repository-level setup

1. Navigate to **Settings → Code & automation → Copilot → Code review**
2. Toggle **"Use custom instructions when reviewing pull requests"** (enabled by default)
3. Commit instruction files to the **base branch** (e.g., `main`)

### Organization-level setup

Organization admins can:
- Enable/disable Copilot code review for all repositories
- Enable Copilot code review for organization members without individual licenses
- Set organization-wide policies that apply unless overridden at repo level

### Prerequisites

| Requirement | Details |
|---|---|
| Copilot plan | Copilot Business or Enterprise ($19+/user/month) |
| Repository visibility | Public or private (private requires Business/Enterprise seat) |
| Feature status | Public preview (no SLA) |
| Rate limits | 10 PRs/hour/repo (default) |

---

## File Types and Locations

Copilot code review reads two types of instruction files:

| File | Location | Scope | Requires Frontmatter |
|---|---|---|---|
| `copilot-instructions.md` | `.github/copilot-instructions.md` | All files in repository | No |
| `*.instructions.md` | `.github/instructions/*.instructions.md` | Files matching `applyTo` pattern | Yes — `applyTo` required |

**Directory structure:**
```
.github/
├── copilot-instructions.md              # Repository-wide (applied to all files)
└── instructions/
    ├── typescript.instructions.md        # Scoped to TS files
    ├── python.instructions.md            # Scoped to Python files
    ├── react.instructions.md             # Scoped to React components
    ├── api.instructions.md               # Scoped to API routes
    ├── security.instructions.md          # Scoped to auth/payment paths
    └── testing.instructions.md           # Scoped to test files
```

**Critical:** `*.instructions.md` files MUST be in `.github/instructions/` directory (or subdirectories). Files in other locations are ignored by Copilot code review.

---

## copilot-instructions.md Format

Plain markdown. No frontmatter required. Applied to every file in the repository.

```markdown
# General Code Review Standards

## Security

- Check for hardcoded secrets, API keys, or credentials
- Verify input validation on all external boundaries
- Look for SQL injection via raw queries

## Code Quality

- Functions should be focused and under 50 lines
- Use descriptive naming conventions
- Ensure proper error handling — no empty catch blocks

## Performance

- Flag N+1 database queries (queries inside loops)
- Check for missing pagination on list endpoints
```

**Best practice:** Only include rules that genuinely apply to ALL code in the repository. Language-specific, framework-specific, and path-specific rules belong in scoped `*.instructions.md` files.

---

## *.instructions.md Format

Requires YAML frontmatter with `applyTo` property. Applied only to files matching the glob pattern.

### Frontmatter properties

| Property | Required | Type | Description |
|---|---|---|---|
| `applyTo` | Yes | String (glob) | Determines which files receive these instructions |
| `excludeAgent` | No | `"code-review"` or `"coding-agent"` | Prevents a specific Copilot agent from reading this file |

### Basic example

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# TypeScript Standards

## Type Safety

- Avoid `any` type — use `unknown` or specific types
- Define interfaces for all object shapes

```typescript
// Avoid
function process(data: any) { return data.value; }

// Prefer
interface DataShape { value: string; }
function process(data: DataShape): string { return data.value; }
```
````

### With excludeAgent

```yaml
---
applyTo: "**/*.ts"
excludeAgent: "coding-agent"
---
```

This file applies to TypeScript files during **code review only** — the Copilot coding agent will not read it. Use this when review-specific rules would confuse the coding agent, or vice versa.

### File naming convention

Use `kebab-case.instructions.md`:
- `typescript.instructions.md` (language)
- `react-components.instructions.md` (framework)
- `api-routes.instructions.md` (domain)
- `packages-api.instructions.md` (monorepo package)

---

## Character and Length Limits

**Copilot code review reads only the first 4,000 characters of any instruction file.** Content beyond this limit is silently ignored — there is no warning.

| Aspect | Limit | Notes |
|---|---|---|
| Hard character limit | 4,000 characters | Only first 4,000 chars influence review |
| Recommended maximum | 2,500–3,500 characters | Leave safety margin |
| Recommended max lines | ~1,000 lines | Files over this may cause inconsistent behavior |
| Applies to | `copilot-instructions.md` AND each `*.instructions.md` | Per-file, not cumulative |
| Does NOT apply to | Copilot Chat, Copilot coding agent | Different context windows |

### Practical implications

- Put highest-priority rules at the top of each file
- Frontmatter (`---\napplyTo: "..."\n---\n`) counts toward the 4,000-character limit
- Code examples consume characters quickly — keep them concise
- Prefer bullet points over prose paragraphs (more rules per character)
- If a concern needs more space, split into two files with narrower `applyTo` scopes

### Measuring characters

```bash
# Single file
wc -c .github/copilot-instructions.md

# All instruction files
for f in .github/instructions/*.instructions.md; do
  echo "$f: $(wc -c < "$f") chars"
done
```

---

## Configuration Levels

Instructions cascade with a defined priority order:

| Level | Source | Priority | Typical use |
|---|---|---|---|
| Personal | User-level Copilot settings | Highest | Individual developer preferences |
| Repository | `.github/copilot-instructions.md` + `.github/instructions/*.instructions.md` | Middle | Project-specific standards |
| Organization | `copilot-instructions.md` in org template repository | Lowest | Company-wide coding standards |

When a file in a PR is reviewed, Copilot loads:
1. Organization-level instructions (if any)
2. `.github/copilot-instructions.md` (always loaded for every file)
3. All `*.instructions.md` files whose `applyTo` pattern matches the file being reviewed
4. Personal instructions (highest priority)

All matching instructions are combined. If rules conflict, higher-priority levels take precedence.

---

## Automatic vs Manual Reviews

| Mode | How to trigger | When to use |
|---|---|---|
| Manual | Open PR → Reviewers menu → Select **Copilot** | Selective review on specific PRs |
| Automatic | Repository → Copilot settings → Enable **Automatic code review** | Review every PR automatically |
| Slash command | Comment `/copilot review` on a PR | Ad-hoc review with optional context |
| Re-review | Click **"Request re-review"** next to Copilot in Reviewers | After pushing new commits (not automatic) |

**Important:** Copilot does NOT automatically re-review after new commits are pushed. You must explicitly request a re-review.

---

## Base Branch Behavior

Copilot reads instruction files from the **base branch** of the pull request — not the feature branch.

| PR target | Instructions read from |
|---|---|
| `feature-branch` → `main` | `main` branch |
| `feature-branch` → `develop` | `develop` branch |

**Implication:** If you add or modify instruction files on a feature branch, those changes will NOT affect Copilot's review of that same PR. You must merge instruction file changes to the base branch first.

**Workflow for updating instructions:**
1. Create a PR that only modifies instruction files
2. Merge to `main` (or your base branch)
3. Subsequent PRs targeting `main` will use the updated instructions

---

## Review Type and Limitations

### What Copilot reviews produce

- Copilot posts **"Comment"** reviews — never "Approve" or "Request changes"
- Review comments do NOT count toward required approvals
- Review comments do NOT block merging
- Copilot can suggest code changes inline (click "Implement suggestion" to have the coding agent apply them)

### What Copilot code review CAN do

| Capability | Example |
|---|---|
| Check for specific code patterns | "All API endpoints must validate with Zod" |
| Enforce naming conventions | "Use PascalCase for React components" |
| Flag security concerns | "Check for SQL injection in raw queries" |
| Catch architectural violations | "No direct database access from controller layer" |
| Provide inline code suggestions | Before/after fix suggestions |

### What Copilot code review CANNOT do

| Unsupported | Why |
|---|---|
| Approve or block PRs | Only posts comment reviews |
| Change comment formatting | Cannot modify review UI (bold, emoji, severity) |
| Modify PR overview comment | No access to PR description editing |
| Follow external links | Content at URLs is never loaded |
| Run code, linters, or tests | Static analysis only |
| Deterministic line counting | Phrase as guidelines, not hard rules |

### Language support

Best results: JavaScript, TypeScript, Python, Go, Java, C#, Ruby
Limited results: Rust, PHP, Swift, Kotlin
Weak results: Assembly, Fortran, niche languages

---

## Quick Setup Checklist

```
□ Copilot Business or Enterprise plan active
□ Code review enabled in repository Copilot settings
□ .github/ directory exists in repository
□ copilot-instructions.md created in .github/
□ .github/instructions/ directory created
□ Scoped *.instructions.md files created with valid frontmatter
□ All instruction files under 4,000 characters
□ Instruction files committed to base branch (e.g., main)
□ Test PR opened and Copilot review requested
□ Review comments verified against instruction rules
```
