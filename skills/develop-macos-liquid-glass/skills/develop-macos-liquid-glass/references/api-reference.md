# Liquid Glass API Reference — macOS 26

> **Reading guide.** This file covers the complete Liquid Glass API surface for macOS 26 (Tahoe) across both SwiftUI and AppKit. iOS-only APIs are explicitly marked with **(iOS only)**. When you see a modifier or class here without that label, it is available on macOS 26+. For design principles watch WWDC 2025 Session 219; for implementation details see Sessions 310 (AppKit) and 323 (SwiftUI).

---

## SwiftUI Liquid Glass APIs

### `.glassEffect(_:in:isEnabled:)`

The primary modifier for applying a Liquid Glass material to any view.

```swift
func glassEffect(
    _ style: Glass,
    in shape: some InsettableShape = .rect,
    isEnabled: Bool = true
) -> some View
```

#### The `Glass` struct

`Glass` defines the visual style of the glass material. Three built-in presets exist:

| Preset | Description | Typical use |
|--------|-------------|-------------|
| `.regular` | Default translucent glass with standard material and vibrancy | Toolbar items, tab bars, floating controls |
| `.clear` | Minimal glass — nearly transparent until hovered/active. **Note:** arrived in Xcode 26 beta 5, not the initial release. On macOS, does not fully replicate Control Center/Dock glass density. | Secondary or de-emphasized controls |
| `.identity` | No glass effect rendered (opt-out while keeping the modifier in the chain) | Conditional toggling |

#### `.tint(_:)` on Glass

Applies a color tint to the glass material. The system composites this tint with the underlying content.

```swift
// Tinted glass button
Button("Archive", systemImage: "archivebox") {
    archive()
}
.glassEffect(.regular.tint(.blue), in: .capsule)
```

> **Note:** Tint colors are blended by the system. High-saturation or high-opacity colors may not render as expected because the glass material composites them with the background.

#### `.interactive()` — (iOS only)

```swift
// iOS ONLY — NOT available on macOS 26
Glass.regular.interactive()
```

The `.interactive()` modifier on `Glass` enables continuous platter tracking on iOS (reacting to finger proximity). This API does **not** exist on macOS. On macOS, glass controls already respond to hover states through the standard `onHover` / `NSTrackingArea` mechanisms.

#### Shape parameter

The `in:` parameter accepts any `InsettableShape`. Common options:

```swift
.glassEffect(.regular, in: .capsule)
.glassEffect(.regular, in: .circle)
.glassEffect(.regular, in: .rect)
.glassEffect(.regular, in: .rect(cornerRadius: 12))
.glassEffect(.regular, in: .ellipse)
```

**Container-concentric corner radius** — aligns the corner radius with the enclosing container automatically:

```swift
.glassEffect(.regular, in: .rect(cornerRadius: .containerConcentric))
```

This is critical when nesting glass elements inside other rounded containers. The system calculates the inset radius so curves remain visually concentric.

---

### `GlassEffectContainer`

Glass cannot sample other glass. When multiple glass elements sit near each other, wrap them in a `GlassEffectContainer` so the system composites them as a group against the non-glass background underneath.

```swift
GlassEffectContainer(spacing: 8) {
    Button("Cut", systemImage: "scissors") { cut() }
        .glassEffect(.regular, in: .circle)
    Button("Copy", systemImage: "doc.on.doc") { copy() }
        .glassEffect(.regular, in: .circle)
    Button("Paste", systemImage: "doc.on.clipboard") { paste() }
        .glassEffect(.regular, in: .circle)
}
```

**Init signatures:**

```swift
init(spacing: CGFloat? = nil, @ViewBuilder content: () -> Content)
init(@ViewBuilder content: () -> Content)
```

The `spacing` parameter controls the gap between glass children. When `nil`, the system applies default spacing. All direct children that carry `.glassEffect` will be composited against the same background snapshot.

> **Why this matters:** Without a container, overlapping glass elements sample each other's already-blurred output, producing visual artifacts (double-blur, incorrect refraction). Always group adjacent glass views in a container.

---

### `glassEffectID(_:in:)`

Associates a glass effect with a `Namespace.ID` for morphing transitions between states. When two views in different branches of the view hierarchy share the same glass effect ID and namespace, the system animates the glass platter between them.

```swift
@Namespace private var glassNS

// In state A
Button("Play", systemImage: "play.fill") { }
    .glassEffect(.regular, in: .circle)
    .glassEffectID("playback", in: glassNS)

// In state B
Button("Pause", systemImage: "pause.fill") { }
    .glassEffect(.regular, in: .circle)
    .glassEffectID("playback", in: glassNS)
```

```swift
func glassEffectID(_ id: some Hashable, in namespace: Namespace.ID) -> some View
```

---

### `glassEffectUnion(id:namespace:)`

Combines multiple spatially separated glass effects into a single visual unit. The system renders one continuous glass platter that stretches to encompass all members of the union.

```swift
@Namespace private var unionNS

HStack {
    Label("Wi-Fi", systemImage: "wifi")
        .glassEffectUnion(id: "connectivity", namespace: unionNS)

    Spacer()

    Label("Bluetooth", systemImage: "antenna.radiowaves.left.and.right")
        .glassEffectUnion(id: "connectivity", namespace: unionNS)
}
.glassEffect(.regular, in: .capsule)
```

```swift
func glassEffectUnion(id: some Hashable, namespace: Namespace.ID) -> some View
```

Use this when you want distant controls to appear as one glass surface even though they are in separate layout branches.

---

### `glassEffectTransition(_:isEnabled:)`

Controls how a glass effect appears and disappears during transitions.

```swift
func glassEffectTransition(
    _ transition: GlassEffectTransition,
    isEnabled: Bool = true
) -> some View
```

#### `GlassEffectTransition` values

| Value | Behavior |
|-------|----------|
| `.identity` | No special transition — standard SwiftUI transitions apply |
| `.matchedGeometry` | Morph between two glass effects that share the same `glassEffectID` |
| `.materialize` | The glass platter fades in with a material-specific dissolve (glass "materializes" from nothing). **Note:** This value could not be independently confirmed by web research — `.identity` and `.matchedGeometry` are widely used in practitioner code; `.materialize` may be from a later SDK seed. Verify against your Xcode 26 build. |

```swift
if showControls {
    ControlBar()
        .glassEffect(.regular, in: .capsule)
        .glassEffectTransition(.materialize)
        .transition(.opacity)
}
```

---

### `.backgroundExtensionEffect()`

**Critical on macOS.** Extends a view's content to fill the entire background region, bleeding edge-to-edge behind system chrome (toolbars, sidebars). This is how you make hero content or sidebar backgrounds appear to extend under the title bar and toolbar on macOS.

```swift
func backgroundExtensionEffect() -> some View
```

```swift
NavigationSplitView {
    SidebarContent()
        .backgroundExtensionEffect()
} detail: {
    DetailView()
}
```

Without this modifier, content stops at the safe area inset boundary. With it, the view renders underneath the glass toolbar and title bar, providing the signature Liquid Glass layered depth effect.

> **macOS-specific behavior:** On macOS, windows have glass toolbars by default in Tahoe. Using `.backgroundExtensionEffect()` on your main content allows it to show through the toolbar glass, which is the intended design language.

---

### `.scrollEdgeEffectStyle(_:for:)`

Controls how content fades at scroll edges (top and bottom).

```swift
func scrollEdgeEffectStyle(
    _ style: ScrollEdgeEffectStyle,
    for edges: Edge.Set = .all
) -> some View
```

#### `ScrollEdgeEffectStyle` values

| Value | Behavior | Default on |
|-------|----------|------------|
| `.automatic` | Platform-determined default | — |
| `.soft` | Content fades out gradually at the edge | **iOS 26** |
| `.hard` | Content clips sharply at the edge (no fade) | **macOS 26** |

```swift
ScrollView {
    ContentList()
}
.scrollEdgeEffectStyle(.soft, for: .top)
```

> **macOS default is `.hard`**, not `.soft`. If you want the iOS-style soft fade on macOS, you must opt in explicitly. The hard edge is the macOS convention because toolbars and title bars provide a clear visual boundary.

---

### Button Styles

Two new glass button styles are available:

```swift
// Standard glass button — translucent background
Button("Save") { save() }
    .buttonStyle(.glass)

// Prominent glass button — accent-tinted glass background
Button("Submit") { submit() }
    .buttonStyle(.glassProminent)
```

| Style | Appearance |
|-------|------------|
| `.glass` | Neutral translucent glass platter |
| `.glassProminent` | Glass platter tinted with the current accent color; use for primary actions |

These styles automatically adapt their shape to the context (capsule in toolbars, rounded rect elsewhere).

---

### Toolbar APIs

macOS 26 introduces several toolbar enhancements for Liquid Glass layouts.

#### `ToolbarSpacer`

Inserts explicit spacing in toolbar layouts.

```swift
ToolbarSpacer(.fixed)    // Fixed-width spacer (non-flexible) — verify enum syntax
ToolbarSpacer(.flexible) // Flexible spacer (expands to fill) — verify enum syntax
// Note: Apple docs confirm ToolbarSpacer() (no arg, flexible default).
// The (.fixed)/(.flexible) enum syntax is from practitioner code — verify against SDK.
```

```swift
.toolbar {
    ToolbarItem(placement: .automatic) {
        Button("Action", systemImage: "bolt") { }
    }
    ToolbarSpacer(.flexible)
    ToolbarItem(placement: .automatic) {
        Button("Settings", systemImage: "gear") { }
    }
}
```

#### `.badge(_:)` on toolbar items

Attaches a badge to a toolbar item.

```swift
.toolbar {
    ToolbarItem {
        Button("Inbox", systemImage: "tray") { }
            .badge(5)
    }
}
```

#### `.sharedBackgroundVisibility(_:)`

Controls whether grouped toolbar items share a single glass background or render individually.

```swift
ToolbarItemGroup {
    Button("Bold", systemImage: "bold") { }
    Button("Italic", systemImage: "italic") { }
    Button("Underline", systemImage: "underline") { }
}
.sharedBackgroundVisibility(.hidden) // Each button gets its own glass platter
```

| Value | Behavior |
|-------|----------|
| `.automatic` | System decides (usually shared) |
| `.hidden` | No shared background; each item renders its own glass |
| `.visible` | Force shared background |

#### `.searchToolbarBehavior(_:)`

Controls how the search field behaves in the toolbar.

> **Verification note:** This exact API name could not be independently confirmed in Apple's public documentation. The behavior (collapsing search to an icon) is real and handled by `NSSearchToolbarItem` in AppKit. The SwiftUI modifier name may differ — verify against your Xcode 26 SDK.

```swift
.searchable(text: $query)
.searchToolbarBehavior(.minimized) // Collapses to icon until activated — verify API name
```

#### `ToolbarItemGroup`

Groups multiple toolbar items so they share a single glass platter.

```swift
.toolbar {
    ToolbarItemGroup(placement: .automatic) {
        Button("Cut", systemImage: "scissors") { }
        Button("Copy", systemImage: "doc.on.doc") { }
        Button("Paste", systemImage: "doc.on.clipboard") { }
    }
}
```

#### `.toolbar(removing:)`

Removes default toolbar elements.

```swift
.toolbar(removing: .title) // Hides the window title from the toolbar
```

---

### TabView

#### `.tabViewStyle(.sidebarAdaptable)`

On macOS, this renders the tab view as a **sidebar** (not the floating tab bar seen on iOS/iPadOS). The sidebar uses the standard Liquid Glass sidebar treatment.

```swift
TabView {
    Tab("Library", systemImage: "books.vertical") {
        LibraryView()
    }
    Tab("Search", systemImage: "magnifyingglass") {
        SearchView()
    }
    Tab("Settings", systemImage: "gear") {
        SettingsView()
    }
}
.tabViewStyle(.sidebarAdaptable)
```

> **macOS behavior:** `.sidebarAdaptable` results in a sidebar navigation on macOS, unlike iOS/iPadOS where it produces a floating glass tab bar. The sidebar can collapse and expand following standard macOS conventions.

---

### Window Modifiers

#### `.windowStyle(_:)`

Sets the window chrome style. In macOS 26, the default window style already includes Liquid Glass toolbars.

```swift
WindowGroup {
    ContentView()
}
.windowStyle(.automatic) // Default Liquid Glass chrome
```

#### `.windowToolbarStyle(_:)`

Controls toolbar density and layout.

```swift
// Full-height unified toolbar (default)
.windowToolbarStyle(.unified)

// Compact toolbar — smaller height, denser layout
.windowToolbarStyle(.unifiedCompact)
```

| Style | Behavior |
|-------|----------|
| `.unified` | Standard toolbar height; title integrated into toolbar |
| `.unifiedCompact` | Reduced toolbar height; suitable for utility windows |

---

### `.controlSize(.extraLarge)`

A new size tier added in macOS 26 / iOS 26. Renders controls at a larger-than-large size.

```swift
Button("Get Started") { onboard() }
    .controlSize(.extraLarge)
    .buttonStyle(.glassProminent)
```

The full size progression is now: `.mini` < `.small` < `.regular` < `.large` < `.extraLarge`.

---

## AppKit Liquid Glass APIs (macOS 26)

These are entirely new classes and properties introduced in macOS 26 for adopting Liquid Glass in AppKit applications.

### `NSGlassEffectView`

The AppKit equivalent of `.glassEffect()`. Renders a Liquid Glass material as a view's background. This is the replacement for `NSVisualEffectView` when targeting the Liquid Glass design language.

```swift
let glass = NSGlassEffectView()
glass.contentView = myContentView  // The view rendered on top of the glass
glass.cornerRadius = 12            // Corner radius of the glass platter
glass.tintColor = .controlAccentColor // Optional tint applied to the glass
```

**Key properties:**

| Property | Type | Description |
|----------|------|-------------|
| `contentView` | `NSView?` | The view displayed on top of the glass platter |
| `cornerRadius` | `CGFloat` | Corner radius of the glass shape |
| `tintColor` | `NSColor?` | Optional color tint composited into the glass material |

> **Migration note:** `NSVisualEffectView` continues to work (it is NOT deprecated) but does not produce the Liquid Glass appearance. To adopt the new design, replace `NSVisualEffectView` instances with `NSGlassEffectView`.

> **Critical production constraint:** `NSGlassEffectView` has NO `.state` property equivalent to `NSVisualEffectView.state`. When the hosting `NSWindow` is not the key window, the glass renders significantly more opaque/solid. Unlike `NSVisualEffectView.state = .active`, there is no public API to force active glass rendering on an inactive window. This breaks HUD-style floating windows that intentionally don't take focus. The only known workarounds involve overriding private `NSWindow` methods (`_hasActiveAppearance`, `_hasKeyAppearance`) — which risks App Store rejection. Unresolved as of macOS 26.4.

---

### `NSGlassEffectContainerView`

Groups multiple `NSGlassEffectView` instances so they composite correctly against the same background. This is the AppKit equivalent of `GlassEffectContainer` in SwiftUI.

```swift
let container = NSGlassEffectContainerView()
container.addSubview(glassButton1)
container.addSubview(glassButton2)
container.addSubview(glassButton3)
```

> **Important:** `NSGlassEffectContainerView` does **not** propagate its `cornerRadius` to children. Each child `NSGlassEffectView` must set its own `cornerRadius` independently.

---

### `NSBackgroundExtensionView`

Extends content edge-to-edge behind system chrome (toolbars, title bar). This is the AppKit equivalent of `.backgroundExtensionEffect()` in SwiftUI.

```swift
let extensionView = NSBackgroundExtensionView()
extensionView.contentView = heroImageView
// Add extensionView as the background of your content area
```

Use this when you need content to bleed under the toolbar glass on macOS — for example, a hero image or a sidebar background color.

---

### `NSView.LayoutRegion`

New layout guides that account for the increased window corner radii in macOS 26 Liquid Glass windows. Windows now have larger corner radii, and content near corners must avoid being clipped.

```swift
let guide = view.layoutGuide(
    for: .safeArea(cornerAdaptation: .horizontal)
)

NSLayoutConstraint.activate([
    childView.leadingAnchor.constraint(equalTo: guide.leadingAnchor),
    childView.trailingAnchor.constraint(equalTo: guide.trailingAnchor),
    childView.topAnchor.constraint(equalTo: guide.topAnchor),
    childView.bottomAnchor.constraint(equalTo: guide.bottomAnchor),
])
```

#### Corner adaptation modes

| Mode | Behavior |
|------|----------|
| `.horizontal` | Insets leading/trailing edges to avoid corner clipping |
| `.vertical` | Insets top/bottom edges to avoid corner clipping |
| `.all` | Insets all edges |

---

### NSToolbarItem Changes

Existing `NSToolbarItem` gains new properties for Liquid Glass integration.

#### Remove glass background

```swift
toolbarItem.isBordered = false // Removes the default glass platter background
```

#### Prominent style

```swift
toolbarItem.style = .prominent // Renders with accent color tint (like .glassProminent)
```

> **Note:** `NSToolbarItem.Style.prominent` is available from macOS 26.0+. An alternative approach using a custom `NSButton` with `bezelStyle = .glass` and `bezelColor = .controlAccentColor` achieves a similar effect if you need more control over the button appearance.

#### Custom background tint

```swift
toolbarItem.backgroundTintColor = NSColor.systemBlue
```

#### Badges

New `NSItemBadge` API for adding badges to toolbar items:

```swift
toolbarItem.badge = .count(4)          // Numeric badge
toolbarItem.badge = .text("New")       // Text badge
toolbarItem.badge = .indicator         // Dot indicator (no text/number)
```

```swift
// Full toolbar item setup with badge
let item = NSToolbarItem(itemIdentifier: .inbox)
item.image = NSImage(systemSymbolName: "tray", accessibilityDescription: "Inbox")
item.badge = .count(12)
item.style = .prominent
```

---

### NSButton Glass Bezel

Buttons gain a new `.glass` bezel style and related tinting controls.

```swift
let button = NSButton(title: "Save", target: self, action: #selector(save))
button.bezelStyle = .glass
button.bezelColor = NSColor.systemGreen   // Optional custom glass tint
```

#### Tint Control

Control glass button tint via `bezelColor` (confirmed API):

```swift
button.bezelColor = NSColor.controlAccentColor  // Accent-tinted glass (primary action)
button.bezelColor = NSColor.clear                // Neutral glass (secondary action)
```

> **Verification note:** Some sources reference a `tintProminence` property with `.automatic`, `.none`, `.secondary`, `.primary` values. This property name could not be independently verified against Apple's public SDK headers. The confirmed path for tint control is `bezelColor` on `NSButton` with `.glass` bezel style. If `tintProminence` exists, it may be from a later Xcode 26 seed — verify against your SDK.

---

### NSSplitView Changes

Split views gain new capabilities for Liquid Glass sidebar layouts.

#### Automatic safe area insets

```swift
splitViewItem.automaticallyAdjustsSafeAreaInsets = true
```

When enabled, the split view item automatically adjusts its content's safe area insets to account for the glass toolbar and window chrome. This replaces manual inset calculations.

#### Accessory view controllers

Add views that align to the top or bottom of a split view pane (useful for sidebar headers/footers):

```swift
splitViewItem.addTopAlignedAccessoryViewController(headerVC)
splitViewItem.addBottomAlignedAccessoryViewController(footerVC)
```

These accessories sit within the pane but align to its top or bottom edge, outside the scroll region.

---

### Control Sizing: `prefersCompactControlSizeMetrics`

macOS 26 increases the default size of many controls to match the Liquid Glass design language. If your layout requires the pre-Tahoe (macOS 15 and earlier) sizing, opt out per-view:

```swift
view.prefersCompactControlSizeMetrics = true
```

This reverts buttons, text fields, and other controls within that view hierarchy to their previous, more compact dimensions. Use this sparingly — the larger sizes are the intended Tahoe experience.

---

## macOS vs iOS Feature Availability

| Feature | macOS 26 | iOS 26 | Notes |
|---------|----------|--------|-------|
| `.glassEffect(_:in:isEnabled:)` | Yes | Yes | Core API, identical on both platforms |
| `Glass.regular` / `.clear` / `.identity` | Yes | Yes | |
| `Glass.tint(_:)` | Yes | Yes | |
| `Glass.interactive()` | **No** | Yes | iOS only — enables continuous platter tracking on touch |
| `GlassEffectContainer` | Yes | Yes | |
| `glassEffectID(_:in:)` | Yes | Yes | Morphing transitions |
| `glassEffectUnion(id:namespace:)` | Yes | Yes | |
| `glassEffectTransition(_:)` | Yes | Yes | `.identity`, `.matchedGeometry`, `.materialize` |
| `.backgroundExtensionEffect()` | **Yes — critical** | Yes | Essential on macOS for toolbar/sidebar bleed-through |
| `.scrollEdgeEffectStyle` default | `.hard` | `.soft` | Defaults differ by platform |
| `.buttonStyle(.glass)` | Yes | Yes | |
| `.buttonStyle(.glassProminent)` | Yes | Yes | |
| `.controlSize(.extraLarge)` | Yes | Yes | New size tier |
| `.tabViewStyle(.sidebarAdaptable)` | Sidebar | Floating tab bar | Same API, different presentation |
| `.tabBarMinimizeBehavior` | **No** | Yes | iOS only — controls tab bar auto-hide behavior |
| Floating sidebar | **No** | Yes | iOS only — macOS uses standard collapsible sidebar |
| `.windowStyle()` | Yes | N/A | macOS window concept |
| `.windowToolbarStyle()` | Yes | N/A | macOS-specific |
| `.toolbar(removing: .title)` | Yes | Yes | |
| `ToolbarSpacer` | Yes | Yes | |
| `.sharedBackgroundVisibility` | Yes | Yes | |
| `.searchToolbarBehavior(.minimized)` | Unverified | Unverified | API name not confirmed in Apple docs — behavior is real via NSSearchToolbarItem |
| `NSGlassEffectView` | Yes | N/A | AppKit only |
| `NSGlassEffectContainerView` | Yes | N/A | AppKit only |
| `NSBackgroundExtensionView` | Yes | N/A | AppKit only |
| `NSView.LayoutRegion` | Yes | N/A | Window corner avoidance (AppKit) |
| `NSButton.bezelStyle = .glass` | Yes | N/A | AppKit only |
| `NSToolbarItem.badge` | Yes | N/A | AppKit only |
| `NSToolbarItem.style = .prominent` | Yes | N/A | AppKit only (macOS 26.0+) |
| `NSSplitView` accessory VCs | Yes | N/A | AppKit only |
| `prefersCompactControlSizeMetrics` | Yes | N/A | Revert to pre-Tahoe sizing (AppKit) |
| Window corner radii (larger) | Yes | N/A | macOS 26 windows have larger corner radii |
| Control shapes (capsule default) | Yes | Yes | Many controls default to capsule shape |
| Search placement in toolbar | Toolbar | Below nav bar | macOS keeps search in toolbar; iOS places below navigation |

---

## WWDC 2025 Session Reference

| Session | Title | When to watch |
|---------|-------|---------------|
| 219 | Meet Liquid Glass | Start here — covers design principles, philosophy, and the visual language behind Liquid Glass |
| 310 | Build an AppKit app with the new design | macOS-specific: `NSGlassEffectView`, `NSBackgroundExtensionView`, toolbar item changes, split view updates |
| 323 | Build a SwiftUI app with the new design | SwiftUI APIs: `.glassEffect()`, `GlassEffectContainer`, transitions, toolbar updates, `TabView` changes |
| 356 | Get to know the new design system | Broader design guidelines: spacing, typography, color, and how Liquid Glass fits the overall system |

**Recommended order for macOS developers:**

1. **Session 219** — Understand the design intent before writing code
2. **Session 356** — Learn the full design system (not just glass)
3. **Session 323** — SwiftUI implementation (covers both platforms, note macOS differences)
4. **Session 310** — AppKit implementation (macOS-only, essential if maintaining an AppKit app)

---

## Quick Reference: Common Patterns

### Minimal glass button

```swift
Button("Action", systemImage: "star") { doSomething() }
    .glassEffect(.regular, in: .capsule)
```

### Grouped glass toolbar

```swift
.toolbar {
    ToolbarItemGroup {
        Button("A", systemImage: "a.circle") { }
        Button("B", systemImage: "b.circle") { }
    }
}
```

### Hero content behind glass toolbar (macOS)

```swift
NavigationSplitView {
    Sidebar()
} detail: {
    HeroImage()
        .backgroundExtensionEffect()
}
.windowToolbarStyle(.unified)
```

### Morphing glass transition

```swift
@Namespace private var ns

if isExpanded {
    ExpandedControl()
        .glassEffect(.regular, in: .rect(cornerRadius: 16))
        .glassEffectID("control", in: ns)
        .glassEffectTransition(.matchedGeometry)
} else {
    CompactControl()
        .glassEffect(.regular, in: .circle)
        .glassEffectID("control", in: ns)
        .glassEffectTransition(.matchedGeometry)
}
```

### AppKit glass button with prominent tint

```swift
let button = NSButton(title: "Submit", target: self, action: #selector(submit))
button.bezelStyle = .glass
button.bezelColor = .controlAccentColor  // Confirmed API for glass tint control
// button.tintProminence = .primary      // Unverified — see Tint Control section above
```

### AppKit toolbar item with badge

```swift
let item = NSToolbarItem(itemIdentifier: .messages)
item.image = NSImage(systemSymbolName: "message", accessibilityDescription: "Messages")
item.badge = .count(3)
item.style = .prominent
```
