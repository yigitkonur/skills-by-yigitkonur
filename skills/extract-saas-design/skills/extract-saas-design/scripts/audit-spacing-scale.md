# audit-spacing-scale.sh

## Purpose

Count common Tailwind spacing classes and CSS spacing declarations across a target UI root. Use this as evidence for spacing-scale extraction and density-zone analysis.

## Usage

```bash
skills/extract-saas-design/skills/extract-saas-design/scripts/audit-spacing-scale.sh /path/to/target-root
```

Run it against the target codebase root or snapshot root, not the skills repo.

## Output Interpretation

- **Tailwind Spacing Class Counts** counts `p-*`, `m-*`, `gap-*`, and `space-*` classes.
- **CSS Spacing Declaration Counts** counts `padding`, `margin`, `gap`, `row-gap`, and `column-gap` declarations.
- **Source Lines With Arbitrary Pixel Spacing** highlights arbitrary Tailwind pixel classes and literal CSS pixel spacing.

## Limitations

- This script counts usage; it does not convert Tailwind units to pixels or judge whether values are correct.
- It scans common UI file extensions and supports HTML/CSS snapshot mode.
- It cannot identify semantic spacing intent by itself; map frequent values back to components and layouts in the docs.
