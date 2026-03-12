# Source Patterns

Use this file when you need to inherit the strongest ideas from earlier build-skills work without dragging over unnecessary bulk.

## Keep these patterns

### 1. Workspace-first evidence gathering

Start with the current working directory.

A skill builder should inspect the local tree, read the real source files, and understand the target repo before importing outside ideas.

### 2. Mandatory remote research for non-trivial work

For new skills, large redesigns, or multi-source merges, outside research should be part of the method, not an optional extra.

### 3. `skills.markdown` as proof of research

The research phase should leave behind a durable artifact that shows what was searched, what was selected, and what was downloaded.

### 4. Comparison before synthesis

The operator should surface a markdown comparison table before proposing the merged strategy.

### 5. Original generation

The final skill should distill patterns and rewrite them for the current repo. It should never be a renamed clone of an earlier `SKILL.md`.

## Avoid these patterns

Do not carry over heavyweight machinery unless the target repo clearly needs it.

Examples to avoid by default:

- scoring or review-loop infrastructure that the target repo does not need
- specialized agent infrastructure that belongs to a separate toolchain
- packaging helpers inside the skill directory
- assets, viewers, and UI extras
- large factory-style reference sprawl
- repo metadata files that do not help the skill run

## Repo-native simplification rule

When contributing to a curated pack, prefer the smallest structure that still preserves the method.

That usually means:

- a lean `SKILL.md`
- a small set of explicitly routed reference files
- no dead files
- no duplicate guidance
- no bundled toolchain unless the workflow truly depends on it

## Selection lens

When translating an earlier source into a new repo-native skill, ask:

1. does this pattern improve how the agent thinks or decides?
2. does this pattern belong in `SKILL.md` or in a reference file?
3. does this pattern fit the target repo’s conventions?
4. would the final skill still feel intentional if this part were removed?

If the answer to the last question is yes, remove it.

## End state

A strong build-skills contribution should feel:

- evidence-led
- comparison-driven
- original
- easy to trust
- clean enough to sit beside other curated skills without adding entropy


---

## Quality spectrum

Not all skill sources are equal. Use this framework to categorize what you find:

### Tier 1: Production-ready reference
- Has a `references/` directory with multiple files
- SKILL.md is under 500 lines with clear routing
- Uses frontmatter correctly
- Demonstrates the skill's own patterns in its structure

### Tier 2: Useful but flawed
- Has good content but structural problems (too long, no references split, inline templates)
- Extract ideas and patterns, but don't copy structure
- Document the flaws in your comparison "avoid" column

### Tier 3: Anti-pattern source
- Over 1000 lines in SKILL.md
- No `references/` directory (everything inline)
- Vague or missing description
- Useful only as a "what not to do" example

## Size filtering rules

Before reading a downloaded skill in detail, check its size:

```bash
# Quick size check
wc -l SKILL.md
find references -name '*.md' -exec wc -l {} + 2>/dev/null | sort -rn | head -5
```

**Guidelines:**
- SKILL.md over 500 lines: Tier 2 at best, likely Tier 3
- No `references/` directory: the skill hasn't been properly decomposed
- Single reference file over 500 lines: content hasn't been split appropriately
- Total reference content over 3000 lines: may indicate scope creep

## Structural signals

When evaluating a downloaded skill, look for these structural indicators:

| Signal | Good | Bad |
|---|---|---|
| SKILL.md line count | Under 300 | Over 500 |
| Reference file count | 5-15 | 0 or 30+ |
| Routing table | Present with "Read when" guidance | Missing or just a file list |
| Frontmatter | Name matches directory, description < 1024 chars | Mismatches or missing |
| Do this / Not that | Present | Missing |
| Output contract | Present with timing hints | Missing or vague |

## Inherit vs. avoid framework

For each downloaded skill in your comparison, explicitly categorize patterns:

| Category | What to record | Example |
|---|---|---|
| **Inherit** | Patterns that align with this skill's standards | "Clean routing table with 'Read when' context" |
| **Adapt** | Good ideas that need structural adjustment | "Useful checklist content, but inline - move to references/" |
| **Avoid** | Anti-patterns or standard violations | "2000-line SKILL.md with everything inline" |

Always have entries in all three categories. A comparison with only "inherit" entries suggests insufficient critical evaluation.
