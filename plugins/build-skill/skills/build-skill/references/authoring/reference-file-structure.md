# Reference File Structure

How to organize and write reference files that agents can effectively consume.

## Directory layout

```
<skill-name>/
├── SKILL.md                    # Required — main instructions
├── references/                 # Optional — detailed reference material
│   ├── category-a/
│   │   ├── topic-one.md
│   │   └── topic-two.md
│   ├── category-b/
│   │   └── guide.md
│   └── shared-reference.md     # Top-level refs for cross-cutting concerns
├── scripts/                    # Optional — executable helpers
│   └── setup.sh
└── assets/                     # Optional — templates, static files
    └── template.html
```

## File categories

| Category | Directory | Loaded how | Token cost | Use for |
|---|---|---|---|---|
| Main skill | `SKILL.md` | Auto on invocation (Level 2) | ≤5K tokens | Routing, workflow, key patterns |
| References | `references/` | On demand via `Read` (Level 3) | Variable | Detailed guides, specs, examples |
| Scripts | `scripts/` | Executed via `Bash` (not read) | Zero | Deterministic operations, scaffolding |
| Assets | `assets/` | Referenced by path (not read) | Zero | Templates, images, binary files |

## Reference file sizing

| Size | Lines | Use case |
|---|---|---|
| Micro | 30-80 | Single concept, one pattern, quick lookup |
| Standard | 100-250 | Topic guide with examples and edge cases |
| Large | 250-400 | Comprehensive reference for complex topics |
| Oversized | 400+ | Should be split into multiple files |

### Target: 200-400 lines per reference file

This range balances detail with token efficiency. Files under 100 lines often lack enough context for the agent. Files over 400 lines consume excessive tokens and should be split.

## Organizing references into subdirectories

### When to use flat structure

```
references/
├── setup.md
├── configuration.md
├── troubleshooting.md
└── api-reference.md
```

Use flat structure when:
- Total reference files ≤ 6
- No natural grouping exists
- Skill covers a single workflow

### When to use subdirectories

```
references/
├── setup/
│   ├── installation.md
│   └── configuration.md
├── guides/
│   ├── authentication.md
│   └── data-modeling.md
├── troubleshooting/
│   ├── build-errors.md
│   └── runtime-errors.md
└── types/
    ├── request-types.md
    └── response-types.md
```

Use subdirectories when:
- Total reference files > 6
- Natural categories exist (concepts, guides, types)
- The decision tree has clear top-level branches

### Naming conventions for subdirectories

| Convention | Example | Use |
|---|---|---|
| Domain concept | `auth/`, `events/`, `models/` | SDK/API skills |
| Workflow phase | `research/`, `comparison/`, `synthesis/` | Process skills |
| Content type | `guides/`, `examples/`, `types/` | Mixed-content skills |

## Writing a reference file

### Required structure

Every reference file should follow this template:

```markdown
# Topic Title

One-line summary of what this file covers and when to read it.

## [Core content sections]

The main material — patterns, examples, API details, workflow steps.

## [Tables, if applicable]

Quick-reference tables for lookups.

## [Examples]

Practical code or workflow examples.

## [Common mistakes / troubleshooting]

What goes wrong and how to fix it.
```

### Header rules

| Rule | Why |
|---|---|
| Start with `# Title` | Agents use the H1 to confirm they loaded the right file |
| Follow with a one-line purpose | Lets agents verify relevance before reading further |
| Use `##` for major sections | Agents scan H2 headers for navigation |
| Use `###` sparingly | Deep nesting reduces scanability |

### Content rules

| Rule | Why |
|---|---|
| Lead with the most important information | Agents may stop reading partway through |
| Use tables for structured lookups | Faster agent parsing than prose |
| Include 2-4 code examples | Demonstrates expected patterns concretely |
| Show good AND bad examples | Helps agents avoid anti-patterns |
| End with troubleshooting | Catches edge cases the main content missed |

## Cross-referencing between files

Reference files can link to other reference files when topics overlap.

### Inline references

```markdown
For authentication details, see `references/auth/oauth.md`.
```

### Contextual references

```markdown
## Related

- Token refresh: `references/auth/token-refresh.md`
- Error handling: `references/errors/auth-errors.md`
```

### Rules for cross-references

1. Only reference files within the same skill
2. Use relative paths from the skill root
3. Don't create circular dependencies between files
4. Cross-references are secondary — the decision tree is primary routing

## The routing contract

Every reference file must be reachable from SKILL.md through at least one of:

1. **Decision tree** — a leaf node points to the file
2. **Reference routing table** — listed with a "when to read" condition
3. **Minimal reading set** — included in a named reading set

### Reference routing table format

```markdown
## Reference files

| File | When to read |
|---|---|
| `references/auth/oauth.md` | Read when implementing OAuth flow or handling tokens. |
| `references/setup/config.md` | Read when configuring the application for the first time. |
```

### Minimal reading set format

```markdown
## Minimal reading sets

### "I need to add authentication"
- `references/auth/oauth.md`
- `references/auth/token-refresh.md`
- `references/errors/auth-errors.md`
```

## File naming conventions

| Convention | Example | Why |
|---|---|---|
| Kebab-case | `token-refresh.md` | Consistent, URL-safe |
| Descriptive | `streaming-patterns.md` | Self-documenting, no ambiguity |
| Max 50 chars | Yes | Keeps tree output readable |
| No version numbers | `auth.md` not `auth-v2.md` | One current version per topic |
| No redundant prefixes | `oauth.md` not `auth-oauth.md` | Directory name provides context |

## Handling large reference material

When a topic requires more than 400 lines:

### Strategy 1: Split by sub-topic

```
references/events/
├── streaming-patterns.md     # How to subscribe and accumulate
├── session-lifecycle.md      # Session start/end/error events
├── tool-events.md            # Tool execution events
└── permission-events.md      # Permission request events
```

### Strategy 2: Split by depth

```
references/auth/
├── oauth-quickstart.md       # 80 lines — get started fast
└── oauth-advanced.md         # 300 lines — edge cases, refresh, revocation
```

### Strategy 3: Extract lookup tables

```
references/types/
├── event-types.md            # 200 lines — every event type with fields
└── rpc-methods.md            # 150 lines — every RPC method signature
```

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Monolithic reference | Single 1000-line file | Split by sub-topic |
| Empty references | File exists but has no useful content | Remove or fill with real content |
| Duplicate content | Same guidance in SKILL.md and references | Keep in one place, reference from the other |
| Orphaned files | File exists but no route from SKILL.md | Add to decision tree or remove |
| README.md in references | Agents may not know to look for it | Use descriptive names, not generic ones |
| Deep nesting | `references/a/b/c/d/file.md` | Max 2 levels: `references/category/file.md` |
| Mixed concerns | One file covers auth + database + caching | One topic per file |

## Loading discipline

Load only the 3-5 reference files relevant to your current step. Use the SKILL.md routing table to decide which files to read. Loading all references at once exhausts context and makes it impossible to trace which file informed which decision. If you find yourself needing more files mid-step, load them in the next step rather than front-loading everything.

**Rule of thumb:** If you have read more than 5 reference files before producing any output, you are over-loading.

## Keep references one level deep

References should be leaves, not branches. Readers enter via SKILL.md, load one reference, and act — without chasing a chain of further reads.

```
Good:   SKILL.md → references/authoring/testing-methodology.md → act

Bad:    SKILL.md → references/authoring/testing-methodology.md
             → references/authoring/pressure-scenarios.md
             → references/authoring/rationalization-capture.md → act
```

If a reference file ends up routing to a second-tier reference, the content should live in one file, not be split across two. Splitting content only makes sense when the two files are independently useful — in which case SKILL.md should route to both directly.

**Rule:** A reference file may *mention* another reference ("the related discipline is covered in X.md") but must not require reading it to act on the current content. If two files are coupled — you cannot act on A without also reading B — merge them.

## Long files need a table of contents

Reference files over 300 lines should open with a short TOC so the reader can scan for the section they need without reading top-to-bottom:

```markdown
# Testing Methodology

How to test a skill before shipping.

## Contents
- [Testing tiers](#testing-tiers) — choose the tier matching your audience
- [Trigger tests](#test-category-1-triggering-tests) — verify the skill loads
- [Functional tests](#test-category-2-functional-tests) — verify outputs are correct
- [Discipline skills: RED baseline](#discipline-enforcing-skills-need-the-red-phase) — for skills that enforce rules

[Sections follow...]
```

TOCs are not decoration. Agents under context pressure read only the sections they need. A missing TOC forces either reading the whole file (wasteful) or guessing at section positions (unreliable).

## Size guard

Before adding content to any reference file, check its current size:

```bash
wc -l references/path/to/file.md
```

If adding your content would push the file beyond 500 lines, split the new content into a separate file and add a routing entry in SKILL.md. Do not let files grow silently past the size limit — this is the most common cause of oversized reference files.

To inspect existing files:
```bash
find references -name '*.md' -exec wc -l {} + | sort -rn | head -5
```

Any file over 500 lines should be split.

## Routing verification

After completing your reference structure, verify that every file is reachable from SKILL.md:

```bash
for f in $(find references -name '*.md' -type f); do
  grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"
done
```

Any file reported by this command is not routed from SKILL.md and will never be loaded by the agent. Either add a routing entry or remove the file.

## Progressive disclosure checklist

When designing the reference structure, ensure:

- [ ] SKILL.md is self-contained for the 80% use case
- [ ] References handle the remaining 20% edge cases
- [ ] No reference is loaded unless explicitly needed
- [ ] The decision tree provides clear routing to every reference
- [ ] Reading sets bundle related references for common scenarios
- [ ] No circular dependencies between reference files
- [ ] Every file has a clear purpose that doesn't overlap with others
