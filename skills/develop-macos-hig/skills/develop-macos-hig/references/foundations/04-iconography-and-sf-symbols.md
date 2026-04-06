# macOS Iconography & SF Symbols — Definitive Reference

> **Scope:** macOS only. All sizes in exact pixels/points. All rendering modes with exact behavior.
> **Sources:** Apple HIG, NSImage.SymbolConfiguration docs, SF Symbols app, bjango.com, iconhandbook, liamrosenfeld squircle proof, sparrowcode, nilcoalescing, avanderlee, Stack Overflow.

---

## 1. App Icon Specifications

### 1.1 Required Sizes — Complete Table

Every macOS app submitted to the Mac App Store must supply all of the following PNG files. The system clips the delivered artwork to a squircle mask; supply square, opaque PNGs with no pre-applied rounding.

| Point size | 1x pixels | 2x pixels (Retina) | Primary usage context |
|---|---|---|---|
| 16 pt | 16 x 16 px | 32 x 32 px | Finder list view, Spotlight results |
| 32 pt | 32 x 32 px | 64 x 64 px | Finder column view, Dock (small) |
| 128 pt | 128 x 128 px | 256 x 256 px | Finder large icon view, Get Info |
| 256 pt | 256 x 256 px | 512 x 512 px | Finder icon view, Cover Flow |
| 512 pt | 512 x 512 px | 1024 x 1024 px | Dock, App Store listing |

**Total assets to supply: 10 PNG files** (5 point sizes x 2 scale factors).

The 1024 x 1024 px file serves as the highest-resolution asset and is displayed in the Mac App Store storefront.

**Xcode asset catalog slot names** (AppIcon.appiconset):

```
icon_16x16.png          (16 x 16,    @1x)
icon_16x16@2x.png       (32 x 32,    @2x)
icon_32x32.png          (32 x 32,    @1x)
icon_32x32@2x.png       (64 x 64,    @2x)
icon_128x128.png        (128 x 128,  @1x)
icon_128x128@2x.png     (256 x 256,  @2x)
icon_256x256.png        (256 x 256,  @1x)
icon_256x256@2x.png     (512 x 512,  @2x)
icon_512x512.png        (512 x 512,  @1x)
icon_512x512@2x.png     (1024 x 1024, @2x)
```

### 1.2 Icon Shape: Squircle (Continuous-Curvature Rounded Rectangle)

macOS applies a **squircle mask** — not a simple rounded rectangle — to all app icons.

**Key geometry:**
- Corner radius formula: `r = 0.45 x L` where L is the side length
- At 1024 px: corner radius ~ **461 px**
- At 512 px: corner radius ~ **230 px**
- At 256 px: corner radius ~ **115 px**
- Alternative approximation: `r = L / 6.4` (~15.6%)
- The continuous Bezier path with r = 45% produces 0 px error against the actual Apple mask

The system adds corner rounding and drop shadow automatically. **Do not pre-apply corner rounding or shadows to your PNG files.**

### 1.3 Design Grid and Safe Area

- **Canvas**: 1024 x 1024 px master file recommended
- **Master grid**: 8-pixel grid for the 1024 px master
- **Safe area**: Content within the inner 80% (~820 x 820 px on a 1024 canvas) to avoid clipping at small sizes
- **Format**: PNG with alpha transparency, sRGB color space
- **No pre-applied effects**: no rounded corners, no drop shadows, no gloss

---

## 2. SF Symbols System

### 2.1 Library Overview

SF Symbols 7 (2025) contains **~6,900 symbols** across:
- Nine weights: Ultralight, Thin, Light, Regular, Medium, Semibold, Bold, Heavy, Black
- Three scales: Small, Medium, Large
- Four rendering modes: Monochrome, Hierarchical, Palette, Multicolor
- Variable color support with 0.0–1.0 threshold
- Variable Draw (SF Symbols 7): progressive path rendering

### 2.2 The Four Rendering Modes

#### Monochrome (Default)
- Single color applied uniformly to all symbol layers
- Color inherited from `foregroundStyle`/`foregroundColor`
- SwiftUI: `Image(systemName: "star").foregroundColor(.blue)`
- AppKit: No special configuration needed

#### Hierarchical
- Single tint color; depth via varying opacity across layers
- Primary layer at full opacity; secondary/tertiary at reduced opacity
- SwiftUI: `.symbolRenderingMode(.hierarchical).foregroundStyle(.indigo)`
- AppKit: `NSImage.SymbolConfiguration(hierarchicalColor: .labelColor)`

#### Palette
- Up to three independent colors, one per layer (primary/secondary/tertiary)
- If fewer colors than layers, last color repeats
- SwiftUI: `.symbolRenderingMode(.palette).foregroundStyle(.red, .green, .blue)`
- AppKit: `NSImage.SymbolConfiguration(paletteColors: [.systemRed, .systemGreen, .systemBlue])`

#### Multicolor
- Colors baked into symbol design by Apple; cannot be overridden
- `foregroundStyle` is ignored in multicolor mode
- Adapts to Light/Dark appearance, vibrancy, accessibility
- Not all symbols support multicolor; unsupported fall back to monochrome
- SwiftUI: `.symbolRenderingMode(.multicolor)`
- AppKit: `NSImage.SymbolConfiguration.preferringMulticolor()`

#### Automatic (Preferred)
- System selects the most appropriate rendering mode based on symbol design
- SwiftUI: `.symbolRenderingMode(.automatic)` (default)

---

## 3. Symbol Sizing & Text Alignment

### 3.1 Symbol Scale Values

| Scale | AppKit | SwiftUI | Visual size |
|---|---|---|---|
| Small | `NSImage.SymbolScale.small` | `.imageScale(.small)` | ~0.75x medium |
| Medium | `NSImage.SymbolScale.medium` | `.imageScale(.medium)` | Default (1.0x) |
| Large | `NSImage.SymbolScale.large` | `.imageScale(.large)` | ~1.33x medium |

Scale does not change baseline position or affect surrounding text layout.

### 3.2 Weight Matching with Adjacent Text

SF Symbols must visually match the stroke weight of adjacent text:

| Weight name | NSImageSymbolWeight | Internal CGFloat |
|---|---|---|
| Ultra Light | `.ultraLight` | -1.0 |
| Thin | `.thin` | -0.75 |
| Light | `.light` | -0.5 |
| Regular | `.regular` | -0.25 |
| Medium | `.medium` | 0.0 |
| Semibold | `.semibold` | 0.25 |
| Bold | `.bold` | 0.5 |
| Heavy | `.heavy` | 0.75 |
| Black | `.black` | 1.0 |

**Rules:**
- Next to `.body` text (regular weight) → use `.regular` symbols
- Next to `.headline` text (bold on macOS) → use `.bold` symbols
- SwiftUI auto-inherits weight from ambient font
- AppKit requires explicit configuration

### 3.3 Alignment with Text

- `Image(systemName:)` inside `Text` aligns to **text baseline** automatically
- Interpolation: `Text("Status \(Image(systemName: "checkmark.circle"))")`
- `Label` handles symbol + text alignment automatically
- **Do not** apply `.resizable()` to SF Symbols — destroys baseline alignment and Dynamic Type scaling

### 3.4 Variable Color

Activates symbol layers progressively based on a 0.0–1.0 value:

```swift
// SwiftUI
Image(systemName: "wifi", variableValue: signalStrength)

// AppKit
let config = NSImage.SymbolConfiguration(variableColorThreshold: 0.75)
```

---

## 4. Toolbar, Sidebar, and Menu Icon Sizing

### 4.1 Toolbar Icons (NSToolbar)

| Size mode | Icon size | Enum |
|---|---|---|
| Regular (default) | **32 x 32 px** | `NSToolbar.SizeMode.regular` |
| Small | **24 x 24 px** | `NSToolbar.SizeMode.small` |

Supply both sizes. Use `NSImage.isTemplate = true` for monochrome icons.

**Streamlined toolbar icons** (Mail, Safari style): 19 x 19 px, PDF format.

### 4.2 Sidebar Icons

User-configurable via System Settings > Appearance > Sidebar icon size:

| Setting | Approximate icon size |
|---|---|
| Small | 16 pt (16 x 16 @1x / 32 x 32 @2x) |
| Medium | ~18 pt (system default) |
| Large | 32 pt (32 x 32 @1x / 64 x 64 @2x) |

Use SF Symbols for sidebar icons — they automatically match the current sidebar size setting.

### 4.3 Menu Bar (NSStatusBar) Icons

| Attribute | Specification |
|---|---|
| Maximum height | **22 pt** (full menu bar height) |
| Recommended visual size | **16 x 16 pt** to **18 x 18 pt** |
| 1x PNG size | 16 x 16 px or 18 x 18 px |
| 2x PNG size (Retina) | 32 x 32 px or 36 x 36 px |

Set `NSImage.isTemplate = true` for automatic light/dark mode adaptation. The system uses only the alpha channel for tinting.

---

## 5. Custom Icon Guidelines

### Design Principles (Big Sur onward)

- Squircle shape is the universal canvas
- Break out of the squircle boundary for depth and character
- Maintain visual weight consistent with system icon family
- Flat representations valid; depth optional but encouraged

### Visual Weight and Optical Adjustments

- **Center of visual mass**: nudge content ~3–5% upward from geometric center
- **Stroke width**: match visual density of similarly-sized system icons
- **Color saturation**: legible both at full size and at 16 px

### Custom SF Symbol Export

Custom symbols must be exported from the SF Symbols app as `.svg` templates with correct layer naming:

| Layer name | Purpose |
|---|---|
| `Monochrome` | Base layer for monochrome rendering |
| `Hierarchical` | Layers with depth ordering |
| `Palette` | Separate layers for independent colors |
| `Multicolor` | Fixed-color artwork |

Weight variants required: **Ultralight**, **Regular**, **Black** (minimum). System interpolates intermediate weights.

---

## 6. Do's and Don'ts

### App Icons

| Do | Don't |
|---|---|
| Supply all 10 PNG sizes | Omit any size — system will scale poorly |
| Deliver square, opaque PNGs | Pre-apply corner rounding, shadows, or gloss |
| Design a unique squircle composition | Place a flat logo on white squircle |
| Use 8-pixel grid on 1024 px master | Only test at large sizes |
| Keep critical content within 80% safe area | Place content near clipping edges |

### SF Symbols

| Do | Don't |
|---|---|
| Match symbol weight to adjacent text weight | Use Regular symbols next to Bold text |
| Use `.font()` to drive symbol size | Use `.resizable().frame()` on symbols |
| Set rendering mode intentionally | Leave multicolor on where tint is needed |
| Use `.imageScale()` to fine-tune | Resize with `scaleEffect()` |
| Use `Label("Title", systemImage:)` for pairs | Manual HStack alignment |

### Toolbar and Menu Bar

| Do | Don't |
|---|---|
| Supply both 32 px and 24 px toolbar variants | Let system scale a single size |
| Set `isTemplate = true` for monochrome icons | Use full-color where template needed |
| Keep menu bar icons <= 22 pt tall | Exceed 22 pt height |
| Use PDF or SVG for menu bar icons | Only provide 1x PNG |

---

## 7. Sources

1. Apple HIG — App Icons
2. Apple HIG — SF Symbols
3. Apple HIG — Icons
4. Apple Developer: NSImage.SymbolConfiguration
5. Apple Developer: NSToolbar.SizeMode — "32 by 32 pixel icons"
6. Apple Developer: SF Symbols app — 6,900+ symbols
7. Bjango — Designing Menu Bar Extras
8. Bjango — Smaller Mac App Icons
9. Icon Handbook — OS X reference
10. liamrosenfeld — Apple Icon Quest (squircle mathematical proof)
11. Sparrowcode — SF Symbols Rendering Modes
12. nilcoalescing — Customizing Symbol Images in SwiftUI
13. nilcoalescing — Adapting Symbols to Dynamic Type
14. danielsaidi — SF Symbols 4 Variable Colors
15. avanderlee — Complete SF Symbols Guide
16. fatbobman — Mixing Text and Graphics in SwiftUI
17. Xojo Blog — SF Symbols on macOS (weight CGFloat mapping)
18. Stack Overflow — OS X icon sizes (complete table)
19. Stack Overflow — NSToolbar icon sizes (32/24 confirmation)
20. Stack Overflow — Sidebar icon size
21. Apple Leopard HIG archive — 8-pixel grid, canvas specs
22. dev.to — WWDC 2025 SF Symbols 7
