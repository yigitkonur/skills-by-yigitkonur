# Observation: F-02/F-10 Bootstrap Divergence

## What happened

**F-02:** SKILL.md says "only bootstrap when missing" but the code block always runs
`playwright-cli install --browser=chrome` unconditionally. This is actually correct
behavior (install ensures browser binary exists) but the framing is confusing.

**F-10:** tabs.md documents `session-stop <name>` cleanup and `config --isolated`
bootstrap patterns that are not mentioned in SKILL.md at all. Following only SKILL.md
misses important isolation and cleanup steps.

## Root cause

M1 (missing step) + S2 (contradiction between documents). The main workflow file
doesn't surface important patterns that exist in reference files.

## Fixes applied

1. Added comment clarifying `install` always runs to ensure browser binary
2. Added `config --isolated` bootstrap snippet
3. Added session-stop cleanup note
