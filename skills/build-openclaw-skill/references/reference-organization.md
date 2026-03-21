# Reference File Organization

How to organize, size, name, and route reference files for OpenClaw skills using progressive disclosure.

## The progressive disclosure principle

OpenClaw skills use a three-level loading system. SKILL.md (Level 2) is loaded on every invocation. Reference files (Level 3) are loaded only when explicitly requested. This means:

- Put routing logic, decisions, and key patterns in SKILL.md
- Put detailed guides, specs, examples, and long code samples in `references/`
- Never put content in `references/` without a route from SKILL.md

## Directory layout

```
my-skill/
+-- SKILL.md                    # Required — routing, workflow, key patterns
+-- references/                 # Optional — detailed reference material
|   +-- category-a/            # Subdirectory for grouped topics
|   |   +-- topic-one.md
|   |   +-- topic-two.md
|   +-- standalone-guide.md    # Top-level ref for cross-cutting concerns
+-- scripts/                    # Optional — executable helpers
+-- assets/                     # Optional — templates, static files
```

## When to use flat vs. nested structure

### Flat structure (recommended for most skills)

```
references/
+-- setup-guide.md
+-- api-reference.md
+-- troubleshooting.md
```

Use when:
- Total reference files is 6 or fewer
- No natural grouping exists
- Skill covers a single workflow

### Nested structure

```
references/
+-- guides/
|   +-- getting-started.md
|   +-- advanced-usage.md
+-- patterns/
|   +-- error-handling.md
|   +-- performance.md
+-- troubleshooting/
    +-- common-errors.md
    +-- debugging.md
```

Use when:
- Total reference files exceeds 6
- Natural categories exist (guides, patterns, types)
- Decision tree has clear top-level branches

### Nesting rules

- Maximum 2 levels deep: `references/category/file.md`
- Never go deeper: `references/a/b/c/file.md` is too deep
- Each subdirectory should contain 2+ files (don't create a directory for one file)

## File sizing

| Size | Lines | Use case |
|---|---|---|
| Micro | 30-80 | Single concept, one pattern, quick lookup |
| Standard | 100-250 | Topic guide with examples and edge cases |
| Large | 250-400 | Comprehensive reference for complex topics |
| Oversized | 400+ | Should be split into multiple files |

**Target: 100-400 lines per reference file.** Files under 100 lines often lack context for the agent. Files over 400 lines consume excessive tokens and should be split.

### Splitting strategies for oversized files

**Strategy 1 — Split by sub-topic:**

```
references/auth/
+-- oauth-setup.md          # How to configure OAuth
+-- token-management.md     # Refresh, revoke, validate tokens
+-- permission-scopes.md    # Available scopes and their meaning
```

**Strategy 2 — Split by depth:**

```
references/deployment/
+-- quickstart.md           # 80 lines — get deployed fast
+-- advanced.md             # 300 lines — custom configs, scaling, monitoring
```

**Strategy 3 — Extract lookup tables:**

```
references/
+-- api-methods.md          # 200 lines — every method with signature
+-- error-codes.md          # 100 lines — every error code with fix
```

## File naming conventions

| Convention | Example | Why |
|---|---|---|
| Kebab-case | `token-refresh.md` | Consistent, URL-safe |
| Descriptive | `streaming-patterns.md` | Self-documenting |
| Max 50 chars | Yes | Keeps tree output readable |
| No version numbers | `auth.md` not `auth-v2.md` | One current version per topic |
| No redundant prefixes | `oauth.md` not `auth-oauth.md` | Directory name provides context |

## Writing a reference file

Every reference file should follow this structure:

```markdown
# Topic Title

One-line summary of what this file covers and when to read it.

## [Core content sections]

The main material — patterns, examples, specifications.

## [Tables for quick lookup]

Structured reference tables.

## [Examples]

Practical code or workflow examples.

## [Common mistakes / troubleshooting]

What goes wrong and how to fix it.
```

### Content rules

| Rule | Rationale |
|---|---|
| Start with `# Title` | Agents use the H1 to confirm they loaded the right file |
| Follow with a one-line purpose | Lets agents verify relevance before reading further |
| Lead with the most important info | Agents may stop reading partway through |
| Use tables for structured lookups | Faster agent parsing than prose |
| Include 2-4 code examples | Demonstrates patterns concretely |
| Show good AND bad examples | Helps agents avoid anti-patterns |
| End with troubleshooting | Catches edge cases the main content missed |

## Routing every reference file

Every file in `references/` must be reachable from SKILL.md through at least one mechanism:

### 1. Decision tree routing

```markdown
## Decision tree

Need authentication? --> references/auth/oauth-setup.md
Need error handling? --> references/patterns/error-handling.md
```

### 2. Reference routing table

```markdown
## Reference routing table

| File | Read when |
|---|---|
| `references/auth/oauth-setup.md` | Implementing OAuth flow or configuring authentication |
| `references/patterns/error-handling.md` | Adding error recovery or handling API failures |
```

### 3. Minimal reading sets

```markdown
## Minimal reading sets

### "I need to add authentication"
- `references/auth/oauth-setup.md`
- `references/auth/token-management.md`
```

### Routing verification

Run this command from the skill directory to find orphaned reference files:

```bash
for f in $(find references -name '*.md' -type f); do
  grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"
done
```

Any file that appears as "ORPHAN" must either be added to SKILL.md routing or removed.

## Cross-referencing between files

Reference files can link to other reference files when topics overlap.

```markdown
For token refresh details, see `references/auth/token-management.md`.
```

Rules for cross-references:
- Only reference files within the same skill
- Use relative paths from the skill root
- Don't create circular dependencies
- Cross-references are secondary — the decision tree in SKILL.md is the primary router

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Monolithic reference | Single 1000-line file | Split by sub-topic or depth |
| Empty reference files | File exists but lacks useful content | Remove or fill with real content |
| Duplicate content | Same guidance in SKILL.md and references | Keep in one place, reference from other |
| Orphaned files | File exists but no route from SKILL.md | Add to routing or remove the file |
| Deep nesting | `references/a/b/c/file.md` | Max 2 levels deep |
| Mixed concerns | One file covers auth + database + caching | One topic per file |
| README.md in references | Agents may not look for README | Use descriptive filenames |

## Checklist

When designing the reference structure:

- [ ] SKILL.md is self-contained for the 80% use case
- [ ] References handle the remaining 20% edge cases
- [ ] No reference loaded unless explicitly needed
- [ ] Decision tree provides clear routing to every reference
- [ ] Every file in `references/` appears in SKILL.md routing
- [ ] No file exceeds 400 lines
- [ ] No directory deeper than 2 levels
- [ ] No circular dependencies between reference files
- [ ] Every file has a clear purpose that doesn't overlap with others
- [ ] File names are kebab-case, descriptive, under 50 chars
