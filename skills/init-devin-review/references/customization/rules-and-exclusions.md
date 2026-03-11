# Customization: Rules, Exclusions, and Severity Tuning

Complete reference for fine-tuning Devin Bug Catcher behavior through REVIEW.md content, dashboard settings, and auto-fix configuration.

---

## How the Bug Catcher Classifies Findings

The Bug Catcher reads your instruction files and classifies each finding into one of four categories:

### Bugs (Actionable — should be fixed)

| Severity | Description | Triggered By |
|----------|-------------|-------------|
| **Severe** | High-confidence issues requiring immediate attention | Rules in Critical Areas / Security sections; imperative language ("must never", "always required") |
| **Non-severe** | Lower-severity issues that should be reviewed | Rules in Conventions section; directive language ("use X instead of Y") |

### Flags (Informational — may or may not need action)

| Class | Description | Triggered By |
|-------|-------------|-------------|
| **Investigate** | Warrants further investigation | Rules in Performance section; suggestive language ("watch for", "consider") |
| **Informational** | Explains behavior, no action needed | Rules in Testing section; descriptive context |

---

## Controlling Severity Through Phrasing

The language in your `REVIEW.md` directly affects classification. Use this guide to control severity:

### Making Rules More Severe

```markdown
## Security
- API keys must NEVER appear in source code. This is a critical security violation.
- All API routes MUST verify authentication. Unauthenticated endpoints are severe bugs.
- SQL injection vulnerabilities MUST be fixed immediately. Use parameterized queries only.
```

Key triggers for severe classification:
- Absolute language: "must never", "always required", "critical", "severe"
- Placement in Critical Areas or Security sections
- Reference to security impact: "enables SQL injection", "allows unauthorized access"

### Making Rules Less Severe (Investigate/Informational)

```markdown
## Performance
- Consider using batch operations instead of individual queries in loops.
- Watch for N+1 query patterns — they may impact performance at scale.
- Large payloads might benefit from pagination for better user experience.
```

Key triggers for lower severity:
- Suggestive language: "consider", "watch for", "might", "prefer"
- Placement in Performance or Testing sections
- No security or data-integrity implication

---

## Custom Review Rule File Paths

By default, Devin reads `**/REVIEW.md`. To add additional instruction files:

1. Go to `Settings > Review > Review Rules`
2. Type a glob pattern (e.g., `docs/**/*.md`, `**/*.review-rules`)
3. Click **Add**

### Use Cases for Custom Rule Paths

| Pattern | Use Case |
|---------|----------|
| `docs/review-guidelines.md` | Team prefers guidelines in docs/ |
| `**/*.review-rules` | Custom extension for review files |
| `.github/review-config.md` | Co-locate with other GitHub configs |
| `packages/*/REVIEW-RULES.md` | Alternative naming for monorepo scoping |

Custom patterns are read in addition to `**/REVIEW.md` — they don't replace the default.

---

## File Exclusions

### In REVIEW.md (Ignore Section)

The Ignore section tells the Bug Catcher to skip specific files and directories:

```markdown
## Ignore
- Auto-generated files in `src/generated/` do not need review.
- Lock files (package-lock.json, yarn.lock, pnpm-lock.yaml) can be skipped.
- Test snapshots in `__snapshots__/` don't need review.
- Build output in `dist/` and `.next/` should never be committed.
- Migration files in `prisma/migrations/` are auto-generated.
```

### Best Practices for Exclusions

1. **Be specific** — list actual paths from your repo, not generic patterns
2. **Qualify exclusions** — "unless dependencies changed" for lock files
3. **Include all generated code** — ORM clients, GraphQL types, protobuf, OpenAPI
4. **Don't exclude things that matter** — migration files may need review even if auto-generated

### Common Exclusion Sets

**JavaScript/TypeScript:**
```markdown
- `node_modules/` — never committed
- `dist/`, `build/`, `.next/`, `.nuxt/` — build output
- `*.d.ts` — auto-generated declarations
- `__snapshots__/` — test snapshots
- `coverage/` — test coverage
- `*.min.js`, `*.min.css` — minified assets
```

**Python:**
```markdown
- `__pycache__/`, `*.pyc` — bytecode
- `.venv/`, `venv/` — virtual environments
- `*.egg-info/` — build artifacts
- `htmlcov/` — coverage reports
```

**Go:**
```markdown
- `vendor/` — vendored dependencies
- `*.pb.go` — generated protobuf
- `go.sum` — unless dependencies changed
```

**Rust:**
```markdown
- `target/` — build output
- `Cargo.lock` — unless dependencies changed
- `*.rs.bk` — backup files from rustfmt
```

**Java / Kotlin:**
```markdown
- `build/`, `out/` — build output
- `*.class`, `*.jar` — compiled artifacts
- `.gradle/` — Gradle cache
```

**Ruby:**
```markdown
- `vendor/bundle/` — bundled gems
- `tmp/` — temporary files
- `log/` — log output
```

---

## Auto-Fix Configuration

Auto-Fix lets Devin propose code changes alongside bug findings.

### Enabling Auto-Fix

| Method | Who Can | Location |
|--------|---------|----------|
| Per-PR toggle | Any reviewer | PR page → settings popover → **Enable Autofix** |
| Embedded view | Any reviewer | Devin Review view → settings → **Enable Autofix** |
| Global setting | Org admins only | `Settings > Customization > Pull request settings > Autofix settings` |

### Global Auto-Fix Modes

| Mode | Behavior |
|------|----------|
| **Respond to specific bots only** | Add `devin-ai-integration[bot]` to allow-list |
| **Respond to all bot comments** | Auto-Fix triggers on any bot comment |

When global mode is set to "Respond to all bot comments", the per-PR toggle appears enabled but is immutable — changes must be made in Customization settings.

### Auto-Fix Behavior

- Generates code suggestions for findings classified as Bugs (severe and non-severe)
- "No Issues Found" summary comments do **not** trigger Auto-Fix
- Suggestions appear as GitHub Suggested Changes or inline code diffs
- Human approval is always required — Devin never merges auto-fixes automatically
- Only org admins can change the global Auto-Fix mode

### What Auto-Fix Can and Cannot Do

| Rule Type | Auto-Fix? | Reason |
|-----------|-----------|--------|
| Import ordering | ✅ Yes | Deterministic rewrite |
| Missing error wrapping | ✅ Yes | Mechanical transformation |
| Architecture violation | ❌ Flag only | Requires design judgment |
| Security concern | ❌ Flag only | Needs human risk assessment |
| Style preference | ✅ If deterministic | Must have one unambiguous fix |

> **Warning:** Vague rules ("write cleaner code", "improve readability") produce unpredictable auto-fixes. Every auto-fixable rule must describe a single, unambiguous transformation.

---

## Avoiding Duplicate Rules

Devin reads multiple instruction files. Duplicating rules across files creates noise:

### Check Before Writing REVIEW.md

| Check | Where | What to look for |
|-------|-------|-----------------|
| **ESLint / linter config** | `.eslintrc`, `eslint.config.js` | Rules already enforced by the linter |
| **CI pipeline** | `.github/workflows/`, `Jenkinsfile` | Checks already run in CI (type-checking, tests) |
| **Prettier / formatter** | `.prettierrc`, `biome.json` | Style rules the formatter handles |
| **CLAUDE.md** | Root | Coding standards already specified |
| **CONTRIBUTING.md** | Root | Workflow instructions already documented |
| **.cursorrules** | Root | Editor-specific rules already defined |
| **AGENTS.md** | Root | Agent behavior instructions already defined |

### Discovering Existing Enforcement

Before adding any rule, walk through this checklist:

1. **Linter configs** — scan `.eslintrc*`, `pyproject.toml [tool.ruff]`, `.rubocop.yml`, `Cargo.toml [lints]` for rules already enforced
2. **CI workflows** — check `.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml` for automated checks (type-check, lint, test)
3. **Pre-commit hooks** — inspect `.pre-commit-config.yaml`, `.husky/`, `lefthook.yml` for commit-time gates
4. **Editor / agent configs** — read `.cursor/rules/*.mdc`, `agents/rules/*.md`, `.editorconfig`
5. **List enforced rules** — write down every rule already caught automatically

> **Duplicating linter rules = noise.** Only add rules to REVIEW.md that linters CAN'T check — architecture patterns, business-logic invariants, security context that requires human judgment.

### `.rules` and `.mdc` Files

Some repos contain rule files for editors and coding agents:

| Path Pattern | Purpose |
|-------------|---------|
| `.cursor/rules/*.mdc` | Cursor editor rules (MDC format) — loaded automatically by Cursor |
| `agents/rules/*.md` | Agent-specific rules — consumed by coding agents (Copilot, Devin, etc.) |

**Read these before writing REVIEW.md.** They often contain style, naming, and architecture rules that overlap. If a rule is already in `.mdc` or agent rules, don't repeat it in REVIEW.md unless you need different severity or Devin-specific behavior.

### Division of Concerns

| Rule Type | Where It Belongs |
|-----------|-----------------|
| "Indent with 2 spaces" | Formatter config (`.prettierrc`) |
| "No unused variables" | Linter config (`.eslintrc`) |
| "All tests must pass" | CI pipeline |
| "Flag SQL injection in diffs" | `REVIEW.md` |
| "Use service layer for business logic" | `AGENTS.md` |
| "How to submit a PR" | `CONTRIBUTING.md` |

### Python Linter Overlap

If your Python project uses standard linters, skip these categories in REVIEW.md:

| Rule Category | Ruff | mypy | Bandit | Skip in REVIEW.md? |
|---------------|------|------|--------|---------------------|
| Import ordering | ✅ `I` rules | — | — | Yes — Ruff handles it |
| Unused variables | ✅ `F841` | — | — | Yes |
| Type mismatches | — | ✅ | — | Yes — mypy catches these |
| Hardcoded secrets | — | — | ✅ `B105` | Yes — Bandit flags them |
| SQL injection | — | — | ✅ `B608` | Partial — add context-specific rules only |
| Architecture patterns | — | — | — | **No** — only REVIEW.md can enforce these |
| Business-logic invariants | — | — | — | **No** — not checkable by linters |

---

## Tuning Review Quality

### Reducing Noise (Too Many Findings)

If Devin produces too many low-value findings:

1. **Add an Ignore section** — skip generated files, lock files, test snapshots
2. **Remove vague rules** — "write clean code" produces random findings; replace with specific, testable rules
3. **Move style rules to linters** — if ESLint can catch it, don't put it in REVIEW.md
4. **Use suggestive language for minor concerns** — "consider" instead of "must" reduces severity
5. **Keep REVIEW.md under 300 lines** — longer files dilute the signal

### Improving Accuracy (Missing Real Bugs)

If Devin misses important issues:

1. **Add specific rules** — "All API endpoints must validate request bodies using Zod" beats "validate inputs"
2. **Add code examples** — Good/Bad patterns in fenced code blocks help the Bug Catcher match anti-patterns
3. **Use imperative language** — "must", "never", "always" for critical rules
4. **Place critical rules first** — content near the top gets higher weighting
5. **Add Critical Areas section** — reference specific paths that need extra scrutiny with reasoning

### Balancing Coverage

Start with a minimal REVIEW.md (Critical Areas + Security + Conventions + Ignore), then iterate:

1. **Week 1**: Deploy minimal config → observe what Devin catches
2. **Week 2**: Review false positives → add Ignore patterns, soften vague rules
3. **Week 3**: Review false negatives → add specific rules for missed issues
4. **Week 4**: Stabilize → remove rules that overlap with linters or CI

---

## Enterprise Configuration

### Multi-Org Setup

- Settings propagate across all orgs in the enterprise
- Only primary org admins can edit org-wide settings
- Non-primary org members can only self-enroll for auto-review

### Consistent Standards Across Repos

For organizations with multiple repositories:

1. **Create a template REVIEW.md** with cross-cutting security and convention rules
2. **Add repo-specific sections** for each repository's unique patterns
3. **Use monorepo scoping** (subdirectory `REVIEW.md` files) for large repos
4. **Document the template** in your organization's engineering handbook

### PR Description Link

Devin can automatically insert a review link into PR descriptions:

- Enabled by default at `Settings > Review`
- Toggle **"Insert link in PR description"** to control this behavior
- The link takes reviewers directly to the Devin Review view for that PR
