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
