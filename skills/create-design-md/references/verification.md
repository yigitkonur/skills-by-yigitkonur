# Verification — Before Claiming Done

Six rungs. Claim only the rung you reached. Never claim a higher rung than you actually verified.

---

## Rung 1 — Structure exists

- [ ] `design.md` exists at the target root.
- [ ] `references/` directory exists at the target root.
- [ ] At least the mandatory contexts have directories: `tokens/`, `typography/`, `components/`.
- [ ] Every per-asset file has a matching pair: for every `NN-slug.md`, there is a `NN-slug.json` with the same stem (and vice-versa).

Failure mode: orphan files. Fix by either deleting the orphan or producing its partner.

```bash
# Orphan detector (run at target root)
find references -name "*.md" | sed 's/\.md$//' | sort > /tmp/md.list
find references -name "*.json" | sed 's/\.json$//' | sort > /tmp/json.list
diff /tmp/md.list /tmp/json.list
```

Expected: empty diff.

---

## Rung 2 — Frontmatter validity

- [ ] `design.md` opens with `---` and closes with `---` for the frontmatter block.
- [ ] Frontmatter parses as valid YAML (lint with any YAML parser).
- [ ] `name:` is set.
- [ ] Every `colors:` entry is a hex string.
- [ ] Every `typography:` entry has at least `fontFamily`, `fontSize`, `fontWeight`.
- [ ] Every `rounded:` entry is a dimension string.
- [ ] Every `spacing:` entry is a dimension string or number.
- [ ] Every `components:` entry uses only valid component properties (`backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`).
- [ ] Every `{path.to.token}` reference resolves to a frontmatter path.

Failure mode: malformed YAML, broken references. Fix by re-parsing per `references/design-md-spec.md`.

```python
# Quick frontmatter parse check
import re, yaml
with open('design.md') as f: content = f.read()
m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
fm = yaml.safe_load(m.group(1))
assert 'name' in fm
```

---

## Rung 3 — Section completeness

- [ ] `design.md` body contains all mandatory `##` sections in canonical order: Overview, Colors, Typography, Components, References Index.
- [ ] Optional sections (Layout, Elevation & Depth, Shapes, Motion, Accessibility, Do's and Don'ts) are either present in canonical position OR explicitly skipped with a one-line `> This design does not implement <topic>.` note under the heading.
- [ ] Section order matches the canonical order in `references/design-md-spec.md` (no reordering).

```bash
# Section header extractor (run at target root)
grep -nE '^## ' design.md
```

Expected output ordered: `## Overview`, `## Colors`, `## Typography`, `## Layout`, `## Elevation & Depth`, `## Shapes`, `## Motion`, `## Components`, `## Accessibility`, `## Do's and Don'ts`, `## References Index` (or a subset, but in this order).

---

## Rung 4 — Every asset is linked from design.md

- [ ] For every `references/[context]/NN-*.md` file, `design.md` contains at least one inline link to it OR a row in `## References Index`.
- [ ] For every `references/[context]/NN-*.json` file, `design.md` contains at least one mention (typically in `## References Index`).
- [ ] Every component named in `## Components` has a corresponding `references/components/NN-*.md` and `.json`.
- [ ] Every color token in frontmatter `colors:` has a corresponding `references/tokens/NN-color-*.md` and `.json` (or grouped asset like `01-color-primary` covering the primary token).
- [ ] Every typography token in frontmatter `typography:` has a corresponding `references/typography/NN-*.md` and `.json`.

```bash
# Link verifier (run at target root)
find references -name "*.md" -type f | while read f; do
  rel="${f#./}"
  grep -qF "$rel" design.md || echo "ORPHAN: $rel not linked from design.md"
done
```

Expected: no `ORPHAN:` output.

---

## Rung 5 — Cross-reference graph

For every JSON in the tree:

- [ ] Every `$id` in any `consumers` array matches a real asset's `$id` in the tree.
- [ ] Every `$id` in any `dependsOn` array matches a real asset's `$id` in the tree.
- [ ] Every token referenced from a component's `tokens` block (`"{colors.primary}"`) resolves to a `design.md` frontmatter path.
- [ ] For every component asset, every token its `tokens` block references has a `consumers` array on the token side that contains this component's `$id`.
- [ ] States in component JSONs are explicitly defined or `"not-implemented"` (never `null`, never missing).

Failure mode: drift between component → token references and token → consumers backlinks. Fix by walking the graph: for each component, add the component's `$id` to the `consumers` array of every token it references.

---

## Rung 6 — Reproducer test

The ultimate test:

> Given only `design.md` plus the `references/[context]/` tree (no access to the source), could a fresh agent reproduce the design's intent and concrete values without guessing?

Self-administer:

1. **Spawn a fresh-context subagent** (e.g. `claude -p` or a subagent invocation) with no chat history.
2. Hand it the original goal: *"Reproduce a UI matching this design system based on these files."*
3. Read the questions it asks. If any question would require guessing at a value that should have been in the spec, that's a gap.
4. Fix the gap in the appropriate asset's `.md` and `.json`, re-run.

Acceptable outputs from the fresh agent:

- "What page layout do you want me to start with?" — UI direction question, fine.
- "Which copy should I use?" — content question, fine.

Unacceptable outputs:

- "What's the hover color for the primary button?" — design.md should have answered this.
- "Is there a dark mode?" — design.md should have answered this with `not-implemented` or values.
- "What's the focus ring style?" — design.md should have answered this.

---

## Quick acceptance bar

```text
Rung 1 — files exist, pairs match                    : structural
Rung 2 — frontmatter parses                          : machine-readable
Rung 3 — sections in canonical order                 : navigable
Rung 4 — every asset linked from design.md           : referenced
Rung 5 — cross-references resolve                    : auditable
Rung 6 — reproducer can rebuild without guessing     : complete
```

Claim "done" only at Rung 6.

---

## Common failure modes and fixes

| Failure | Fix |
|---|---|
| Asset `.json` has `states: { ... default, hover, focus }` — `disabled`, `loading`, `error` missing. | Add them as `not-implemented` if source doesn't implement. |
| `consumers` arrays are empty everywhere. | Walk every component JSON's `tokens` block; for each referenced token, add this component's `$id` to that token's `consumers` array. |
| Component listed under `## Components` but no asset pair exists. | Either remove from `design.md` or write the asset pair. |
| Asset pair exists but not linked from `design.md`. | Add a link in the appropriate section + a row in `## References Index`. |
| Token reference `{colors.brand}` but frontmatter has `colors.primary` (no `brand`). | Fix the reference to match the frontmatter, or rename the frontmatter token to match the source's naming. |
| Hover/active states identical to default. | Verify with source. If truly identical, write the same values; if source has different values, fix the capture. |
| Source has dark mode but `mode` field is missing on color tokens. | Capture dark values from source; populate `mode: { light, dark }`. |
| Generated `design.md` exceeds reasonable length (>500 lines of body) | Move per-component descriptions to the asset's `.md`; keep `design.md` lean — its job is routing, not full documentation. |
