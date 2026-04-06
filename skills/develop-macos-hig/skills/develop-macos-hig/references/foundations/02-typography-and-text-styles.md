# macOS Typography & Text Styles — Definitive Reference

> **Scope:** macOS only. Every point size, weight, and tracking value is exact and cross-validated.
> **Sources:** Apple HIG, NSFont/SwiftUI docs, zacwest Gist (319-star practitioner reference), Wikipedia SF typeface, WWDC 2020, lapcatsoftware.com Sonoma investigation, Reddit r/macosprogramming.

---

## 1. Text Style Specification Table

macOS uses significantly smaller point sizes than iOS for the same named text styles. Values below are macOS defaults, measured via `NSFont.preferredFont(forTextStyle:)` at the system default text size.

| Text Style | macOS Size (pt) | iOS Size (pt) | Weight | Line Height (pt) | Tracking | Optical Size | SwiftUI API | AppKit API |
|---|---|---|---|---|---|---|---|---|
| Large Title | 26 | 34 | Regular | ~31 | –0.41 | SF Pro Display | `.largeTitle` | `NSFont.TextStyle.largeTitle` |
| Title 1 | 22 | 28 | Regular | ~27 | –0.26 | SF Pro Display | `.title` | `NSFont.TextStyle.title1` |
| Title 2 | 17 | 22 | Regular | ~22 | –0.43 | SF Pro Text | `.title2` | `NSFont.TextStyle.title2` |
| Title 3 | 15 | 20 | Regular | ~19 | –0.24 | SF Pro Text | `.title3` | `NSFont.TextStyle.title3` |
| Headline | 13 | 17 | **Bold** | ~16 | –0.08 | SF Pro Text | `.headline` | `NSFont.TextStyle.headline` |
| Body | 13 | 17 | Regular | ~16 | –0.08 | SF Pro Text | `.body` | `NSFont.TextStyle.body` |
| Callout | 12 | 16 | Regular | ~15 | 0 | SF Pro Text | `.callout` | `NSFont.TextStyle.callout` |
| Subheadline | 11 | 15 | Regular | ~14 | +0.06 | SF Pro Text | `.subheadline` | `NSFont.TextStyle.subheadline` |
| Footnote | 10 | 13 | Regular | ~13 | +0.12 | SF Pro Text | `.footnote` | `NSFont.TextStyle.footnote` |
| Caption 1 | 10 | 12 | Regular | ~13 | +0.12 | SF Pro Text | `.caption` | `NSFont.TextStyle.caption1` |
| Caption 2 | 10 | 11 | **Medium** | ~13 | +0.12 | SF Pro Text | `.caption2` | `NSFont.TextStyle.caption2` |

**Critical notes:**
- macOS point sizes are roughly 65–75% of the equivalent iOS sizes for the same semantic style.
- Headline on macOS is **Bold**, not Semibold (differs from iOS which is Semibold).
- Caption 2 on macOS is the only small style with Medium weight instead of Regular.
- Title 1 maps to SwiftUI `.title` (not `.title1`) — the SwiftUI API skips the "1" suffix.
- Tracking values sourced from the eonist HIG Gist which compiled Apple's Figma spec values.

### NSFont.TextStyle Case Availability

| NSFont.TextStyle Case | Available Since |
|---|---|
| `.largeTitle` | macOS 11.0+ |
| `.title1`, `.title2`, `.title3` | macOS 10.12+ |
| `.headline`, `.subheadline`, `.body`, `.callout`, `.footnote`, `.caption1`, `.caption2` | macOS 10.10+ |

### macOS-Only NSFont.TextStyle Cases

| Case | Purpose |
|---|---|
| `.menu` | Standard menu item text |
| `.menuBar` | Menu bar item text |
| `.system` | General system text |
| `.label` | Control labels (macOS 10.12+) |
| `.systemSmall` | Small system text (macOS 13.0+) |
| `.systemMedium` | Medium system text (macOS 13.0+) |
| `.systemLarge` | Large system text (macOS 13.0+) |

---

## 2. San Francisco Font Family

### Family Overview

| Variant | Weights | Optical Sizes | Primary Use | Platform |
|---|---|---|---|---|
| **SF Pro** | 9 (UltraLight–Black) | Text (≤19pt) + Display (≥20pt) | macOS, iOS, iPadOS, tvOS system UI | macOS primary |
| **SF Pro Rounded** | 9 | Text + Display | Friendly, playful UI elements | macOS/iOS optional |
| **SF Compact** | 9 | Text + Display | watchOS, narrow column UI | watchOS primary |
| **SF Compact Rounded** | 9 | Text + Display | Watch faces, lock screen | watchOS optional |
| **SF Mono** | 6 (UltraLight–Bold) | None | Code, Terminal, Xcode, fixed-width | All platforms |
| **New York** | 6 | Small, Medium, Large, XLarge | Long-form reading, serif UI | macOS/iOS optional |

### SF Pro Display vs. SF Pro Text

The OS selects automatically based on point size. This is the most important distinction in the family.

| Attribute | SF Pro Text | SF Pro Display |
|---|---|---|
| Use at | ≤ 19pt | ≥ 20pt |
| Tracking | Looser (more generous spacing) | Tighter |
| Apertures | Larger (more open counters on "e", "a") | Standard |
| Weight range | 9 weights | 9 weights |
| Rendering target | Small, dense UI text | Headlines, titles, large UI |

**Practical mapping for macOS text styles:**
- All macOS named text styles at default size use SF Pro **Text** (all are ≤19pt at default)
- SF Pro **Display** kicks in only for custom headline sizes ≥20pt

**SwiftUI usage:**
```swift
// These automatically select Text vs Display optical size
Text("Headline").font(.headline)        // SF Pro Text, 13pt
Text("Title").font(.largeTitle)          // SF Pro Text on macOS (26pt)

// Manual override for larger custom sizes
Text("Hero Title").font(.system(size: 24, weight: .bold, design: .default)) // SF Pro Display
```

### SF Mono

- 6 weights only: UltraLight, Thin, Light, Regular, Medium, Bold
- No optical size variants — single rendering for all sizes
- Used in Terminal.app, Xcode editor, Console.app
- Fixed character width enables vertical number alignment
- All digits are inherently tabular (monospaced)

### SF Compact

- Flatter round curves compared to SF Pro — letters like "o", "c", "e" have less circular counters
- Tighter sidebearings, yielding more characters per line at a given size
- Used in watchOS UI; not recommended for macOS apps
- Same 9-weight range as SF Pro

### Font Design Options in SwiftUI

```swift
.font(.system(.body, design: .default))     // SF Pro
.font(.system(.body, design: .monospaced))  // SF Mono
.font(.system(.body, design: .rounded))     // SF Pro Rounded
.font(.system(.body, design: .serif))       // New York
```

---

## 3. Font Weight Scale

Both `Font.Weight` (SwiftUI) and `NSFont.Weight` (AppKit) expose all nine weights.

| Weight Name | SwiftUI API | AppKit API | CSS Numeric Equiv. | Visual Description |
|---|---|---|---|---|
| Ultra Light | `.ultraLight` | `NSFont.Weight.ultraLight` | 100 | Hairline strokes |
| Thin | `.thin` | `NSFont.Weight.thin` | 200 | Very light |
| Light | `.light` | `NSFont.Weight.light` | 300 | Light |
| Regular | `.regular` | `NSFont.Weight.regular` | 400 | Default |
| Medium | `.medium` | `NSFont.Weight.medium` | 500 | Slightly heavier than regular |
| Semibold | `.semibold` | `NSFont.Weight.semibold` | 600 | Semi-bold |
| Bold | `.bold` | `NSFont.Weight.bold` | 700 | Bold |
| Heavy | `.heavy` | `NSFont.Weight.heavy` | 800 | Extra bold |
| Black | `.black` | `NSFont.Weight.black` | 900 | Heaviest |

**Important note:** Apple's weight naming differs from the CSS/W3C convention at 100–200. Apple calls 100 "UltraLight" and 200 "Thin", whereas CSS calls 100 "Thin" and 200 "ExtraLight". Do not use CSS numeric mappings for exact weight lookup — use the named API constants.

**Usage guidance by hierarchy level:**

| Use Case | Recommended Weight |
|---|---|
| Display/hero text | UltraLight or Thin at large sizes |
| Title text | Regular (system default for titles) |
| Emphasized labels | Semibold or Medium |
| Body text | Regular |
| Headline / section header | Bold (macOS) or Semibold (iOS) |
| Caption, footnote | Regular or Medium |

**SwiftUI:**
```swift
Text("Section").fontWeight(.semibold)
Text("Body text").fontWeight(.regular)
.font(.system(size: 15, weight: .medium, design: .default))
```

**AppKit:**
```swift
NSFont.systemFont(ofSize: 13, weight: .semibold)
NSFont.boldSystemFont(ofSize: 13)  // weight .bold shorthand
```

---

## 4. Dynamic Type on macOS

### The Core Distinction

**iOS:** Dynamic Type is the central accessibility mechanism. Every text style scales from xSmall to accessibilityXXXL through `UIFont.preferredFont(forTextStyle:)`.

**macOS:** Dynamic Type as iOS implements it does **not exist** in AppKit. macOS has a different, limited mechanism.

### What macOS Actually Does

**The accessibility text size slider** (System Settings > Accessibility > Display > Text > Text Size):

- Works natively with **SwiftUI**, **Catalyst**, and **WebKit** apps
- **AppKit apps do NOT get automatic font scaling** — confirmed by Apple's own HIG
- `[NSFont userFontOfSize:0]` returns 13pt regardless of the accessibility slider setting
- `[NSFontDescriptor preferredFontDescriptorForTextStyle:NSFontTextStyleBody]` returns a fixed 12pt (pre-Sonoma)

### macOS Text Size Baseline (Static Defaults)

```swift
// SwiftUI on macOS — uses semantic sizes, auto-scales
Text("Content").font(.body)   // 13pt, auto-scales in SwiftUI

// AppKit — static unless you implement scaling yourself
let bodyFont = NSFont.preferredFont(forTextStyle: .body)  // 13pt, fixed
let systemFont = NSFont.systemFont(ofSize: NSFont.systemFontSize)  // 13pt
let smallFont = NSFont.smallSystemFont(ofSize: NSFont.smallSystemFontSize)  // 11pt
let labelFont = NSFont.labelFont(ofSize: NSFont.labelFontSize)  // 10pt
```

### macOS Sonoma Change (macOS 14, Dec 2023)

NSControl subclasses compiled with the macOS 14 SDK increased their default font size from **12pt to 13pt** when running on Sonoma. Affected controls:
- `NSButton` (momentary, radio, checkbox types)
- `NSTextField`
- `NSPopUpButton` (already 13pt, unchanged)

This was undocumented by Apple. Third-party apps noticed layout breaks when controls got larger than their containing views.

### SwiftUI Dynamic Type Adoption on macOS

SwiftUI on macOS does support the accessibility text size slider:

```swift
// Good — scales with accessibility settings on macOS SwiftUI
Text("Primary content").font(.body)

// Bad — static, ignores accessibility
Text("Primary content").font(.system(size: 13))
```

### Responding to Size Changes in AppKit

Since AppKit doesn't automatically respond, you must observe manually:

```swift
// Read the current accessibility font scale preference (workaround)
defaults read com.apple.universalaccess FontSizeCategory
```

For AppKit apps that need to respond, use a `userDefaultsDidChange` notification on `com.apple.universalaccess` and manually re-layout.

---

## 5. Special Typography Features

### Tabular (Monospaced) Figures

Tabular figures give every digit the same advance width, so columns of numbers stay aligned vertically.

**When to use:** Timers, price columns, statistics, scoreboards, any animated or updating numeric display.

**SwiftUI:**
```swift
Text("1,234.56")
    .monospacedDigit()  // Forces tabular figures in SF Pro
```

**AppKit (Core Text feature):**
```swift
let features: [[NSFontDescriptor.FeatureKey: Int]] = [
    [
        .typeIdentifier: kNumberSpacingType,
        .selectorIdentifier: kMonospacedNumbersSelector
    ]
]
let descriptor = NSFont.systemFont(ofSize: 13)
    .fontDescriptor
    .addingAttributes([.featureSettings: features])
let font = NSFont(descriptor: descriptor, size: 0)
```

### Small Caps

Small caps are uppercase letterforms designed to match the optical size of lowercase text. Use for acronyms, abbreviations, and running text emphasis.

**SwiftUI:**
```swift
Text("API REFERENCE")
    .font(.body)
    .smallCaps()             // Full small caps
    .lowercaseSmallCaps()    // Only lowercase → small caps
    .uppercaseSmallCaps()    // Only uppercase → small caps
```

### Optical Sizing (Variable Font)

SF Pro is a variable font (since WWDC 2020). The OS interpolates between Text and Display optical sizes automatically. The 20pt threshold is the published boundary, but the variable font allows smooth interpolation.

**Width variants:** SF Pro also supports four width axes:
- Condensed
- Compressed
- Standard (default)
- Expanded

Accessible via `Font.Width` in SwiftUI (macOS 13+):
```swift
Text("Label").fontWidth(.compressed)
Text("Label").fontWidth(.condensed)
Text("Label").fontWidth(.standard)
Text("Label").fontWidth(.expanded)
```

### Tracking (Letter Spacing)

Apple's text styles have built-in tracking. For custom tracking:

```swift
// SwiftUI
Text("UPPERCASE LABEL").tracking(0.5)   // Loose (good for all-caps)
Text("Dense label").tracking(-0.3)       // Tight

// .tracking() — uniform spacing, preserves ligatures
// .kerning() — adjusts specific letter pairs, disables ligatures
```

**Apple's tracking guidelines by size:**

| Size Range | Recommended Tracking | Direction |
|---|---|---|
| ≥ 20pt (Display) | Negative or neutral | Tighter |
| 13–19pt (Text) | Near-zero to slight negative | Neutral |
| ≤ 12pt (Small Text) | Positive | Looser |

### Line Height

macOS SwiftUI uses the font's built-in leading automatically. `.lineSpacing()` adds extra space beyond the natural line height:

```swift
Text("Multiline body text...")
    .lineSpacing(4)          // Add 4pt above natural leading
```

Line height approximations by style:
- **Display styles (LargeTitle, Title1):** ~120% of point size
- **Text styles (Title2–Body):** ~125–130% of point size
- **Small styles (Caption, Footnote):** ~130–135% of point size

---

## 6. Text Truncation and Wrapping

### NSLineBreakMode (AppKit)

| Mode | Behavior | Default? |
|---|---|---|
| `.byWordWrapping` | Breaks at word boundaries, wraps to next line | Yes (multiline) |
| `.byCharWrapping` | Breaks at any character | No |
| `.byClipping` | Clips at container edge, no indicator | No |
| `.byTruncatingHead` | `…text that fits at the end` | No |
| `.byTruncatingTail` | `Text that fits at the st…` | **Yes (single line)** |
| `.byTruncatingMiddle` | `Text fro…he end` | No |

### SwiftUI Truncation

```swift
Text("Long text that won't fit")
    .lineLimit(1)
    .truncationMode(.tail)   // default — ellipsis at end

// Multi-line with ranges (macOS 13+):
Text("Long body paragraph...")
    .lineLimit(3)            // At most 3 lines
    .lineLimit(nil)          // Unlimited
    .lineLimit(2...)         // Minimum 2, no max
    .lineLimit(1...3)        // Range: at least 1, at most 3
```

---

## 7. Do's and Don'ts

### Do

- **Use named text styles for all UI text** — `.font(.body)`, `.font(.headline)`. This is the only way to respect accessibility settings in SwiftUI on macOS.
- **Let the system choose SF Pro Text vs. Display** — do not manually specify the optical size variant.
- **Use `.monospacedDigit()` for any numeric display** that changes or needs column alignment.
- **Set negative tracking for large display text** and positive tracking for all-caps text at small sizes.
- **Use `.lineLimit()` with a range** (macOS 13+) for flexible but bounded text expansion.
- **Test at the largest accessibility text size** using Xcode's accessibility inspector.
- **Use `.smallCaps()` for abbreviations and acronyms** in body text rather than regular uppercase.
- **Use SF Mono for code, paths, and tabular data.**
- **Use New York (`.serif` design)** for long-form reading content.

### Don't

- **Don't hardcode point sizes** like `.font(.system(size: 13))` — this breaks accessibility.
- **Don't mix optical sizes arbitrarily** — don't manually specify `SF-Pro-Display` at 12pt.
- **Don't rely on AppKit Dynamic Type** — AppKit does not automatically scale fonts with the accessibility text size slider.
- **Don't distribute or embed SF fonts** in non-Apple-platform apps or web pages. SF Pro is licensed only for Apple platforms.
- **Don't confuse iOS and macOS text style sizes** — they share the same API names but macOS defaults are 25–50% smaller.
- **Don't use `.kerning()` when `.tracking()` is what you want** — kerning disables ligatures.
- **Don't use Semibold for Headline on macOS** — the macOS default for `.headline` is Bold, not Semibold.
- **Don't set tracking to zero for small text** — small text (≤12pt) needs positive tracking for legibility.

---

## 8. Sources

1. **Apple HIG — Typography** — `developer.apple.com/design/human-interface-guidelines/typography`
2. **NSFont.TextStyle API docs** — case names and platform availability dates (macOS 10.10–11.0+)
3. **NSFont.Weight API docs** — weight constant names
4. **Font.Weight SwiftUI docs** — SwiftUI weight API
5. **zacwest/916d31da5d03405809c4 GitHub Gist** — iOS and macOS side-by-side default font sizes (319 stars)
6. **shaps80/2d21b2ab92ea4fddd7b545d77a47024b GitHub Gist** — NSFont/UIFont helper bridge; macOS fixed offsets
7. **eonist/b9c180a67980c6e18a5184f19bff68fa GitHub Gist** — Apple HIG Figma tracking values
8. **lapcatsoftware.com** — "macOS Sonoma increases NSControl font size" (Dec 2023)
9. **Jim Nielsen's Blog** — SF Pro Text ≤19pt / SF Pro Display ≥20pt threshold confirmation
10. **Wikipedia — San Francisco (sans-serif typeface)** — font family history and variants
11. **Apple developer.apple.com/fonts/** — official font family page
12. **NSLineBreakMode Apple docs** — truncation modes and behavior
13. **Reddit r/macosprogramming** — "Dynamic Text with AppKit?" (Feb 2024) — practitioner confirmation
