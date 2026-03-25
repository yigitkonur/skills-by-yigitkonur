# Corpus Inspection

## Quick overview

After downloading, get an immediate picture of the corpus:

Default auto-categorization puts each downloaded `SKILL.md` at depth 3 (`<output>/<category>/<owner>--<repo>--<skill>/SKILL.md`). The `find ... -maxdepth 3` commands below also work when you used `--no-auto-category`. If `tree` is unavailable, use `find ./corpus -maxdepth 3 -type d | sort`.

```bash
# Total skills downloaded
find ./corpus -name "SKILL.md" -maxdepth 3 | wc -l

# Corpus size
du -sh ./corpus

# Top-level structure
tree -L 2 ./corpus
```

## Per-skill inventory

For each downloaded skill, capture file counts and structure:

```bash
find ./corpus -name "SKILL.md" -maxdepth 3 | sort | while read f; do
  d=$(dirname "$f")
  name=$(basename "$d")
  total=$(find "$d" -type f | wc -l)
  refs=$(find "$d/references" -type f 2>/dev/null | wc -l)
  scripts=$(find "$d/scripts" -type f 2>/dev/null | wc -l)
  lines=$(wc -l < "$f")
  echo "${name}: ${total} files (refs: ${refs}, scripts: ${scripts}, SKILL.md: ${lines} lines)"
done
```

## Quality triage

Classify each skill into tiers before reading deeply. Run these checks:

| Check | Command | Pass criteria |
|---|---|---|
| SKILL.md size | `wc -l SKILL.md` | Under 500 lines |
| Has references | `ls references/ 2>/dev/null` | Directory exists with files |
| Frontmatter valid | First 5 lines of SKILL.md | Has `name:` and `description:` |
| Description length | Character count of description | Under 1024 characters |
| No angle brackets in frontmatter | `head -5 SKILL.md \| grep '[<>]'` | No matches |
| Reference routing exists | `grep 'references/' SKILL.md` | At least one reference route |

**Tier classification:**

- **Tier 1** (read deeply): Passes all checks, has references, clear structure
- **Tier 2** (skim selectively): Passes most checks, missing some structure
- **Tier 3** (anti-pattern only): Fails 3+ checks, useful only as negative example

## Deep reading protocol

For each Tier 1 skill:

1. **Read SKILL.md fully.** Note: trigger boundary, workflow structure, decision rules, output contract, and guardrails.
2. **Tree its `references/` directory.** Note: file count, naming scheme, nesting depth, organization philosophy.
3. **Read the 2-3 most relevant reference files.** Pick by filename relevance and routing logic in SKILL.md.
4. **Check `scripts/`, `rules/`, or `examples/` if present.** These folders often carry automation, constraints, or worked examples that SKILL.md alone does not show.

## Note-taking template

For each skill worth noting, capture:

```markdown
### {skill-name} ({owner}/{repo})

- **Structure:** [flat/nested, SKILL.md length, reference count]
- **Workflow style:** [sequential/branching/iterative]
- **Reference organization:** [how references are decomposed and routed]
- **Strengths:** [what it does well]
- **Weaknesses:** [what it does poorly or violates]
- **Inherit:** [specific patterns worth adopting, with file paths]
- **Avoid:** [specific patterns to reject, with reasoning]
```

## Preparing notes for build-skills

If the corpus will feed into a `build-skills` workflow:

1. Complete the note-taking template for every Tier 1 skill
2. Identify 2-3 skills that are closest to your target design
3. Note specific file paths for patterns you want to inherit
4. Flag quality violations as "avoid" signals
5. Save notes to `skills.markdown` in the workspace root — this is the required research artifact for `build-skills`

## Batch quality check

Run this one-liner to quickly flag quality issues across the entire corpus:

```bash
find ./corpus -name "SKILL.md" -maxdepth 3 | sort | while read f; do
  d=$(dirname "$f")
  name=$(basename "$d")
  lines=$(wc -l < "$f")
  has_refs=$(test -d "$d/references" && echo "yes" || echo "no")
  has_desc=$(head -5 "$f" | grep -q 'description:' && echo "yes" || echo "no")
  has_angles=$(head -5 "$f" | grep -q '[<>]' && echo "FAIL" || echo "ok")
  echo "${name}: ${lines} lines, refs=${has_refs}, desc=${has_desc}, angles=${has_angles}"
done
```

## Corpus cleanup

Remove low-quality or irrelevant skills after triage:

```bash
# Remove a specific skill
rm -rf ./corpus/owner--repo--skill-name/

# Remove all Tier 3 skills (after manual identification)
# List them first, then remove
```

Do not delete skills before completing the triage. You may discover unexpected patterns in skills that initially look weak.
