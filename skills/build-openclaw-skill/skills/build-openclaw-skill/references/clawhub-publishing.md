# ClawHub Publishing Guide

How to publish OpenClaw skills to ClawHub, the marketplace for discovering and sharing skills.

## What is ClawHub

ClawHub is the official marketplace for OpenClaw skills. Developers publish skills to ClawHub, and users install them via the `clawhub install` command. It provides discovery, versioning, and quality signals for the skill ecosystem.

## Installing skills from ClawHub

Users install published skills with:

```bash
clawhub install slug
```

Where `slug` is the unique identifier for the skill on ClawHub (typically `author/skill-name`).

## Publishing workflow

### 1. Pre-publish quality check

Before publishing, verify your skill meets all quality standards. Run through this checklist:

**Content quality:**

- [ ] SKILL.md has valid frontmatter with `name` and `description`
- [ ] Description follows "Use skill if you are..." formula
- [ ] Description contains 3+ trigger phrases
- [ ] Decision tree routes to all reference files
- [ ] No orphaned reference files (all routed from SKILL.md)
- [ ] All examples are tested and working
- [ ] Common pitfalls table covers real mistakes
- [ ] Guardrails prevent agent misuse

**Structural quality:**

- [ ] Directory name matches frontmatter `name` exactly
- [ ] All files use kebab-case naming
- [ ] Reference files are 100-400 lines each
- [ ] SKILL.md is under 500 lines
- [ ] No binary files or large assets
- [ ] No secrets, credentials, or personal data
- [ ] Metadata field (if present) uses single-line JSON

**Testing:**

- [ ] Skill load was confirmed in the runtime before counting test results
- [ ] 5+ should-trigger and 5+ should-NOT-trigger queries passed
- [ ] Primary workflow completes without error
- [ ] Self-check test passes ("When would you use this skill?")

### 2. Prepare the repository

Skills are published from GitHub repositories. Structure your repo correctly:

**Single-skill repository:**

```
my-skill/
+-- SKILL.md
+-- references/
|   +-- guide-a.md
|   +-- guide-b.md
+-- LICENSE
+-- README.md
```

**Multi-skill repository (skill pack):**

```
skills-collection/
+-- README.md
+-- LICENSE
+-- skills/
    +-- skill-a/
    |   +-- SKILL.md
    |   +-- references/
    +-- skill-b/
        +-- SKILL.md
        +-- references/
```

### 3. Required repository files

| File | Required | Purpose |
|---|---|---|
| `SKILL.md` | Yes | The skill itself |
| `references/` | If referenced | Detailed reference material |
| `LICENSE` | Recommended | Legal clarity (Apache-2.0 or MIT recommended) |
| `README.md` | Recommended | Human-readable documentation for the repo |
| `.gitignore` | Recommended | Exclude OS/editor artifacts |

### 4. Write the README

The README is the landing page for human users browsing ClawHub.

```markdown
# Skill Name

One-line description matching the SKILL.md description.

## What this skill does

2-3 sentences expanding on the description.

## Quick install

clawhub install author/skill-name

## What's included

- SKILL.md — main instructions with decision tree
- references/ — N files covering [topics]

## Usage

Invoke with `/skill-name` or let the agent auto-detect from your prompt.

## Requirements

- [Binary requirements from metadata]
- [Environment variables from metadata]

## License

[License name]
```

### 5. Submit to ClawHub

Submit your skill via the ClawHub interface or CLI. The platform indexes skills by searching standard paths:

- `skills/{name}/`
- `{name}/`
- `.skills/{name}/`
- `.openclaw/skills/{name}/`
- `src/skills/{name}/`

Frontmatter is parsed for `name` and `description`, which populate the ClawHub listing.

## Discovery optimization

### How ClawHub ranks skills

| Signal | Impact | How to optimize |
|---|---|---|
| Description quality | High | Include specific trigger phrases and technology keywords |
| Install count | High | Grow organically through quality |
| Search relevance | Medium | Name and description match common search queries |
| Repo stars | Medium | Good README, solve real problems |
| Author reputation | Low | Multiple published skills signal experience |

### Keywords strategy

Include keywords that match how users think about the problem:

```yaml
description: Use skill if you are building TypeScript REST APIs with Express.js and need route scaffolding, middleware configuration, error handling, and OpenAPI documentation. Trigger phrases include "express api", "REST API", "route scaffolding", "openapi", "middleware".
```

The keywords match searches for: "express api", "REST API", "typescript api", "openapi", "middleware".

## Versioning

### Semantic versioning (SemVer)

```
MAJOR.MINOR.PATCH

1.0.0 --> Initial stable release
1.1.0 --> New reference files added
1.2.0 --> New decision tree branches
2.0.0 --> Breaking change: restructured references, renamed files
```

### What counts as a breaking change

| Change | Breaking? | Why |
|---|---|---|
| Adding new reference files | No | Existing workflows unaffected |
| Reorganizing into subdirectories | Yes | File paths change |
| Renaming the skill directory | Yes | Slash command changes |
| Changing frontmatter `name` | Yes | Lookup key changes |
| Updating content in existing files | No | Paths stable |
| Removing reference files | Yes | Skills referencing them break |

### Version tracking

Use frontmatter `version` field plus git tags:

```yaml
---
name: my-skill
description: ...
version: 1.2.0
---
```

Tag the release in git:

```bash
git tag v1.2.0
git push origin v1.2.0
```

## Community standards

### Quality expectations

The OpenClaw skill community values:

1. **Specificity over breadth** — a skill that does one thing well beats one that covers everything poorly
2. **Evidence over opinion** — claims should be traceable to verified sources
3. **Progressive disclosure** — load minimal context, expand on demand
4. **Original synthesis** — distill patterns, don't clone existing skills
5. **Maintenance commitment** — published skills should stay current

### Content guidelines

| Do | Don't |
|---|---|
| Include working code examples | Include untested examples |
| Cite sources for best practices | Present opinions as facts |
| Version your frontmatter | Ship without version tracking |
| Keep reference files focused | Create monolithic reference dumps |
| Test with the target agent | Assume it works without testing |

## Maintenance after publishing

### Active maintenance schedule

| Frequency | Action |
|---|---|
| Monthly | Check for outdated API references or deprecated patterns |
| Quarterly | Review install metrics, update based on user issues |
| On dependency release | Verify examples still work with new versions |
| On user report | Fix confirmed issues within a week |

### Deprecation process

When retiring a skill:

1. Add a deprecation notice to SKILL.md description
2. Update description to mention the replacement
3. Keep the skill available for 6 months
4. Archive the repository after the grace period

```yaml
---
name: old-skill
description: "[DEPRECATED] Use new-skill instead. This skill is no longer maintained."
---
```

## Common publishing mistakes

| Mistake | What happens | Fix |
|---|---|---|
| No LICENSE file | Users uncertain about usage rights | Add MIT or Apache-2.0 |
| Secrets in repo | Credentials exposed publicly | Remove and rotate immediately |
| Untested skill | Users hit errors on first use | Run full test suite before publishing |
| Vague README | Users don't understand the skill | Write clear what/install/usage sections |
| Missing version | No way to track updates | Add `version` to frontmatter, use git tags |
| Orphaned references | ClawHub indexes the skill but references break | Run routing verification before publishing |
| No `.gitignore` | OS artifacts committed | Add standard .gitignore |
| Description too vague | Skill doesn't appear in relevant searches | Add trigger phrases and technology keywords |
