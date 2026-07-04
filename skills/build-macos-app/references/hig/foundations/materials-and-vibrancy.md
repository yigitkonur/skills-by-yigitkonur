# macOS Materials, Vibrancy & Visual Effects — Definitive Reference

---

## 1. Material Types Catalog

macOS visual materials are implemented through `NSVisualEffectView` (AppKit) and SwiftUI's `.background()` modifier with system materials. Every material is a combination of blur radius, tint color, and opacity tuned for a specific UI role.

### Standard Named Materials (NSVisualEffectView.Material)

| Material Case | Visual Appearance | Blending Mode (default) | Primary Usage | Introduced |
|---|---|---|---|---|
| `.titlebar` | Subtle translucent blur matching system title bar chrome | `.withinWindow` | Window title bars | macOS 10.10 |
| `.selection` | Semi-transparent darker tint; highlights selected rows | `.withinWindow` | Table/list row selection | macOS 10.10 |
| `.menu` | Light, fine-grained blur; near-opaque feel | `.behindWindow` | Drop-down and contextual menus | macOS 10.10 |
| `.popover` | Moderate blur; slightly brighter tone than sidebar | `.behindWindow` | Popover panels | macOS 10.10 |
| `.sidebar` | Translucent, slightly dark blur; visually distinct from content | `.withinWindow` | Navigation sidebars (Finder, Mail) | macOS 10.10 |
| `.headerView` | Subtle blur for section headers | `.withinWindow` | Table/collection view section headers | macOS 10.10 |
| `.sheet` | Gentle blur matching surrounding window; medium opacity | `.withinWindow` | Modal sheets attached to windows | macOS 10.10 |
| `.windowBackground` | Uniform translucent fill; general window content area | `.withinWindow` | Window content area backgrounds | macOS 10.10 |
| `.hudWindow` | Dark, high-contrast blur; elevated opacity | `.behindWindow` | Heads-up display overlays | macOS 10.10 |
| `.fullscreenUI` | Strong blur; reinforces readability in full-screen contexts | `.withinWindow` | Full-screen HUDs (e.g., video controls) | macOS 10.10 |
| `.toolTip` | Light, thin-bordered; delicate translucency | `.behindWindow` | Tooltip windows | macOS 10.10 |
| `.contentBackground` | Balanced blur; adapts to light/dark appearance | `.withinWindow` | Generic content containers | macOS 10.10 |
| `.underWindowBackground` | Blur rendered **behind** the window's boundary | `.behindWindow` | Full-window glass framing effect | macOS 10.10 |
| `.underPageBackground` | Behind-page blur in scroll views | `.behindWindow` | Web views, document scrollers | macOS 10.14 |

### Deprecated Materials

| Deprecated Case | Reason | Replacement |
|---|---|---|
| `.light` | Pre-10.10 raw tint (no blur context) | `.appearanceBased` or specific material |
| `.dark` | Pre-10.10 raw dark tint | `.appearanceBased` or specific material |
| `.mediumLight` | Pre-10.10 intermediate tint | `.windowBackground` |
| `.menuBar` | Deprecated macOS 10.14 | `.titlebar` |

### AppKit API

```swift
let effectView = NSVisualEffectView()
effectView.material = .sidebar
effectView.blendingMode = .behindWindow
effectView.state = .active
```

### SwiftUI API (macOS 12+)

```swift
.background(.regularMaterial)      // thickest
.background(.thickMaterial)
.background(.thinMaterial)
.background(.ultraThinMaterial)    // thinnest
.background(.ultraThickMaterial)
```

SwiftUI's named materials (`.regularMaterial`, `.thinMaterial`, etc.) map to `NSVisualEffectView` under the hood but do not expose the specific named cases like `.sidebar` or `.menu` directly. Use `NSViewRepresentable` to access those specific materials in SwiftUI.

---

## 2. Blending Modes

macOS materials have exactly two blending modes. This distinction is one of the most misunderstood aspects of `NSVisualEffectView`.

### `.behindWindow` (Behind-Window Blending)

**What it blurs:** The content of other windows and the desktop wallpaper that sit *behind* the current window in the window stack.

**Visual effect:** The material samples pixels from whatever is rendered behind the window on screen. Moving the window over different content dynamically changes what bleeds through. Classic sidebar in Finder (pre-Tahoe) used this: drag the window over a red document and the sidebar picks up red tint.

**Constraint:** Only works when the window itself has a transparent background. Requires setting `NSWindow.isOpaque = false` and `NSWindow.backgroundColor = .clear`.

**Use cases:** Sidebars (`.sidebar`), menus (`.menu`), popovers (`.popover`), tooltips (`.toolTip`), HUD windows (`.hudWindow`), `underWindowBackground`.

```swift
let effectView = NSVisualEffectView()
effectView.blendingMode = .behindWindow
effectView.material = .sidebar
effectView.state = .active
window.isOpaque = false
window.backgroundColor = .clear
```

### `.withinWindow` (Within-Window Blending)

**What it blurs:** Only the content rendered *within the same window*, behind this view in the z-order within the window's view hierarchy.

**Visual effect:** Blurs views that are siblings or ancestors within the same window. Other windows and the desktop do not contribute to the blur. Used for elements like title bars, where you want the blur to act on the window's own scroll content.

**Constraint:** The `titlebar` material **requires** `.withinWindow`; using `.behindWindow` with titlebar produces undefined results per Apple's documentation.

**Use cases:** Title bars (`.titlebar`), selection highlights (`.selection`), headers (`.headerView`), sheets (`.sheet`).

### Active / Inactive State

| State | Behavior |
|---|---|
| `.followsWindowActiveState` | Default. Renders active blur when window is key/main, dims when inactive |
| `.active` | Forces active (vibrant) appearance regardless of window focus — important for HUD-style floating windows |
| `.inactive` | Forces dimmed appearance |

**Critical production gotcha:** `NSGlassEffectView` (macOS 26) does NOT have a `state` property equivalent. If the hosting `NSWindow` is not a key window, `NSGlassEffectView` becomes significantly more opaque/solid. Unlike `NSVisualEffectView.state = .active`, there is no public API to force active glass rendering on an inactive window as of macOS 26.0–26.4.

---

## 3. Vibrancy Effects

Vibrancy is a secondary rendering layer applied to **subviews** of an `NSVisualEffectView`, not to the blur background itself. It makes foreground content (text, icons, controls) optically readable against the blurred material beneath.

### How Vibrancy Works

The blur background of a material creates a sampled, averaged color from pixels beneath. Without vibrancy, labels and icons placed on this blurred background can lose contrast depending on what's behind the window. Vibrancy compensates by applying a per-pixel adaptive compositing operation to the foreground layer.

The result: text on a `.sidebar` material appears to "glow" slightly, with contrast maintained whether the background content is dark or light. This is achieved via `NSVibrancyEffect`.

### Vibrancy on Content Types

| Content Type | Vibrancy Behavior |
|---|---|
| Labels (`.labelColor`, `.secondaryLabelColor`) | Rendered vibrantly — color adapts to maintain contrast against the blurred background |
| Icons / Template images | Rendered with vibrancy — luminosity adapts to background content |
| Custom colored text | Does NOT automatically vibrate; use `.labelColor` family for automatic vibrancy |
| Images (non-template) | Not vibrancy-aware; renders at face value |
| Controls (NSButton, NSSlider) | System controls render vibrantly when placed inside NSVisualEffectView |

### Vibrancy in SwiftUI

SwiftUI applies vibrancy automatically when you use system materials as view backgrounds:

```swift
Text("Sidebar Item")
    .foregroundStyle(.primary)  // automatically vibrant on material background
    .background(.regularMaterial)
```

---

## 4. Standard Surface Materials

Apple maps specific UI surfaces to specific materials. Deviating from these mappings creates visual inconsistency.

| UI Surface | Recommended Material | Blending Mode | State | Notes |
|---|---|---|---|---|
| **Sidebar** | `.sidebar` | `.behindWindow` | `.followsWindowActiveState` | In Tahoe with Liquid Glass, becomes `NSGlassEffectView`-based floating panel |
| **Menu** | `.menu` | `.behindWindow` | `.active` | Menus always appear active |
| **Popover** | `.popover` | `.behindWindow` | `.active` | Slightly brighter than sidebar; includes a stem/arrow |
| **Sheet** | `.sheet` | `.withinWindow` | `.followsWindowActiveState` | Attached to parent window; dims parent window |
| **Tooltip** | `.toolTip` | `.behindWindow` | `.active` | Smallest, most delicate material |
| **Title bar** | `.titlebar` | `.withinWindow` | `.followsWindowActiveState` | **Must use `.withinWindow`** |
| **HUD** | `.hudWindow` | `.behindWindow` | `.active` | Dark, high-contrast; for floating tool overlays |
| **Selection** | `.selection` | `.withinWindow` | `.followsWindowActiveState` | Row/item selection highlight |
| **Full-screen controls** | `.fullscreenUI` | `.withinWindow` | `.active` | Video playback controls |
| **Window background** | `.windowBackground` | `.withinWindow` | `.followsWindowActiveState` | General content area |

**Practical notes:**
- `.sidebar` with `.behindWindow` is the classic "translucent sidebar" seen in Finder, Mail, Music pre-Tahoe
- `.menu` must always have `.state = .active` — system menus are never rendered inactive
- Sidebar blending requires `window.isOpaque = false` and `window.backgroundColor = .clear`
- The common pattern for a translucent window (e.g., terminal/editor backgrounds) is `.underWindowBackground` with `.behindWindow`

---

## 5. Desktop Tinting

### How Desktop Tinting Works

macOS has a "Tint window background with wallpaper colour" system feature (System Settings > Appearance). When enabled, window chrome elements — including sidebar materials and title bars — sample the dominant color of the desktop wallpaper and apply a subtle tint to their material blur.

The mechanism is purely system-level: apps using standard `NSVisualEffectView` materials automatically receive wallpaper tinting without any developer action.

### Wallpaper Tinting Behavior

- **Behind-window materials** (`.sidebar`, `.menu`, `.popover`) already sample pixels from behind the window, so they naturally reflect the wallpaper when no other window covers that area.
- **Within-window materials** (`.titlebar`) receive wallpaper tint from the system compositor via the tinting feature — they tint toward the wallpaper's dominant hue even though they blur within-window content.
- The effect is subtle by design: Apple uses low-saturation, low-opacity wallpaper sampling.

### Liquid Glass Wallpaper Tinting (macOS 26 / Tahoe)

In macOS 26, Liquid Glass sidebars adopt **ambient lighting simulation**. The sidebar "glass" reflects colors from *nearby* content (other windows placed adjacent to it) rather than strictly reading pixels from behind it. This is a physics simulation — the glass is treated as having a refractive surface that collects light from its surroundings.

- Dragging a window containing a red element next to (but not under) a sidebar causes the sidebar to pick up a red ambient tint
- When that window moves underneath the sidebar (occluded), the sidebar loses the red tint
- This distinguishes Liquid Glass ambient lighting from the classic behindWindow blur

**User Setting:** System Settings > Appearance > "Allow wallpaper tinting in windows" controls the wallpaper color tinting of traditional `NSVisualEffectView` materials. However, Liquid Glass sidebars pick up wallpaper ambient color regardless of this setting.

---

## 6. Liquid Glass / macOS 26 (Tahoe) Material System

### What Liquid Glass Is

Introduced at WWDC 2025 and shipped in macOS 26 (Tahoe), Liquid Glass is a **new rendering primitive** that sits alongside `NSVisualEffectView`.

| Dimension | NSVisualEffectView (pre-Tahoe) | Liquid Glass (macOS 26+) |
|---|---|---|
| Core optical technique | Gaussian blur + tint | **Lensing** — active light bending/refraction |
| Background interaction | Blurs sampled pixels behind view | Refracts and bends light; reflects ambient colors from surrounding content |
| Surface behavior | Static material definition | Dynamic: adapts opacity, tint, shadow based on content behind and nearby |
| Size adaptation | None | Larger elements automatically become more frosted/opaque |
| Interaction response | None | Touch/click causes glass to flex and emit illumination |
| Window activity | `state` property controls | No public `state` control (key window state controls appearance) |
| API | `NSVisualEffectView` | `NSGlassEffectView` (AppKit) / `.glassEffect()` (SwiftUI) |

### Liquid Glass Variants

**Regular Glass**
- Default variant
- Adaptive: automatically shifts tint, adjusts shadow depth, flips between light/dark for legibility
- Works on any background — adjusts to maintain visual separation

**Clear Glass**
- More transparent; deliberately shows background through it
- Does NOT have adaptive behaviors
- Requires a dimming overlay layer for text/icon legibility
- Use only when: (1) the element sits over media-rich content, (2) the content layer can accommodate a dimming overlay, (3) overlying symbols are bold and bright
- Used by: macOS Dock, Control Center

### AppKit API: NSGlassEffectView

```swift
let glassView = NSGlassEffectView()
glassView.cornerRadius = 10.0
glassView.tintColor = .systemBlue  // optional tint
let hostingView = NSHostingView(rootView: contentView)
glassView.contentView = hostingView
parentView.addSubview(glassView)
```

`NSGlassEffectContainerView` groups multiple `NSGlassEffectView` instances so they merge visually into a unified glass surface.

### SwiftUI API: .glassEffect()

```swift
// SwiftUI modifier (macOS 26+)
Button("Action") { ... }
    .glassEffect(in: RoundedRectangle(cornerRadius: 8))

// GlassEffectContainer groups multiple glass elements
GlassEffectContainer {
    Button(...) { }
    Button(...) { }
}
```

### Content Layer vs. Control Layer Philosophy

- **Control Layer**: Where Liquid Glass lives. Navigation bars, sidebars, toolbars, tab bars. Glass elements should be confined to this layer. Do not stack glass on glass.
- **Content Layer**: The app's actual content. Should remain free of glass unless a purposeful dimming overlay is applied.

### macOS 26-Specific Behaviors

- **Floating sidebars**: Sidebars in Finder, Settings, and updated apps are now floating panels with padding (no longer edge-attached). The sidebar shows the window content behind it with lensing.
- **Transparent menu bar**: macOS 26 introduces a fully transparent menu bar option.
- **Dock**: Rebuilt with Liquid Glass layers; the Dock itself is "Clear" variant glass.
- **App icons**: Surrounded by Liquid Glass background; third-party icons that don't conform get enclosed in a glass squircle frame.

### Key Developer Constraint (macOS 26)

`NSGlassEffectView` lacks the `state` property of `NSVisualEffectView`. When the window is not the key window, the glass renders significantly more opaque. This breaks HUD-style windows that intentionally float without taking focus. No public workaround exists as of macOS 26.4.

---

## 7. Do's and Don'ts

### Do

- **Match material to UI role.** Use `.sidebar` for sidebars, `.menu` for menus, `.toolTip` for tooltips. Each material was tuned for its surface.
- **Use `.behindWindow` for surfaces that should show desktop/other-window content.** Sidebars, menus, popovers, and HUDs should blur what's behind the window.
- **Force `.state = .active` on HUD windows.** Floating tool windows that don't take focus should force active appearance to remain readable.
- **Use system label colors for vibrant text.** `.labelColor`, `.secondaryLabelColor`, `.tertiaryLabelColor` render vibrantly on materials. Custom colors do not.
- **Respect the active/inactive state.** Materials intentionally dim when the window loses focus — this is functional, not a bug.
- **Use `NSGlassEffectContainerView` when grouping glass elements.** Multiple adjacent `NSGlassEffectView` instances merge into a unified glass surface when wrapped in a container.
- **Test on varied wallpapers.** Both traditional vibrancy and Liquid Glass behave entirely differently on plain gray vs. colorful gradient wallpapers.
- **Use Accessibility system settings in testing.** "Reduce Transparency" replaces blur with opaque fills; "Increase Contrast" forces black/white rendering. Your UI must remain usable under both.

### Don't

- **Don't use `.behindWindow` on a title bar.** The title bar material must use `.withinWindow`. Explicitly stated in Apple documentation.
- **Don't create custom blur effects using private `CABackdropLayer` APIs.** Bypasses system settings (Reduce Transparency), fails App Store review, and breaks between macOS versions.
- **Don't place Liquid Glass in the content layer.** Glass belongs on navigation/control chrome, not on content areas. Glass-on-glass creates visual noise.
- **Don't assume wallpaper tinting is consistent.** In macOS 26, Liquid Glass picks up ambient color from *adjacent* windows, not just the wallpaper.
- **Don't rely on `NSGlassEffectView.state`** to force active rendering — it doesn't exist.
- **Don't use Clear glass variant for text-heavy surfaces.** Clear glass requires a dimming overlay for legibility — designed for Dock and Control Center, not general app content.
- **Don't use deprecated material cases** (`.light`, `.dark`, `.mediumLight`, `.menuBar`). They produce inconsistent results or may be ignored silently.
- **Don't assume blur appears on plain/black/white wallpapers.** Liquid Glass's visual quality degrades to near-opaque gray on solid wallpapers.

---

## 8. Sources

| Source | Type |
|---|---|
| Apple Developer Documentation — NSVisualEffectView.Material | Official API docs |
| Apple Developer Documentation — blendingMode | Official API docs |
| Apple Developer Documentation — NSVisualEffectView | Official API docs |
| WWDC 2025 Session 219 — Liquid Glass design philosophy | Official Apple session |
| Apple Newsroom — macOS Tahoe Liquid Glass introduction | Official press release |
| r/SwiftUI — NSGlassEffectView beta transparency issue | Practitioner thread |
| r/SwiftUI — "3 days at Apple NYC" Liquid Glass design lab | First-person developer account |
| r/swift — Public API for macOS floating window with glass | Practitioner implementation thread |
| r/swift — Translucent side panel blending mode | NSVisualEffectView implementation Q&A |
| r/MacOS — "I don't understand liquid glass" | Community analysis of ambient lighting behavior |
| r/MacOSBeta — Why Liquid Glass fails on macOS | Design analysis thread |
| r/QtFramework — NSGlassEffectView implementation | Cross-framework implementation details |
| r/SwiftUI — Translucent title bar implementation | NSVisualEffectView+SwiftUI pattern |

> **Shelf-life note:** The Liquid Glass section reflects macOS 26.0–26.4 behavior as of April 2026. The `NSGlassEffectView` API should be re-verified against the macOS 27 SDK when available.
