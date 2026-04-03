# Liquid Glass Migration Guide

Migrating existing macOS SwiftUI and AppKit apps to Liquid Glass on macOS 26 Tahoe. Follow phases sequentially; each builds on the previous.

## Phase 1: Automatic Adoption (Compile with Xcode 26)

Recompile your existing project with Xcode 26 and the macOS 26 SDK. The following elements adopt glass automatically with **no code changes**:

- **Toolbars** -- render as a floating glass surface above window content
- **Sidebars** -- become floating and translucent with depth
- **Window controls** -- traffic lights and title bar integrate with glass chrome
- **Menu bar** -- system-wide glass treatment
- **Dock** -- system-wide glass treatment
- **Sheets and popovers** -- glass-backed presentation with system blur
- **Standard controls** -- buttons, sliders, toggles, segmented controls gain glass styling
- **NSPopover** -- glass background replaces legacy vibrancy

> **Action:** Build, run, and visually audit every screen before making any code changes. File bugs for rendering issues at this stage -- they may be system-level.

## Phase 2: Remove Conflicting Customizations

These customizations conflict with Liquid Glass rendering. Remove or guard them behind `#available` checks:

### SwiftUI

| Remove This | Why |
|---|---|
| `.toolbarBackground(.visible)` | Overrides glass with an opaque layer |
| `.toolbarBackground(Color(...))` | Paints a solid color behind the glass surface |
| `.toolbarColorScheme(...)` | Forces a color scheme that makes icons unreadable on glass |
| `.presentationBackground(...)` | System handles sheet backgrounds; custom values clip glass edges |

### AppKit

| Remove This | Why |
|---|---|
| Custom `NSVisualEffectView` materials on navigation elements | Conflicts with automatic glass on toolbars and sidebars |
| Custom background layers behind toolbars | Occludes the glass surface |
| Custom tab bar appearances (`NSTabBarAppearance` overrides) | System tab bars are now glass; custom appearances break the effect |

```swift
// BEFORE -- forced toolbar background
.toolbar {
    ToolbarItem(placement: .principal) { Text("Title") }
}
.toolbarBackground(.visible, for: .windowToolbar)
.toolbarBackground(Color.blue, for: .windowToolbar)
.toolbarColorScheme(.dark, for: .windowToolbar)

// AFTER -- let glass take over
.toolbar {
    ToolbarItem(placement: .principal) { Text("Title") }
}
// All .toolbarBackground and .toolbarColorScheme modifiers removed
```

## Phase 3: Enhance with Glass APIs

Once automatic adoption looks clean, layer in new APIs for richer glass integration.

### Background Extension Effect

Use `.backgroundExtensionEffect()` to let content bleed into the glass chrome. Apply to sidebar content and hero images that should visually merge with the toolbar or navigation bar:

```swift
ScrollView {
    heroImage
        .backgroundExtensionEffect()  // Image extends behind glass toolbar
    // ... remaining content
}
```

### Glass Effect Containers

Group custom glass elements so the system treats them as a unified glass surface:

```swift
GlassEffectContainer {
    HStack(spacing: 12) {
        Button("Play", systemImage: "play.fill") { play() }
            .buttonStyle(.glass)
        Button("Skip", systemImage: "forward.fill") { skip() }
            .buttonStyle(.glass)
    }
}
```

### Glass Button Styles

```swift
// Standard glass button -- subtle, translucent
Button("Action") { }
    .buttonStyle(.glass)

// Prominent glass button -- higher contrast, use for primary actions
Button("Save") { }
    .buttonStyle(.glassProminent)
```

### Toolbar Layout Spacers

```swift
.toolbar {
    ToolbarItem(placement: .automatic) {
        Button("Share", systemImage: "square.and.arrow.up") { }
    }
    ToolbarSpacer(.flexible)  // Pushes subsequent items to the right
    ToolbarItem(placement: .automatic) {
        Button("Settings", systemImage: "gear") { }
    }
    ToolbarSpacer(.fixed)     // Fixed-width gap between items
    ToolbarItem(placement: .automatic) {
        Button("Help", systemImage: "questionmark.circle") { }
    }
}
```

### Glass Morphing Transitions

Assign stable identifiers to glass elements so the system can morph between them during navigation or state changes:

```swift
ForEach(items) { item in
    ItemView(item: item)
        .glassEffectID(item.id)  // Enables morphing transition
}
```

### Tab and Scroll Behaviors

```swift
// iOS -- minimize tab bar on scroll (not applicable to macOS)
// .tabBarMinimizeBehavior(.onScrollDown)

// macOS -- use sidebar-adaptable tab style instead
TabView {
    // tabs...
}
.tabViewStyle(.sidebarAdaptable)

// Scroll edge styling -- verify macOS default is correct for your layout
ScrollView {
    content
}
.scrollEdgeEffectStyle(.hard, for: .top)
```

## Phase 4: Platform-Specific Refinements for macOS

macOS glass rendering has subtleties that differ from iOS. Apply these refinements.

### Glass Button Tinting

On macOS, glass buttons render correctly with a clear tint. Without this, the button may pick up an unwanted accent color:

```swift
Button("Action") { }
    .buttonStyle(.glass)
    .tint(.clear)  // Required for proper macOS glass rendering
```

### Window Background for Editing Surfaces

When you need a solid background behind editable content (text editors, canvases), use the window background style rather than a Material:

```swift
// WRONG -- Material fights with glass
TextEditor(text: $content)
    .background(.ultraThinMaterial)

// RIGHT -- uses the window's own background
TextEditor(text: $content)
    .background(WindowBackgroundShapeStyle.windowBackground)
```

### macOS Toolbar Placement

Use `.secondaryAction` placement for macOS-specific toolbar items that should appear in the trailing section:

```swift
.toolbar {
    ToolbarItem(placement: .secondaryAction) {
        Button("Inspector", systemImage: "sidebar.right") { }
    }
}
```

### Compact Control Size

If the taller default controls in macOS 26 break your layout, opt into compact metrics:

```swift
// AppKit
window.contentViewController?.prefersCompactControlSizeMetrics = true

// SwiftUI
.controlSize(.small)
```

### SF Symbol Variant Updates

macOS 26 prefers non-circle symbol variants. Update SF Symbol references:

```swift
// BEFORE (pre-macOS 26) -- circle variants
Image(systemName: "plus.circle")
Image(systemName: "trash.circle")

// AFTER (macOS 26+) -- plain variants render better on glass
Image(systemName: "plus")
Image(systemName: "trash")
```

## Phase 5: Accessibility and Testing

### Automatic Accessibility Adaptations

Liquid Glass adapts automatically to these system settings:

| Setting | Glass Behavior |
|---|---|
| **Reduce Transparency** | Glass becomes a frosted, nearly opaque surface |
| **Increase Contrast** | High-contrast borders appear around glass elements |
| **Reduce Motion** | Morphing and parallax animations are dampened or removed |

No additional code is needed for these adaptations, but you **must** verify them visually.

### Testing Checklist

Run through every item before shipping:

- [ ] Light mode -- glass renders correctly, text is legible
- [ ] Dark mode -- glass renders correctly, text is legible
- [ ] Reduce Transparency enabled -- frosted appearance, no invisible elements
- [ ] Increase Contrast enabled -- borders visible, nothing lost
- [ ] Reduce Motion enabled -- no jarring animations, morphing suppressed
- [ ] Dynamic Type at all sizes -- glass elements resize, no clipping
- [ ] VoiceOver navigation through glass elements -- all interactive elements announced
- [ ] Keyboard navigation (Tab / Shift+Tab) -- focus rings visible on glass surfaces

## NSVisualEffectView to NSGlassEffectView Migration

For AppKit codebases that use `NSVisualEffectView` directly, migrate to `NSGlassEffectView`:

| Old Pattern | New Pattern |
|---|---|
| `NSVisualEffectView` with `.material` property | `NSGlassEffectView()` -- material is automatic |
| `NSVisualEffectView.state = .active` | Automatic -- adapts to window focus state |
| `NSVisualEffectView` blending modes | Automatic -- glass handles blending internally |
| `NSVisualEffectView` in toolbar | Remove entirely -- toolbar gets glass automatically |
| `NSVisualEffectView.maskImage` for shapes | `NSGlassEffectView.cornerRadius` + standard shape masks |

> **NSVisualEffectView is NOT deprecated.** Keep it as a fallback for pre-Tahoe deployment targets. Use `#available` checks to choose the right view at runtime.

```swift
func makeBackgroundView() -> NSView {
    if #available(macOS 26.0, *) {
        let glass = NSGlassEffectView()
        glass.cornerRadius = 12
        return glass
    } else {
        let vibrancy = NSVisualEffectView()
        vibrancy.material = .sidebar
        vibrancy.blendingMode = .behindWindow
        vibrancy.state = .followsWindowActiveState
        return vibrancy
    }
}
```

## SwiftUI Material Migration

```swift
// OLD (pre-macOS 26)
.background(.ultraThinMaterial)
.presentationBackground(Color.white)

// NEW (macOS 26)
.glassEffect()
// Remove .presentationBackground -- system handles sheet backgrounds
```

For inline replacement across a codebase, the mapping is:

| Old Modifier | New Modifier |
|---|---|
| `.background(.ultraThinMaterial)` | `.glassEffect()` |
| `.background(.thinMaterial)` | `.glassEffect()` |
| `.background(.regularMaterial)` | `.glassEffect(.regular)` |
| `.background(.thickMaterial)` | `.glassEffect(.regular)` |
| `.background(.ultraThickMaterial)` | `.glassEffect(.regular)` |

## Backward Compatibility Patterns

### Adaptive Glass Modifier

A drop-in `View` extension that uses glass on macOS 26+ and falls back to material on earlier versions:

```swift
extension View {
    @ViewBuilder
    func adaptiveGlassEffect(in shape: some Shape = Capsule()) -> some View {
        if #available(macOS 26.0, *) {
            self.glassEffect(.regular, in: shape)
        } else {
            self.background(
                shape.fill(.ultraThinMaterial)
                    .overlay(shape.stroke(.white.opacity(0.2), lineWidth: 1))
            )
        }
    }
}
```

### Marking Legacy Code for Removal

Use `@available` annotations so the compiler flags dead code once you drop pre-Tahoe support:

```swift
@available(macOS, introduced: 15, obsoleted: 26,
           message: "Remove for macOS 26 glass effect")
func applyLegacyVibrancy(to view: NSView) {
    let effect = NSVisualEffectView()
    effect.material = .sidebar
    effect.blendingMode = .behindWindow
    view.addSubview(effect)
    // ... constraint setup
}
```

## Temporary Opt-Out

If your app has critical layout issues and you need time to fix them, you can temporarily opt out of Liquid Glass:

```xml
<!-- Info.plist -->
<key>UIDesignRequiresCompatibility</key>
<true/>
```

> **This opt-out is temporary and will stop working in macOS 27.** Plan to complete your migration before then.

> **Note:** The `com.apple.SwiftUI.DisableSolarium` user default stopped working as of macOS 26.2. Do not rely on it for testing or production opt-out.

## Migration Decision Tree

Use this to determine your migration path:

```
Is your app pure SwiftUI with standard controls?
├── YES
│   └── Follow Phases 1 through 5 sequentially.
│       Most work is removing conflicting modifiers (Phase 2).
│
└── NO (AppKit or mixed)
    │
    ├── Does the app use NSVisualEffectView?
    │   ├── YES
    │   │   └── Replace with NSGlassEffectView where appropriate.
    │   │       Keep NSVisualEffectView as fallback for pre-Tahoe targets.
    │   │       Then follow Phases 1 through 5.
    │   │
    │   └── NO
    │       │
    │       ├── Does it use custom blur or material implementations?
    │       │   ├── YES
    │       │   │   └── Replace custom implementations with system glass APIs.
    │       │   │       Then follow Phases 1 through 5.
    │       │   │
    │       │   └── NO
    │       │       └── Compile with Xcode 26, run the test checklist, ship.
    │       │           Standard AppKit controls adopt glass automatically.
```

## Common Migration Pitfalls

1. **Leaving `.toolbarColorScheme(.dark)` in place** -- causes white icons on a light glass surface, making them invisible. Always remove.
2. **Using `.presentationBackground` on sheets** -- clips glass edges and produces hard borders. Let the system handle sheet backgrounds.
3. **Forgetting `.tint(.clear)` on macOS glass buttons** -- buttons inherit the accent color, looking out of place on glass.
4. **Not testing Reduce Transparency** -- glass becomes opaque. If your layout assumed translucency for visual hierarchy, it may look flat.
5. **Assuming `NSVisualEffectView` removal is required** -- it is not deprecated. Only replace where glass is a better fit.
