# Greptile Configuration Specification

Complete parameter reference for all Greptile configuration files.

## Configuration Hierarchy

Priority order (highest wins):

1. **Org-enforced rules** (dashboard, admin-only) — cannot be overridden
2. **`.greptile/` folder** (per-directory, cascading) — recommended
3. **`greptile.json`** (repo root, single-file) — simpler repos
4. **Dashboard settings** (org-wide defaults) — fallback

If `.greptile/` AND `greptile.json` exist in the same directory, `.greptile/` wins and `greptile.json` is **silently ignored**.

---

## `.greptile/config.json` — Primary Configuration

Every parameter is optional. Only include what you need.

### Review Behavior

| Parameter | Type | Default | Description |
|---|---|---|---|
| `strictness` | integer (1-3) | 2 | 1=verbose, 2=balanced, 3=critical-only |
| `commentTypes` | string[] | all four | Subset of: `"logic"`, `"syntax"`, `"style"`, `"info"` |
| `triggerOnUpdates` | boolean | false | true = review every push, not just PR open |
| `skipReview` | string | omit | Set to `"AUTOMATIC"` to disable auto-review; manual via `@greptileai` |
| `model` | string | — | Optional model override (e.g., `"gpt-4"`) |

### PR Filters

| Parameter | Type | Description |
|---|---|---|
| `labels` | string[] | Only review PRs with these labels |
| `disabledLabels` | string[] | Skip PRs with these labels |
| `includeAuthors` | string[] | Empty = all (except excluded). Populate to review only specific people |
| `excludeAuthors` | string[] | Never review these authors |
| `includeBranches` | string[] | Only review PRs targeting these branches |
| `excludeBranches` | string[] | Never review PRs targeting these branches |
| `includeKeywords` | string | Newline-separated keywords in PR title/description |
| `ignoreKeywords` | string | Newline-separated keywords to skip |
| `fileChangeLimit` | integer (>=1) | Skip PRs with more changed files. **0 = skip ALL PRs** |

### File Patterns

| Parameter | Type | Format | Description |
|---|---|---|---|
| `ignorePatterns` | string | **Newline-separated** (`\n`) | Files to skip during review (not indexing) |

**Common ignore patterns:**
```
*.generated.*\n*.min.js\n*.min.css\ndist/**\nbuild/**\nout/**\n.next/**\nnode_modules/**\n**/vendor/**\n**/__snapshots__/**\npackage-lock.json\nyarn.lock\npnpm-lock.yaml\n*.lock\n**/*.d.ts\n**/migrations/**
```

> **⚠ Format trap:** `scope` is an **array** of strings: `["src/**"]`. `ignorePatterns` is a **newline-separated string**: `"dist/**\nnode_modules/**"`. Mixing these up causes silent failures — no error, just no matching.

### Cross-Repo Context

| Parameter | Type | Format | Description |
|---|---|---|---|
| `patternRepositories` | string[] | `"org/repo"` | Repos to index for cross-repo validation. Never use full URLs |

### Rules

```json
{
  "rules": [
    {
      "id": "unique-kebab-case-id",
      "rule": "Precise, measurable rule text",
      "scope": ["src/api/**/*.ts"],
      "severity": "high"
    }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | If child dirs may disable | Unique identifier for override/disable |
| `rule` | string | Yes | The rule text — specific and measurable |
| `scope` | string[] | Recommended | Glob patterns — **must be an array**, not comma-separated |
| `severity` | string | No | `"high"`, `"medium"`, or `"low"` |

### Disabled Rules (Child Configs)

```json
{
  "disabledRules": ["rule-id-from-parent"]
}
```

### Review Output

| Parameter | Type | Default | Description |
|---|---|---|---|
| `comment` | string | — | Prefix on every summary comment |
| `shouldUpdateDescription` | boolean | false | Update PR description instead of posting comment |
| `updateExistingSummaryComment` | boolean | — | Update existing comment vs. post new one |
| `updateSummaryOnly` | boolean | false | Suppress inline comments, only show summary |
| `fixWithAI` | boolean | false | Add AI fix suggestions |
| `hideFooter` | boolean | false | Hide Greptile branding |
| `statusCheck` | boolean | — | GitHub status check (also suppresses "X files reviewed" comments) |
| `statusCommentsEnabled` | boolean | — | Main review summary comment |

### Review Components

| Parameter | Type | Default | Description |
|---|---|---|---|
| `includeIssuesTable` | boolean | — | Include issues table in summary |
| `includeConfidenceScore` | boolean | — | Include confidence score |
| `includeSequenceDiagram` | boolean | false | Auto-selects diagram type: sequence/ER/class/flow |

### Section-Level Control

Each section can be independently configured:

```json
{
  "summarySection":          { "included": true,  "collapsible": true,  "defaultOpen": true  },
  "issuesTableSection":      { "included": true,  "collapsible": true,  "defaultOpen": false },
  "confidenceScoreSection":  { "included": true,  "collapsible": true,  "defaultOpen": false },
  "sequenceDiagramSection":  { "included": false, "collapsible": true,  "defaultOpen": false }
}
```

---

## `.greptile/rules.md` — Prose Rules

Use for rules that need narrative context, code examples, or nuanced reasoning. The entire file is passed to the reviewer, scoped to the directory containing the `.greptile/` folder.

**Format:** Standard markdown with code fences. Include good/bad examples.

```markdown
## Error Handling

All async functions must use try-catch. Never swallow errors silently.
At minimum, log with: error object, function name, input context.

### Good
\`\`\`ts
async function getUser(id: string) {
  try {
    return await db.users.findUnique({ where: { id } });
  } catch (error) {
    logger.error('getUser failed', { id, error });
    throw new AppError('USER_FETCH_FAILED', error);
  }
}
\`\`\`

### Bad
\`\`\`ts
async function getUser(id: string) {
  try {
    return await db.users.findUnique({ where: { id } });
  } catch (e) {
    // silently swallowed
  }
}
\`\`\`
```

---

## `.greptile/files.json` — Context Files

Point the reviewer to architecture docs, schemas, API specs:

```json
{
  "files": [
    {
      "path": "docs/architecture.md",
      "description": "System architecture — read before reviewing any PR"
    },
    {
      "path": "prisma/schema.prisma",
      "description": "Database schema — validate model relationships",
      "scope": ["src/db/**", "src/repositories/**"]
    }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `path` | string | Yes | Relative path from repo root to the document |
| `description` | string | Yes | What the document provides and how to use it |
| `scope` | string[] | No | Glob patterns for when this context is relevant |

### Qualifying Criteria for Context Files

Not every document should be in `files.json`. A context file qualifies when it provides information a reviewer **needs** to validate correctness — not just background reading.

**Include:**
| File type | Why it qualifies | Example scope |
|---|---|---|
| Database schemas (Prisma, Drizzle, SQLAlchemy) | Validates model field usage, relationships, migrations | `src/db/**`, `src/repositories/**` |
| API specs (OpenAPI, GraphQL SDL) | Validates endpoint contracts, request/response shapes | `src/api/**`, `src/routes/**` |
| Shared type definitions | Validates interface conformance across packages | Package-specific |
| Architecture Decision Records (ADRs) | Explains *why* the code is structured a certain way | All files |
| Architecture diagrams/docs | Provides system boundaries for dependency reviews | All files |

**Exclude:**
- READMEs (too generic, rarely inform review decisions)
- Changelogs (historical, not prescriptive)
- Contributing guides (process, not code quality)
- Config files (tsconfig, package.json) — the reviewer already sees these
- Test fixtures and sample data

---

## `greptile.json` — Legacy Single-File Alternative

Supports all parameters from `config.json` plus `customContext` and `instructions`:

```json
{
  "strictness": 2,
  "instructions": "Focus on security and type safety",
  "customContext": {
    "rules": [
      { "rule": "Rule text", "scope": ["glob/**"] }
    ],
    "files": [
      { "path": "docs/style.md", "description": "Style guide", "scope": ["src/**"] }
    ],
    "other": [
      { "content": "Legacy code from 2018 — be conservative", "scope": ["src/legacy/**"] }
    ]
  },
  "patternRepositories": ["org/repo"]
}
```

Migrate away from this format. `.greptile/` is preferred.

---

## Cascading Configuration (Monorepos)

```
repo-root/
├── .greptile/
│   ├── config.json      ← Root: applies everywhere
│   ├── rules.md         ← Prose: applies everywhere
│   └── files.json       ← Context: applies everywhere (or scoped)
├── packages/
│   ├── api/
│   │   └── .greptile/
│   │       └── config.json  ← Extends root + can override
│   ├── payments/
│   │   └── .greptile/
│   │       └── config.json  ← strictness: 1 (stricter)
│   └── internal-tools/
│       └── .greptile/
│           └── config.json  ← strictness: 3, disabledRules: [...]
```

### Inheritance Behavior

| Parameter | Child behavior |
|---|---|
| `strictness` | **Overrides** parent |
| `commentTypes` | **Overrides** parent |
| `triggerOnUpdates` | **Overrides** parent |
| `rules` | **Extends** parent (adds new rules to inherited set) |
| `disabledRules` | **Disables** specific parent rules by `id` |
| `ignorePatterns` | **Extends** parent patterns |

### Example Child Override

`packages/internal-tools/.greptile/config.json`:
```json
{
  "strictness": 3,
  "disabledRules": ["no-raw-sql"],
  "rules": [
    {
      "id": "internal-tools-logging",
      "rule": "Internal tools may use console.log for debugging.",
      "scope": ["**/*.ts"],
      "severity": "low"
    }
  ]
}
```

---

## Output Format Template

When generating Greptile configuration, present it in this exact order:

1. **File tree** — markdown code block showing `.greptile/` directory structure
2. **Complete file contents** — each file in a fenced code block with the filename as header
3. **Reasoning annotations** — markdown list tying each rule to repo evidence:
   ```markdown
   - **rule-id**: Added because [specific repo observation] (see `path/to/file:line`)
   ```
4. **Canary test** — a temporary low-severity rule to verify config is being read:
   ```json
   {
     "id": "canary",
     "rule": "Comment 'canary active' on any PR modifying a README.",
     "scope": ["**/README.md"],
     "severity": "low"
   }
   ```
5. **Migration notes** — only if replacing `greptile.json` with `.greptile/`

---

## Permissions

| Action | Owner | Admin | Member |
|---|---|---|---|
| View custom context | Yes | Yes | Yes |
| Create/edit dashboard rules | Yes | Yes | No |
| Edit `.greptile/` or `greptile.json` | Anyone with repo write access |||
| View/approve suggested rules | Yes | Yes | Yes |
