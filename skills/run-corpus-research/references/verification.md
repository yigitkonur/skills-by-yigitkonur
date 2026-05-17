# Verification

The Phase 7 completion gate. Concrete commands, no ambiguity. Run
before declaring done.

Read this in **Phase 7** after the master summary is written.

## The completion-gate procedure

The orchestrator runs the gate personally; subagents do not. The
gate produces a completion statement appended to or alongside the
master summary.

Steps:

1. Run the structural commands (file counts, MAX-N compliance, no
   junk).
2. Run the template-coverage audit (every axis addressed in every
   `core` pack).
3. Run the link integrity check.
4. Run the source-ledger audit.
5. Run the placeholder-text check.
6. Verify profile pages and master summary present and structured.
7. Write the completion statement.

If any check fails, fix before declaring done. Do not declare done
with known failures.

## Structural commands

```bash
CORPUS=<corpus-root-absolute-path>

# Total file count (informational)
TOTAL=$(find "$CORPUS" -type f -name '*.md' | wc -l)
echo "Total markdown files: $TOTAL"

# No hidden junk
JUNK=$(find "$CORPUS" \( -name '.DS_Store' -o -name 'Thumbs.db' \
       -o -name '*.tmp' -o -name '*.bak' \) | wc -l)
test "$JUNK" -eq 0 && echo "no junk: OK" || echo "JUNK FOUND ($JUNK)"

# MAX 15 per entity folder
for entity in "$CORPUS"/*/; do
  base=$(basename "$entity")
  case "$base" in _meta|_cross) continue;; esac
  count=$(find "$entity" -maxdepth 1 -type f -name '*.md' | wc -l)
  test "$count" -gt 15 && echo "OVER (entity): $base has $count"
done

# MAX 12 per cross-axis folder
for axis in "$CORPUS"/_cross/*/; do
  count=$(find "$axis" -maxdepth 1 -type f -name '*.md' | wc -l)
  test "$count" -gt 12 && echo "OVER (cross): $(basename "$axis") has $count"
done

# MAX 8 per meta
META_COUNT=$(find "$CORPUS"/_meta -maxdepth 1 -type f -name '*.md' | wc -l)
test "$META_COUNT" -gt 8 && echo "OVER (meta): $META_COUNT files"
```

## Template-coverage audit (THE comprehensiveness check)

For every `core` entity, verify every axis in `_meta/03-axes.md` is
addressed — either with a content file in the entity's folder OR
with an "insufficient evidence" entry inside an existing file.

The exact awk patterns depend on the table format used in
`_meta/02-entities.md` and `_meta/03-axes.md`. Adapt the orchestrator's
extraction to whatever shape was written. Conceptually:

```bash
# Read axis slugs (one per line)
AXES=$(extract_axis_slugs "$CORPUS"/_meta/03-axes.md)

# Read core entity slugs (one per line)
ENTITIES=$(extract_core_entity_slugs "$CORPUS"/_meta/02-entities.md)

# For each (entity, axis) pair, verify coverage
for entity in $ENTITIES; do
  for axis in $AXES; do
    file_match=$(find "$CORPUS/$entity" -maxdepth 1 -name "*${axis}*.md" | head -1)
    note_match=$(grep -lE "(insufficient evidence|no evidence).*$axis" \
                 "$CORPUS/$entity"/*.md 2>/dev/null | head -1)
    if [ -z "$file_match" ] && [ -z "$note_match" ]; then
      echo "GAP: entity=$entity, axis=$axis"
    fi
  done
done
```

Every (entity, axis) gap is a Wave 2 retry candidate or an explicit
"surface in master summary as known gap" decision.

## Link integrity check

Walk every markdown file; for every relative link `[text](path)`
inside the corpus, verify the path resolves.

```ruby
require 'pathname'
corpus = ARGV[0] or abort "usage: ruby check_links.rb <corpus-root>"
root = Pathname.new(corpus).realpath
broken = []

Dir.glob("#{root}/**/*.md").each do |file|
  body = File.read(file)
  body.scan(/\[[^\]]+\]\(([^)]+)\)/) do |link|
    target = link[0]
    next if target.start_with?('http://', 'https://', '#', 'mailto:')
    abs = Pathname.new(File.dirname(file)).join(target).cleanpath
    broken << "#{file}: #{target}" unless abs.exist?
  end
end

if broken.empty?
  puts "links OK"
else
  puts "BROKEN LINKS:"
  broken.each { |b| puts "  #{b}" }
  exit 1
end
```

## Source-ledger audit

Every `core` entity has `09-sources.md` (or equivalent) with the
claims ledger.

```bash
for entity in $ENTITIES; do
  if ! ls "$CORPUS/$entity"/09-sources.md "$CORPUS/$entity"/*sources*.md \
       2>/dev/null | head -1 >/dev/null; then
    echo "MISSING ledger: $entity"
  fi
done
```

## Placeholder-text check

Zero `TODO`, `TBD`, `fill later`, `<placeholder>`, `???` strings in
core or cross files.

```bash
PLACEHOLDERS=$(grep -rEnw '(TODO|TBD|fill later|<placeholder>|\?\?\?)' \
               "$CORPUS"/*/  "$CORPUS"/_cross/  2>/dev/null | wc -l)
test "$PLACEHOLDERS" -eq 0 && echo "no placeholders: OK" || \
  echo "PLACEHOLDERS FOUND: $PLACEHOLDERS"
```

## Profile-page presence

Every `core` entity has a profile page at corpus root (only if
profile pages were part of the deliverable).

```bash
for entity in $ENTITIES; do
  if [ ! -f "$CORPUS/$entity.md" ]; then
    echo "MISSING profile: $entity.md"
  fi
done
```

## Master summary present and structured

```bash
test -f "$CORPUS"/_meta/00-master-summary.md && echo "master OK" || \
  echo "master MISSING"

SECTIONS=$(grep -c '^## ' "$CORPUS"/_meta/00-master-summary.md)
test "$SECTIONS" -ge 7 && echo "master sections: $SECTIONS OK" || \
  echo "master sections: $SECTIONS (need ≥7)"
```

The 7 required sections (per `synthesis.md`): Document index,
Critical findings, Cross-domain insights, Action items, Coverage
scope, Open gaps, Recommendation.

## Insufficient-evidence specificity audit

Every "insufficient evidence" entry should name the specific data
gap. Generic "TBD" or "more research needed" is not acceptable.

```bash
grep -rEn 'insufficient evidence' "$CORPUS" | while IFS=: read -r file line content; do
  context=$(sed -n "${line},$((line+5))p" "$file")
  if ! echo "$context" | grep -qE '(specific|gap|unable|missing|public data|no third-party|not documented)'; then
    echo "VAGUE insufficient-evidence: $file:$line"
  fi
done
```

## Completion statement

After all checks pass, write the completion statement at the end
of `_meta/00-master-summary.md`:

```markdown
## Completion statement

- Corpus path: <absolute-path>
- Capture date: <YYYY-MM-DD>
- Total markdown files: <N>
- Entity counts: <core>, <secondary>, <discovered-only>
- Axis count: <M>
- Wave history: <waves run, sub-waves per wave, retries per wave>
- Verification results:
  - Structural: PASS / FAIL (and what)
  - Template coverage: PASS / FAIL (and what)
  - Link integrity: PASS / FAIL (and what)
  - Source ledger: PASS / FAIL (and what)
  - Placeholder check: PASS / FAIL (and what)
  - Profile pages: PASS / FAIL (and what)
  - Master summary: PASS / FAIL (and what)
- Top entry points: <path>, <path>, <path>
- Critical findings: 3-5 bullets (cited)
- Unresolved gaps: 0-N items, each with a specific data-gap
  description and proposed resolution path
```

## What to do when a check fails

- **Structural fail (MAX-N over)**: Split the offending folder
  (`pricing-and-billing/` → `pricing/` + `billing/`) or merge thin
  files. Update `_meta/06-file-budget.md`.

- **Template-coverage gap**: Send the relevant Wave 2 agent back
  with a narrower brief addressing the missing axis. MAX 2
  retries. If still failing, log the gap explicitly in the master
  summary and the entity's `09-sources.md`.

- **Broken link**: Either fix the target (file may have been
  renamed) or remove the dead reference. Re-run.

- **Missing source ledger**: Send the entity's Wave 2 agent back
  with an "every claim must trace to a source" reminder. Or write
  the ledger personally if the underlying claims are already in
  the pack.

- **Placeholder text found**: Replace with content or remove the
  paragraph. Re-run.

- **Vague insufficient-evidence entries**: Either substantiate the
  gap (the agent's evidence may have been incomplete) or rewrite
  the entry to name the specific data gap.

## When to declare done

All seven checks pass AND the master summary's recommendation is
unambiguous to the orchestrator on a fresh-context re-read.

If the recommendation depends on a variable the corpus did not
research (e.g., "depends on whether the team has a Kubernetes
operator on staff"), name that variable as an open question — do
not pad with speculative reasoning.

A corpus declared done is one whose master summary is
fresh-context legible, whose claims are source-traceable, whose
cross-axis comparisons surface contradictions cleanly, and whose
gaps are named specifically with proposed resolution paths.
