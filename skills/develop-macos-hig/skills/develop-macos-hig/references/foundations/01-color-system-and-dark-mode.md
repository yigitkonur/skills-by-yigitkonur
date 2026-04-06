# macOS Color System & Dark Mode — Complete Reference

> **Audience:** Senior macOS developers and UI designers who need an exact, actionable reference for Apple's color system. Every token, hex value, and behavioral rule is drawn from Apple's official documentation, WWDC sessions, and verified practitioner sources. No filler.

---

## 1. System Colors Overview

### 1.1 Fixed System Colors (Vivid Palette)

These colors are **opaque, fixed-saturation** values with slightly brighter/more saturated dark-mode variants. They do **not** follow the user's accent color preference. Use them for branding, status indicators, or any element that must always be a specific hue.

| NSColor Property | SwiftUI Name | Light Mode Hex | Light RGB | Dark Mode Hex | Dark RGB | Typical Use |
|---|---|---|---|---|---|---|
| `systemBlue` | `.systemBlue` | `#007AFF` | 0, 122, 255 | `#0A84FF` | 10, 132, 255 | Links, default button tint, informational |
| `systemBrown` | `.systemBrown` | `#A2845E` | 162, 132, 94 | `#AC8E68` | 172, 142, 104 | Earthy/natural context |
| `systemGray` | `.systemGray` | `#8E8E93` | 142, 142, 147 | `#98989D` | 152, 152, 157 | Neutral, disabled, secondary |
| `systemGreen` | `.systemGreen` | `#28CD41` | 40, 205, 65 | `#32D74B` | 50, 215, 75 | Success, available, positive |
| `systemIndigo` | `.systemIndigo` | `#5856D6` | 88, 86, 214 | `#5E5CE6` | 94, 92, 230 | Accent variant, depth |
| `systemOrange` | `.systemOrange` | `#FF9500` | 255, 149, 0 | `#FF9F0A` | 255, 159, 10 | Warnings, caution states |
| `systemPink` | `.systemPink` | `#FF2D55` | 255, 45, 85 | `#FF375F` | 255, 55, 95 | Favorites, emotional accent |
| `systemPurple` | `.systemPurple` | `#AF52DE` | 175, 82, 222 | `#BF5AF2` | 191, 90, 242 | Accent variant, creative |
| `systemRed` | `.systemRed` | `#FF3B30` | 255, 59, 48 | `#FF453A` | 255, 69, 58 | Destructive actions, errors |
| `systemTeal` | `.systemTeal` | `#55BEF0` | 85, 190, 240 | `#5AC8F5` | 90, 200, 245 | Communication, tech accent |
| `systemYellow` | `.systemYellow` | `#FFCC00` | 255, 204, 0 | `#FFD60A` | 255, 214, 10 | Alerts, warnings |

**Pattern:** Dark-mode variants are consistently brighter and slightly more saturated (+10–15 luminance units) to maintain perceived contrast against dark backgrounds. These are Apple's macOS-specific values; iOS values for some colors differ (e.g., `systemGreen` is `#34C759` on iOS vs `#28CD41` on macOS).

**Source:** GitHub Gist `andrejilderda/8677c565cddc969e6aae7df48622d47c` (runtime-extracted from macOS), cross-referenced with `developer.apple.com/documentation/appkit/nscolor`

---

### 1.2 Semantic UI Element Colors — Label Group

Labels convey text hierarchy. They use **opacity-based** values to ensure they read correctly on any background color without requiring separate light/dark tokens.

| NSColor Property | Purpose | Light Hex (approx) | Light RGBA | Dark Hex (approx) | Dark RGBA |
|---|---|---|---|---|---|
| `labelColor` | Primary text, highest emphasis | `#000000` (opaque) | 0,0,0 / 1.0 | `#FFFFFF` (opaque) | 255,255,255 / 1.0 |
| `secondaryLabelColor` | Supporting text, captions | `#3C3C4399` | 60,60,67 / 0.6 | `#EBEBF599` | 235,235,245 / 0.6 |
| `tertiaryLabelColor` | Placeholder-level text | `#3C3C434D` | 60,60,67 / 0.3 | `#EBEBF54D` | 235,235,245 / 0.3 |
| `quaternaryLabelColor` | Lowest-priority decorative text | `#3C3C432E` | 60,60,67 / 0.18 | `#EBEBF52E` | 235,235,245 / 0.18 |
| `quinaryLabel` | Ultra-subtle, rarely used (macOS 14+) | Similar to quaternary minus opacity | — | — | — |
| `placeholderTextColor` | Hint text in text fields | `#3C3C434D` | Same as tertiary | `#EBEBF54D` | Same as tertiary |

**Critical rule:** Secondary, tertiary, and quaternary label colors use **alpha transparency**, not flat hex values. They are designed to blend against any background color — including vibrant or tinted backgrounds. Never hard-code their "resolved" hex value; always reference the token.

**Source:** WWDC 2018 Session 210, sarunw.com dark color cheat sheet, GitHub Gist runtime values

---

### 1.3 Semantic UI Element Colors — Text Group

Used for text editing contexts (text fields, text views, document bodies).

| NSColor Property | Purpose | Light Mode | Dark Mode |
|---|---|---|---|
| `textColor` | Body text in editors/text views | Black `#000000` | White `#FFFFFF` |
| `textBackgroundColor` | Background of text areas | White `#FFFFFF` | Dark `#1E1E1E` |
| `selectedTextColor` | Text when selected by user | Black `#000000` | White `#FFFFFF` |
| `selectedTextBackgroundColor` | Highlight behind selected text | `#B3D7FF` (blue tint) | `#3F638B` |
| `unemphasizedSelectedTextColor` | Selected text when window loses focus | Black `#000000` | White `#FFFFFF` |
| `unemphasizedSelectedTextBackgroundColor` | Background when window loses focus | `#DCDCDC` | `#464646` |
| `keyboardFocusIndicatorColor` | Keyboard focus ring | `#0067F4` | `#1AA9FF` |

**Source:** GitHub Gist `andrejilderda/8677c565cddc969e6aae7df48622d47c`

---

### 1.4 Semantic UI Element Colors — Content Group

For lists, tables, collections, and general content areas.

| NSColor Property | Purpose | Light Mode | Dark Mode |
|---|---|---|---|
| `linkColor` | Hyperlinks and navigation links | `#0068DA` | `#419CFF` |
| `separatorColor` | Horizontal/vertical dividers | Semi-transparent black | Semi-transparent white |
| `selectedContentBackgroundColor` | Active selection in tables/lists (focused) | `#0063E1` | `#0058D0` |
| `unemphasizedSelectedContentBackgroundColor` | Selection when window loses focus | `#DCDCDC` | `#464646` |
| `alternatingContentBackgroundColors[0]` | Even rows in alternating lists | `#FFFFFF` | `#1E1E1E` |
| `alternatingContentBackgroundColors[1]` | Odd rows in alternating lists | `#F4F5F5` | `#FFFFFF` (with slight dark tint) |

**Source:** GitHub Gist, Apple AppKit documentation

---

### 1.5 Semantic UI Element Colors — Control Group

For interactive controls: buttons, sliders, checkboxes, segmented controls.

| NSColor Property | Purpose | Light Mode | Dark Mode |
|---|---|---|---|
| `controlAccentColor` | The user's chosen accent color for controls | `#007AFF` (default blue) | `#007AFF` (same, adapts to user choice) |
| `controlColor` | Control surface background | White `#FFFFFF` | White `#FFFFFF` (rendered differently) |
| `controlBackgroundColor` | Background of large control regions | `#FFFFFF` | `#1E1E1E` |
| `controlTextColor` | Text on controls | Black `#000000` | White `#FFFFFF` |
| `disabledControlTextColor` | Text on disabled controls | Black (low opacity) | White (low opacity) |
| `selectedControlColor` | Control highlight when selected | `#B3D7FF` | `#3F638B` |
| `selectedControlTextColor` | Text of selected control | Black `#000000` | White `#FFFFFF` |
| `alternateSelectedControlTextColor` | Text on strongly selected controls (e.g., highlighted button) | White `#FFFFFF` | White `#FFFFFF` |
| `scrubberTexturedBackground` | Touch Bar scrubber background | `#FFFFFF` | `#FFFFFF` |

**Source:** GitHub Gist `andrejilderda/8677c565cddc969e6aae7df48622d47c`, Apple AppKit docs

---

### 1.6 Semantic UI Element Colors — Window Group

| NSColor Property | Purpose | Light Mode | Dark Mode |
|---|---|---|---|
| `windowBackgroundColor` | Standard window background | `#ECECEC` (236,236,236) | `#323232` (50,50,50) |
| `windowFrameTextColor` | Text in window title bar | Black `#000000` | White `#FFFFFF` |
| `underPageBackgroundColor` | Area behind document content (e.g., Preview margins) | `#969696` (150,150,150) | `#282828` (40,40,40) |

---

### 1.7 Semantic UI Element Colors — Menu, Table, Highlight Groups

| NSColor Property | Purpose | Light Mode | Dark Mode |
|---|---|---|---|
| `selectedMenuItemTextColor` | Text of highlighted menu item | White `#FFFFFF` | White `#FFFFFF` |
| `gridColor` | Grid lines in tables | `#E6E6E6` | `#1A1A1A` |
| `headerTextColor` | Column header text in tables | Black `#000000` | White `#FFFFFF` |
| `findHighlightColor` | "Find" match highlight | Yellow `#FFFF00` | Yellow `#FFFF00` |
| `highlightColor` | Raised surface highlight | White `#FFFFFF` | `#B4B4B4` |
| `shadowColor` | Drop shadow color | Black `#000000` | Black `#000000` |

**Source:** GitHub Gist `andrejilderda/8677c565cddc969e6aae7df48622d47c`

---

### 1.8 Fill Colors (macOS 14 Sonoma+, AppKit)

Fill colors layer transparency for subtle surface emphasis. They are transparent and appear different depending on the background.

| NSColor Property | Purpose | Available Since |
|---|---|---|
| `systemFill` | Thin fill for controls on any background | macOS 14+ |
| `secondarySystemFill` | Secondary fill, lighter emphasis | macOS 14+ |
| `tertiarySystemFill` | Tertiary fill, large area subtle emphasis | macOS 14+ |
| `quaternarySystemFill` | Quaternary fill, lightest | macOS 14+ |
| `quinarySystemFill` | Quinary fill, barely visible | macOS 14+ |

**Note:** Fill colors are transparent overlays and do not have single resolved hex values — they adapt to the background they sit on.

**Source:** `developer.apple.com/documentation/appkit/nscolor/systemfill`

---

## 2. Dynamic Color Behavior

### 2.1 How Dynamic Colors Resolve

macOS colors are **not static hex values at runtime**. Every dynamic color:

1. Is resolved at **draw time** based on the current `NSAppearance`
2. Consults the current **appearance** (Aqua, Dark Aqua, High Contrast Aqua, High Contrast Dark Aqua, Vibrant Light, Vibrant Dark)
3. Considers **vibrancy context** — when drawn inside an `NSVisualEffectView`, the color may resolve to a vibrancy-adapted variant
4. Adapts to the **Increase Contrast** accessibility setting by swapping in high-contrast variants (if provided)

**Resolution order:** Appearance → Vibrancy context → Contrast variant → Resolved RGBA

### 2.2 Named Colors in Asset Catalogs

Asset catalog colors are the recommended mechanism for custom brand colors that must adapt. Each color set has **appearance slots**:

| Slot | When Active |
|---|---|
| Any Appearance | Light mode (default) |
| Dark | Dark mode (macOS 10.14+) |
| High Contrast | Light mode with Increase Contrast enabled |
| High Contrast Dark | Dark mode with Increase Contrast enabled |

**Implementation (AppKit):**
```swift
// macOS
let aColor = NSColor(named: NSColor.Name("MyBrandColor"))
```

**Implementation (SwiftUI):**
```swift
Color("MyBrandColor")  // Automatically resolves correct slot
```

**Critical:** Color literals in code do **not** support dynamic/named colors. Do not drag colors from the picker into code as literals if you need dark mode or high contrast support.

**Source:** WWDC 2018 Session 210, onmyway133/blog issue #792, appcoda.com macOS dark theme guide

### 2.3 Programmatic Dynamic Colors (macOS 10.15+)

```swift
// Create a color that adapts at draw time
let dynamicColor = NSColor(name: "HeaderColor") { appearance in
    appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
        ? NSColor(red: 0.9, green: 0.9, blue: 0.9, alpha: 1.0)
        : NSColor(red: 0.1, green: 0.1, blue: 0.1, alpha: 1.0)
}
```

### 2.4 Detecting Current Appearance

```swift
extension NSAppearance {
    var isDarkMode: Bool {
        bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
    }
}
```

**Warning:** Reading `UserDefaults.standard.string(forKey: "AppleInterfaceStyle") == "Dark"` is a legacy technique and unreliable in sandboxed apps. Use `NSAppearance.bestMatch(from:)` instead.

### 2.5 CALayer Does Not Auto-Adapt

`NSView`/`NSControl` subclasses automatically redraw when appearance changes. `CALayer` does **not**. Any `CGColor` set on a layer (e.g., `layer.borderColor`, `layer.backgroundColor`) is captured as a static value and must be manually refreshed.

**Pattern for layer colors:**
```swift
override func viewDidChangeEffectiveAppearance() {
    super.viewDidChangeEffectiveAppearance()
    layer?.borderColor = NSColor.separatorColor.cgColor
}
```

**Source:** WWDC 2018 Session 210, onmyway133/blog issue #792

---

## 3. Dark Mode Adaptation

### 3.1 The Four Appearance Variants

macOS defines four standard appearance names:

| `NSAppearanceName` | Description |
|---|---|
| `.aqua` | Light mode (standard) |
| `.darkAqua` | Dark mode (standard) |
| `.accessibilityHighContrastAqua` | Light mode + Increase Contrast |
| `.accessibilityHighContrastDarkAqua` | Dark mode + Increase Contrast |

Two legacy vibrancy appearances exist but should only be used within `NSVisualEffectView`:
- `.vibrantLight` — for vibrancy in light contexts
- `.vibrantDark` — for vibrancy in dark contexts

### 3.2 How Colors Adapt: The Concrete Rules

**Rule 1 — System semantic colors adapt automatically.** `labelColor`, `controlAccentColor`, `windowBackgroundColor`, etc. resolve to their correct light or dark values with zero code changes.

**Rule 2 — Dark-mode colors are generally brighter and more saturated.** Light gray surfaces become dark grays. White text-on-dark reads at higher contrast than black-on-light in many system contexts. Apple intentionally inverts the lightness hierarchy.

**Rule 3 — Backgrounds invert in layered hierarchy.** In light mode: primary background is light, content areas are white. In dark mode: primary background is dark `#323232`, content areas are a slightly lighter dark `#1E1E1E` — the layering inverts but the hierarchy is preserved.

**Rule 4 — The key window vs. non-key window states both must work.** `selectedContentBackgroundColor` (`#0063E1` light / `#0058D0` dark) is the focused state. `unemphasizedSelectedContentBackgroundColor` (`#DCDCDC` / `#464646`) is the non-focused state. Both must be visually distinct.

**Rule 5 — Pressed/hover states must be described semantically.** Do not apply a fixed "darken 30%" transform. In Dark Mode, darkening already-dark controls produces invisible results. Use the system-provided pressed state variant of `controlAccentColor` or describe states as "active", "pressed", "hover" in your asset catalog.

**Rule 6 — `underPageBackgroundColor` provides depth cues.** The area behind document content (scroll region outside pages) uses `#969696` in light and `#282828` in dark, creating visual depth. Do not use `windowBackgroundColor` for under-page regions.

**Source:** WWDC 2018 Session 210 (nonstrict.eu transcript), Apple AppKit documentation

### 3.3 Manual Appearance Override

Use `NSAppearance` overrides only when strictly necessary (e.g., a document editor that must stay light for print fidelity):

```swift
// Force an entire window to light mode
window.appearance = NSAppearance(named: .aqua)

// Force a specific view and its subtree
myView.appearance = NSAppearance(named: .darkAqua)
```

**Anti-pattern:** Overriding appearance on individual subviews creates visual inconsistencies. Override at the window level only.

**Anti-pattern:** Forcing `.vibrantDark` on the whole window. Use `.darkAqua` for opaque areas, and only use `.vibrantDark` within the `NSVisualEffectView` that needs it.

### 3.4 Auditing for Dark Mode Readiness

Check your codebase for:
1. **Static RGBA/hex literals** — must be replaced with semantic `NSColor` properties or asset catalog names
2. **Non-template images** used as icons — must be converted to template images so they adopt `labelColor` automatically
3. **Hardcoded appearance overrides** in Interface Builder (e.g., "Light Aqua" forced on a view)
4. **Non-semantic materials** in `NSVisualEffectView` — deprecated fixed-look materials don't adapt

**Source:** WWDC 2018 Session 210

---

## 4. Accent & Tint Colors

### 4.1 The Accent Color System

macOS Mojave (10.14) introduced system-wide accent colors. macOS Big Sur (11) reorganized the API.

**User-selectable accent colors (System Settings > Appearance):**

| Color Name | Approximate Hex |
|---|---|
| Blue (default) | `#007AFF` |
| Purple | `#BF5AF2` |
| Pink | `#FF375F` |
| Red | `#FF453A` |
| Orange | `#FF9F0A` |
| Yellow | `#FFD60A` |
| Green | `#32D74B` |
| Graphite | `#8E8E93` |
| Multicolor | App controls use each app's own accent |

**Key token:** `NSColor.controlAccentColor` — dynamically resolves to whichever accent color the user has selected. This is the single most important token for interactive controls.

### 4.2 Accent Color Behavioral Rules

**Rule 1 — `controlAccentColor` follows the user's preference.** Buttons, checkboxes, radio buttons, progress indicators, and focus rings automatically use it. Your custom controls should call `NSColor.controlAccentColor` instead of a fixed blue.

**Rule 2 — Multicolor is the app-respects-accent mode.** When the user selects "Multicolor," the system honors the app's own `NSColor.controlAccentColor` override or the accent color set in the app's asset catalog. If the user picks any specific color, the system overrides the app's color.

**Rule 3 — Graphite makes all accents grayscale.** When the user selects Graphite, `controlAccentColor` resolves to the gray value. Interactive controls that rely on `controlAccentColor` become grayscale. Ensure your UI remains legible and functional in this state.

**Rule 4 — Fixed-color sidebar glyphs are exempt.** Application-defined colors on sidebar item symbols (e.g., Finder's colored folder icons) are not overridden by the accent preference.

**Rule 5 — `systemBlue` is not the same as `controlAccentColor`.** `systemBlue` is always blue. `controlAccentColor` tracks the user's preference. Use `systemBlue` when the color conveys fixed meaning (e.g., informational links). Use `controlAccentColor` for interactive affordances.

### 4.3 Highlight Color

The **Highlight Color** (formerly a separate setting) was unified with the Accent Color preference in macOS Big Sur. The highlight color (selection color) now derives from the accent color selection.

`NSColor.selectedContentBackgroundColor` reflects this selection.

**Source:** 512pixels.net Big Sur accent/highlight analysis, WWDC 2018 Session 210, idownloadblog.com accent color guide

### 4.4 SwiftUI Tint Color

In SwiftUI, `.tint(_:)` modifier sets the accent color for a view hierarchy:

```swift
Button("Submit") { ... }
    .tint(.green)  // Overrides system accent for this button
```

Note: `.accentColor(_:)` is deprecated as of iOS 15 / macOS 12. Use `.tint(_:)` instead.

**Source:** r/SwiftUI thread on `.accentColor` deprecation

---

## 5. Accessibility

### 5.1 Color Contrast Requirements

Apple follows WCAG 2.1 (and references WCAG 2.2) for App Store accessibility evaluation. Apple's own App Store Connect accessibility review explicitly references the 4.5:1 ratio as the standard.

| Text Type | WCAG AA Minimum | WCAG AAA Target |
|---|---|---|
| Normal text (< 18pt regular or < 14pt bold) | **4.5:1** | 7:1 |
| Large text (≥ 18pt regular or ≥ 14pt bold) | **3:1** | 4.5:1 |
| Non-text UI (icons, input borders, focus indicators) | **3:1** | — |
| Decorative elements | No requirement | — |

**Apple's stated standard (App Store Connect):** "Most modern accessibility guidelines recommend a minimum contrast ratio of 4.5 to 1 between foreground text and its background."

**Source:** `developer.apple.com/help/app-store-connect/manage-app-accessibility/sufficient-contrast-evaluation-criteria/`, WCAG 2.1 (webaim.org/articles/contrast/)

### 5.2 High Contrast Mode (Increase Contrast)

macOS accessibility includes "Increase Contrast" (System Settings > Accessibility > Display > Increase Contrast). When enabled:

- The system activates the `.accessibilityHighContrastAqua` or `.accessibilityHighContrastDarkAqua` appearance
- System semantic colors automatically resolve to higher-contrast variants
- UI elements get **more visible borders, stronger separators, and less translucency**
- Dynamic colors defined in asset catalogs with a "High Contrast" slot are automatically promoted
- If your asset catalog color has no High Contrast slot, the system uses its own algorithm to adjust

**How to support it:**
1. Open your asset catalog color set
2. Enable the "High Contrast" appearance checkbox
3. Set the high-contrast light and high-contrast dark values — typically increased saturation, stronger contrast against backgrounds

**Testing:**
```
System Settings → Accessibility → Display → Increase Contrast
```

**Detection in code (if needed):**
```swift
NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast
```

### 5.3 Reduce Transparency

When the user enables "Reduce Transparency" (System Settings > Accessibility > Display > Reduce Transparency):

- `NSVisualEffectView` materials lose their translucency
- Materials fall back to **opaque, non-blurred backgrounds** using semantic colors
- `windowBackgroundColor` is used as the fallback
- Apps should not hard-code assumptions about material appearance — the system handles this automatically when using `NSVisualEffectView`

**Detection:**
```swift
NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency
```

### 5.4 Color Blindness Considerations

Apple does not mandate specific color-blindness accommodations beyond the general guidance to never use color as the only differentiator:

- Pair color with a **shape, icon, or text label** to convey state (e.g., error states need more than a red border)
- Use the **Color Filters** accessibility setting (System Settings > Accessibility > Display > Color Filters) to test your UI under various simulated color vision deficiencies
- SF Symbols with multiple rendering modes (hierarchical, palette, multicolor) provide built-in color independence when combined with semantic colors

### 5.5 System Color Adaptation Under Accessibility Settings

System semantic colors automatically apply the correct contrast variant when accessibility settings change — no code change required for `NSColor` semantic properties. The runtime applies the following logic:

```
appearance: accessibilityHighContrastAqua
  → labelColor resolves to pure black (higher opacity, no softening)
  → separatorColor resolves to fully opaque (vs. semi-transparent in standard)
  → controlColor gets more visible borders
```

**Source:** WWDC 2018 Session 210, Apple accessibility documentation

---

## 6. Materials & Vibrancy Interaction

### 6.1 Two Blending Modes

macOS `NSVisualEffectView` supports two fundamentally different blending modes:

| Blending Mode | `NSVisualEffectView.BlendingMode` | What Is Blended | Use Case |
|---|---|---|---|
| Behind Window | `.behindWindow` | Desktop wallpaper + content behind the app window | Sidebars, toolbar, window chrome, full-window transparency |
| Within Window | `.withinWindow` | Other layers within the same window | Popovers, overlapping panels, drawer-style content |

**Behind-window blending** is the default. It makes the window background feel connected to the desktop. It is what gives macOS sidebars their characteristic frosted appearance — the wallpaper bleeds through.

**Within-window blending** samples from sibling layers. It creates depth between UI elements inside a single window without exposing the desktop.

### 6.2 Material Types

`NSVisualEffectView.Material` defines the visual "recipe" — how opaque or translucent the blur is, and what color tint sits on top:

| Material | `.material` Value | Description | Primary Use |
|---|---|---|---|
| Titlebar | `.titlebar` | Matches the window title bar appearance | Window chrome |
| Selection | `.selection` | Highlighted/selected state overlay | List row selection |
| Menu | `.menu` | Menus and context menus | `NSMenu` popups |
| Popover | `.popover` | Floating popover panels | `NSPopover` |
| Sidebar | `.sidebar` | Persistent side navigation | `NSSplitView` sidebars |
| Header | `.headerView` | Header rows in tables/source lists | Column headers |
| Sheet | `.sheet` | Modal sheets | Document sheets |
| Window Background | `.windowBackground` | Generic window content area | General-purpose |
| HUD Window | `.hudWindow` | Heads-up display windows | Floating panels |
| Full Screen UI | `.fullScreenUI` | Content during full-screen transitions | Spaces transitions |
| Tool Tip | `.toolTip` | Hover tooltips | `NSToolTip` |
| Content Background | `.contentBackground` | Background of content areas | Split view content panes |
| Under Window Background | `.underWindowBackground` | Region physically below the window in the visual stack | Underneath page content |
| Under Page Background | `.underPageBackground` | Document background behind pages | PDF-style page backing |

**Semantic materials adapt automatically.** They change appearance when the system switches between light/dark mode, high contrast mode, and reduced transparency. Non-semantic (deprecated) materials are fixed and do not adapt.

### 6.3 How Vibrancy Interacts with Color

Vibrancy is the effect where content viewed through a material appears more saturated and vivid:

**Colors that work well on vibrancy:**
- **Opaque grayscale colors** — the material's blending adds color from the background, creating natural-looking tints
- **Semantic system colors** — designed to be legible on vibrant backgrounds

**Colors that degrade on vibrancy:**
- Semi-transparent white/black overlays — desaturate the background and reduce legibility
- Hard-coded RGBA tinted colors — will clash with the blended background colors and appear muddy

**Critical vibrancy rule:** Non-colored artwork (icons, glyphs, text) should be rendered as **vibrant** (template images that adopt `labelColor`). Colored artwork (status badges, tags, brand icons) should be **non-vibrant** (full-color images rendered without vibrancy treatment).

**Vibrancy and text:** `labelColor`, `secondaryLabelColor`, etc. are specifically tuned to provide legible contrast on vibrant surfaces. They use the system's vibrancy-aware draw path automatically when rendered inside an `NSVisualEffectView` with vibrancy enabled.

### 6.4 Color in Sidebar Context

Sidebars use `.behindWindow` blending and `.sidebar` material. Color behavior:

- Background: Derived from desktop wallpaper + sidebar material tint
- Selected row: `selectedContentBackgroundColor` (blue in focused, gray in unfocused)
- Icons: Template images adopt current appearance (dark icons in light sidebar, light icons in dark sidebar)
- Tinted folder/category icons (Finder): Non-template, retain their assigned color even when accent color changes

### 6.5 Liquid Glass (macOS Tahoe / macOS 26 and later)

macOS Tahoe (macOS 26) introduced "Liquid Glass" — an evolution of materials with stronger refraction, specular highlights, and depth cues. Key color implications:

- Liquid Glass materials are more transmissive, revealing more background color
- Controls inside Liquid Glass may need **more vibrant tint colors** to maintain legibility
- Standard system controls (buttons, checkboxes, etc.) update automatically; custom controls may need tint color adjustments
- The system handles light/dark adaptation; the key challenge is ensuring branded tint colors remain visible on the more transparent surfaces
- App icons that interact with Liquid Glass chrome should use strongly saturated colors for legibility

**Source:** WWDC 2018 Session 210, `developer.apple.com/documentation/AppKit/NSVisualEffectView`, HIG Materials page, oskargroth.com NSVisualEffectView reverse engineering (Dec 2025), r/iOSProgramming Liquid Glass threads

---

## 7. Do's and Don'ts

### 7.1 Color Token Usage

| Do | Don't |
|---|---|
| Use `NSColor.labelColor` for primary text | Hard-code `NSColor(white: 0, alpha: 1)` for text — it breaks in Dark Mode |
| Use `NSColor.controlAccentColor` for interactive affordances | Always use `NSColor.systemBlue` for controls — breaks Graphite and non-blue accent colors |
| Use `NSColor.systemRed` for destructive actions | Hard-code `#FF0000` for errors — not calibrated for dark mode legibility |
| Use `NSColor.windowBackgroundColor` for window backgrounds | Use `#ECECEC` directly — will not adapt to dark mode |
| Use semantic fill colors for control surfaces | Layer pure white at 10% opacity — reduces legibility on dark backgrounds |
| Use opacity-based label colors (secondary/tertiary) | Use flat gray hex values for secondary text — wrong contrast on colored backgrounds |

### 7.2 Dark Mode Implementation

| Do | Don't |
|---|---|
| Define light and dark variants in asset catalog color sets | Provide only a light variant and assume it works everywhere |
| Add High Contrast variants to every custom color | Assume standard light/dark variants work for accessibility |
| Convert icon images to template images | Use full-color image assets for monochrome icons — they disappear or look wrong in dark mode |
| Express UI state semantically (pressed, hover, selected) using system states | Apply constant 30% darkening for pressed states — produces invisible controls in dark mode |
| Override `NSAppearance` at the window level when forced | Apply `NSAppearance` overrides per-view — causes visual glitches at boundaries |
| Use `NSColor.controlAccentColor` in custom controls | Reference `accentColor` preference via `UserDefaults` directly |
| Let system colors handle vibrancy context | Draw fixed RGB colors into vibrant surfaces — produces muddy, unsaturated appearance |

### 7.3 Accessibility

| Do | Don't |
|---|---|
| Verify 4.5:1 contrast ratio for all body text against its background | Assume system colors are always accessible — check custom combinations |
| Pair color with shape/label for state communication | Use color as the only differentiator (e.g., only a red border for error) |
| Test with Increase Contrast and Reduce Transparency enabled | Only test in default light and dark modes |
| Provide High Contrast variants for custom asset catalog colors | Provide only standard appearance slots |
| Use Color Filters simulator for color blindness testing | Only test with normal color vision |
| Use SF Symbol multicolor/hierarchical rendering for icons | Use single-color icons where multiple semantic levels exist |

### 7.4 Vibrancy & Materials

| Do | Don't |
|---|---|
| Use semantic `NSVisualEffectView` materials (`.sidebar`, `.menu`, etc.) | Use deprecated fixed-appearance materials — they do not adapt to dark mode |
| Use opaque grayscale colors for content rendered on vibrancy | Use white/black at low opacity for vibrancy content — desaturates the background |
| Use template images for glyphs inside `NSVisualEffectView` | Use full-color images for monochrome glyphs on vibrancy |
| Refresh `CALayer` color properties in `viewDidChangeEffectiveAppearance` | Set `layer.backgroundColor` once and assume it adapts |
| Use `.behindWindow` blending for sidebars and toolbars | Force `.withinWindow` for elements that need desktop-blending effect |

---

## 8. Sources

All claims in this document trace to the following verified sources:

| Source | URL | What It Provides |
|---|---|---|
| Apple HIG — Color | `developer.apple.com/design/human-interface-guidelines/color` | Primary color philosophy and macOS-specific guidance |
| Apple HIG — Dark Mode | `developer.apple.com/design/human-interface-guidelines/dark-mode` | Dark mode adaptation rules |
| Apple HIG — Materials | `developer.apple.com/design/human-interface-guidelines/materials` | Material types, blending modes |
| Apple HIG — Accessibility | `developer.apple.com/design/human-interface-guidelines/accessibility` | Color accessibility requirements |
| NSColor AppKit Docs | `developer.apple.com/documentation/appkit/nscolor` | Official token list |
| NSColor UI Element Colors | `developer.apple.com/documentation/appkit/ui-element-colors` | Complete semantic color table |
| NSColor Fill Colors (systemFill) | `developer.apple.com/documentation/appkit/nscolor/systemfill` | Fill color hierarchy (macOS 14+) |
| NSVisualEffectView Docs | `developer.apple.com/documentation/AppKit/NSVisualEffectView` | Material types, blending modes, vibrancy |
| Apple Accessibility Contrast Criteria | `developer.apple.com/help/app-store-connect/manage-app-accessibility/sufficient-contrast-evaluation-criteria/` | Apple's 4.5:1 contrast standard |
| WWDC 2018 Session 210 — Introducing Dark Mode | `nonstrict.eu/wwdcindex/wwdc2018/210/` | Core dark mode rules, NSColor behavior, vibrancy |
| WWDC 2018 Session 218 — Advanced Dark Mode | `docs.huihoo.com/apple/wwdc/2018/218_advanced_dark_mode.pdf` | NSVisualEffectView advanced patterns |
| WWDC 2014 Session 220 — Advanced UI OS X Yosemite | `nonstrict.eu/wwdcindex/wwdc2014/220/` | Behind-window vs. within-window blending |
| Runtime NSColor Hex Values | `gist.github.com/andrejilderda/8677c565cddc969e6aae7df48622d47c` | Exact hex values extracted at runtime from macOS |
| Dynamic Color Guide | `github.com/onmyway133/blog/issues/792` | Asset catalog implementation, CALayer adaptation |
| Dark Color Cheat Sheet | `sarunw.com/posts/dark-color-cheat-sheet/` | RGBA values for semantic colors |
| Big Sur Accent Colors | `512pixels.net/2020/11/big-sur-accent-highlight-colors/` | Accent/highlight color behavior after Big Sur |
| NSHipster — Color Literals | `nshipster1.rssing.com/chan-6995329/all_p18.html` | Color literals cannot use named/dynamic colors |
| NSVisualEffectView Reverse Engineering | `oskargroth.com/blog/reverse-engineering-nsvisualeffectview` | Blending mode internals (Dec 2025) |
| WCAG 2.1 Contrast Requirements | `webaim.org/articles/contrast/` | Contrast ratio specifications (4.5:1, 3:1, 7:1) |
| Liquid Glass UI (macOS 26) | `medium.com/@dorangao/build-a-macos-swiftui-app-with-a-tahoe-style-liquid-glass-ui-fecb8029b2d8` | Liquid Glass material and color interaction |
| macOS Accent Color History | `idownloadblog.com/2018/06/18/mac-accent-color-howto/` | Available accent colors since macOS Mojave |

---

## Quick Lookup Cheat Sheet

### "What color do I use for...?"

| Use Case | Token |
|---|---|
| Primary text | `NSColor.labelColor` / `Color(.labelColor)` |
| Secondary text | `NSColor.secondaryLabelColor` |
| Placeholder text | `NSColor.placeholderTextColor` |
| Window background | `NSColor.windowBackgroundColor` |
| Content area background | `NSColor.controlBackgroundColor` |
| Behind document content | `NSColor.underPageBackgroundColor` |
| Interactive control (button, checkbox) | `NSColor.controlAccentColor` |
| Destructive action | `NSColor.systemRed` |
| Success/positive state | `NSColor.systemGreen` |
| Warning | `NSColor.systemOrange` |
| Link / navigation | `NSColor.linkColor` |
| Table/list row divider | `NSColor.separatorColor` |
| Selected row (focused window) | `NSColor.selectedContentBackgroundColor` |
| Selected row (unfocused window) | `NSColor.unemphasizedSelectedContentBackgroundColor` |
| Column header text | `NSColor.headerTextColor` |
| Error/find highlight | `NSColor.findHighlightColor` |
| Sidebar background material | `NSVisualEffectView` with `.sidebar` material |
| Focus ring | `NSColor.keyboardFocusIndicatorColor` |
| Disabled control text | `NSColor.disabledControlTextColor` |
| Alternating table rows | `NSColor.alternatingContentBackgroundColors[0/1]` |

---

## 9. Custom Dynamic Colors in AppKit

`NSColor(name:dynamicProvider:)` (macOS 10.15+) creates colors that adapt to all four appearance variants:

```swift
let brandColor = NSColor(name: "Brand") { appearance in
    switch appearance.name {
    case .aqua, .vibrantLight, .accessibilityHighContrastVibrantLight:
        return NSColor(srgbRed: 0.0, green: 0.48, blue: 1.0, alpha: 1.0)
    case .darkAqua, .vibrantDark, .accessibilityHighContrastVibrantDark:
        return NSColor(srgbRed: 0.04, green: 0.52, blue: 1.0, alpha: 1.0)
    case .accessibilityHighContrastAqua:
        return NSColor(srgbRed: 0.0, green: 0.30, blue: 0.85, alpha: 1.0)
    case .accessibilityHighContrastDarkAqua:
        return NSColor(srgbRed: 0.2, green: 0.65, blue: 1.0, alpha: 1.0)
    default: return NSColor(srgbRed: 0.0, green: 0.48, blue: 1.0, alpha: 1.0)
    }
}
```

All 8 `NSAppearance.Name` values: `.aqua`, `.darkAqua`, `.vibrantLight`, `.vibrantDark`, `.accessibilityHighContrastAqua`, `.accessibilityHighContrastDarkAqua`, `.accessibilityHighContrastVibrantLight`, `.accessibilityHighContrastVibrantDark`.

## 10. Color Resolution in SwiftUI

`Color.resolve(in:)` (macOS 14+) extracts concrete RGBA at runtime:

```swift
@Environment(\.self) private var environment
let resolved = color.resolve(in: environment)  // Color.Resolved — Float RGBA in linear extended sRGB
```

Use for: custom Canvas drawing, exporting colors, computing contrast ratios, bridging to AppKit/Metal. Don't use for general styling — pass `Color` directly.

## 11. Display P3 Wide Gamut

Use P3 for vivid colors outside the sRGB triangle. All Apple Silicon Macs support P3.

```swift
let p3Red = NSColor(displayP3Red: 1.0, green: 0.0, blue: 0.0, alpha: 1.0)  // macOS 10.12+
```

Asset catalog: set Color Space dropdown to "Display P3". Use 16-bit depth to avoid banding.

**Extended sRGB:** Same primaries as sRGB but components can exceed 0–1. The most saturated P3 red maps to extended sRGB ~(1.09, -0.23, -0.15). Clamp to 0–1 before converting to hex.

## 12. CALayer Color Refresh Pattern

**The problem:** `CALayer.backgroundColor`, `.borderColor`, `.shadowColor` take `CGColor` — a frozen snapshot that doesn't update on appearance change.

**The fix:**
```swift
override func viewDidChangeEffectiveAppearance() {
    super.viewDidChangeEffectiveAppearance()
    effectiveAppearance.performAsCurrentDrawingAppearance {  // macOS 11+
        layer?.backgroundColor = NSColor.controlBackgroundColor.cgColor
        layer?.borderColor = NSColor.separatorColor.cgColor
    }
}
```

Alternative: override `updateLayer()` with `wantsUpdateLayer = true` — appearance is already correct there.

| API | Auto-adapts? |
|---|---|
| `NSColor` semantic token | Yes |
| `NSColor(name:dynamicProvider:)` | Yes |
| Asset catalog `NSColor(named:)` | Yes |
| `CGColor` from `.cgColor` | **No** — frozen |
| `CALayer` color properties | **No** — must refresh |
| SwiftUI `Color` | Yes |
| `Color.Resolved` | **No** — snapshot |

## 13. Color Asset Catalogs

Define colors in `.xcassets` with per-appearance slots: Any, Light, Dark, High Contrast Light, High Contrast Dark. Set Color Space to sRGB or Display P3 per slot.

```swift
// AppKit
let color = NSColor(named: "BrandBlue")  // auto-adapts to appearance

// SwiftUI
Color(.brandBlue)  // generated symbol (Xcode 15+)
Color("BrandBlue") // string name
```

Asset catalog colors are fully dynamic — no manual refresh needed (unlike programmatic CGColor).

**Sources:** Apple Developer Documentation (NSColor dynamic provider, NSColorSpace.displayP3, Color.resolve), WWDC 2016/2019, Jesse Squires CGColor articles, Zenn/usagimaru appearance article.
