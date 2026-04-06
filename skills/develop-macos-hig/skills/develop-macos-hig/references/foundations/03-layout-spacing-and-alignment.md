# macOS Layout, Spacing, and Alignment Reference

**Scope:** macOS only. All values in points (pt).  
**Applies to:** macOS 13 Ventura, 14 Sonoma, 15 Sequoia. macOS 26 Tahoe deviations noted in Section 9.  
**Sources:** Apple ADC archive, Apple HIG practitioner synthesis, WWDC sessions, bjango.com, community measurements. All values cited.

---

## 1. Spacing Scale

The macOS spacing system uses an 8 pt baseline grid. All standard values are multiples or sub-multiples of 4 pt.

| Token | Value | Primary Use |
|---|---|---|
| spacing.xxs | 1 pt | Button separators inside bottom bars |
| spacing.xs | 4 pt | Description label top gap; slider title-to-label spacing; mini-control sub-spacing |
| spacing.s | 6 pt | Stacked regular controls (minimum); radio vertical spacing; checkbox stacking; colon-to-section spacing |
| spacing.m | 8 pt | Label-to-control (regular size); between columns; toolbar control spacing; group separation bonus |
| spacing.l | 10 pt | GroupBox internal top/bottom (measured SwiftUI default: top 10, bottom 6) |
| spacing.ml | 12 pt | Section separator padding above and below; bottom-controls-to-button-row; tab view top margin from titlebar; minimum section white-space; small-control section spacing |
| spacing.xl | 14 pt | First control below titlebar/toolbar (no tab view); description label minimum indent |
| spacing.xxl | 16 pt | GroupBox internal all-around margin (HIG canonical); tab view internal content margin minimum |
| spacing.xxxl | 20 pt | Window content margin (left, right, bottom); tab view side/bottom margin; separator line horizontal margin; new-window cascade offset |
| spacing.xxxxl | 24 pt | Maximum section white-space; menu bar height (Big Sur through Sequoia) |

**Sources:** leopard-adc.pepas.com (Apple ADC archive); marioaguzman.github.io/design/layoutguidelines/; bjango.com/articles/designingmenubarextras/; zenn.dev/usagimaru

---

## 2. Window Layout

### 2a. Content Margins

| Location | Value | Notes |
|---|---|---|
| Left margin | 20 pt | Window edge to first content element |
| Right margin | 20 pt | Window edge to last content element |
| Bottom margin | 20 pt | Window edge to last control (regular-size controls) |
| Top margin — no tab view | 14 pt | From titlebar/toolbar bottom to first control |
| Top margin — with tab view | 12 pt | From titlebar/toolbar bottom to tab view top edge |
| Tab view: side and bottom margin | 20 pt | Same as general window margin |
| Tab view: internal content margin | ≥ 16 pt | Within the tab view content area |
| Small-control window (no group boxes) | 20 pt L/R/B | Same as regular |
| Small-control window (with group boxes) | 10 pt L/R/B | Reduced when group boxes provide visual containment |
| Mini-control window | 10 pt L/T/R | Bottom: 14 pt |

**Sources:** marioaguzman.github.io/design/layoutguidelines/; zenn.dev/usagimaru (macOS 15 confirmed)

### 2b. Window Chrome Dimensions

| Element | Value | Version / Notes |
|---|---|---|
| Menu bar height | 24 pt | macOS 11 Big Sur through macOS 15 Sequoia |
| Menu bar height (legacy) | 22 pt | macOS 10.x and earlier |
| Menu bar height — 14-in/16-in MacBook Pro (camera housing) | 37 pt | Physical height with notch; logical content area is still 24 pt |
| Menu extras working area | 22 pt | Status items cannot exceed this height |
| Menu extras recommended icon | 16 × 16 pt | Circular icons; no required padding unless vertically centering |
| Title bar height (no toolbar) | ~22 pt | Standard document/utility window |
| Unified title + toolbar (Big Sur+, regular mode) | ~52 pt | Combined height; cannot be resized |
| NSToolbar height (legacy, pre–Big Sur) | ~53 pt | Separate toolbar; stock size cannot be changed |
| NSToolbar small size mode | ~38 pt | Compact toolbar variant |
| Bottom bar height — regular controls | 32 pt | Includes the 1 pt separator line |
| Bottom bar height — small controls | 22 pt | Includes the 1 pt separator line |
| Bottom bar button height — regular | 18 pt | |
| Bottom bar button height — small | 14 pt | |
| Bottom bar button width — regular | 31 pt | |
| Bottom bar button width — small | ≥ 25 pt | Minimum |
| Bottom bar edge spacing — regular | 8 pt | Leading/trailing from button group to bar edge |
| Bottom bar edge spacing — small | 6 pt | |
| Bottom bar button separation | 1 pt | Between adjacent buttons within bar |
| New window cascade offset | 20 pt right, 20 pt down | Each subsequent window opens offset from the previous |

**Sources:** bjango.com/articles/designingmenubarextras/; leopard-adc.pepas.com (XHIGWindows); stackoverflow.com/questions/16416959 (toolbar height); stackoverflow.com/questions/2867503 (menu bar height)

### 2c. Safe Areas and Window-Edge Behavior

| Context | Behavior |
|---|---|
| Standard Mac display | No safe area insets; entire screen area is usable |
| MacBook Pro 14-in / 16-in (camera housing models) | `NSScreen.safeAreaInsets` returns a non-zero top inset covering the notch |
| API availability | `NSScreen.safeAreaInsets` available macOS 12+; use it to avoid drawing behind the camera |
| Maximized window top margin | A small reserved margin remains at the very top of the screen when a window is fully expanded — intentional system behavior protecting menu bar access, not a layout bug |
| Window-edge content behavior | System-defined; content should never be clipped or obscured by window chrome in any size |

**Source:** developer.apple.com/documentation/appkit/nsscreen/safeareainsets; Reddit r/MacOS confirmed as intentional behavior

---

## 3. Control Spacing

### 3a. Control Dimensions

| Control | Size | Dimension |
|---|---|---|
| Push button | Regular | 22 pt tall |
| Push button | Small | 18 pt tall |
| Push button | Mini | 15 pt tall |
| Text field | Regular | 22 pt tall |
| Text field | Small | 19 pt tall |
| Text field | Mini | 15 pt tall |
| Checkbox (hit area) | Regular | 14 pt tall |
| Checkbox (hit area) | Small | 12 pt tall |
| Checkbox (hit area) | Mini | 10 pt tall |
| Radio button (hit area) | Regular | 14 pt tall |
| Radio button (hit area) | Small | 12 pt tall |
| Radio button (hit area) | Mini | 10 pt tall |
| Segmented control | Regular | 22 pt tall |
| Segmented control | Small | 17 pt tall |
| Segmented control | Mini | 14 pt tall |
| Segment icon | Regular | 17 × 15 pt |
| Segment icon | Small | 14 × 13 pt |
| Segment icon | Mini | 12 × 11 pt |
| Slider — horizontal linear, directional, no ticks | Regular | 19 pt wide (track) |
| Slider — horizontal linear, directional, with ticks | Regular | 25 pt wide |
| Slider — horizontal linear, round thumb | Regular | 15 pt wide |
| Slider — horizontal linear, directional, no ticks | Small | 14 pt |
| Slider — horizontal linear, directional, with ticks | Small | 19 pt |
| Slider — horizontal linear, round thumb | Small | 12 pt |
| Slider — horizontal linear, directional, no ticks | Mini | 11 pt |
| Slider — horizontal linear, directional, with ticks | Mini | 17 pt |
| Slider — horizontal linear, round thumb | Mini | 10 pt |
| Slider — circular, with ticks | Regular | 32 pt diameter |
| Slider — circular, no ticks | Regular | 24 pt diameter |
| Slider — circular, with ticks | Small | 22 pt diameter |
| Slider — circular, no ticks | Small | 18 pt diameter |
| Help button | Regular | 20 pt diameter |
| Bevel button | Standard | 20 × 20 pt |
| Round button | Regular | 25 pt diameter |
| Round button | Mini | 20 pt diameter |
| Icon button icon | Standard | 24–32 pt |
| Bevel button icon margin | Standard | 5–15 pt |
| Stepper-to-text-field gap | Regular / Small | 2 pt |
| Stepper-to-text-field gap | Mini | 1 pt |
| NSTableView row height | Default | 22 pt |
| Table image (macOS) | WWDC 2022 example | 20 × 20 pt |

**Source:** leopard-adc.pepas.com (Apple ADC controls archive); WWDC 2022 session 10052

### 3b. Label-to-Control Spacing

| Control type | Size | Horizontal gap (label to control) |
|---|---|---|
| Radio button | Regular | 8 pt |
| Radio button | Small | 6 pt |
| Radio button | Mini | 5 pt |
| Checkbox | Regular | 8 pt |
| Checkbox | Small | 6 pt |
| Checkbox | Mini | 5 pt |
| Pop-up menu (intro label) | Regular | 8 pt |
| Pop-up menu (intro label) | Small | 6 pt |
| Pop-up menu (intro label) | Mini | 5 pt |
| Pop-up menu item left indent | Regular | 9 pt |
| Pop-up menu item left indent | Small | 7 pt |
| Pop-up menu item left indent | Mini | 5 pt |
| Combo box (intro label) | Regular | 8 pt |
| Combo box (intro label) | Small | 6 pt |
| Combo box (intro label) | Mini | 5 pt |
| Two-column form: label column to control column | Any | 8 pt |

**Source:** leopard-adc.pepas.com; zenn.dev/usagimaru

### 3c. Control-to-Control Spacing (Vertical)

| Context | Size | Value |
|---|---|---|
| Stacked controls (same type) | Regular | ≥ 6 pt |
| Radio button group | Regular | 6 pt |
| Radio button group | Small | 6 pt |
| Radio button group | Mini | 5 pt |
| Checkbox group | Regular | 8 pt |
| Checkbox group | Small | 8 pt |
| Checkbox group | Mini | 7 pt |
| Stacked pop-up menus | Regular | 10 pt |
| Stacked pop-up menus | Small | 8 pt |
| Stacked pop-up menus | Mini | 6 pt |
| Stacked combo boxes | Regular | 12 pt |
| Stacked combo boxes | Small | 10 pt |
| Stacked combo boxes | Mini | 8 pt |
| Stacked sliders | Regular | 12 pt |
| Stacked sliders | Small | 10 pt |
| Stacked sliders | Mini | 8 pt |
| Round button / icon button to any element | — | 12 pt |
| Help button to any element | — | 12 pt |
| Rectangular-style toolbar controls: label spacing | — | 8 pt |
| Capsule-style toolbar controls: spacing | — | 8 pt |
| Icon buttons with ≥24 pt icons: between buttons | — | 8 pt |
| Icon button to other elements | — | 10 pt margin around each icon button |

**Source:** leopard-adc.pepas.com (Apple ADC)

### 3d. Grouping and Section Spacing

| Context | Value | Notes |
|---|---|---|
| Group separation — extra white space only (no separator) | 6 pt baseline + 8 pt extra = 14 pt total | 8 pt bonus on top of the 6 pt minimum |
| Separator (NSBox) padding above | 12 pt | Before the divider line |
| Separator (NSBox) padding below | 12 pt | After the divider line |
| Separator horizontal margin from window edge | ≥ 20 pt | Each side |
| Space between last control row and button row | 12 pt | Before Cancel/OK/action buttons |
| Section white-space minimum | 12 pt | Between unrelated groups |
| Section white-space maximum | 24 pt | Do not use more than this |
| Section title to first control below (small/mini windows) | 8 pt | |
| GroupBox internal padding (HIG canonical) | 16 pt (all sides) | |
| GroupBox internal padding (SwiftUI measured) | Top: 10, Left: 8, Right: 8, Bottom: 6 pt | Measured default via SwiftUI GroupBox |
| Optional description label indent from left margin | ≥ 14 pt | Aligns description under its control |
| Optional description label gap from control above | 4 pt | |

**Sources:** marioaguzman.github.io/design/layoutguidelines/; stackoverflow.com/questions/31627267 (groupbox measurement)

---

## 4. Form Layouts

### 4a. Alignment Rules

| Rule | Specification |
|---|---|
| Section labels | Right-aligned (trailing edge), end at the colon |
| Input controls | Left-aligned; leading edge aligns to a fixed column position |
| Two-column layout column gap | 8 pt between label column trailing edge and control column leading edge |
| Within-row alignment | Align controls and their labels on the first text baseline |
| Similar controls | Pop-up menus and combo boxes in the same window should share identical widths |
| Description text alignment | Left-aligned with the control it describes; indent ≥ 14 pt from left window edge |
| Block centering | The entire label+control two-column block is horizontally center-equalized within the window |

### 4b. SwiftUI Form Patterns

| API / Pattern | macOS Behavior |
|---|---|
| `Form { }` | Applies system-standard form inset (~15 pt per side); two-column label+control layout on macOS |
| `Form { }.formStyle(.grouped)` | macOS 13+; grouped sections with rounded containers, matching System Settings visual style |
| `LabeledContent("Label") { Control() }` | macOS 13+; correct two-column label alignment without manual alignment guides |
| `Toggle().toggleStyle(.checkbox)` | macOS-specific; renders as native checkbox (not a toggle switch) |
| `Picker().pickerStyle(.inline)` | macOS-specific; inline layout without popup |
| `.padding()` — no argument | Dynamic and system-calculated; NOT a fixed point value. Varies by device, accessibility settings, layout context. |
| `.padding(.all, 20)` | Use this explicit value to match the standard 20 pt window content margin |
| `.padding(.all, 16)` | Use for GroupBox / card internal padding |
| `.padding(.all, 8)` | Use for label-to-control column gap |

**Sources:** stackoverflow.com/questions/70962859; WWDC 2022 session 10052; stackoverflow.com/questions/65368402

### 4c. Dialog and Alert Layout

| Context | Value | Notes |
|---|---|---|
| Panel and dialog content margin | 20 pt | Same as window content margin, all four sides |
| Space before button row | 12 pt | Between last control group and Cancel/OK buttons |
| Button row side and bottom margins | 20 pt | Standard window edge margin applies |
| System-applied Form inset (AppKit) | ~15 pt per side | Not a public constant; approximated from measurements |

---

## 5. Sidebar and Navigation Dimensions

### 5a. Sidebar Widths

Apple does not publish a single canonical sidebar width. The ranges below are practitioner consensus from developer documentation, community measurements, and API examples.

| Sidebar type | Minimum | Ideal / Default | Maximum | Notes |
|---|---|---|---|---|
| Navigation sidebar (general) | 180 pt | 200–220 pt | 300 pt | Common range; all values are developer-set |
| NavigationSplitView — sidebar column | Set via API | 200 pt (typical) | 300 pt (typical) | `.navigationSplitViewColumnWidth(min:ideal:max:)` |
| NavigationSplitView — content column | Set via API | 300–380 pt | 500 pt (typical) | Developer responsibility |
| Inspector / trailing panel | 200 pt | 260–280 pt | 400 pt | `.inspectorColumnWidth(min:ideal:max:)` |
| Full-height sidebar (Ventura+) | 200 pt | — | 300 pt | `allowsFullHeightLayout = true` on `NSSplitViewItem` |
| NSSplitViewItem minimumThickness | No system default | — | No system maximum | Set explicitly in code |

**Tahoe note:** `.navigationSplitViewColumnWidth` is not reliably respected in macOS 26 (Tahoe) betas. Verify at final release.

**Sources:** stackoverflow.com/questions/61524009; medium.com/@bancarel.paul; hackingwithswift.com forums; Reddit r/SwiftUI

### 5b. Toolbar

| Element | Value | Notes |
|---|---|---|
| NSToolbar regular size mode (Big Sur+, unified) | ~52 pt combined with title bar | Unified title+toolbar; not separately resizable |
| NSToolbar small size mode | ~38 pt | Compact variant |
| Toolbar SF Symbol icon — recommended | 18–24 pt | Use `.medium` symbol scale for toolbar buttons |
| Toolbar custom icon | 18 × 18 pt or 24 × 24 pt | Depends on control style |
| NSToolbar cannot be custom-resized | — | Use a custom NSView-based toolbar for non-standard heights |

### 5c. List and Table Rows

| Element | Value | Notes |
|---|---|---|
| NSTableView default row height | 22 pt | AppKit default; view-based tables |
| macOS table row image size | 20 × 20 pt | WWDC 2022 macOS-specific platform value (vs 32×32 on iOS) |
| SwiftUI List default row height | Not a fixed constant | System-calculated from content |
| `defaultMinListRowHeight` | Set via `\.defaultMinListRowHeight` | Environment value; not hardcoded |
| Source list / sidebar row | 22–24 pt | Typical practitioner range |

---

## 6. Grid and Stack Layouts

### 6a. Standard Gap Values

| Layout context | Gap value | Notes |
|---|---|---|
| VStack / HStack — no explicit spacing | System-calculated | Not a fixed constant; varies by adjacent view types |
| VStack / HStack — explicit standard gap | 8 pt | Use for consistent control-to-control spacing |
| Two-column form: label column to control column | 8 pt | Horizontal gap |
| Card / grouped section internal padding | 16 pt | Equivalent to GroupBox canonical margin |
| Section separation (minimum) | 12 pt | |
| Section separation (maximum) | 24 pt | |
| Multi-column grid: column gap | 8 pt (minimum) | Matches the standard inter-element gap |

### 6b. NSGridView

NSGridView has no universal default spacing — all gaps are set by the developer per-row and per-column.

| Property | Typical value | Notes |
|---|---|---|
| `NSGridRow.topPadding` | 4–6 pt | Per-row padding |
| `NSGridRow.bottomPadding` | 4–6 pt | Per-row padding |
| Column gap (via `xPlacement`) | 8 pt | Standard two-column form gap |
| Content hugging priority (H + V) | 600 | Standard constraint priority for cells |

**Source:** tothenew.com/blog/nsgridview-a-new-layout-container-for-macos/

### 6c. Alignment Principles

| Principle | Rule |
|---|---|
| Baseline alignment | Align text labels and controls on their first baseline within each row |
| Column leading alignment | All controls in the same column share a common leading edge |
| Column trailing alignment | All labels in the label column share a common trailing edge |
| Toolbar icon-to-label spacing | 8 pt between icon and label (same rule as control-to-control) |
| Separator horizontal margins | ≥ 20 pt from both window edges |
| Minimum interactive target | No mandatory macOS minimum (unlike iOS 44 pt); system controls are appropriately sized by default |
| Concentricity (macOS 26+) | `inner_radius + padding = outer_radius` — padding value must honor the concentric corner radius relationship |

---

## 7. Typography Reference (Layout Context)

macOS body text is 13 pt — not 17 pt as on iOS. This is the most important platform difference for row heights, readable line lengths, and column sizing.

| Text style | Size | Weight | Leading | Use |
|---|---|---|---|---|
| Large Title | 28 pt | Regular | ~34 pt | Major headings |
| Title 1 | 22 pt | Regular | ~26 pt | Section titles |
| Title 2 | 17 pt | Regular | ~22 pt | Subsection headings |
| Title 3 | 15 pt | Regular | ~19 pt | Tertiary headings |
| Headline | 13 pt | Bold | ~16 pt | Emphasized body text |
| Body | 13 pt | Regular | ~16 pt | Main content |
| Callout | 12 pt | Regular | ~15 pt | Secondary descriptions |
| Subheadline | 11 pt | Regular | ~14 pt | Small labels |
| Footnote | 10 pt | Regular | ~13 pt | Annotations |
| Caption 1 | 10 pt | Regular | ~13 pt | Captions |
| Caption 2 | 10 pt | Regular | ~13 pt | Micro-copy |

---

## 8. Do's and Don'ts

| Do | Don't |
|---|---|
| Use 20 pt for all window content margins (L/R/B) | Use arbitrary or asymmetric content margins |
| Use 8 pt for label-to-control and column gaps | Use 4 pt or 16 pt for label-to-control spacing |
| Use ≥ 6 pt between stacked regular controls | Stack controls with zero vertical spacing |
| Use 12 pt for section spacing (separator or extra white space) | Skip visual grouping cues between unrelated sections |
| Use 16 pt for GroupBox internal padding | Use tight padding (< 8 pt) inside group boxes |
| Leave 14 pt between toolbar bottom and first control | Place content flush against the title bar |
| Use `LabeledContent` (macOS 13+) for form rows | Manually align label/control columns with separate stacks |
| Set explicit `.navigationSplitViewColumnWidth(min:200, ideal:220, max:300)` | Leave sidebar width undefined |
| Use 24 pt for menu bar height calculations | Assume 22 pt applies to all Macs (notch models report 37 pt) |
| Use `.formStyle(.grouped)` for Settings-style forms on macOS 13+ | Apply iOS-style forms directly to macOS |
| Use 13 pt as macOS body text size | Use iOS body text (17 pt) on macOS |
| Set explicit `spacing: 8` on VStack/HStack for precise layouts | Rely on SwiftUI's dynamic default spacing |
| Provide `NSScreen.safeAreaInsets`-awareness on MacBook Pro models | Draw into the camera housing area |
| Use 22 pt for NSTableView row height in dense lists | Use iOS-style 44 pt row heights on macOS |

---

## 9. macOS 26 (Tahoe) / Liquid Glass Addendum

macOS 26 introduces Liquid Glass. Key layout implications as of the beta period (mid-2025):

| Topic | Status | Notes |
|---|---|---|
| Concentricity rule | New requirement | `outer_radius = inner_radius + padding`. Every container's corner radius must be concentric with its child elements. Padding values now imply a specific corner radius relationship. |
| Sidebar material | Changed appearance | Sidebars refract/reflect background content via translucent material. Standard width ranges (200–300 pt) are unchanged. |
| NavigationSplitView column width | Unreliable in Tahoe | `.navigationSplitViewColumnWidth` is not respected in beta; verify at shipping. |
| Liquid Glass numeric specs | Not published | Apple has not released specific corner radius values or material thickness specs. |
| Consistency | Incomplete in beta | Liquid Glass applied inconsistently — some segmented controls use it, others do not. Do not treat beta behavior as canonical spec. |
| Pre-Tahoe spacing values | Still valid | All spacing values in sections 1–8 remain the baseline. Tahoe does not change the point values; it adds a concentricity constraint on top. |

**Sources:** apple.com/newsroom/2025/06; Reddit r/MacOSBeta (253 upvotes); medium.com/@zainshariff6506/wwdc-2025-design-changes

---

## 10. Sources

| Source | Type | What it covers |
|---|---|---|
| `leopard-adc.pepas.com` — XHIGControls | Archived Apple ADC (authoritative) | All control dimensions, label spacing, all size variants |
| `leopard-adc.pepas.com` — XHIGWindows | Archived Apple ADC (authoritative) | Bottom bar dimensions, window cascade offset |
| `marioaguzman.github.io/design/layoutguidelines/` | Apple HIG derivative (high confidence) | Window margins, grouping rules, section spacing, control stacking |
| `bjango.com/articles/designingmenubarextras/` | Expert practitioner (Bjango) | Menu bar heights across every macOS version |
| `zenn.dev/usagimaru/articles/b2a328775124ef` | Practitioner — macOS 15 context | 20 pt window margin, 8 pt column gap, separator margins |
| `developer.apple.com/videos/play/wwdc2022/10052/` | WWDC 2022 (official Apple) | SwiftUI macOS form patterns, table image sizes, window sizes |
| `stackoverflow.com/questions/31627267` | Developer measurement | GroupBox actual padding: top 10, L 8, R 8, B 6 pt |
| `stackoverflow.com/questions/61524009` | Developer community | Sidebar width min/ideal/max patterns |
| `stackoverflow.com/questions/16416959` | Developer measurement | NSToolbar default height ~53 pt |
| `stackoverflow.com/questions/70962859` | Developer community | macOS Form inset ~15 pt; LabeledContent alignment |
| `stackoverflow.com/questions/65368402` | Developer community | SwiftUI `.padding()` is dynamic, not a fixed constant |
| `stackoverflow.com/questions/2867503` | Developer measurement | Menu bar height: 22 pt legacy, updated post-Big Sur |
| `medium.com/@bancarel.paul` | Practitioner | Full-height sidebar min: 200 pt, max: 300 pt |
| `apple.com/newsroom/2025/06` | Apple official | Concentricity rule for macOS 26 Liquid Glass |
| Reddit r/MacOSBeta `1n6tjwv` | Community (253 upvotes) | macOS 26 spacing inconsistency in beta |
| Reddit r/MacOS `1fkhqxl` | Community | Maximized window top margin is intentional |
| `developer.apple.com/documentation/appkit/nsscreen/safeareainsets` | Official API docs | Safe area insets on MacBook Pro with camera housing |
