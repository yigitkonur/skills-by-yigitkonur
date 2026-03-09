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
