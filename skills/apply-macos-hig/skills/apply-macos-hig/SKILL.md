---
name: apply-macos-hig
description: "Use skill if you are building, reviewing, or designing macOS SwiftUI or AppKit interfaces and need HIG-compliant component specs, spacing values, color tokens, accessibility rules, or platform patterns."
---

# macOS Human Interface Guidelines — Complete Design System Reference

Definitive reference for building native macOS applications. Backed by 21 exhaustively sourced reference documents totaling 13,286 lines — every claim traced to Apple HIG, AppKit API docs, SDK headers, WWDC sessions, or verified practitioner sources. Covers macOS Sequoia (15) through Tahoe (26) including Liquid Glass, Compositional Layout, SF Symbol effects, AutoFill/Passkeys, and window tiling.

The skill body below contains **critical values you need constantly** — spacing scale, typography sizes, component decision trees, and core patterns. For detailed specs, **read the corresponding reference file** from the Reference Index. Do not guess dimensions or behaviors — look them up.

---

## 1. The Three Laws of macOS UI

1. **Every action must be in the menu bar.** Toolbars can be hidden/customized. The menu bar is the source of truth for discoverability. Every toolbar action needs a menu bar equivalent.

2. **Standard keyboard shortcuts are sacred.** `Cmd-Q` quits, `Cmd-W` closes, `Cmd-,` opens Settings, `Cmd-Z/X/C/V/A/S/F` do what users expect. Breaking any of these is immediately noticed.

3. **Settings take effect immediately.** No Save/Cancel/Apply buttons in preferences. macOS settings are live.

---

## 2. Spacing Scale

macOS uses an 8pt baseline grid. All standard values are multiples or sub-multiples of 4pt.

| Token | Value | Use |
|---|---|---|
| xxs | 1pt | Button separators in bottom bars |
| xs | 4pt | Description label gaps, mini-control sub-spacing |
| s | 6pt | Stacked controls minimum, radio/checkbox spacing |
| **m** | **8pt** | **Label-to-control gap, column gap, toolbar spacing** |
| l | 10pt | GroupBox internal top/bottom |
| ml | 12pt | Section separator padding, last-control-to-button-row |
| xl | 14pt | First control below titlebar (no tab view) |
| xxl | 16pt | GroupBox internal margin (canonical) |
| **xxxl** | **20pt** | **Window content margin (L/R/B)** |
| xxxxl | 24pt | Menu bar height, max section whitespace |

**The 20-8-6 rule:** 20pt window margins, 8pt label-to-control gaps, 6pt minimum between stacked controls.

---

## 3. Typography Quick Reference

macOS text styles are 25-50% smaller than iOS equivalents for the same semantic name.

| Style | macOS Size | Weight | SwiftUI | Use |
|---|---|---|---|---|
| Large Title | 26pt | Regular | `.largeTitle` | Major headings |
| Title 1 | 22pt | Regular | `.title` | Section titles |
| Title 2 | 17pt | Regular | `.title2` | Subsections |
| Title 3 | 15pt | Regular | `.title3` | Tertiary headings |
| **Headline** | **13pt** | **Bold** | `.headline` | Emphasized body |
| **Body** | **13pt** | Regular | `.body` | Main content |
| Callout | 12pt | Regular | `.callout` | Secondary descriptions |
| Subheadline | 11pt | Regular | `.subheadline` | Small labels |
| Footnote | 10pt | Regular | `.footnote` | Annotations |
| Caption 1 | 10pt | Regular | `.caption` | Captions |
| Caption 2 | 10pt | Medium | `.caption2` | Micro-copy |

**Critical:** macOS body text is 13pt, not 17pt. Headline on macOS is Bold, not Semibold. SF Pro Text for sizes <= 19pt; SF Pro Display at >= 20pt.

---

## 4. Control Size Tiers

| Size | SwiftUI | AppKit | Typical Height | Use |
|---|---|---|---|---|
| Mini | `.mini` | `.mini` | ~16pt | Dense forms, table accessories |
| Small | `.small` | `.small` | ~19pt | Toolbars, inspectors |
| **Regular** | `.regular` | `.regular` | **~22pt** | **Default for everything** |
| Large | `.large` | `.large` | ~26-32pt | Primary actions, onboarding |

---

## 5. Component Decision Trees

### Which Button Type?

```
Is it an action that executes immediately?
  YES -> Push button (.bordered / .borderedProminent)
    Is it the most likely action? -> Default button (Return key, accent fill)
    Is it destructive? -> .destructive role (system red, NOT the default)
    Does it open more UI? -> Add ellipsis: "Export..."
  NO -> Is it a binary on/off?
    YES -> Is it a major feature toggle taking effect immediately?
      YES -> NSSwitch / Toggle(.switch)
      NO -> Checkbox / Toggle(.checkbox)
    NO -> Is it one of 2-5 mutually exclusive options?
      YES -> Radio buttons (vertical preferred)
      NO -> Pop-up button (NSPopUpButton / Picker(.menu))
```

### Which Container for Additional UI?

```
Blocks a critical operation? -> Alert (NSAlert) or Modal Sheet
Anchored to a control, brief and transient? -> Popover (.transient)
Persistent property editing alongside content? -> Inspector panel
Full-focus task, window still accessible? -> Sheet (beginSheetModal)
Inline expansion in current layout? -> DisclosureGroup / Disclosure triangle
```

### Which Data Display Component?

```
Is the data hierarchical?
  YES -> Column-by-column navigation? -> NSBrowser
         Expandable tree? -> NSOutlineView
  NO -> Grid layout (equal-size items)? -> NSCollectionView / LazyVGrid
        List/rows?
          Need max performance (5000+ rows)? -> NSTableView (AppKit)
          Simple list (<1000 rows)? -> SwiftUI Table or List
          Sidebar navigation? -> NSOutlineView with .sourceList
```

### Checkbox vs Toggle (NSSwitch)?

```
Major feature-level on/off, immediate effect, standalone? -> Toggle/Switch
Minor/detail setting, part of a form, or hierarchy of options? -> Checkbox
Already using checkboxes in same UI? -> Keep using checkboxes (consistency)
Deferred apply (Save/Submit button)? -> Checkbox
```

---

## 6. Window and Toolbar Patterns

### Toolbar Styles (macOS 11+)

| Style | Use | Item Labels |
|---|---|---|
| `.unified` | Most apps (default) | Hidden by default |
| `.unifiedCompact` | Apps needing vertical space | Hidden |
| `.expanded` | Document-based apps | Shown, compact |
| `.preference` | Settings windows | Shown, selected highlighted |

### Toolbar Item Ordering

Leading: Sidebar toggle (anchored) -> App-specific items -> Center: Navigation -> Trailing: Search -> Share -> Inspector toggle

### Sidebar Specs

| Property | Value |
|---|---|
| `preferredThicknessFraction` | 0.15 (15% of window) |
| Content list fraction (with sidebar) | 0.28 |
| Inspector standard size | 270pt (fixed) |
| Practical sidebar range | 160-400pt |
| Material | `.sidebar` with `.behindWindow` blending |

---

## 7. Dialog and Alert Rules

### Button Placement (macOS Convention)

```
[Destructive]     [Cancel]     [Default Action]
  <- left           middle       right (Return) ->
```

- Default button: trailing (rightmost), accent-colored, bound to Return
- Cancel: second from right, bound to Escape
- **Never** make a destructive button the default
- Use specific verbs ("Delete", "Erase"), not "OK" or "Yes"/"No"

### Alert Text

- `messageText` (bold, larger): State the specific action — "Delete 'Project Alpha'?"
- `informativeText` (regular, smaller): State consequences — "You can't undo this."

---

## 8. Menu Bar Requirements

Standard menus in order: **App Menu** -> **File** -> **Edit** -> **View** -> [App-specific] -> **Window** -> **Help**

- "Settings..." (not "Preferences..." on macOS 13+) with `Cmd-,`
- Ellipsis only when further input required (Open..., Save As...) — NOT for About, Quit
- Toggle titles describe the action: "Show Toolbar" / "Hide Toolbar"
- Modifier glyph order: **Fn -> Ctrl -> Opt -> Shift -> Cmd**
- Help menu always contains a search field at top (system-provided)

---

## 9. Color System Essentials

### Label Hierarchy (auto-adapts light/dark)

| Level | NSColor | SwiftUI | Use |
|---|---|---|---|
| Primary | `.labelColor` | `.primary` | Main text |
| Secondary | `.secondaryLabelColor` | `.secondary` | Supporting text |
| Tertiary | `.tertiaryLabelColor` | `.tertiary` | Placeholder text |
| Quaternary | `.quaternaryLabelColor` | — | Watermark |

- Use semantic colors, never hardcoded hex — they auto-adapt to light/dark/high-contrast
- `controlAccentColor` follows the user's system accent color choice
- `CALayer` does NOT auto-adapt — refresh in `viewDidChangeEffectiveAppearance()`
- Asset catalog colors support 4 slots: Any, Dark, High Contrast, High Contrast Dark

---

## 10. Materials and Vibrancy

| Blending Mode | What It Blurs | Use |
|---|---|---|
| `.behindWindow` | Other windows + desktop | Sidebars, menus, popovers |
| `.withinWindow` | Content within same window | Title bars, selection, sheets |

**Critical:** Title bar material MUST use `.withinWindow`. Sidebar uses `.behindWindow` (requires `window.isOpaque = false`).

### Liquid Glass (macOS 26)

- API: `NSGlassEffectView` (AppKit) / `.glassEffect()` (SwiftUI)
- Variants: Regular (adaptive) and Clear (needs dimming overlay)
- Glass on **control layer** only (toolbars, sidebars) — never content
- No `.state` property — appearance depends on key window status

---

## 11. Motion and Animation

| Context | Duration | Curve |
|---|---|---|
| NSAnimationContext default | 0.25s | easeInEaseOut |
| SwiftUI `.default` | 0.35s | easeInEaseOut |
| Window resize / sheet | ~0.20s | system default |
| **Rule of thumb** | **< 0.4s** | **Always on macOS** |

Use no-bounce or near-zero bounce springs on macOS. Always check `accessibilityReduceMotion` — substitute `.opacity` for spatial transitions.

---

## 12. Accessibility Non-Negotiables

- Every interactive element needs `accessibilityLabel` (unless visible text serves as label)
- Every custom `NSView` control must adopt a role-specific protocol (`NSAccessibilityButton`, etc.)
- Decorative images: `.accessibilityHidden(true)` / `setAccessibilityElement(false)`
- Test with VoiceOver (`Cmd-F5`) and Full Keyboard Access

---

## 13. SwiftUI vs AppKit

| Scenario | Recommendation |
|---|---|
| Simple forms, settings, < 1000 rows | SwiftUI |
| Complex tables, 5000+ rows | NSTableView via AppKit |
| Native sidebar vibrancy | AppKit `NSVisualEffectView` |
| Window lifecycle control | AppKit |
| Rich drag-and-drop | AppKit |
| Cross-platform (macOS + iOS) | SwiftUI |

**Practitioner consensus:** SwiftUI implements HIG for you on iOS; on macOS, it fights you at every turn. Use SwiftUI for layout, fall back to AppKit via `NSViewRepresentable` for complex controls.

---

## 14. Common Mistakes

1. **Treating macOS as a big iPad** — No bottom tab bars, no full-screen sheets
2. **Save/Cancel/Apply in Settings** — Settings changes are immediate
3. **Missing standard keyboard shortcuts** — `Cmd-,` `Cmd-W` `Cmd-Q` `Cmd-Z/X/C/V/A/S/F`
4. **Missing menu bar items** — Every action needs a menu equivalent
5. **iOS body text size (17pt)** — macOS body is 13pt
6. **iOS row heights (44pt)** — macOS default is 22pt
7. **Custom dark mode toggle** — Respect `NSAppearance`
8. **SwiftUI List/Table for large datasets** — Falls apart past ~1000 rows
9. **Missing Services menu** — Text apps must support NSServicesMenuRequestor
10. **Hardcoded colors** — Use semantic `NSColor` tokens or asset catalog names

---

## Reference Index

Read these files for detailed specs. Each contains exact values, API examples, and do's/don'ts.

### Foundations

| Topic | File | Key Content |
|---|---|---|
| Color System & Dark Mode | `references/foundations/01-color-system-and-dark-mode.md` | 50+ color tokens, dark mode, accent colors, dynamic color construction, P3 wide gamut, CALayer refresh pattern, asset catalogs |
| Typography & Text Styles | `references/foundations/02-typography-and-text-styles.md` | All text styles, SF Pro family, Dynamic Type, tracking |
| Layout, Spacing & Alignment | `references/foundations/03-layout-spacing-and-alignment.md` | Window chrome dimensions, form layouts, sidebar widths |
| Iconography & SF Symbols | `references/foundations/04-iconography-and-sf-symbols.md` | 10 app icon sizes, squircle geometry, SF Symbols rendering, animated symbol effects (.bounce/.pulse/.wiggle/.breathe/.rotate) |
| Materials, Vibrancy & Effects | `references/foundations/05-materials-vibrancy-and-effects.md` | 14 named materials, blending modes, Liquid Glass API |
| Motion & Animation | `references/foundations/06-motion-and-animation.md` | Timing values, spring parameters, easing curves, Reduced Motion |

### Components

| Topic | File | Key Content |
|---|---|---|
| Buttons & Action Controls | `references/components/01-buttons-and-action-controls.md` | 20+ button variants, segmented controls, dialog button rules |
| Text Inputs, Labels & Search | `references/components/02-text-inputs-labels-and-search.md` | Text fields, search fields, token fields, combo boxes, validation, AutoFill/NSTextContentType, passkey integration |
| Selection Controls & Pickers | `references/components/03-selection-controls-and-pickers.md` | Checkboxes, radio buttons, sliders, steppers, color wells, NSLevelIndicator (4 styles), NSPathControl (3 styles) |
| Menus & Menu Bar | `references/components/04-menus-and-menu-bar.md` | Complete menu system, NSMenu delegate lifecycle, validation, Services menu, dynamic menus, toggle states, Format menu |
| Popovers, Tooltips & Disclosure | `references/components/05-popovers-tooltips-and-disclosure.md` | Popover sizing/behavior, tooltip timing, disclosure controls |
| Tables, Lists & Outlines | `references/components/06-tables-lists-and-outlines.md` | NSTableView, NSOutlineView, NSCollectionView, NSBrowser, NSCollectionViewCompositionalLayout |
| Alerts, Sheets & Dialogs | `references/components/07-alerts-sheets-and-dialogs.md` | Alert styles, button placement, modality levels, accessoryView, SwiftUI limits, NSPanel patterns, Save Changes pattern, multi-item phrasing |

### Platform Patterns

| Topic | File | Key Content |
|---|---|---|
| Window Management & Types | `references/platform-patterns/01-window-management-and-types.md` | Window types, title bar 28pt, traffic lights, full-screen, Stage Manager, tabbing, proxy icons, tiling |
| Sidebars & Split Views | `references/platform-patterns/02-sidebars-source-lists-split-views.md` | Sidebar types, width specs, inspectors, collapse, macOS 26 floating Liquid Glass sidebars, migration path |
| Toolbars & Title Bars | `references/platform-patterns/03-toolbars-and-title-bars.md` | 5 toolbar styles, customization, overflow |
| Keyboard Shortcuts & Input | `references/platform-patterns/04-keyboard-shortcuts-and-input.md` | Complete shortcut table, focus system |
| Drag, Drop & File Management | `references/platform-patterns/05-drag-drop-and-file-management.md` | Drag lifecycle, cursor badges, file promises |

### Technologies

| Topic | File | Key Content |
|---|---|---|
| Accessibility | `references/technologies/01-accessibility-and-assistive-tech.md` | VoiceOver, keyboard navigation, 33-item audit checklist |
| Widgets, Notifications & System | `references/technologies/02-widgets-notifications-system.md` | Widget dimensions, notifications, Spotlight, Services |

### Context

| Topic | File | Key Content |
|---|---|---|
| Practitioner Insights | `references/context/01-practitioner-insights.md` | Common mistakes, what devs override, SwiftUI vs AppKit reality |

---

## Using References

When implementing a component or pattern:

1. **Identify the reference file** from the index above
2. **Read it** for exact dimensions, API examples, states, and do's/don'ts
3. **Cross-reference** practitioner insights for real-world gotchas
4. **Check accessibility** requirements in the accessibility reference

Do not rely on memory alone — the references are authoritative.
