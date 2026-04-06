# Design Diagnosis: Transformation Catalog

> Read existing SwiftUI code. Spot what is dated. Fix it. Every entry explains WHY the old pattern is wrong and HOW the new pattern is better.
>
> Verified against macOS 26 Tahoe, Xcode 26, Swift 6 -- March 2026.

---

## Section 1: Deprecated API Replacements

Each row is a concrete find-and-replace. The "Design Reason" column is what you tell the developer in a code review.

### Navigation and Structure

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 1 | `NavigationView { }` | `NavigationStack { }` or `NavigationSplitView { }` | iOS 16 / macOS 13 | Type-safe navigation path. `NavigationView` cannot participate in glass transitions or morphing. |
| 2 | `NavigationLink(destination:)` | `NavigationLink(value:)` with `.navigationDestination(for:)` | iOS 16 / macOS 13 | Decouples link from destination. Enables programmatic navigation and deep linking. |
| 3 | `List { }.listStyle(.sidebar)` | `NavigationSplitView { sidebar } detail: { }` | macOS 13 | Proper floating glass sidebar with automatic depth, collapse behavior, and `backgroundExtensionEffect` support. |
| 4 | `HSplitView { }` / `VSplitView { }` | `NavigationSplitView` or `HStack` with `.inspector()` | macOS 13 | Legacy split views do not participate in glass chrome. `NavigationSplitView` gets automatic glass sidebar. |
| 5 | `.navigationBarTitle()` | `.navigationTitle()` | iOS 14 / macOS 11 | The old modifier was iOS-only naming; `.navigationTitle()` works cross-platform and integrates with glass toolbar title area. |

### State Management (Observation)

> **Important:** `@StateObject`, `@ObservedObject`, `@EnvironmentObject`, and `ObservableObject` are **not officially deprecated** — Apple has not added deprecation annotations to these APIs. However, the `@Observable` macro (iOS 17 / macOS 14) is the preferred modern pattern and offers significant performance advantages. The replacements below are recommendations, not deprecation-driven requirements.

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 6 | `class VM: ObservableObject` | `@Observable class VM` | iOS 17 / macOS 14 | Precise property-level invalidation. Only views reading a changed property re-render. Eliminates phantom redraws that cause glass shimmer artifacts. |
| 7 | `@StateObject private var vm = VM()` | `@State private var vm = VM()` (with `@Observable`) | iOS 17 / macOS 14 | With `@Observable`, `@State` owns the lifecycle. Note: `@StateObject` has unique deferred-initialization semantics that `@State` on `@Observable` does not replicate — verify your use case before migrating. |
| 8 | `@ObservedObject var vm: VM` | Direct property `var vm: VM` (with `@Observable`) | iOS 17 / macOS 14 | Observation tracking is implicit. No wrapper needed. |
| 9 | `@EnvironmentObject var store: Store` | `@Environment(Store.self) var store` | iOS 17 / macOS 14 | Type-safe. Compiler error if not injected, instead of runtime crash. |
| 10 | `@Published var name: String` | Remove (automatic in `@Observable`) | iOS 17 / macOS 14 | Every stored property is observed by default. `@Published` is `ObservableObject`-era boilerplate. |
| 11 | `.environmentObject(store)` | `.environment(store)` | iOS 17 / macOS 14 | Matches the `@Environment(Type.self)` consumption side. |

### Styling and Appearance

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 12 | `.foregroundColor(.blue)` | `.foregroundStyle(.blue)` | iOS 17 / macOS 14 | `foregroundStyle` accepts `ShapeStyle`, enabling hierarchical styles (`.primary`, `.secondary`, `.tertiary`) that adapt to glass vibrancy automatically. |
| 13 | `.background(Color.blue)` | `.background(.blue)` with `ShapeStyle` | iOS 17 / macOS 14 | Semantic backgrounds adapt to light/dark mode and glass context. Hardcoded `Color` objects do not. |
| 14 | `.accentColor(.blue)` | `.tint(.blue)` | iOS 15 / macOS 12 | `.accentColor` is deprecated. `.tint()` propagates correctly through glass button styles. |
| 15 | `.cornerRadius(12)` | `.clipShape(.rect(cornerRadius: 12))` | iOS 17 / macOS 14 | `.cornerRadius` clips without considering glass shape. `.clipShape` integrates with `.glassEffect(in:)` shape parameter. |

### Animation

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 16 | `.animation(.spring())` (no value) | `.animation(.spring, value: x)` | iOS 17 / macOS 14 | Value-less `.animation()` animates ALL state changes, causing phantom glass morphing. Value-bound animation is deterministic. |
| 17 | `withAnimation(.easeInOut) { }` (for glass morphing) | `withAnimation(.spring) { }` | macOS 26 | Glass morphing uses spring dynamics internally. Matching the curve prevents visual discontinuity between the glass platter animation and content animation. |
| 18 | `.transition(.slide)` on glass | `.glassEffectTransition(.materialize)` + `.transition(.opacity)` | macOS 26 | Glass requires its own transition. Slide transitions cause the glass platter to clip or trail. |

### Toolbar and Chrome (macOS 26 Liquid Glass)

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 19 | `.toolbarBackground(.visible, for: .windowToolbar)` | Remove entirely | macOS 26 | Overrides glass with an opaque layer. Glass toolbars are automatic. |
| 20 | `.toolbarBackground(Color(...), for: .windowToolbar)` | Remove entirely | macOS 26 | Paints a solid color behind the glass surface, blocking translucency. |
| 21 | `.toolbarColorScheme(.dark, for: .windowToolbar)` | Remove entirely | macOS 26 | Forces a color scheme that makes icons unreadable on glass. Glass adapts to system appearance automatically. |
| 22 | `.presentationBackground(.ultraThinMaterial)` on sheets | Remove entirely | macOS 26 | System applies glass to sheets automatically. Custom presentation backgrounds clip glass edges. |
| 23 | `.presentationBackground(Color.white)` on sheets | Remove entirely | macOS 26 | Opaque sheet backgrounds eliminate the glass layered depth effect. |
| 24 | `.background(.ultraThinMaterial)` on navigation elements | `.glassEffect(.regular, in: shape)` | macOS 26 | Materials are pre-Liquid Glass. Glass provides lensing, specular highlights, motion response, and automatic accessibility adaptation that materials cannot. |
| 25 | `.background(.thinMaterial)` on floating controls | `.glassEffect(.regular, in: shape)` | macOS 26 | Same as above. All material variants on the navigation layer should become glass. |
| 26 | Custom toolbar with `.background(.bar)` | Use `.toolbar { }` (let system handle glass) | macOS 26 | The `.bar` background style predates glass. System toolbars get glass for free. |

### Controls and Buttons

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 27 | `.buttonStyle(.bordered)` for primary actions | `.buttonStyle(.glassProminent)` | macOS 26 | `.bordered` renders flat. `.glassProminent` renders with accent-tinted glass fill, the intended primary action treatment. |
| 28 | `.buttonStyle(.borderedProminent)` | `.buttonStyle(.glassProminent)` | macOS 26 | Direct replacement. Glass prominent has depth and translucency that bordered prominent lacks. |
| 29 | `.buttonStyle(.bordered)` for secondary actions | `.buttonStyle(.glass)` | macOS 26 | Neutral translucent glass platter. Visually consistent with the glass design system. |
| 30 | `Toggle(isOn:) { }.toggleStyle(.switch)` | Same (system auto-adopts glass) | macOS 26 | No code change needed. Standard toggles adopt glass styling automatically when compiled with macOS 26 SDK. |

### Images and Media

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 31 | `Image(systemName: "plus.circle")` in toolbars | `Image(systemName: "plus")` | macOS 26 | macOS 26 prefers non-circle SF Symbol variants. Circle variants look doubled when rendered on a glass platter. |
| 32 | `Image(systemName: "trash.circle")` in toolbars | `Image(systemName: "trash")` | macOS 26 | Same principle. Plain variants render cleanly on glass. |
| 33 | `Image("photo").resizable().frame(width: 300, height: 200)` | `Image("photo").resizable().aspectRatio(contentMode: .fit)` | General | Fixed frames break on different window sizes. Adaptive sizing works with the responsive Liquid Glass layout system. |

### Forms and Input

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 34 | `TextField("Name", text: $name).textFieldStyle(.roundedBorder)` | `TextField("Name", text: $name)` (system default) | macOS 26 | Default text field style adopts glass-era appearance. Explicit `.roundedBorder` overrides the system treatment. |
| 35 | `TextEditor(text: $content).background(.ultraThinMaterial)` | `TextEditor(text: $content).background(.windowBackground)` | macOS 26 | Material on an editing surface conflicts with glass. Window background provides the correct opaque surface for text editing. |

### Sheets and Presentation

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 36 | `.sheet { content.background(.ultraThinMaterial) }` | `.sheet { content }` | macOS 26 | System provides glass sheet background. Manual material blocks glass and can crash (pitfall #24). |
| 37 | `.popover { }.background(Color.white)` | `.popover { }` | macOS 26 | Popovers get automatic glass. Opaque backgrounds defeat the translucency. |

### Window and Scene

| # | Old API | New API | Since | Design Reason |
|---|---------|---------|-------|---------------|
| 38 | `.windowStyle(.hiddenTitleBar)` | `.windowToolbarStyle(.unified(showsTitle: false))` | macOS 26 | Hidden title bar removes glass chrome entirely. Unified toolbar with hidden title preserves glass while removing the title text. |
| 39 | No `Settings` scene | Add `Settings { }` scene | macOS 11 | Every macOS app should have a Settings window (Cmd+Comma). Glass is applied automatically. |
| 40 | `.commands { }` absent | Add `.commands { CommandMenu(...) { } }` | macOS 11 | macOS apps without menu commands feel like ported iOS apps. Menu commands are a platform expectation. |
| 41 | `.controlSize(.regular)` (pre-Tahoe) | Accept new default sizing or use `.controlSize(.small)` | macOS 26 | macOS 26 increases default control height. If old layout is pixel-tuned, adopt the new sizes or explicitly request `.small`. |

---

## Section 2: Design Smell Detection

Each smell is a pattern you can grep for. When you find it, you know the code needs attention.

---

### Smell 1: Hardcoded Colors on Navigation Layer

**What it looks like:**
```swift
// DATED
.background(Color(red: 0.15, green: 0.15, blue: 0.15))

// also DATED
.background(Color(hex: "#1A1A1A"))
.background(Color.black.opacity(0.85))
```

**Why it is wrong:** Hardcoded colors do not adapt to dark mode, Reduce Transparency, Increase Contrast, or the Liquid Glass tinting pipeline. They occlude the glass surface and create a visual "dead spot" in the interface.

**Fix:**
```swift
// NATIVE: Semantic + glass
.glassEffect(.regular, in: .rect(cornerRadius: 12))
```

**Grep pattern:** `Color(red:` or `Color(hex:` or `Color.black.opacity` in navigation-layer views.

---

### Smell 2: Custom Blur Instead of Glass

**What it looks like:**
```swift
// DATED
.background(.ultraThinMaterial)
.cornerRadius(12)
```

**Why it is wrong:** Materials are the pre-Liquid Glass transparency system. They provide a static blur without lensing, specular highlights, motion response, or accessibility adaptation. On macOS 26, combining `.ultraThinMaterial` with `.glassEffect()` causes a runtime crash (pitfall #24).

**Fix:**
```swift
// NATIVE: Glass replaces material on the navigation layer
.glassEffect(.regular, in: .rect(cornerRadius: 12))
```

**Grep pattern:** `.ultraThinMaterial`, `.thinMaterial`, `.regularMaterial`, `.thickMaterial`, `.ultraThickMaterial` on navigation-layer views.

---

### Smell 3: Multiple Tinted Primary Actions

**What it looks like:**
```swift
// DATED: Everything is tinted, nothing stands out
Button("Save") { }.tint(.blue)
Button("Share") { }.tint(.green)
Button("Export") { }.tint(.orange)
```

**Why it is wrong:** When every button is tinted, nothing communicates hierarchy. Liquid Glass uses a single `.glassProminent` action to draw the eye. Everything else is neutral `.glass`.

**Fix:**
```swift
// NATIVE: One primary, rest neutral
Button("Save") { }.buttonStyle(.glassProminent)  // primary
Button("Share") { }.buttonStyle(.glass)           // secondary
Button("Export") { }.buttonStyle(.glass)          // secondary
```

**Grep pattern:** Multiple `.tint(` calls in the same `HStack` or `ToolbarItemGroup`.

---

### Smell 4: Custom Sidebar Layout

**What it looks like:**
```swift
// DATED: Manual sidebar with divider
HStack(spacing: 0) {
    VStack {
        sidebarContent
    }
    .frame(width: 200)
    Divider()
    VStack {
        detailContent
    }
}
```

**Why it is wrong:** Custom sidebars do not get automatic glass treatment, floating behavior, collapse/expand animations, or safe area integration. The `Divider()` is a static line; the glass sidebar has a layered depth effect.

**Fix:**
```swift
// NATIVE: NavigationSplitView
NavigationSplitView {
    sidebarContent
        .backgroundExtensionEffect()
} detail: {
    detailContent
}
```

**Grep pattern:** `HStack` containing a `.frame(width:` followed by `Divider()`.

---

### Smell 5: Fixed Font Sizes

**What it looks like:**
```swift
// DATED: Pixel-perfect typography
Text("Title").font(.system(size: 24, weight: .bold))
Text("Subtitle").font(.system(size: 14))
Text("Body").font(.custom("Helvetica", size: 13))
```

**Why it is wrong:** Fixed sizes do not respond to Dynamic Type. Users who increase text size in System Settings see no change. The HIG text styles also carry correct optical sizing, leading, and tracking for glass surfaces.

**Fix:**
```swift
// NATIVE: Dynamic Type text styles
Text("Title").font(.title)
Text("Subtitle").font(.subheadline)
Text("Body").font(.body)
```

**Grep pattern:** `.font(.system(size:` or `.font(.custom(` without a corresponding `.dynamicTypeSize` clamp.

---

### Smell 6: No Keyboard Shortcuts

**What it looks like:**
```swift
// DATED: Button without keyboard shortcut
Button("New Document") { createDoc() }
```

**Why it is wrong:** macOS users expect standard keyboard shortcuts. An app without shortcuts feels like a ported iOS app. Every standard operation should have a corresponding shortcut.

**Fix:**
```swift
// NATIVE: Button with keyboard shortcut
Button("New Document") { createDoc() }
    .keyboardShortcut("n")
```

**Grep pattern:** `Button(` without a corresponding `.keyboardShortcut(` in the same modifier chain, for standard operations like New, Save, Delete.

---

### Smell 7: Custom Window Chrome

**What it looks like:**
```swift
// DATED: Hidden title bar with custom close/minimize buttons
.windowStyle(.hiddenTitleBar)
// ... custom traffic light buttons
HStack {
    Circle().fill(.red).frame(width: 12)
    Circle().fill(.yellow).frame(width: 12)
    Circle().fill(.green).frame(width: 12)
}
```

**Why it is wrong:** Custom window chrome does not participate in Liquid Glass. The system traffic lights integrate with the glass toolbar. Hiding them and recreating them produces buttons that look wrong on Tahoe and break accessibility (VoiceOver, Reduce Motion).

**Fix:**
```swift
// NATIVE: Let glass handle toolbar and window chrome
.windowToolbarStyle(.unified)
.toolbar {
    ToolbarItem(placement: .confirmationAction) {
        Button("Done") { }
    }
}
```

**Grep pattern:** `.hiddenTitleBar`, custom `Circle()` views mimicking traffic lights, `NSWindow.standardWindowButton`.

---

### Smell 8: Glass on Content

**What it looks like:**
```swift
// WRONG: Glass applied to individual list rows
ForEach(items) { item in
    ItemRow(item: item)
        .glassEffect(.regular, in: .rect(cornerRadius: 8))
}
```

**Why it is wrong:** Glass is for the navigation layer only (toolbars, sidebars, floating controls, sheets). Applying glass to content creates visual noise, kills readability, and tanks performance (each `.glassEffect()` creates a `CABackdropLayer` with 3 offscreen textures).

**Fix:**
```swift
// NATIVE: Glass on floating overlay, not on content
ZStack {
    List {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
    VStack {
        Spacer()
        FloatingActionButton()
            .glassEffect(.regular, in: .circle)
    }
}
```

**Grep pattern:** `.glassEffect(` inside `ForEach` or `List` content builders.

---

### Smell 9: Standalone Glass Elements Without Container

**What it looks like:**
```swift
// WRONG: Multiple ungrouped glass effects side by side
HStack {
    Button("A") { }.glassEffect(.regular, in: .capsule)
    Button("B") { }.glassEffect(.regular, in: .capsule)
    Button("C") { }.glassEffect(.regular, in: .capsule)
}
```

**Why it is wrong:** Glass cannot sample other glass. Each element renders independently against whatever is behind it. When glass elements overlap or sit adjacent, they sample each other's blurred output, producing double-blur and inconsistent tinting.

**Fix:**
```swift
// NATIVE: Grouped in container
GlassEffectContainer(spacing: 12) {
    Button("A") { }.glassEffect(.regular, in: .capsule)
    Button("B") { }.glassEffect(.regular, in: .capsule)
    Button("C") { }.glassEffect(.regular, in: .capsule)
}
```

**Grep pattern:** Multiple `.glassEffect(` calls in the same `HStack` or `VStack` without an enclosing `GlassEffectContainer`.

---

### Smell 10: Missing backgroundExtensionEffect

**What it looks like:**
```swift
// DATED: Content stops at safe area boundary
NavigationSplitView {
    List { content }
} detail: {
    DetailView()
}
```

**Why it is wrong:** Without `.backgroundExtensionEffect()`, the sidebar and detail content stop at the safe area inset. Content does not appear through the glass toolbar, eliminating the signature Liquid Glass layered depth effect.

**Fix:**
```swift
// NATIVE: Content extends behind glass chrome
NavigationSplitView {
    List { content }
        .backgroundExtensionEffect()
} detail: {
    HeroImage()
        .backgroundExtensionEffect()
}
```

**Grep pattern:** `NavigationSplitView` without any `.backgroundExtensionEffect()` in its content.

---

### Smell 11: Missing Accessibility Labels on Icon Buttons

**What it looks like:**
```swift
// DATED: Icon button with no label for VoiceOver
Button { doAction() } label: {
    Image(systemName: "gear")
}
```

**Why it is wrong:** VoiceOver reads "button" with no description. Screen reader users cannot determine what the button does.

**Fix:**
```swift
// NATIVE: Label provides both icon and accessibility text
Button("Settings", systemImage: "gear") { doAction() }
// Or, if custom label layout is needed:
Button { doAction() } label: {
    Image(systemName: "gear")
}
.accessibilityLabel("Settings")
```

**Grep pattern:** `Button { }` with an `Image(systemName:` label but no `.accessibilityLabel(` and no `Label(` containing a text string.

---

### Smell 12: Wrong Toolbar Placement

**What it looks like:**
```swift
// DATED: All items in .automatic placement
.toolbar {
    ToolbarItem(placement: .automatic) {
        Button("Cancel") { }
    }
    ToolbarItem(placement: .automatic) {
        Button("Save") { }
    }
}
```

**Why it is wrong:** macOS toolbar placements have semantic meaning. `.cancellationAction` goes leading, `.confirmationAction` goes trailing with `.glassProminent` treatment. `.automatic` dumps everything together without visual hierarchy.

**Fix:**
```swift
// NATIVE: Semantic placements
.toolbar {
    ToolbarItem(placement: .cancellationAction) {
        Button("Cancel") { dismiss() }
    }
    ToolbarItem(placement: .confirmationAction) {
        Button("Save") { save() }
    }
}
```

**Grep pattern:** Multiple `ToolbarItem(placement: .automatic)` with semantically distinct actions.

---

### Smell 13: Missing Settings Scene

**What it looks like:**
```swift
// DATED: No Settings scene in App body
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        // No Settings scene
    }
}
```

**Why it is wrong:** Cmd+Comma does nothing. macOS users expect a preferences window. Its absence is a platform fidelity failure.

**Fix:**
```swift
// NATIVE: Settings scene with tabs
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        Settings {
            TabView {
                GeneralSettings()
                    .tabItem { Label("General", systemImage: "gear") }
                AppearanceSettings()
                    .tabItem { Label("Appearance", systemImage: "paintpalette") }
            }
            .frame(width: 450, height: 250)
        }
    }
}
```

**Grep pattern:** `struct.*App:.*App` body without a `Settings {` scene.

---

### Smell 14: Incorrect Sheet Presentation with Custom Background

**What it looks like:**
```swift
// DATED: Custom background on sheet
.sheet(isPresented: $show) {
    SheetContent()
        .presentationBackground(.ultraThinMaterial)
        .presentationDetents([.medium, .large])
}
```

**Why it is wrong:** `.presentationBackground()` overrides the system glass. On macOS 26, sheets get automatic glass treatment that adapts to Reduce Transparency and Increase Contrast. Custom backgrounds block this.

**Fix:**
```swift
// NATIVE: Let system handle sheet glass
.sheet(isPresented: $show) {
    SheetContent()
        .presentationDetents([.medium, .large])
}
```

**Grep pattern:** `.presentationBackground(` inside a `.sheet` modifier.

---

### Smell 15: No Menu Commands

**What it looks like:**
```swift
// DATED: App with no .commands modifier
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

**Why it is wrong:** The app has only the default system menus. No custom commands, no domain-specific shortcuts. Power users cannot discover functionality through the menu bar, and Cmd+Shift+/ (Help menu search) finds nothing app-specific.

**Fix:**
```swift
// NATIVE: Custom commands with shortcuts
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            CommandMenu("Document") {
                Button("New from Template") { newFromTemplate() }
                    .keyboardShortcut("n", modifiers: [.command, .shift])
                Divider()
                Button("Export as PDF") { exportPDF() }
                    .keyboardShortcut("e", modifiers: [.command, .shift])
            }
        }
    }
}
```

**Grep pattern:** `struct.*App:.*App` body without `.commands {`.

---

### Smell 16: Non-Adaptive Layout

**What it looks like:**
```swift
// DATED: Fixed-size layout
VStack {
    content
}
.frame(width: 800, height: 600)
```

**Why it is wrong:** Fixed frames do not adapt to window resizing, Dynamic Type, or different display sizes. On macOS, users resize windows constantly. Fixed layouts either clip content or leave empty space.

**Fix:**
```swift
// NATIVE: Flexible layout with constraints
VStack {
    content
}
.frame(minWidth: 400, idealWidth: 800, minHeight: 300, idealHeight: 600)
```

**Grep pattern:** `.frame(width:.*height:` without `min` or `ideal` on top-level container views.

---

### Smell 17: Wrong Button Hierarchy

**What it looks like:**
```swift
// DATED: All buttons look the same
VStack {
    Button("Save") { }.buttonStyle(.bordered)
    Button("Cancel") { }.buttonStyle(.bordered)
    Button("Delete") { }.buttonStyle(.bordered)
}
```

**Why it is wrong:** No visual hierarchy. The user cannot instantly identify the primary action. Liquid Glass provides three distinct button treatments for this purpose.

**Fix:**
```swift
// NATIVE: Clear hierarchy
VStack {
    Button("Save") { }.buttonStyle(.glassProminent)   // primary
    Button("Cancel") { }.buttonStyle(.glass)           // secondary
    Button("Delete", role: .destructive) { delete() }  // destructive gets system red
}
```

**Grep pattern:** Three or more `Button(` with identical `.buttonStyle(.bordered)` in the same container.

---

### Smell 18: Stale ObservableObject Pattern

**What it looks like:**
```swift
// DATED: Full ObservableObject ceremony
class ViewModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var selectedItem: Item?
    @Published var isLoading = false
}

struct ContentView: View {
    @StateObject private var viewModel = ViewModel()
    // ...
}
```

**Why it is wrong:** `ObservableObject` triggers view invalidation when ANY `@Published` property changes, regardless of which property the view actually reads. This causes unnecessary redraws, which on glass surfaces can produce visible shimmer.

**Fix:**
```swift
// NATIVE: @Observable with precise tracking
@Observable
class ViewModel {
    var items: [Item] = []
    var selectedItem: Item?
    var isLoading = false
}

struct ContentView: View {
    @State private var viewModel = ViewModel()
    // Only re-renders when the specific property read in body changes
}
```

**Grep pattern:** `class.*:.*ObservableObject`, `@StateObject`, `@ObservedObject`, `@Published`.

---

### Smell 19: Missing #Preview Macro

**What it looks like:**
```swift
// DATED: Old PreviewProvider
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
```

**Why it is wrong:** `PreviewProvider` is deprecated. `#Preview` is shorter, supports multiple named previews per file, and enables trait-based previews for testing glass under different accessibility settings.

**Fix:**
```swift
// NATIVE: #Preview macro with traits
#Preview("Default") {
    ContentView()
}

#Preview("Dark Mode") {
    ContentView()
        .preferredColorScheme(.dark)
}

#Preview("Reduce Transparency") {
    ContentView()
        .environment(\.accessibilityReduceTransparency, true)
}
```

**Grep pattern:** `PreviewProvider` protocol conformance.

---

### Smell 20: Wrong Image Handling

**What it looks like:**
```swift
// DATED: Fixed-size image with no accessibility
Image("hero")
    .resizable()
    .frame(width: 400, height: 200)
```

**Why it is wrong:** Fixed frames, no aspect ratio control, no accessibility description. The image clips on smaller windows and wastes space on larger ones. VoiceOver cannot describe it.

**Fix:**
```swift
// NATIVE: Adaptive image with accessibility
Image("hero")
    .resizable()
    .aspectRatio(contentMode: .fill)
    .frame(maxHeight: 300)
    .clipped()
    .accessibilityLabel("Hero image showing application dashboard")
    .backgroundExtensionEffect()  // extend behind glass toolbar
```

**Grep pattern:** `Image(` followed by `.frame(width:` without `.aspectRatio(`.

---

### Smell 21: Incorrect Form Patterns

**What it looks like:**
```swift
// DATED: Manual form layout
VStack(alignment: .leading) {
    Text("Name")
    TextField("", text: $name)
    Text("Email")
    TextField("", text: $email)
}
.padding()
```

**Why it is wrong:** No grouping, no system form styling, no automatic labels. The layout does not match the macOS HIG for settings and input forms.

**Fix:**
```swift
// NATIVE: Form with sections
Form {
    Section("Personal Information") {
        TextField("Name", text: $name)
        TextField("Email", text: $email)
    }
    Section("Preferences") {
        Toggle("Notifications", isOn: $notifications)
        Picker("Theme", selection: $theme) {
            Text("Automatic").tag(Theme.automatic)
            Text("Light").tag(Theme.light)
            Text("Dark").tag(Theme.dark)
        }
    }
}
.formStyle(.grouped)
```

**Grep pattern:** `VStack` with alternating `Text(` and `TextField(` without an enclosing `Form`.

---

### Smell 22: Using .interactive() on macOS

**What it looks like:**
```swift
// WRONG: iOS-only API
Button("Action") { }
    .glassEffect(.regular.interactive(), in: .capsule)
```

**Why it is wrong:** `.interactive()` enables continuous platter tracking for iOS touch input. It does not exist on macOS and may crash in early betas. macOS glass controls respond to hover states through standard mechanisms.

**Fix:**
```swift
// NATIVE macOS: Use hover
@State private var isHovered = false

Button("Action") { }
    .glassEffect(.regular, in: .capsule)
    .onHover { isHovered = $0 }
    .scaleEffect(isHovered ? 1.02 : 1.0)
    .animation(.easeInOut(duration: 0.2), value: isHovered)
```

**Grep pattern:** `.interactive()` in macOS code paths.

---

### Smell 23: Missing Reduce Motion Support

**What it looks like:**
```swift
// DATED: Unconditional animation
.onAppear {
    withAnimation(.spring(duration: 1.0)) {
        isExpanded = true
    }
}
```

**Why it is wrong:** Users with Reduce Motion enabled still see a full spring animation. Glass morphing is automatically dampened, but custom animations are not. The app feels jarring to motion-sensitive users.

**Fix:**
```swift
// NATIVE: Respect Reduce Motion
@Environment(\.accessibilityReduceMotion) var reduceMotion

.onAppear {
    if reduceMotion {
        isExpanded = true
    } else {
        withAnimation(.spring(duration: 1.0)) {
            isExpanded = true
        }
    }
}
```

**Grep pattern:** `withAnimation(` without checking `accessibilityReduceMotion` for animations longer than 0.3s.

---

### Smell 24: TabView Without Sidebar Adaptable on macOS

**What it looks like:**
```swift
// DATED: Default tab view on macOS
TabView {
    LibraryView()
        .tabItem { Label("Library", systemImage: "books.vertical") }
    SearchView()
        .tabItem { Label("Search", systemImage: "magnifyingglass") }
}
```

**Why it is wrong:** Without `.tabViewStyle(.sidebarAdaptable)`, macOS renders a tab view with a small toolbar-embedded tab picker. The sidebar-adaptable style produces the proper macOS sidebar with glass treatment, collapsible behavior, and full navigation integration.

**Fix:**
```swift
// NATIVE: Sidebar-adaptable on macOS
TabView {
    Tab("Library", systemImage: "books.vertical") {
        LibraryView()
    }
    Tab("Search", systemImage: "magnifyingglass") {
        SearchView()
    }
}
.tabViewStyle(.sidebarAdaptable)
```

**Grep pattern:** `TabView {` without `.tabViewStyle(.sidebarAdaptable)` in macOS targets.

---

### Smell 25: Missing Glass Button Tint Clear on macOS

**What it looks like:**
```swift
// WRONG: Glass button without .tint(.clear) on macOS
Button("Action") { }
    .buttonStyle(.glass)
```

**Why it is wrong:** On macOS, glass buttons inherit the system accent color by default, which produces an unwanted colored tint on what should be a neutral glass surface.

**Fix:**
```swift
// NATIVE: Clear tint for neutral macOS glass
Button("Action") { }
    .buttonStyle(.glass)
    .tint(.clear)
```

**Grep pattern:** `.buttonStyle(.glass)` without a subsequent `.tint(.clear)` on macOS.

---

### Smell 26: Hardcoded Dark Mode Colors

**What it looks like:**
```swift
// DATED: Manual dark mode handling
@Environment(\.colorScheme) var colorScheme

Text("Label")
    .foregroundStyle(colorScheme == .dark ? Color.white : Color.black)
```

**Why it is wrong:** Manual color scheme switching is fragile, does not handle Increase Contrast, and ignores glass vibrancy. Semantic styles adapt to all appearance contexts automatically.

**Fix:**
```swift
// NATIVE: Semantic style handles all contexts
Text("Label")
    .foregroundStyle(.primary)
```

**Grep pattern:** `colorScheme == .dark ?` or `colorScheme == .light ?` for color switching.

---

### Smell 27: Using GeometryReader for Basic Layout

**What it looks like:**
```swift
// DATED: GeometryReader for proportional sizing
GeometryReader { geo in
    HStack {
        sidebar.frame(width: geo.size.width * 0.3)
        detail.frame(width: geo.size.width * 0.7)
    }
}
```

**Why it is wrong:** `GeometryReader` proposes zero size to its children, complicates layout, and does not participate in the navigation system. For sidebar/detail splits, `NavigationSplitView` handles proportions, glass treatment, and collapse behavior.

**Fix:**
```swift
// NATIVE: NavigationSplitView handles proportional layout
NavigationSplitView {
    sidebar
        .navigationSplitViewColumnWidth(min: 180, ideal: 250, max: 350)
} detail: {
    detail
}
```

**Grep pattern:** `GeometryReader` wrapping an `HStack` that contains sidebar-like and detail-like views.

---

### Smell 28: Mixing .regular and .clear Glass Variants

**What it looks like:**
```swift
// WRONG: Mixed variants in same hierarchy
VStack {
    Toolbar()
        .glassEffect(.regular, in: .rect(cornerRadius: 16))
    MediaOverlay()
        .glassEffect(.clear, in: .rect(cornerRadius: 12))
}
```

**Why it is wrong:** `.regular` and `.clear` use different opacity and blending. Mixing them in the same view hierarchy creates visual inconsistency -- one surface is translucent while the other is nearly transparent. Choose one variant per view hierarchy.

**Fix:**
```swift
// NATIVE: One variant per hierarchy
// Either all .regular (most cases)
VStack {
    Toolbar()
        .glassEffect(.regular, in: .rect(cornerRadius: 16))
    ActionBar()
        .glassEffect(.regular, in: .rect(cornerRadius: 12))
}

// Or all .clear (media-rich context only)
VStack {
    MediaToolbar()
        .glassEffect(.clear, in: .rect(cornerRadius: 16))
    MediaOverlay()
        .glassEffect(.clear, in: .rect(cornerRadius: 12))
}
```

**Grep pattern:** `.glassEffect(.regular` and `.glassEffect(.clear` in the same file.

---

### Smell 29: Missing ToolbarSpacer in Toolbar Layout

**What it looks like:**
```swift
// DATED: All items clustered together
.toolbar {
    ToolbarItem { Button("A") { } }
    ToolbarItem { Button("B") { } }
    ToolbarItem { Button("C") { } }
}
```

**Why it is wrong:** Without spacers, all items cluster in one region. `ToolbarSpacer(.flexible)` pushes items apart; `ToolbarSpacer(.fixed)` creates consistent gaps. Proper spacing is part of the Liquid Glass toolbar design.

**Fix:**
```swift
// NATIVE: Spaced toolbar layout
.toolbar {
    ToolbarItem(placement: .cancellationAction) {
        Button("Cancel") { }
    }
    ToolbarSpacer(.flexible)
    ToolbarItemGroup(placement: .primaryAction) {
        Button("Draw", systemImage: "pencil") { }
        Button("Erase", systemImage: "eraser") { }
    }
    ToolbarSpacer(.fixed)
    ToolbarItem(placement: .confirmationAction) {
        Button("Save") { }
    }
}
```

**Grep pattern:** Three or more `ToolbarItem` without any `ToolbarSpacer`.

---

### Smell 30: Using .onAppear for Data Loading Without Task

**What it looks like:**
```swift
// DATED: Launching async work from onAppear
.onAppear {
    Task {
        await loadData()
    }
}
```

**Why it is wrong:** The `Task` created inside `.onAppear` is not cancelled when the view disappears, leading to potential state updates on a dismissed view. On macOS with multiple windows, this creates dangling tasks.

**Fix:**
```swift
// NATIVE: .task handles lifecycle automatically
.task {
    await loadData()
}
```

**Grep pattern:** `.onAppear {` containing `Task {`.

---

## Section 3: Complete View Transformation Example

### Before: A "Works But Looks Dated" macOS View

This view compiles and runs. It displays data. It is also riddled with design smells.

```swift
import SwiftUI

// BEFORE: Legacy patterns throughout

class DocumentViewModel: ObservableObject {               // Smell 18: ObservableObject
    @Published var documents: [Document] = []              // Smell 18: @Published
    @Published var selectedDocument: Document?
    @Published var isLoading = false

    func loadDocuments() async {
        isLoading = true
        documents = await DocumentService.fetchAll()
        isLoading = false
    }
}

struct DocumentBrowserView: View {
    @StateObject private var viewModel = DocumentViewModel()  // Smell 18: @StateObject

    var body: some View {
        NavigationView {                                       // Smell: NavigationView
            HStack(spacing: 0) {                               // Smell 4: Custom sidebar
                VStack {
                    Text("Documents")
                        .font(.system(size: 18, weight: .bold)) // Smell 5: Fixed font
                        .foregroundColor(.primary)               // Smell: .foregroundColor
                        .padding()

                    List(viewModel.documents, selection: $viewModel.selectedDocument) { doc in
                        NavigationLink(destination: DocumentDetail(document: doc)) { // Smell: old NavigationLink
                            HStack {
                                Image(systemName: "doc.circle")  // Smell: circle variant
                                Text(doc.title)
                            }
                        }
                    }
                    .listStyle(.sidebar)                        // Smell: old sidebar style
                }
                .frame(width: 250)                              // Smell 4: Fixed sidebar width
                .background(Color(red: 0.15, green: 0.15, blue: 0.15)) // Smell 1: Hardcoded color

                Divider()                                       // Smell 4: Manual divider

                VStack {
                    if let doc = viewModel.selectedDocument {
                        DocumentDetail(document: doc)
                    } else {
                        Text("Select a document")
                            .foregroundColor(.gray)              // Smell: .foregroundColor
                            .font(.system(size: 16))             // Smell 5: Fixed font
                    }
                }
            }
        }
        .toolbar {
            ToolbarItem(placement: .automatic) {                // Smell 12: Wrong placement
                Button("New") { }                               // Smell 6: No shortcut
            }
            ToolbarItem(placement: .automatic) {
                Button("Delete") { }
                    .tint(.red)
            }
        }
        .toolbarBackground(.visible, for: .windowToolbar)       // Smell: Blocks glass
        .toolbarColorScheme(.dark, for: .windowToolbar)         // Smell: Unreadable on glass
        .onAppear {                                             // Smell 30: onAppear + Task
            Task {
                await viewModel.loadDocuments()
            }
        }
    }
}

struct DocumentDetail: View {
    let document: Document

    var body: some View {
        VStack(alignment: .leading) {                           // Smell 21: Manual form
            Text(document.title)
                .font(.system(size: 24, weight: .bold))         // Smell 5: Fixed font
            Text(document.body)
                .font(.system(size: 14))                        // Smell 5: Fixed font
        }
        .padding()
        .frame(width: 600, height: 400)                         // Smell 16: Fixed frame
    }
}

struct DocumentBrowserView_Previews: PreviewProvider {          // Smell 19: Old PreviewProvider
    static var previews: some View {
        DocumentBrowserView()
    }
}
```

### After: The Same View Redesigned for macOS 26 with Liquid Glass

```swift
import SwiftUI

// AFTER: Modern patterns, Liquid Glass, macOS-native

@Observable                                                     // [Fix 18] Precise observation
class DocumentViewModel {
    var documents: [Document] = []                              // [Fix 18] No @Published needed
    var selectedDocumentID: Document.ID?
    var isLoading = false

    func loadDocuments() async {
        isLoading = true
        documents = await DocumentService.fetchAll()
        isLoading = false
    }
}

struct DocumentBrowserView: View {
    @State private var viewModel = DocumentViewModel()          // [Fix 18] @State with @Observable
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) { // [Fix 4] Proper split view
            List(viewModel.documents, selection: $viewModel.selectedDocumentID) { doc in
                NavigationLink(value: doc.id) {                  // [Fix 2] Value-based nav link
                    Label(doc.title, systemImage: "doc")         // [Fix 31] Non-circle SF Symbol
                }
            }
            .backgroundExtensionEffect()                        // [Fix 10] Extend behind glass
            .navigationSplitViewColumnWidth(min: 180, ideal: 220, max: 300)
        } detail: {
            if let id = viewModel.selectedDocumentID,
               let doc = viewModel.documents.first(where: { $0.id == id }) {
                DocumentDetail(document: doc)
            } else {
                ContentUnavailableView(                          // [New] System empty state
                    "Select a Document",
                    systemImage: "doc",
                    description: Text("Choose a document from the sidebar to view its contents.")
                )
            }
        }
        .navigationTitle("Documents")                           // [Fix 5] System title in glass toolbar
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("New Document", systemImage: "plus") {    // [Fix 6, 11] Label + icon
                    createDocument()
                }
                .keyboardShortcut("n")                          // [Fix 6] Standard shortcut
            }
            ToolbarSpacer(.flexible)                            // [Fix 29] Proper spacing
            ToolbarItem(placement: .secondaryAction) {
                Button("Delete", systemImage: "trash", role: .destructive) { // [Fix 31] Non-circle icon
                    deleteDocument()
                }
                .keyboardShortcut(.delete)                      // [Fix 6] Standard shortcut
            }
        }
        // [Fix 19, 20, 21] Removed: .toolbarBackground, .toolbarColorScheme
        .navigationDestination(for: Document.ID.self) { docID in // [Fix 2] Destination registration
            if let doc = viewModel.documents.first(where: { $0.id == docID }) {
                DocumentDetail(document: doc)
            }
        }
        .task {                                                 // [Fix 30] Lifecycle-managed task
            await viewModel.loadDocuments()
        }
    }

    private func createDocument() { /* ... */ }
    private func deleteDocument() { /* ... */ }
}

struct DocumentDetail: View {
    let document: Document

    var body: some View {
        ScrollView {                                            // [Fix 16] Scrollable, not fixed
            VStack(alignment: .leading, spacing: 16) {
                Text(document.title)
                    .font(.title)                               // [Fix 5] Dynamic Type
                    .foregroundStyle(.primary)                   // [Fix 12] Semantic style

                Text(document.body)
                    .font(.body)                                // [Fix 5] Dynamic Type
                    .foregroundStyle(.secondary)                 // [Fix 12] Hierarchical style
            }
            .padding()
            .frame(minWidth: 300, idealWidth: 600)              // [Fix 16] Flexible sizing
            .backgroundExtensionEffect()                        // [Fix 10] Extend behind toolbar
        }
    }
}

#Preview("Default") {                                           // [Fix 19] Modern preview macro
    DocumentBrowserView()
        .frame(width: 900, height: 600)
}

#Preview("Dark Mode") {
    DocumentBrowserView()
        .preferredColorScheme(.dark)
        .frame(width: 900, height: 600)
}
```

### Annotation Summary

| Line | Change | Reason |
|------|--------|--------|
| Model class | `ObservableObject` to `@Observable` | Precise invalidation; only views reading changed properties re-render |
| `@StateObject` | Changed to `@State` | Correct ownership pattern for `@Observable` |
| `@Published` | Removed | All stored properties automatically observed in `@Observable` |
| `NavigationView` | Replaced with `NavigationSplitView` | Glass sidebar, proper column management, type-safe navigation |
| `HStack + Divider` | Removed | `NavigationSplitView` provides sidebar/detail split with glass treatment |
| Hardcoded `Color(red:)` | Removed | Sidebar background is now automatic glass |
| `List(.sidebar)` | Moved into `NavigationSplitView` content column | Glass sidebar is automatic |
| `.foregroundColor()` | Changed to `.foregroundStyle()` | Supports hierarchical styles that adapt to glass |
| `.font(.system(size:))` | Changed to `.font(.title)`, `.font(.body)` | Dynamic Type compliance |
| `Image("doc.circle")` | Changed to `Image("doc")` | Non-circle variants on glass toolbar |
| `NavigationLink(destination:)` | Changed to `NavigationLink(value:)` | Type-safe, decoupled navigation |
| `.toolbarBackground(.visible)` | Removed | Was blocking glass toolbar rendering |
| `.toolbarColorScheme(.dark)` | Removed | Was making icons unreadable on glass |
| `.onAppear { Task { } }` | Changed to `.task { }` | Lifecycle-managed, auto-cancelled on disappear |
| `ToolbarItem(.automatic)` | Changed to semantic placements | Correct macOS toolbar layout |
| Added `ToolbarSpacer` | New | Proper visual separation in glass toolbar |
| Added `.keyboardShortcut()` | New | macOS platform expectation |
| Added `.backgroundExtensionEffect()` | New | Content extends behind glass chrome |
| Added `ContentUnavailableView` | New | System-provided empty state |
| `PreviewProvider` | Changed to `#Preview` | Modern, multiple named previews with traits |
| Fixed `.frame()` | Changed to flexible with min/ideal | Adapts to window resizing |

---

## Section 4: The Diagnosis Checklist

Use this checklist when reviewing any existing macOS SwiftUI file. Read through the file once, marking each item. Any unchecked box is a finding that needs a fix.

### Navigation and Structure

```
[ ] NavigationSplitView or NavigationStack used (not NavigationView)
[ ] NavigationLink uses value-based initializer (not destination-based)
[ ] navigationDestination(for:) registered for each navigation value type
[ ] Sidebar implemented via NavigationSplitView column (not custom HStack + Divider)
[ ] .backgroundExtensionEffect() present on sidebar content and hero images
[ ] Column widths use min/ideal/max (not fixed .frame(width:))
```

### State Management

```
[ ] @Observable used (not ObservableObject)
[ ] @State owns @Observable instances (not @StateObject)
[ ] No @Published properties (automatic in @Observable)
[ ] @Environment(Type.self) used (not @EnvironmentObject)
[ ] .environment(value) used (not .environmentObject(value))
[ ] Per-window state uses @State inside view (not app-level @State)
[ ] App-wide state injected via .environment() from App body
```

### Colors and Typography

```
[ ] All colors semantic (.primary, .secondary, .accent, .label)
[ ] No hardcoded RGB/hex colors (Color(red:), Color(hex:))
[ ] No manual dark mode switching (colorScheme == .dark ?)
[ ] .foregroundStyle() used (not .foregroundColor())
[ ] All text uses Dynamic Type styles (.title, .body, .caption, etc.)
[ ] No .font(.system(size:)) without explicit justification
[ ] No .font(.custom()) without Dynamic Type consideration
```

### Liquid Glass Placement

```
[ ] Glass applied only to navigation layer (toolbars, sidebars, floating controls, sheets)
[ ] No glass on content (list rows, cards, text blocks, images)
[ ] .regular variant used unless media-rich background justifies .clear
[ ] No mixing of .regular and .clear in same view hierarchy
[ ] GlassEffectContainer wraps all adjacent glass elements
[ ] GlassEffectContainer spacing parameter tuned for layout
[ ] No standalone glass effects that should be grouped
```

### Toolbar

```
[ ] Using semantic placements (.cancellationAction, .confirmationAction, .primaryAction)
[ ] ToolbarSpacer(.flexible) / ToolbarSpacer(.fixed) used for layout
[ ] Related items grouped in ToolbarItemGroup
[ ] No .toolbarBackground() (blocks glass)
[ ] No .toolbarColorScheme() (unreadable on glass)
[ ] .toolbar(removing: .title) used if title is not needed
[ ] Primary action uses .confirmationAction placement
```

### Keyboard Shortcuts and Menu Commands

```
[ ] Standard operations have keyboard shortcuts (New, Save, Delete, Find)
[ ] .commands { } present on WindowGroup with domain-specific menus
[ ] focusedSceneValue used for menu-to-window communication
[ ] No system shortcut reassignment (Cmd+Q, Cmd+W, Cmd+H, Cmd+Comma)
```

### Accessibility

```
[ ] Accessibility labels on all icon-only buttons
[ ] .accessibilityLabel() on decorative images that convey meaning
[ ] Reduce Motion respected for animations > 0.3s
[ ] @Environment(\.accessibilityReduceTransparency) checked defensively
[ ] Tested with Increase Contrast (glass adds high-contrast borders)
[ ] Semantic foreground styles used for text (.primary, .secondary)
[ ] VoiceOver can navigate all interactive elements
[ ] Keyboard navigation (Tab/Shift+Tab) reaches all controls
```

### Sidebar

```
[ ] NavigationSplitView used (not custom HStack + Divider)
[ ] .backgroundExtensionEffect() on sidebar content
[ ] Column widths use navigationSplitViewColumnWidth(min:ideal:max:)
[ ] Selection binding type matches navigation value type
```

### Sheets and Popovers

```
[ ] No .presentationBackground() on sheets
[ ] No .background(.ultraThinMaterial) inside sheets
[ ] System glass applied automatically to sheet chrome
[ ] No opaque Color backgrounds on popover content
```

### Buttons and Controls

```
[ ] One primary action uses .buttonStyle(.glassProminent)
[ ] Secondary actions use .buttonStyle(.glass)
[ ] .tint(.clear) on macOS glass buttons for neutral appearance
[ ] Destructive actions use Button(role: .destructive)
[ ] No multiple tinted buttons in the same group
[ ] .controlSize appropriate for context
```

### Window and Scene

```
[ ] Settings { } scene present for Cmd+Comma
[ ] .windowStyle(.automatic) or .windowToolbarStyle(.unified) on WindowGroup
[ ] No .windowStyle(.hiddenTitleBar) (removes glass chrome)
[ ] MenuBarExtra uses .menuBarExtraStyle(.window) if popover needed
[ ] defaultSize and windowResizeAnchor set on window groups
```

### Images

```
[ ] .resizable() + .aspectRatio(contentMode:) on user images
[ ] No fixed .frame(width:height:) without flexible alternatives
[ ] Non-circle SF Symbol variants in toolbars
[ ] .accessibilityLabel() on meaningful images
[ ] .backgroundExtensionEffect() on hero/splash images
```

### Forms and Input

```
[ ] Form { Section { } } used for settings-style input
[ ] .formStyle(.grouped) applied where appropriate
[ ] TextField uses title label (not separate Text above)
[ ] Picker, Toggle, Stepper inside Form sections
[ ] TextEditor background uses .windowBackground (not material)
```

### Performance

```
[ ] Glass elements grouped in GlassEffectContainer (shared sampling)
[ ] No glass on individual scroll items
[ ] LazyVStack/LazyHStack used for large scrolling lists
[ ] #if arch(arm64) / #else for Intel Mac fallbacks if targeting older hardware
```

### Backward Compatibility

```
[ ] #available(macOS 26, *) gates all Liquid Glass APIs
[ ] Non-glass fallback provided (material or plain background)
[ ] No .interactive() leaking to macOS code paths
[ ] @available annotations on legacy code for future cleanup
```

### Previews

```
[ ] #Preview macro used (not PreviewProvider)
[ ] Multiple previews: default, dark mode, accessibility variants
[ ] Frame size specified for macOS previews
[ ] Mock data provided for meaningful preview content
```
