# Skill Organization Patterns

When to split, when to combine, and how to structure skills for different scales.

## The fundamental question

> Should this be one skill or multiple skills?

### Split into separate skills when

- The workflows are independent — invoking one never requires the other
- Different trigger phrases activate each workflow
- The combined SKILL.md would exceed 500 lines
- Reference files don't overlap between workflows
- Different `allowed-tools` are needed for each workflow

### Keep as one skill when

- The workflows share reference files
- Users naturally combine the tasks in one session
- The combined SKILL.md stays under 300 lines
- Splitting would create skills with only 1-2 reference files each
- The description would be nearly identical for both

## Skill complexity tiers

### Tier 1: Micro-skill (1-3 files)

```
simple-task/
├── SKILL.md                    # 50-150 lines, self-contained
└── references/
    └── edge-cases.md           # Optional, for uncommon scenarios
```

**Characteristics**:
- Single workflow, single output
- Most content lives in SKILL.md
- 0-2 reference files
- Description is highly specific

**Example**: A skill that generates a specific file type (Dockerfile, CI config).

### Tier 2: Standard skill (4-10 files)

```
standard-workflow/
├── SKILL.md                    # 150-300 lines, with decision tree
└── references/
    ├── setup.md
    ├── patterns.md
    ├── troubleshooting.md
    └── api-reference.md
```

**Characteristics**:
- 2-3 related workflows
- Decision tree with 3-5 top-level branches
- 3-8 reference files, possibly with 1 subdirectory
- Minimal reading sets for 2-3 scenarios

**Example**: A skill for a specific library (React Query, Prisma).

### Tier 3: Comprehensive skill (10-30 files)

```
full-framework/
├── SKILL.md                    # 250-400 lines, extensive decision tree
└── references/
    ├── setup/
    │   ├── installation.md
    │   └── configuration.md
    ├── guides/
    │   ├── auth.md
    │   ├── data.md
    │   └── api.md
    ├── patterns/
    │   ├── advanced-pattern.md
    │   └── scaling.md
    └── types/
        ├── request-types.md
        └── response-types.md
```

**Characteristics**:
- Full SDK or framework coverage
- Decision tree with 6-10 top-level branches
- 10-30 reference files in 3-5 subdirectories
- Minimal reading sets for 5-7 scenarios
- Pitfalls table with 8+ entries

**Example**: A skill for a full SDK (Copilot SDK, Stripe API).

### Tier 4: Skill pack (multiple skills, shared repo)

```
skills/
├── skill-a/
│   ├── SKILL.md
│   └── references/
├── skill-b/
│   ├── SKILL.md
│   └── references/
└── skill-c/
    ├── SKILL.md
    └── references/
```

**Characteristics**:
- Related but independent skills in one repository
- Each skill has its own SKILL.md and references
- No shared reference files between skills
- README.md at repo root describes the collection

**Example**: A curated skill pack for a team or domain.

## Content placement rules

### What belongs in SKILL.md

| Content type | Why in SKILL.md |
|---|---|
| Decision tree | Primary routing — must be immediately visible |
| Quick start (one example) | Covers the 80% use case without loading references |
| Key patterns (2-5) | Essential patterns every user needs |
| Pitfalls table | Quick-reference for common mistakes |
| Minimal reading sets | Routing guide for specific scenarios |
| Guardrails | Constraints that always apply |

### What belongs in references/

| Content type | Why in references/ |
|---|---|
| Detailed API docs | Too large for SKILL.md, loaded only when needed |
| Exhaustive examples | Multiple variants of a pattern |
| Type definitions | Lookup tables for types and interfaces |
| Configuration guides | Step-by-step for specific setups |
| Troubleshooting guides | Comprehensive error resolution |
| Advanced patterns | Used by a minority of users |

### What belongs in scripts/

| Content type | Why in scripts/ |
|---|---|
| Scaffolding generators | Deterministic file creation |
| Validation scripts | Checking output correctness |
| Search/discovery scripts | Automating research workflows |
| Data transformation | Converting between formats |

### What does NOT belong in a skill

| Content type | Why not |
|---|---|
| Package.json / build config | Skills are not npm packages |
| CI/CD pipelines | Belongs in the consuming repo |
| Test suites | Skills are documentation, not code |
| Binary assets | Cannot be read by agents |
| Node_modules or dependencies | Skills are self-contained docs |

## Splitting a growing skill

When a skill outgrows its tier, follow this sequence:

### Step 1: Audit content

Count lines in SKILL.md and each reference file. Identify:
- Sections in SKILL.md that exceed 50 lines → candidate for reference extraction
- Reference files exceeding 400 lines → candidate for splitting
- Reference files with unrelated content → candidate for separation

### Step 2: Extract to references

Move large SKILL.md sections to reference files:

```
Before:
  SKILL.md (500 lines) — includes 200-line API guide

After:
  SKILL.md (320 lines) — references the guide
  references/api-guide.md (200 lines) — extracted content
```

### Step 3: Group into subdirectories

When reference count exceeds 6:

```
Before:
  references/
  ├── auth.md
  ├── tokens.md
  ├── setup.md
  ├── config.md
  ├── errors.md
  ├── migration.md
  ├── advanced.md
  └── types.md

After:
  references/
  ├── auth/
  │   ├── auth.md
  │   └── tokens.md
  ├── setup/
  │   ├── installation.md
  │   └── configuration.md
  └── troubleshooting/
      ├── errors.md
      └── migration.md
```

### Step 4: Consider skill splitting

If the decision tree has branches that never intersect, those branches may be separate skills:

```
Before: one skill with branches for "create app" and "deploy app"
After:  create-app/ and deploy-app/ as separate skills
```

Split only when the workflows are genuinely independent.

## File count guidelines

| Metric | Target | Hard limit |
|---|---|---|
| Reference files per skill | 5-15 | 40 |
| Subdirectories in references/ | 2-5 | 8 |
| Files per subdirectory | 2-6 | 10 |
| Scripts | 0-2 | 5 |
| Total files per skill | 8-20 | 50 |

## Dependency between skills

Skills in a pack should be independent. If skill A requires skill B:

1. **Preferred**: Merge them into one skill
2. **Acceptable**: Reference skill B from skill A's description
3. **Avoid**: Shared reference files between skills (creates coupling)

## Evolving a skill over time

| Phase | Action |
|---|---|
| v0.1 — Draft | Single SKILL.md, no references. Get the workflow right. |
| v0.5 — Working | Add 2-3 reference files for the most common edge cases. |
| v1.0 — Stable | Full decision tree, 5-10 references, reading sets, pitfalls. |
| v1.x — Growing | Add references as new topics arise. Reorganize into subdirectories if needed. |
| v2.0 — Major | Rethink the decision tree. Split if workflows have diverged. |
