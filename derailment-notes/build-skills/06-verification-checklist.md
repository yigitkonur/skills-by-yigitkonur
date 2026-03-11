# Derailment Test: Verification Checklist

## Pre-fix state verification

Before applying any fixes, verify these baseline conditions:

```bash
# 1. Current line count of SKILL.md
wc -l skills/build-skills/SKILL.md
# Expected: ~285 lines (well under 500)

# 2. Reference routing completeness
# List all reference files
find skills/build-skills/references -name "*.md" -type f | sort

# Check each is mentioned in SKILL.md
for f in $(find skills/build-skills/references -name "*.md" -type f); do
  basename_f=$(basename "$f")
  if ! grep -q "$basename_f" skills/build-skills/SKILL.md; then
    echo "ORPHAN: $f"
  fi
done

# 3. No angle brackets in frontmatter
head -20 skills/build-skills/SKILL.md | grep -n '[<>]'
# Expected: no output

# 4. Name matches directory
grep '^name:' skills/build-skills/SKILL.md
# Expected: name: build-skills

# 5. No reserved names
grep -i 'claude\|anthropic' skills/build-skills/SKILL.md | head -5
# Expected: no matches in name/description fields
```

## Post-fix verification

After applying all fixes, verify:

```bash
# 1. Still under 500 lines
wc -l skills/build-skills/SKILL.md
# Expected: ~315 lines

# 2. No new orphaned references
for f in $(find skills/build-skills/references -name "*.md" -type f); do
  basename_f=$(basename "$f")
  if ! grep -q "$basename_f" skills/build-skills/SKILL.md; then
    echo "ORPHAN: $f"
  fi
done
# Expected: no output

# 3. All friction point fixes applied
# F-03: skill-dl prerequisite check exists
grep -c 'skill-dl --version\|skill-dl.*available\|Verify.*skill-dl' skills/build-skills/SKILL.md
# Expected: >= 1

# F-06: skill-dl search example with argument format
grep -c 'skill-dl search.*keyword\|skill-dl search.*mcp' skills/build-skills/SKILL.md
# Expected: >= 1

# F-13: Checklist routing split between Step 7 and Step 9
grep -c 'master-checklist' skills/build-skills/SKILL.md
# Expected: >= 1 (in Step 9 area, not Step 7)

# F-14: Creation vs revision conditional for trigger tests
grep -c 'revision\|new skill\|creation' skills/build-skills/SKILL.md
# Expected: >= 1 in Step 8 area

# 4. No stale references to old wording
grep -c 'Emit.*skills\.markdown' skills/build-skills/SKILL.md
# Expected: 0 (changed to "Create")

# 5. Artifact output section exists
grep -c 'Artifact output\|artifact.*output' skills/build-skills/SKILL.md
# Expected: >= 1

# 6. Frontmatter unchanged
head -5 skills/build-skills/SKILL.md
# Expected: same name and description
```

## Consistency check: no contradictions introduced

```bash
# Check that workspace-first discipline is preserved
grep -n 'workspace.*first\|local.*evidence.*first\|Workspace first' skills/build-skills/SKILL.md
# Expected: still present in non-negotiable rules

# Check comparison table still required
grep -n 'comparison.*table\|Comparison.*before' skills/build-skills/SKILL.md
# Expected: still present in non-negotiable rules and Step 5

# Check progressive disclosure still enforced
grep -n 'progressive.*disclosure\|references.*routing' skills/build-skills/SKILL.md
# Expected: still present
```
