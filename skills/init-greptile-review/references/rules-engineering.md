# Rules Engineering

Complete guide to writing, scoping, and managing Greptile review rules.

---

## Rule Philosophy

Greptile rules must leverage its LLM-powered semantic understanding. A good Greptile rule requires understanding intent, architecture, or cross-file implications — not pattern matching that a linter could handle.

**The litmus test**: If ESLint, Pylint, or `grep` can catch it, it should not be a Greptile rule.

| Good Greptile Rule | Bad Greptile Rule |
|-------------------|-------------------|
| "Service methods must not call HTTP endpoints directly — use the gateway client" | "Use semicolons" |
| "All database mutations must be wrapped in transactions" | "Indent with 2 spaces" |
| "API error responses must include requestId, timestamp, and error code" | "No unused imports" |
| "Never hold a Mutex guard across an await point" | "Use camelCase" |

---

## Rule Formats

Greptile supports four rule formats with cascading precedence:

### 1. JSON Rules (`.greptile/config.json`)

Structured, versionable, programmatically manageable:

```json
{
  "rules": [
    {
      "id": "no-raw-sql",
      "rule": "Use parameterized queries via the ORM. Never interpolate user input into SQL strings.",
      "scope": ["src/db/**", "src/repositories/**"],
      "severity": "high"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Recommended | Unique kebab-case identifier. Required if child directories may disable it |
| `rule` | string | Yes | The rule text — specific, measurable, actionable |
| `scope` | string[] | Recommended | Glob patterns targeting relevant directories. **Must be an array** |
| `severity` | string | No | `"high"`, `"medium"`, or `"low"` |

### 2. Prose Rules (`.greptile/rules.md`)

For rules needing narrative context, code examples, or nuanced reasoning:

```markdown
## Error Handling

All async functions must use try-catch with structured logging.
Never swallow errors silently.

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

The entire file is passed to the reviewer, scoped to the directory containing the `.greptile/` folder. Best for:
- Rules with good/bad code examples
- Nuanced architectural guidelines
- Migration patterns (old way → new way)

### 3. Dashboard Rules

Created via `app.greptile.com` → **Custom Context** → **Rules**:
- Visual form for id, rule text, scope, severity
- Auto-syncs to repository
- Good for quick additions without commits
- Can conflict with local `.greptile/` rules (dashboard takes precedence if org-level)

### 4. Org-Enforced Rules

Set by organization admins in the dashboard:
- Cannot be overridden by repository-level config
- Apply across all repos in the organization
- Use for compliance, security baselines, company-wide standards
- Propagation delay: 5-10 minutes after changes

---

## Rule Quality Checklist

Every rule must pass these criteria:

### 1. Specific
Not "Keep functions short" but "Functions must not exceed 50 lines excluding comments and blank lines."

### 2. Measurable
Pass/fail criteria must be unambiguous. A reviewer should never have to guess whether the rule applies.

### 3. Scoped
Every rule gets a `scope` array targeting relevant directories. A database rule should not fire on frontend components:

```json
{
  "scope": ["src/db/**", "src/repositories/**"]
}
```

**Never** use a comma-separated string:
```json
// WRONG — silently fails to match
{ "scope": "src/db/**, src/repositories/**" }
```

### 4. Actionable
The developer must know exactly what to change. Include:
- What is wrong
- What the correct approach is
- Where to find the right pattern (import path, utility function, etc.)

### 5. Semantic
Rules that require understanding, not pattern matching.

### 6. Identifiable
Every disableable rule gets a unique `id` so child directories can disable it:

```json
// Parent config
{ "id": "no-console-log", "rule": "Use structured logger..." }

// Child config (internal tools)
{ "disabledRules": ["no-console-log"] }
```

---

## Rule Categories

Scan the repository for these categories and write rules for applicable ones:

### Security
**Signal**: SQL queries, user input handling, auth code, PII, file system access
```json
{
  "id": "no-raw-sql",
  "rule": "Use parameterized queries via the ORM. Never interpolate user input into SQL strings.",
  "scope": ["src/db/**", "src/repositories/**"],
  "severity": "high"
}
```

### Architecture
**Signal**: Controller/service/repository layers, module boundaries, dependency direction
```json
{
  "id": "no-business-logic-in-controllers",
  "rule": "Controllers must only handle HTTP request/response. Business logic belongs in src/services/.",
  "scope": ["src/controllers/**/*.ts"],
  "severity": "medium"
}
```

### Error Handling
**Signal**: try-catch patterns, error logging, error response shapes
```json
{
  "id": "async-error-handling",
  "rule": "All async functions must have try-catch with structured logging. Never swallow errors.",
  "scope": ["src/**/*.ts"],
  "severity": "medium"
}
```

### API Contracts
**Signal**: OpenAPI specs, shared API types, cross-service calls
```json
{
  "id": "api-response-shape",
  "rule": "API error responses must include: status (number), message (string), timestamp (ISO 8601), requestId (UUID).",
  "scope": ["src/api/**/*.ts"],
  "severity": "high"
}
```

### Performance
**Signal**: Database queries in loops, N+1 patterns, unbounded fetches
```json
{
  "id": "no-n-plus-one",
  "rule": "QuerySets must use select_related() or prefetch_related() to avoid N+1 queries.",
  "scope": ["**/views.py", "**/serializers.py"],
  "severity": "high"
}
```

### Dependencies
**Signal**: Shared libraries, internal packages, design systems
```json
{
  "id": "design-system-usage",
  "rule": "Use components from @acme/design-system. Do not create custom UI primitives.",
  "scope": ["src/components/**/*.tsx"],
  "severity": "medium"
}
```

### Migration
**Signal**: JS→TS migration, legacy patterns being phased out
```json
{
  "id": "no-new-js-files",
  "rule": "All new files must be TypeScript. Do not add new .js files.",
  "scope": ["**/*"],
  "severity": "medium"
}
```

### Compliance
**Signal**: PII handling, logging restrictions, audit requirements
```json
{
  "id": "pci-no-pii-logging",
  "rule": "Never log credit card numbers, CVVs, or full SSNs. Mask all PII in logs.",
  "scope": ["**/*.ts"],
  "severity": "high"
}
```

### Naming
**Signal**: Component naming, hook prefixes, file naming conventions
```json
{
  "id": "hooks-naming",
  "rule": "Custom hooks must be in src/hooks/ and prefixed with 'use'. Never call hooks conditionally.",
  "scope": ["src/**/*.ts", "src/**/*.tsx"],
  "severity": "high"
}
```

---

## Severity Levels

| Level | When to Use | Effect |
|-------|------------|--------|
| `high` | Security issues, data loss risk, crash potential | Always reported regardless of strictness |
| `medium` | Architecture violations, maintainability concerns | Reported at strictness 1-2, suppressed at 3 |
| `low` | Style preferences, suggestions, minor improvements | Reported only at strictness 1 |

### Severity + Strictness Interaction

```
strictness: 1 (Verbose)   → Reports high + medium + low
strictness: 2 (Balanced)  → Reports high + medium
strictness: 3 (Critical)  → Reports high only
```

---

## Scoping Patterns

### Glob Syntax

| Pattern | Matches |
|---------|---------|
| `src/**/*.ts` | All TypeScript files under src/ |
| `**/views.py` | All views.py files at any depth |
| `src/api/**` | Everything under src/api/ |
| `**/*.{ts,tsx}` | All .ts and .tsx files |
| `packages/*/src/**` | All src/ dirs in any package |

### Scoping Strategy

| Repo Type | Strategy |
|-----------|----------|
| Single-service | Scope to `src/**` for app code, exclude tests |
| Monorepo | Scope to specific package: `packages/api/src/**` |
| Full-stack | Separate scopes for frontend and backend |
| Multi-language | Language-specific scopes: `**/*.py`, `**/*.go` |

---

## Disabling Rules

Child `.greptile/config.json` files can disable parent rules by `id`:

```json
{
  "disabledRules": ["no-console-log", "typescript-strict"]
}
```

Use cases:
- Internal tools that allow console.log
- Prototypes that skip strict typing
- Test directories that need different rules
- Legacy code directories during migration

---

## Rule Evolution

### Auto-Suggested Rules

After approximately 10 PRs, Greptile auto-suggests rules based on patterns it observes in your codebase. These appear in the dashboard under **Custom Context → Suggested Rules**.

- Review and accept relevant suggestions
- Duplicates of existing rules may appear — this is normal
- Suggestions improve as Greptile processes more PRs

### Rule Maintenance

1. **Start lean** — 5-10 rules maximum initially
2. **Measure noise** — if a rule triggers on 80%+ of PRs, it is either too broad or should be a linter rule
3. **Scope aggressively** — every high-volume rule needs a scope
4. **Review quarterly** — remove rules that no longer apply, add rules for new patterns
5. **Check "Last Applied"** — rules that never trigger may have scope/syntax issues
