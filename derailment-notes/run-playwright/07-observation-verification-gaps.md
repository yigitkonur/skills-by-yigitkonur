# Observation: F-06/F-07/F-08 Verification Gaps

## What happened

**F-06:** `mousewheel 0 900` should scroll down (deltaY=900) but the CLI swaps
parameters internally, causing horizontal scroll. This is an external tool bug
but should be documented as a known quirk.

**F-07:** Step 5 says "inspect returned artifact files" but never explains that
commands like `console`, `network`, `snapshot` write to files and print paths.
A literal reader expects inline output.

**F-08:** `--clear` flags produce no visible output (silent success). Undocumented
behavior causes confusion about whether the command worked.

## Root cause

O2 (external tool behavior) for F-06 and F-08. M4 (missing prerequisite) for F-07.

## Fixes applied

1. screenshots.md: Added mousewheel parameter-order warning
2. SKILL.md step 5: Added artifact-inspection callout
3. SKILL.md + debugging.md: Added --clear silent-success notes
