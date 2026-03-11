# Comparison Workflow

Use this file when multiple sources influence the design.

Do not combine patterns in your head and only show the conclusion.

## The sequence

Always separate the work into four layers:

1. **Evidence** — what the local and remote sources actually contain
2. **Comparison** — where those sources agree, differ, overlap, or conflict
3. **Selection** — what should be inherited, rejected, or simplified
4. **Generation** — the new or revised skill artifacts

If those layers blur together, the result becomes harder to trust.

## Required comparison table

Before synthesis, create a markdown table with columns like these:

| Source | Focus | Strengths | Gaps | Relevant paths or sections | Inherit / avoid |
|---|---|---|---|---|---|

For richer tasks, expand the table with:

- lifecycle coverage
- bundled resources
- trigger quality
- repo-fit observations

## What counts as a good row

A good comparison row does all of the following:

- names the source clearly
- explains what that source is best at
- states what it is weak at or too heavy on
- points to concrete paths or sections
- ends with a decision, not just an observation

Example decision language:

- inherit the comparison discipline, avoid the extra packaging surface
- inherit the trigger language pattern, avoid the bulky body
- inherit the reference routing, avoid duplicate guidance

## Decision rules

When choosing what to keep:

1. prefer patterns that improve decision quality, clarity, or reuse
2. prefer patterns that fit the target repo’s conventions
3. reject patterns that add toolchain bulk without helping the requested outcome
4. reject duplication between `SKILL.md` and `references/`
5. reject anything that makes the result feel copied instead of synthesized

## Synthesis handoff

After the table exists, summarize the strategy in plain language:

- what evidence is strongest
- what patterns will be inherited
- what will be avoided
- how the new result stays original
- which files should exist in the final skill

Only then should you draft or revise the actual skill files.

## Anti-patterns

Avoid these failure modes:

- skipping the table because the sources "already look similar"
- citing broad impressions instead of concrete paths
- inheriting everything from the most detailed source
- using the comparison section as a hidden draft of the final skill
- deciding on the final structure before the evidence is compared


---

## Per-skill notes template

Use this template when examining each downloaded skill. Fill it out before writing your comparison table row:

```markdown
### [Skill Name]
- **Source:** [GitHub URL or skill-dl ID]
- **SKILL.md lines:** [count]
- **Has references/?:** [yes/no, file count]
- **Tier:** [1/2/3 per source-patterns.md quality spectrum]

#### Strengths (inherit)
- [specific pattern with file reference]

#### Weaknesses (avoid)
- [specific anti-pattern with evidence]

#### Adaptable ideas
- [pattern that needs structural adjustment]
```

## Comparison table columns

Your markdown comparison table should include these columns:

| Column | Purpose | Example |
|---|---|---|
| Skill name | Identifier | `build-mcp-server` |
| Source | Where found | `skill-dl` / GitHub / skills.sh |
| Tier | Quality level | 1 / 2 / 3 |
| Lines (SKILL.md) | Size indicator | 287 |
| Ref files | Decomposition quality | 12 |
| Key strength | Best inherit candidate | "Clean MCP tool routing" |
| Key weakness | Primary avoid signal | "No output contract" |
| Verdict | Use decision | Inherit routing / Avoid structure |

## Completeness gate

Before moving from comparison (Step 5) to synthesis (Step 7), verify:

- [ ] At least 3 skills compared in detail (not just listed)
- [ ] Every comparison row has both "strength" and "weakness" entries
- [ ] At least one Tier 1 reference identified (or documented why none exist)
- [ ] At least 2 "avoid" patterns documented across all sources
- [ ] Per-skill notes exist for every skill in the comparison table
- [ ] Quality tiers assigned using the spectrum from `source-patterns.md`

If fewer than 3 skills are available, document the search terms used and why more weren't found. A thin comparison is acceptable when justified; a fabricated one never is.
