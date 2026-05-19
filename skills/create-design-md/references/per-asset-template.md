# Per-Asset Template — .md + .json pair

The exact body shape for every `NN-slug.md` and `NN-slug.json` file produced. Use this as the structural blueprint.

For complete worked examples:
- Component pair: `references/examples/component-asset-example.md`
- Token pair: `references/examples/token-asset-example.md`

For the JSON shape per asset type: `references/token-format.md`.

---

## The `.md` file — prose

Required sections, in order:

```markdown
# <Asset Name>

> <One sentence: what this is, what it's for.>

**Type:** <token | component | scale | pattern>
**Context:** <tokens | typography | spacing | radius | elevation | motion | layout | components | ...>
**Source:** `<file:path>` (`<selector>` or `<cssVar>`)
**Paired JSON:** `./<NN-slug>.json`

---

## Why

When and why this asset exists in the system. One paragraph answering: *what problem does this asset solve in this design? where does it live in the hierarchy?*

---

## Anatomy / Hierarchy

For **components**, draw an ASCII diagram of the structure with dimensions:

\`\`\`
+-- [container] ----------------------------------------+
|                                                        |
|  +--[icon 16x16]--+  [label 14px]                   |
|  +----------------+                                   |
|                                                        |
|  <-- 36px tall, 16px horiz padding -->               |
+--------------------------------------------------------+
\`\`\`

For **tokens** or **scales**, describe the place in the scale and the surrounding tokens.

For **patterns**, describe the shape of the pattern and its boundary conditions.

---

## States

| State | Behavior |
|---|---|
| Default | <values that always apply> |
| Hover | <changes on hover; transition timing> |
| Focus-visible | <ring / outline values> |
| Active / Pressed | <visual change> |
| Disabled | <opacity, pointer-events, cursor> |
| Loading | <spinner / skeleton or "not-implemented"> |
| Error / aria-invalid | <ring / border changes or "not-implemented"> |
| Selected / data-[state=active] | <changes or "N/A"> |

Use `not-implemented` (exact string) when the source does not implement a state. Use `N/A` only when the state genuinely cannot apply (e.g. `Loading` on a plain color token).

---

## Composition

For **components**: how this asset is used with siblings.

\`\`\`
<Card>
  <CardHeader>
    <CardTitle />
  </CardHeader>
  <CardContent>
    <Input />
  </CardContent>
  <CardFooter>
    <Button variant="ghost">Cancel</Button>
    <Button>Save</Button>    <!-- THIS asset -->
  </CardFooter>
</Card>
\`\`\`

For **tokens**: list the components that consume this token (mirror the JSON's `consumers` array).

---

## Source Evidence

The file path, selector, CSS variable, and (when available) the precise line range that prove this asset's values. If the source is a live URL, record the URL + computed selector.

\`\`\`
File:      src/components/ui/Button.tsx
Lines:     12-48
Selector:  button[data-variant=primary]
CSS var:   --primary
\`\`\`

---

## Cross-references

Other `references/[context]/NN-*.md` files this asset depends on or is depended on by:

- **Depends on:** `../tokens/01-color-primary.md`, `../typography/03-weight-scale.md`, `../radius/01-radius-scale.md`.
- **Depended on by:** `../components/04-card.md` (uses this button in its footer composition).

---

## Notes

Anything important not captured above. Inconsistencies in the source. Hardcoded values that bypass the token system. Browser-specific quirks.
```

---

## The `.json` file — values

The shape varies by asset `type`. Refer to `references/token-format.md` for the exact JSON schema per type. Quick summary:

| Asset type | Required JSON top-level keys |
|---|---|
| token | `$id`, `name`, `type`, `tokenType`, `$type`, `$value`, `$description`, `consumers`, `source` |
| component | `$id`, `name`, `type`, `anatomy`, `props`, `tokens`, `states`, `accessibility`, `source` |
| scale | `$id`, `name`, `type`, `scaleType`, `values`, `$description`, `consumers`, `source` |
| pattern | `$id`, `name`, `type` + pattern-specific keys, `source` |

The `.md` and `.json` cover the **same** asset from two angles: prose (`why`, `anatomy`, `composition`, `source evidence`) and machine values (`tokens`, `states`, `props`, `consumers`). Never duplicate information across them; **cross-reference** instead.

---

## Validation hints

When writing each pair:

- [ ] The `.md` `# Title` is identical to the `.json`'s `name`.
- [ ] The `.md`'s **Type** header matches the `.json`'s `type`.
- [ ] The `.md`'s **Context** header matches the parent directory name.
- [ ] The `.md`'s **Paired JSON** link points to a real `.json` with the same stem.
- [ ] Every reference in the `.md`'s **Cross-references** section points to an existing `references/[context]/NN-*.md` file.
- [ ] In the JSON, every `consumers` `$id` exists in the tree.
- [ ] In the JSON, every `tokens` reference (`{colors.primary}`) resolves to a key in `design.md` frontmatter.
- [ ] States that the source does not implement are explicitly `not-implemented` (not `null`, not missing).

The verification pass (`references/verification.md`) automates these checks.
