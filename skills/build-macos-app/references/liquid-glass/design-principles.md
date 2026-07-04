# Liquid Glass Design Principles — macOS 26

> **What this file is.** This is not an API reference. This is a decision framework. Every principle here is operational: what decision to make, why Apple made it, and what fails when the rule is ignored. For API surface details, see `api-reference.md`. For macOS-specific patterns, see `macos-patterns.md`.

---

## 1. The Liquid Glass Design Language

Liquid Glass is not frosted glass. It is not a blur. It is not `UIVisualEffectView` with a new name. Treating it as "a nicer blur" produces code that looks like 2019 with a fresh coat of paint.

Liquid Glass uses **real-time light lensing** to create translucent surfaces. Content behind the glass remains visible — not smeared into a Gaussian haze, but optically bent. The glass itself picks up color from whatever sits beneath it, creating dynamic tonal shifts as the user scrolls, resizes, or moves the window.

Glass is a living material. It has three defining properties:

**Lensing.** Glass bends light from the content behind it. This creates a sense of physical depth without hiding information. A toolbar rendered with `.glassEffect(.regular)` does not obscure the scrolling list beneath it — it refracts it. This is the core visual innovation. The user perceives two distinct layers coexisting, not one layer painted over another.

**Motion.** Glass responds to device motion. On MacBooks with accelerometers, tilting the device shifts specular highlights across the glass surface. On desktop Macs without accelerometers, the system uses cursor proximity and window focus state to drive subtle highlight shifts. The system owns this behavior; custom materials or opacity overrides can break it.

**Adaptive behavior.** Glass is not a fixed material. It shifts its appearance based on three inputs: the content beneath it (dark content produces dark-tinted glass; bright content produces light-tinted glass), the ambient system appearance (light mode, dark mode, accent color), and accessibility settings (Reduce Transparency replaces glass with an opaque frosted surface; Increase Contrast adds visible borders). Hardcoded colors, forced color schemes, and manual opacity block that adaptation.

### The mental model

Model Liquid Glass as a physical pane of tinted glass sitting between two layers: navigation chrome and the content behind it. The implementation only identifies pane placement, shape, and tint. The system handles lensing, light response, and accessibility adaptation.

Manual opacity, blur, shadow tweaks, or background overrides on a glass surface usually mean the implementation is taking over work the system already performs.

---

## 2. The Navigation/Content Divide

This is the most important Liquid Glass decision. If this boundary is wrong, the rest of the styling cannot compensate.

**Glass belongs to the navigation layer. Glass never belongs to the content layer.**

This architectural rule determines whether the app feels native or like a modifier was applied indiscriminately.

### What is the navigation layer?

The navigation layer is everything the user interacts with to *move through* the app — to change views, trigger actions, switch contexts, or control the window. These elements sit above content and provide the structural chrome of the application.

**Navigation layer elements (GETS glass):**
- Toolbars and toolbar items
- Tab bars
- Sidebars (the column itself, not the rows in it)
- Floating action buttons
- Sheets and popovers (the container, not the content inside)
- Menus and context menus
- Alerts and confirmation dialogs
- Inspector panels
- Window-level controls
- Status bars and bottom bars

### What is the content layer?

The content layer is everything the user *looks at* or *reads* — the information the app exists to present. Content is what fills the space that navigation defines.

**Content layer elements (NEVER gets glass):**
- List rows and table cells
- Grid items
- Text blocks and paragraphs
- Images and media
- Cards and content tiles
- Form fields and input areas
- Detail views
- Collection view cells
- Charts and data visualizations
- Document content areas

### The test

Apply this test when an element is ambiguous:

**If removing the element removes the ability to navigate or act, it is navigation — it gets glass.**

**If removing the element removes information, it is content — it does not get glass.**

A sidebar is navigation: remove it and the user cannot switch between sections. A list row is content: remove it and the user loses a piece of data.

A toolbar button is navigation: remove it and the user cannot perform an action. A card showing a summary is content: remove it and the user loses information.

### Why this matters

Glass creates a visual layer that says "this is above the content, this is structural, this is chrome." Glass on content tells the visual system that a list row is structural chrome. The result feels wrong even when the reason is hard to articulate.

Apple's own apps are ruthlessly consistent about this. In Finder, the toolbar and sidebar have glass. List rows never do. In Mail, the toolbar has glass. Message cells never do. In Photos, the toolbar and sidebar have glass. Photo thumbnails never do. There are zero exceptions in Apple's shipping apps.

### The one gray area

Floating controls that sit over content — like a media playback overlay, a zoom control cluster, or a floating formatting palette — are navigation (they enable actions), not content. These get glass. The fact that they overlap content does not make them content.

---

## 3. Concentricity — Apple's Shape Language

Concentricity is the principle that nested shapes share proportional corner radii. It is one reason Apple interfaces feel internally aligned without obvious decoration.

The window's corners establish a baseline radius. Every nested element — toolbar buttons, sidebar items, grouped controls — uses a corner radius that is mathematically proportional to the window's radius. The result is that shapes feel like they belong together, like concentric ripples in water.

### How it works in practice

On macOS 26, the system handles most concentricity automatically. Opt in with `.rect(cornerRadius: .containerConcentric)` instead of hardcoding a radius value:

```swift
// ✅ PREFERRED — concentric corner radius token
.glassEffect(.regular, in: .rect(cornerRadius: .containerConcentric))

// ✅ ALTERNATIVE — dedicated concentric shape type
.glassEffect(.regular, in: ConcentricRectangle())

// ❌ WRONG — hardcoded radius breaks concentric alignment
.glassEffect(.regular, in: .rect(cornerRadius: 12))
```

> **API name note:** `ConcentricRectangle()` is a confirmed SwiftUI Shape type in macOS 26 / iOS 26. The concentric corner radius token on `.rect(cornerRadius:)` may be named `.concentric` in SwiftUI (not `.containerConcentric` — that is the UIKit name on `UICornerConfiguration.containerConcentric(minimum:)`). WWDC sessions reference both approaches. Verify the exact SwiftUI token name against the active Xcode 26 SDK; this document uses `.containerConcentric` as a placeholder that may need updating to `.concentric`.

The concentric system tells the framework: "make this shape's corners proportional to the containing surface." Toolbar children become concentric with the toolbar. Sidebar children become concentric with the sidebar.

### macOS corner radius tiers

The window itself has a corner radius determined by its toolbar style:

| Window Configuration | Approximate Corner Radius | Example |
|---------------------|--------------------------|---------|
| Title-bar-only (no toolbar) | ~16pt | Settings panel, utility window |
| Compact toolbar (icon-only) | ~20pt | Finder, Mail |
| Standard toolbar (icon+text) | ~26pt | Photos, Keynote |

> **Note:** These values are community-measured from macOS 26 betas, not published by Apple. The no-toolbar tier was previously estimated at ~12pt but multiple independent measurements converge on ~16pt.

Toolbar elements are concentric with the window. Buttons within toolbar glass get smaller concentric radii automatically when `.containerConcentric` is used.

### When to use specific shapes

| Shape | When to use | API |
|-------|------------|-----|
| Capsule | High-prominence buttons, large actions | `.capsule` |
| Rounded rectangle (concentric) | Most controls, toolbar items | `.rect(cornerRadius: .containerConcentric)` |
| Circle | Icon-only actions with equal width/height | `.circle` |
| Custom radius | Almost never — only for non-standard UI | `.rect(cornerRadius: N)` |

### The rule

Hardcoded corner radius values inside `.glassEffect()` are almost always a mistake. Use `.containerConcentric`, `.capsule`, or `.circle`.

---

## 4. Hierarchy Through Tinting, Not Weight

Apple does not express UI hierarchy by making important things bigger, bolder, or more colorful. That is the approach of interfaces that shout. Apple expresses hierarchy through **tinting** — a single, restrained application of color that draws the eye without overwhelming it.

### The tinting grammar

Liquid Glass has a precise hierarchy of visual weight controlled entirely by tint and glass variant:

| Level | Purpose | Implementation | Visual weight |
|-------|---------|---------------|---------------|
| **Primary action** | The one most likely next action | `.buttonStyle(.glassProminent)` with `.tint(.accentColor)` | Highest |
| **Secondary actions** | Other available actions | `.buttonStyle(.glass)` with no tint | Medium |
| **Destructive action** | Delete, remove, cancel-with-consequences | `.buttonStyle(.glass)` with `.tint(.red)` | High (by alarm, not prominence) |
| **Informational** | Status indicators, badges, passive elements | Plain glass, no tint, no prominence | Lowest |

### The ONE rule

**One primary action per screen. One. Not two. Not "well, these are both important." One.**

> This rule is consistent with Apple's stated intent ("Apply a single, purposeful tint per screen" — WWDC 2025 Session 219) and mirrors the HIG's long-standing "one default button per view at most" rule for push buttons. While not stated in exactly these words by Apple, violating it produces visual noise.

If a screen has two tinted prominent buttons, neither reads as primary. Pick the most likely next action and make everything else neutral glass.

```swift
// ✅ CORRECT — one primary action
.toolbar {
    ToolbarItem(placement: .cancellationAction) {
        Button("Cancel") { dismiss() }
    }
    ToolbarItem(placement: .confirmationAction) {
        Button("Save") { save() }     // System auto-promotes this
            .tint(.accentColor)
    }
}

// ❌ WRONG — two tinted actions competing for attention
.toolbar {
    ToolbarItem {
        Button("Share") { share() }
            .tint(.blue)
            .buttonStyle(.glassProminent)
    }
    ToolbarItem {
        Button("Save") { save() }
            .tint(.green)
            .buttonStyle(.glassProminent)
    }
}
```

### macOS-specific tinting behavior

macOS toolbar buttons are **monochrome by default**. The system renders them in a neutral tone that matches the glass surface. You apply `.tint()` only to the primary action — the one button that needs to stand out.

On macOS, some practitioners report that glass buttons render with unexpected tint bleed from the accent color. A common workaround is `.tint(.clear)` on secondary actions. This is a practitioner-discovered pattern, not official Apple guidance:

```swift
// macOS secondary button — practitioner workaround for tint bleed
Button("Export", systemImage: "square.and.arrow.up") { export() }
    .buttonStyle(.glass)
    .tint(.clear)  // removes accent tint bleed on some macOS configurations
```

> **Note:** This `.tint(.clear)` pattern is not documented in any WWDC session or Apple API doc. It addresses a rendering quirk, not a design requirement. Test on the target macOS version before applying universally.

### What restraint looks like

Open any Apple app on macOS 26. Count the tinted elements. In Finder: one (the sidebar selection highlight). In Mail: one (the compose button or the send button, never both simultaneously). In Photos: one (the primary editing action). In Settings: zero on most panes — just neutral glass everywhere.

If an app has more tinted elements than a comparable Apple app, remove tint until only the primary action remains.

---

## 5. Typography on Glass

Glass surfaces are dynamic backgrounds. The content behind the glass changes as the user scrolls, the window moves, or the system appearance shifts. This means text on glass must be readable over any background — bright, dark, colorful, or monochrome.

The system handles this through **vibrancy**: text rendered on glass gets a subtle luminance boost that preserves contrast regardless of what sits behind the glass. This only works when the system text rendering pipeline remains intact.

### Rules

**Use `.foregroundStyle(.primary)` — never hardcode text colors.**

```swift
// ✅ CORRECT — system handles contrast on glass
Text("Documents")
    .foregroundStyle(.primary)

// ❌ WRONG — white text becomes invisible on light glass
Text("Documents")
    .foregroundColor(.white)

// ❌ WRONG — fixed color does not adapt to dark mode or glass tinting
Text("Documents")
    .foregroundStyle(Color(red: 0.2, green: 0.2, blue: 0.2))
```

**Use text styles, not point sizes.**

```swift
// ✅ CORRECT — scales with Dynamic Type, adapts to context
Text("Section Title")
    .font(.headline)

// ❌ WRONG — fixed size ignores user preferences
Text("Section Title")
    .font(.system(size: 17, weight: .semibold))
```

**Text style hierarchy for glass surfaces:**

| Text Style | Use on glass | Example |
|-----------|-------------|---------|
| `.largeTitle` | Rarely — only in sheet headers | Welcome screen title |
| `.title`, `.title2`, `.title3` | Section headers in glass sheets | Settings group label |
| `.headline` | Primary label on glass control | Toolbar title |
| `.subheadline` | Secondary label, subtitle | Toolbar subtitle |
| `.body` | Descriptions within glass sheets | Sheet body text |
| `.caption`, `.caption2` | Metadata, timestamps | Badge count, status |
| `.footnote` | Tertiary information | Help text |

**On glass toolbars, prefer symbols over text.** Toolbar space is limited and glass toolbars look cleanest with SF Symbol icons. Use text labels only for the primary action or when the icon would be ambiguous:

```swift
// ✅ Preferred — icon-based toolbar items
Button("Add", systemImage: "plus") { }           // Label hidden by system on macOS
Button("Delete", systemImage: "trash") { }

// ✅ Acceptable — text for primary action
Button("Publish") { }
    .buttonStyle(.glassProminent)
    .tint(.accentColor)
```

---

## 6. Color on Glass — Semantic Only

This principle is absolute: **never use hardcoded colors on glass surfaces.** Not `Color.white`. Not `Color.black`. Not `Color(red:green:blue:)`. Not `Color("MyBrandBlue")`.

Glass adapts to light mode, dark mode, accent color preferences, Reduce Transparency, and Increase Contrast. A hardcoded color cannot adapt to any of these. Fixed color on glass breaks at least one system configuration.

### The color translation table

Translate specific colors to semantic equivalents:

| You want | You type | Why |
|----------|----------|-----|
| White text | `.foregroundStyle(.primary)` | Adapts to dark mode, vibrancy, contrast settings |
| Black text | `.foregroundStyle(.primary)` | Same token — system picks the right value |
| Gray text | `.foregroundStyle(.secondary)` | De-emphasized but still accessible |
| Faint text | `.foregroundStyle(.tertiary)` | Lowest emphasis, still meets contrast ratios |
| Blue accent | `.tint(.blue)` | System blue, which adapts |
| Red for danger | `.tint(.red)` | System red — semantic, accessible, consistent |
| Brand color | `.tint(.accentColor)` | Respects user's system accent color preference |
| Gray background | `.background(.secondary)` | Adapts to appearance and context |
| Custom background | `.glassEffect(.regular)` | Glass IS the background — do not layer another one |

### The tint function rule

Tint communicates function. It is not decoration.

A tinted glass button means: "this button has elevated importance" (primary action), "this action is dangerous" (destructive), or "this item is selected" (active state). If the tint does not communicate one of these three things, remove it.

```swift
// ✅ Tint communicates function — this is the primary action
Button("Send") { send() }
    .buttonStyle(.glassProminent)
    .tint(.accentColor)

// ✅ Tint communicates danger — this deletes data
Button("Delete All", role: .destructive) { deleteAll() }
    .tint(.red)

// ❌ Tint is decorative — purple does not mean anything here
Button("Export") { export() }
    .buttonStyle(.glass)
    .tint(.purple)
```

### Asset catalog colors

If an app has brand colors in the asset catalog, do not apply them directly to glass surfaces. Set the brand color as the app accent color in the asset catalog (`AccentColor`), then use `.tint(.accentColor)` on the primary action. Brand identity still appears, but the glass material system remains intact.

---

## 7. The Shape Language

macOS 26 introduces a relationship between control size and shape. Larger controls get rounder shapes (capsule); smaller controls get tighter shapes (rounded rectangle). This maps visual weight to physical size.

| Control Size | Default Shape | Visual Weight | Typical Use |
|-------------|--------------|---------------|-------------|
| Mini | Rounded rectangle (tight radius) | Minimal | Compact toolbar items, inline controls |
| Small | Rounded rectangle | Low | Secondary actions, sidebar items |
| Regular/Medium | Rounded rectangle | Medium | Standard buttons, toolbar items |
| Large | Capsule | High | Primary actions, sheet CTAs |
| Extra-large | Capsule | Highest | Hero actions, onboarding CTAs |

### The capsule rule

**Capsule shape equals high visual weight. Use it sparingly.**

A capsule button carries high visual weight. A rounded rectangle stays quieter. If every toolbar button is a capsule, hierarchy collapses. Most controls should be rounded rectangles. Reserve capsule for the single primary action when that context needs one.

```swift
// ✅ CORRECT — primary action is capsule, secondary is rounded rect
HStack {
    Button("Cancel") { dismiss() }
        .buttonStyle(.glass)
        // System uses rounded rect at regular size

    Button("Save") { save() }
        .buttonStyle(.glassProminent)
        .controlSize(.large)
        // System uses capsule at large size
}
```

### Shape and glass interaction

The shape passed to `.glassEffect(in:)` determines the glass outline. The glass material fills exactly that shape: `.capsule` makes pill-shaped glass; `.rect(cornerRadius: .containerConcentric)` matches the container proportions.

Choose the shape that matches the control's function. A toolbar item is a rounded rectangle. A prominent CTA is a capsule. An avatar is a circle.

---

## 8. Scroll Edge Effects

When content scrolls under a glass toolbar, macOS needs to decide how to handle the boundary between content and glass. This is the scroll edge effect.

macOS defaults to `.hard` — a visible dividing line at the scroll edge. iOS defaults to `.soft` — a gradual fade. Override deliberately.

### When to use each style

| Style | Behavior | Use when |
|-------|---------|----------|
| `.hard` (macOS default, ALL edges) | Strong dividing line at scroll edge | Document apps, utilities, dense content, any app where clear toolbar/content separation aids comprehension |
| `.soft` (iOS default) | Gradual fade at scroll edge | Media apps, creative tools, immersive experiences where the toolbar should feel like it floats over content |
| `.none` | No effect at scroll edge | Rarely appropriate — content clips under the toolbar with no visual treatment. Exists as a valid API case but use with caution. |

> **Platform defaults:** `.automatic` resolves to `.hard` on macOS for ALL edges (top and bottom). On iOS, `.automatic` resolves to `.soft`. There is no per-edge platform default difference — macOS is `.hard` everywhere.

```swift
// Override macOS default for a media-centric app
.scrollEdgeEffectStyle(.soft, for: .top)

// Keep the default for a document app (or just omit it entirely)
// .scrollEdgeEffectStyle(.hard, for: .top) ← this is the default, don't write it
```

### The decision framework

Ask: "Does the content behind the toolbar contribute to the experience?"

- **Yes** (photo gallery, video editor, canvas) → `.soft` — let content breathe through the glass
- **No** (email list, file browser, settings) → `.hard` — separate toolbar from content clearly

If in doubt, keep the macOS default (`.hard`). It is safe and familiar. Overriding to `.soft` when it is not warranted makes the app feel like a ported iOS app.

---

## 9. Spacing and Density

macOS is denser than iOS. Windows are larger. Controls are smaller. Spacing is tighter. Users have a precise pointing device. Glass does not change that; it adds visual depth without adding visual weight, so spacing can stay tight compared to pre-glass macOS.

### Toolbar spacing

Toolbars are the most common glass surface, and their internal spacing determines whether the app feels organized or chaotic.

**Use spacers to create logical groups:**

```swift
.toolbar {
    // Left group: navigation
    ToolbarItem(placement: .navigation) {
        Button("Back", systemImage: "chevron.left") { }
    }

    // Flexible spacer pushes groups apart
    ToolbarSpacer(.flexible)

    // Center group: editing tools (tightly spaced)
    ToolbarItemGroup {
        Button("Bold", systemImage: "bold") { }
        Button("Italic", systemImage: "italic") { }
        Button("Underline", systemImage: "underline") { }
    }

    // Flexible spacer
    ToolbarSpacer(.flexible)

    // Right group: primary action
    ToolbarItem(placement: .confirmationAction) {
        Button("Done") { }
            .tint(.accentColor)
    }
}
```

**`ToolbarSpacer(.flexible)`** pushes groups apart — use between logically distinct clusters.
**`ToolbarSpacer(.fixed)`** adds a small consistent gap — use within a group to separate sub-clusters.
**`ToolbarItemGroup`** clusters items together — the system may merge their glass platters when appropriate.

### Content spacing

The 8-point grid system remains fundamental on macOS 26. All spacing values should be multiples of 4 (minimum) or 8 (preferred): 4, 8, 12, 16, 20, 24, 32.

Glass adds visual separation between elements because the glass boundary itself creates a perceptual gap. Explicit padding between glass elements can be lower than padding between non-glass elements:

```swift
// Glass elements can be tighter because the glass boundary provides separation
GlassEffectContainer {
    HStack(spacing: 4) {     // 4pt is enough — glass edges provide visual breathing room
        Button("A") { }
            .glassEffect(.regular, in: .capsule)
        Button("B") { }
            .glassEffect(.regular, in: .capsule)
    }
}
```

### GlassEffectContainer spacing

`GlassEffectContainer` has a `spacing` parameter that controls when nearby glass elements visually merge into a single platter versus remaining separate. This is a design decision: merged platters look unified (good for related controls); separate platters look distinct (good for independent actions).

```swift
// Tight spacing — buttons may merge into one glass platter
GlassEffectContainer(spacing: 0) { ... }

// Standard spacing — buttons remain visually separate
GlassEffectContainer(spacing: 8) { ... }
```

### The macOS primary action placement

On macOS, the primary action in a toolbar appears as a **prominent text button**, not just an icon. This is different from iOS where the primary action is often an icon. On macOS, text buttons carry more weight and clarity because users expect explicit labels in toolbar chrome:

```swift
// ✅ macOS primary action — text label, prominent style
ToolbarItem(placement: .confirmationAction) {
    Button("Publish") { publish() }
        .buttonStyle(.glassProminent)
        .tint(.accentColor)
}

// ❌ Icon-only primary action — unclear on macOS
ToolbarItem(placement: .confirmationAction) {
    Button("Publish", systemImage: "paperplane.fill") { publish() }
}
```

---

## 10. Accessibility Is Not Optional

Glass adapts to accessibility settings automatically when the implementation preserves the system adaptation path. Every custom override, hardcoded value, and manual material is a potential accessibility regression.

### What the system does

| Accessibility Setting | Glass Behavior | Do not |
|----------------------|----------------|---------------------|
| **Reduce Transparency** | Glass becomes frosted/opaque solid surface | Override with custom opacity or `.ultraThinMaterial` |
| **Increase Contrast** | Glass gains high-contrast borders and stronger tints | Force transparent backgrounds or remove system borders |
| **Reduce Motion** | Glass animations are dampened or eliminated | Use custom animations that ignore `accessibilityReduceMotion` |
| **Bold Text** | Text weight increases system-wide | Hardcode font weights that do not respect the bold text preference |
| **Dynamic Type** | All text scales to user-preferred size | Use fixed point sizes instead of text styles |

### Code implications

**Every icon-only button needs an accessibility label.** Glass makes icon-only toolbar buttons look beautiful, but VoiceOver users cannot see the icon. Every single one needs `.accessibilityLabel()`:

```swift
Button("Add Item", systemImage: "plus") { addItem() }
    .accessibilityLabel("Add new item")

Button("Delete", systemImage: "trash") { delete() }
    .accessibilityLabel("Delete selected items")
```

**Keyboard navigation must work through all glass controls.** macOS users navigate with Tab and Shift+Tab. Every interactive glass element must be reachable via keyboard. Test by pressing Tab repeatedly — if a glass button gets skipped, it has a focus issue.

**Never override system glass with custom opacity:**

```swift
// ❌ BREAKS Reduce Transparency — glass becomes semi-visible instead of opaque
.glassEffect(.regular)
.opacity(0.7)

// ✅ Let the system handle all opacity states
.glassEffect(.regular)
```

**Test these combinations.** Not individually — in combination. Reduce Transparency + Increase Contrast + Bold Text is a real user configuration. Your glass UI must look correct and usable in that state.

---

## 11. The "Apple Would Never" List

These are patterns that immediately mark code as non-native. If a reviewer sees any of these in production macOS 26 code, the code needs revision.

1. **Glass on list rows or table cells.** Content does not get glass. Ever. Not even "just a subtle touch." The navigation/content divide is absolute.

2. **More than one tinted prominent action per screen.** If two buttons are both `.glassProminent` with `.tint()`, the hierarchy is broken. Pick one.

3. **Hardcoded colors on glass surfaces.** No `Color.white`, no `Color.black`, no `Color(red:green:blue:)` anywhere that glass is rendered. Semantic colors only.

4. **`.interactive()` called on macOS.** This is an iOS-only API. It does not exist on macOS. `.glassEffect(.regular.interactive())` will not compile in macOS code.

5. **Custom blur instead of `.glassEffect()`.** `.blur()`, `.ultraThinMaterial`, or `VisualEffectView` on a surface that should be glass means the code is using deprecated techniques. Use `.glassEffect()`.

6. **`.toolbarBackground(.visible)` on macOS 26.** This forces the old-style opaque toolbar background, which blocks glass rendering entirely. Remove it.

7. **Decorative tinting without semantic meaning.** Apple uses tint to communicate function: blue for standard primary actions, green for positive/confirm, red for destructive. Using tint purely for decoration (any color) weakens the signal. If the tint does not convey primary/destructive/selected status, consider removing it.

8. **Fixed font sizes.** `.font(.system(size: 14))` instead of `.font(.body)`. This breaks Dynamic Type and looks wrong at non-default text sizes.

9. **Missing keyboard shortcuts.** macOS users expect Cmd+N, Cmd+S, Cmd+W, Cmd+Z, Cmd+Comma at minimum. A macOS app without keyboard shortcuts is not a macOS app.

10. **Sidebar without NavigationSplitView.** A sidebar-based layout with `HStack { sidebar; detail }` instead of `NavigationSplitView` loses automatic glass styling, column resizing, collapse behavior, and accessibility.

11. **Custom window chrome.** Hiding the titlebar and drawing a custom toolbar to "make it look like glass" fights the system. Use `.windowStyle(.automatic)` and `.toolbar {}` so the system owns glass chrome.

12. **Glass everywhere.** Applying `.glassEffect()` broadly "to make it look modern" misunderstands the design language. Glass is reserved and structural. Most UI should have zero glass.

---

## 12. The "Apple Ships It" Checklist

Passing every item on this list indicates the code is making the right design decisions, not merely using the right APIs.

### Architecture
- [ ] Navigation layer has glass; content layer does not
- [ ] `NavigationSplitView` used for sidebar-based layouts
- [ ] `.backgroundExtensionEffect()` applied to sidebar content
- [ ] Window style matches app archetype (`.automatic` unless justified)
- [ ] `GlassEffectContainer` wraps all groups of glass elements

### Hierarchy
- [ ] ONE primary action with `.glassProminent` and `.tint(.accentColor)` per screen
- [ ] All other actions use `.buttonStyle(.glass)` with no tint (apply `.tint(.clear)` if tint bleed occurs on macOS)
- [ ] Destructive actions use `.tint(.red)` and `role: .destructive`
- [ ] Glass variant is `.regular` (use `.clear` only if media-rich background justifies it)

### Color and Typography
- [ ] All colors are semantic — no hardcoded RGB, no `Color.white`, no `Color.black`
- [ ] All text uses Dynamic Type text styles (`.title`, `.body`, `.caption` — never fixed sizes)
- [ ] `.foregroundStyle(.primary)` used for text — never `.foregroundColor()` (deprecated)
- [ ] Tint is used for function (primary, destructive, selected) — never for decoration

### Toolbar and Controls
- [ ] Toolbar uses `ToolbarSpacer(.flexible)` and `ToolbarItemGroup` for grouping
- [ ] macOS primary action is a text button (not icon-only) in the toolbar
- [ ] Shape matches control size (rounded rect for standard, capsule for large/hero)
- [ ] Corner radii use `.containerConcentric` — no hardcoded values

### Accessibility
- [ ] All icon-only buttons have `.accessibilityLabel()`
- [ ] Keyboard navigation (Tab/Shift+Tab) reaches all interactive glass elements
- [ ] Tested with Reduce Transparency (glass becomes opaque)
- [ ] Tested with Increase Contrast (glass gains borders)
- [ ] Tested with Dynamic Type at largest size

### macOS Platform
- [ ] Keyboard shortcuts for standard actions (Cmd+N, Cmd+S, Cmd+W, Cmd+Z)
- [ ] Settings scene bound to Cmd+Comma
- [ ] Menu bar commands for all keyboard shortcuts
- [ ] `.scrollEdgeEffectStyle` chosen deliberately (`.hard` for documents, `.soft` for media)
- [ ] No iOS-only APIs (`.interactive()`, iOS-specific placements)
- [ ] No deprecated APIs (`NavigationView`, `.foregroundColor()`, `.background(.ultraThinMaterial)`)

---

## Summary: The Three Questions

Before writing any glass code, answer these three questions:

1. **Is this element navigation or content?** If content, no glass. Stop here.
2. **Is this element the primary action?** If yes, it gets `.glassProminent` with `.tint(.accentColor)`. If no, it gets `.glass` with no tint.
3. **Is the code overriding anything the system would do automatically?** If yes, remove the override.

Get these three answers right, and the rest follows naturally.
