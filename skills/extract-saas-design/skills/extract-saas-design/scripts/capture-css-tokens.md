# capture-css-tokens.sh

## Purpose

Inventory CSS custom property definitions/usages and color-space signals from a target UI root. Use this as evidence for color token extraction, especially when the target may be a plain HTML/CSS snapshot.

## Usage

```bash
skills/extract-saas-design/skills/extract-saas-design/scripts/capture-css-tokens.sh /path/to/target-root
```

Run it against the target codebase root, not the skills repo.

## Output Interpretation

- **Color Space Counts** shows detected `oklch`, `hsl`, `rgb`, and hex usage.
- **CSS Custom Property Definitions** lists unique `--token: value` definitions with counts.
- **CSS Custom Property Usage Counts** lists `var(--token)` usage frequency.
- **Chart And Sidebar Token Lines** highlights `--chart-*` and `--sidebar-*` definitions/usages for dashboard-specific token scopes.

## Limitations

- This is an inventory helper, not a resolver. Follow `var()` chains manually in the extraction docs.
- It scans common UI file extensions and ignores generated/vendor folders.
- It does not evaluate runtime-computed styles; use browser evidence when runtime values matter.
