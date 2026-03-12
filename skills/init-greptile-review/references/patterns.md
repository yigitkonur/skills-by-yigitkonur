# Common Configuration Patterns

Ready-to-adapt configuration templates for common repository types. Every rule must be justified by actual repository context — never copy verbatim.

---

## Repository Exploration Method

Before selecting a pattern, map the repository systematically. This section provides the HOW — the pattern sections below provide the WHAT.

### Step-by-step exploration

1. **Read workspace config** to determine repo structure:
   ```bash
   # Monorepo detection
   cat pnpm-workspace.yaml 2>/dev/null || cat lerna.json 2>/dev/null || cat nx.json 2>/dev/null || cat turbo.json 2>/dev/null || cat Cargo.toml 2>/dev/null
   ```

2. **List top-level directories** to understand layout:
   ```bash
   ls -d */ 2>/dev/null | head -20
   ```

3. **Identify languages and frameworks** from dependency manifests:
   ```bash
   # JavaScript/TypeScript
   cat package.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('deps:', list(d.get('dependencies',{}).keys())[:15]); print('dev:', list(d.get('devDependencies',{}).keys())[:10])"
   
   # Python
   cat pyproject.toml 2>/dev/null || cat requirements.txt 2>/dev/null | head -20
   
   # Go
   head -20 go.mod 2>/dev/null
   
   # Rust
   head -30 Cargo.toml 2>/dev/null
   ```

4. **Find risk-sensitive directories** by searching for keywords:
   ```bash
   find . -type d \( -name auth -o -name payment* -o -name billing -o -name webhook* -o -name middleware -o -name migration* -o -name security \) -not -path '*/node_modules/*' 2>/dev/null
   ```

5. **Find context-worthy files** (schemas, specs, architecture docs):
   ```bash
   find . -name '*.prisma' -o -name '*.graphql' -o -name 'openapi*' -o -name 'swagger*' -o -name '*.proto' 2>/dev/null | grep -v node_modules
   ls docs/ architecture.md ADR* ARCHITECTURE* 2>/dev/null
   ```

6. **Detect existing linters/formatters**:
   ```bash
   ls .eslintrc* prettier.config* biome.* .stylelintrc* pyproject.toml .rubocop.yml .golangci.yml 2>/dev/null
   ```

### Depth guidance

| Repo size | Exploration depth | When to stop |
|---|---|---|
| Small (<50 files) | Directory listing + dependency manifest | You can answer all 7 mapping items |
| Medium (50-500 files) | + Read key config files, check 2-3 representative source files | You understand the architecture |
| Large (500+ files) | + Check each top-level package purpose, key deps, risk dirs | You can confidently scope rules |
| Monorepo (multiple packages) | + Read each package's package.json/deps, identify divergent risk profiles | You know which packages need child configs |

**Stop signal:** You can confidently write the `scope` arrays for your rules and the `ignorePatterns` string without guessing.

---

## Pattern Selection Guide

| Repository Type | Strictness | Comment Types | Key Focus Areas |
|----------------|-----------|---------------|-----------------|
| TypeScript Backend API | 2 | `["logic", "syntax"]` | SQL injection, error handling, API contracts |
| React/Vue Frontend | 2 | `["logic", "syntax", "style"]` | Component boundaries, hooks rules, design system usage |
| Python Django/Flask | 2 | `["logic", "syntax"]` | ORM usage, N+1 queries, view permissions |
| Go Microservice | 2 | `["logic", "syntax"]` | Error wrapping, context propagation, goroutine safety |
| Rust/Tauri Desktop | 2 | `["logic", "syntax"]` | Command safety, mutex scope, no panics |
| Monorepo | 2 (root) | `["logic", "syntax"]` | Cascading overrides, per-package strictness |
| Mobile (React Native) | 2 | `["logic", "syntax"]` | Platform-specific code, native module safety |
| Data Pipeline | 2 | `["logic", "syntax"]` | Schema validation, idempotency, retry logic |

---

## Universal Ignore Patterns

These patterns apply to virtually every repository. Start here and add project-specific patterns:

```
node_modules/**
dist/**
build/**
out/**
.next/**
*.min.js
*.min.css
*.generated.*
package-lock.json
yarn.lock
pnpm-lock.yaml
*.lock
**/__snapshots__/**
```

### Language-Specific Additions

| Language | Additional Ignore Patterns |
|----------|--------------------------|
| TypeScript | `**/*.d.ts`, `coverage/**` |
| Python | `*.pyc`, `__pycache__/**`, `*.egg-info/**`, `.tox/**`, `htmlcov/**`, `migrations/**` |
| Go | `vendor/**`, `*.pb.go`, `*_generated.go`, `bin/**`, `mocks/**` |
| Rust | `target/**`, `Cargo.lock` |
| Java | `*.class`, `target/**`, `build/**`, `.gradle/**` |
| Ruby | `vendor/bundle/**`, `coverage/**`, `tmp/**` |


### Discovering Project-Specific Ignore Patterns

Beyond universal patterns, every repo has unique noise. Discover it:

```bash
# Find generated files (often have 'generated', 'auto', or header comments)
find . -name '*generated*' -o -name '*auto*' -o -name '*.gen.*' 2>/dev/null | grep -v node_modules | head -10

# Find build output directories
find . -type d \( -name dist -o -name build -o -name out -o -name .next -o -name target -o -name bin \) -not -path '*/node_modules/*' 2>/dev/null

# Find large binary or data files
find . -size +100k \( -name '*.json' -o -name '*.csv' -o -name '*.sql' \) -not -path '*/node_modules/*' 2>/dev/null | head -10

# Find snapshot/fixture directories
find . -type d \( -name __snapshots__ -o -name fixtures -o -name __mocks__ -o -name testdata \) 2>/dev/null | head -10
```

Common project-specific patterns to add:

| Project type | Additional ignore patterns |
|---|---|
| Next.js | `.next/**`, `.vercel/**`, `out/**` |
| Monorepo with build caching | `.turbo/**`, `.nx/**` |
| Projects with code generation | `**/*.generated.ts`, `**/*_gen.go`, `**/*.pb.ts` |
| Projects with bundled assets | `public/build/**`, `static/dist/**` |
| Database projects | `**/migrations/**`, `**/seeds/**` |
| Mobile apps | `android/app/build/**`, `ios/Pods/**`, `*.xcworkspace/**` |


---

## Universal Bot Exclusions

Always exclude automated bot authors to avoid reviewing dependency updates:

```json
{
  "excludeAuthors": ["dependabot[bot]", "renovate[bot]", "github-actions[bot]", "snyk-bot"]
}
```

---

## TypeScript Backend Pattern

For Express/Fastify/NestJS APIs with database access:

### Key Rules
```json
{
  "rules": [
    {
      "id": "no-raw-sql",
      "rule": "Use parameterized queries via the ORM. Never interpolate user input into SQL strings.",
      "scope": ["src/db/**", "src/repositories/**"],
      "severity": "high"
    },
    {
      "id": "api-rate-limiting",
      "rule": "All API endpoints must have rate limiting middleware.",
      "scope": ["src/api/**/*.ts", "src/routes/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "structured-logging",
      "rule": "Use the structured logger. Never use console.log/warn/error in production code.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "async-error-handling",
      "rule": "All async functions must have try-catch with structured logging. Never swallow errors.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "no-business-logic-in-controllers",
      "rule": "Controllers must only handle HTTP request/response. Business logic belongs in services.",
      "scope": ["src/controllers/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "api-response-shape",
      "rule": "API error responses must include: status, message, timestamp (ISO 8601), requestId.",
      "scope": ["src/api/**/*.ts"],
      "severity": "high"
    }
  ]
}
```

### Context Files
```json
{
  "files": [
    { "path": "docs/architecture.md", "description": "System architecture — read before reviewing any PR" },
    { "path": "openapi/spec.yaml", "description": "API contracts", "scope": ["src/api/**", "src/routes/**"] },
    { "path": "prisma/schema.prisma", "description": "Database schema", "scope": ["src/db/**", "src/repositories/**"] }
  ]
}
```

---

## React Frontend Pattern

For React apps with design system, API client, and hooks:

### Key Rules
```json
{
  "rules": [
    {
      "id": "design-system-usage",
      "rule": "Use components from the design system. Do not create custom UI primitives (buttons, inputs, modals).",
      "scope": ["src/components/**/*.tsx"],
      "severity": "medium"
    },
    {
      "id": "no-direct-dom",
      "rule": "Do not use document.querySelector or direct DOM manipulation. Use React refs.",
      "scope": ["src/**/*.tsx", "src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "hooks-rules",
      "rule": "Custom hooks must be in src/hooks/ and prefixed with 'use'. Never call hooks conditionally.",
      "scope": ["src/**/*.ts", "src/**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "api-contract-match",
      "rule": "API calls must use typed API client functions. No raw fetch() or axios calls.",
      "scope": ["src/api/**/*.ts", "src/hooks/use*.ts"],
      "severity": "high"
    },
    {
      "id": "no-inline-styles",
      "rule": "Do not use inline style objects for layout. Use CSS modules or the design system's spacing utilities.",
      "scope": ["src/components/**/*.tsx"],
      "severity": "low"
    }
  ]
}
```

### When to Include "style" Comment Type
- **Include** if no Prettier/ESLint/Stylelint configured
- **Exclude** if strong linting exists (most modern React projects)

---

## Python Django Pattern

For Django REST Framework APIs:

### Key Rules
```json
{
  "rules": [
    {
      "id": "no-raw-sql",
      "rule": "Use Django ORM or parameterized raw() calls. Never use string formatting for SQL.",
      "scope": ["**/views.py", "**/models.py", "**/managers.py", "**/queries.py"],
      "severity": "high"
    },
    {
      "id": "no-n-plus-one",
      "rule": "QuerySets in views/serializers must use select_related() or prefetch_related().",
      "scope": ["**/views.py", "**/serializers.py", "**/viewsets.py"],
      "severity": "high"
    },
    {
      "id": "view-permission-classes",
      "rule": "All API views must declare permission_classes explicitly.",
      "scope": ["**/views.py", "**/viewsets.py"],
      "severity": "high"
    },
    {
      "id": "no-print-statements",
      "rule": "Use the logging module. No print() statements in production code.",
      "scope": ["**/*.py"],
      "severity": "medium"
    },
    {
      "id": "model-str-method",
      "rule": "All Django models must implement __str__.",
      "scope": ["**/models.py"],
      "severity": "low"
    }
  ]
}
```

---

## Go Microservice Pattern

For Go services with gRPC/HTTP, structured logging:

### Key Rules
```json
{
  "rules": [
    {
      "id": "error-wrapping",
      "rule": "Errors must be wrapped with fmt.Errorf(\"...: %w\", err). Never return bare errors.",
      "scope": ["**/*.go"],
      "severity": "high"
    },
    {
      "id": "context-propagation",
      "rule": "All I/O functions must accept context.Context as first parameter.",
      "scope": ["**/*.go"],
      "severity": "high"
    },
    {
      "id": "no-goroutine-leak",
      "rule": "Every goroutine must have a clear termination path via context or done channel.",
      "scope": ["**/*.go"],
      "severity": "high"
    },
    {
      "id": "structured-logging",
      "rule": "Use slog or zerolog. No log.Println or fmt.Println in production code.",
      "scope": ["**/*.go"],
      "severity": "medium"
    }
  ]
}
```

---

## Monorepo Cascading Pattern

Root config + per-package overrides:

### Root `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "excludeAuthors": ["dependabot[bot]"],
  "rules": [
    {
      "id": "no-console-log",
      "rule": "Use structured logger. No console.log/warn/error.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "typescript-strict",
      "rule": "All new files must be TypeScript.",
      "scope": ["**/*"],
      "severity": "medium"
    }
  ]
}
```

### `packages/payments/.greptile/config.json`
```json
{
  "strictness": 1,
  "rules": [
    {
      "id": "pci-no-pii-logging",
      "rule": "Never log credit card numbers, CVVs, or full SSNs.",
      "scope": ["**/*.ts"],
      "severity": "high"
    },
    {
      "id": "payments-idempotency",
      "rule": "All payment mutation endpoints must require an idempotency key.",
      "scope": ["src/api/**/*.ts"],
      "severity": "high"
    }
  ]
}
```

### `packages/internal-admin/.greptile/config.json`
```json
{
  "strictness": 3,
  "disabledRules": ["no-console-log"]
}
```

### Strictness Strategy for Monorepos

| Package Type | Recommended Strictness | Rationale |
|-------------|----------------------|-----------|
| Payments, auth, security | 1 (Verbose) | Maximum scrutiny for critical paths |
| Core application code | 2 (Balanced) | Standard production code |
| Internal tools, scripts | 3 (Critical only) | Minimize noise on non-customer-facing code |
| Prototypes, experiments | 3 or skip | Avoid blocking rapid iteration |


### Monorepo Exploration Checklist

Before deciding on child configs, answer these for each top-level package:

| Question | Impact on config |
|---|---|
| Does this package handle payments, auth, or PII? | → Child config with `strictness: 1` |
| Does this package have its own linters? | → May need different `commentTypes` |
| Does this package have unique risk patterns? | → Needs package-specific rules |
| Is this an internal tool or prototype? | → Child config with `strictness: 3` |
| Does this package share types/contracts with others? | → May need `patternRepositories` or `files.json` |

If fewer than 2 packages answer YES to any question, skip child configs entirely and use root-only configuration.


---

## Next.js Application Pattern

### Server/Client Component Rules
```json
{
  "rules": [
    {
      "id": "server-component-boundary",
      "rule": "Files in app/ are Server Components by default. Add 'use client' only when using hooks, event handlers, or browser APIs.",
      "scope": ["app/**/*.tsx"],
      "severity": "medium"
    },
    {
      "id": "no-env-exposure",
      "rule": "Never use NEXT_PUBLIC_ prefix for secrets. Server-only env vars must only be accessed in server components or API routes.",
      "scope": ["**/*.ts", "**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "metadata-required",
      "rule": "All page.tsx files must export metadata or generateMetadata for SEO.",
      "scope": ["app/**/page.tsx"],
      "severity": "medium"
    },
    {
      "id": "server-action-validation",
      "rule": "All server actions must validate input with zod before processing.",
      "scope": ["app/**/actions.ts", "src/actions/**/*.ts"],
      "severity": "high"
    }
  ]
}
```

---

## MCP Server Pattern

### Protocol Compliance Rules
```json
{
  "rules": [
    {
      "id": "mcp-input-validation",
      "rule": "All tool handlers must validate inputs with Zod schemas. Never trust raw input.",
      "scope": ["src/tools/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-structured-errors",
      "rule": "Tool handlers must return structured error responses with error code and message. Never throw unstructured errors.",
      "scope": ["src/tools/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-no-command-injection",
      "rule": "Never pass user-provided input directly to shell commands. Use argument arrays and validate against allowlists.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-timeout-enforcement",
      "rule": "All external calls in tool handlers must have explicit timeouts.",
      "scope": ["src/tools/**/*.ts"],
      "severity": "medium"
    }
  ]
}
```

---

## Context Files Patterns

### What to Include as Context

| File Type | What It Provides | Example Scope |
|-----------|-----------------|---------------|
| Architecture docs | System boundaries, service topology | All files |
| API specs (OpenAPI) | Endpoint contracts | `src/api/**`, `src/routes/**` |
| Database schemas | Model relationships | `src/db/**`, `src/models/**` |
| ADRs | Decision rationale | All files |
| Style guides | Team conventions | All files |
| Type definitions | Cross-service types | Service-specific |

### Scoping Context Files

Always scope context files to relevant directories. A Prisma schema is useless context when reviewing React components:

```json
{
  "files": [
    {
      "path": "prisma/schema.prisma",
      "description": "Database schema — validate model relationships",
      "scope": ["src/db/**", "src/repositories/**"]
    },
    {
      "path": "docs/api-conventions.md",
      "description": "API design conventions",
      "scope": ["src/api/**", "src/routes/**"]
    }
  ]
}
```
