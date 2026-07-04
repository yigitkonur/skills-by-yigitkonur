# macOS-Specific Liquid Glass UI Patterns

This reference covers UI patterns that are unique to macOS 26 with Liquid Glass. These patterns have no iOS equivalent or behave fundamentally differently on macOS. For shared cross-platform patterns, see the general Liquid Glass reference.

---

## Toolbar Patterns with Liquid Glass

Toolbar items on macOS 26 automatically adopt Liquid Glass styling. The system renders toolbar buttons as glass-backed controls that inherit ambient color from the content behind them.

### Standard Toolbar Layout

```swift
.toolbar {
    ToolbarItem(placement: .cancellationAction) {
        Button("Cancel", systemImage: "xmark") { }
    }
    ToolbarSpacer(.flexible)
    ToolbarItemGroup(placement: .primaryAction) {
        Button("Draw", systemImage: "pencil") { }
        Button("Erase", systemImage: "eraser") { }
    }
    ToolbarSpacer(.fixed)
    ToolbarItem(placement: .confirmationAction) {
        Button("Save", systemImage: "checkmark") { }
            .badge(3)
    }
}
.toolbar(removing: .title) // Clean glass toolbar without title text
```

### Toolbar Rules

| Rule | Detail |
|------|--------|
| Icons | Monochrome by default. The system tints them to match glass appearance. |
| `.tint()` | Use only on primary action buttons to draw visual emphasis. |
| `.confirmationAction` | Intended for primary confirmation actions. May receive `.glassProminent` treatment automatically (not independently verified — apply explicit `.buttonStyle(.glassProminent)` if needed). |
| `.toolbar(removing: .title)` | Removes the window title from the toolbar area for a cleaner glass surface. |
| Grouping | Use `ToolbarItemGroup` to cluster related actions. Glass groups them visually. |
| Spacers | `ToolbarSpacer(.flexible)` for push-apart layout, `.fixed` for consistent gaps. |

---

## NavigationSplitView Sidebar Patterns

On macOS 26, the sidebar in `NavigationSplitView` automatically becomes a floating Liquid Glass panel. Content flows behind the floating sidebar, creating a layered depth effect.

### Two-Column Layout

```swift
NavigationSplitView {
    List(items, selection: $selected) { item in
        Label(item.name, systemImage: item.icon)
    }
    .backgroundExtensionEffect()
    .navigationSplitViewColumnWidth(min: 180, ideal: 200) // Note: unreliable on macOS 26.0–26.1; verify on your target version
} detail: {
    DetailView(item: selected)
}
```

### Three-Column Layout with Inspector

```swift
NavigationSplitView {
    List(categories, selection: $selectedCategory) { category in
        Label(category.name, systemImage: category.icon)
    }
    .backgroundExtensionEffect()
    .navigationSplitViewColumnWidth(min: 180, ideal: 200)
} content: {
    List(filteredItems, selection: $selectedItem) { item in
        ItemRow(item: item)
    }
    .navigationSplitViewColumnWidth(min: 200, ideal: 250)
} detail: {
    DetailView(item: selectedItem)
}
```

### Sidebar Behavior

- The sidebar floats as a glass panel above the main content.
- Content scrolls behind the sidebar, visible through the glass.
- `.backgroundExtensionEffect()` extends the sidebar's visual background so it blends smoothly with the glass chrome.
- The sidebar picks up ambient reflections from nearby colorful content, reinforcing the glass metaphor.
- Collapse/expand animations are system-managed and glass-aware.

---

## Inspector Panel Pattern

Inspectors on macOS slide in from the trailing edge as a glass-backed panel. They are distinct from detail columns and are intended for contextual property editing.

```swift
struct ContentView: View {
    @State private var showInspector = false

    var body: some View {
        MainEditorView()
            .inspector(isPresented: $showInspector) {
                InspectorView()
                    .inspectorColumnWidth(min: 200, ideal: 300, max: 400)
            }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Inspector", systemImage: "sidebar.trailing") {
                        showInspector.toggle()
                    }
                }
            }
    }
}
```

The inspector receives an edge-to-edge glass treatment alongside the content (not floating like the sidebar). This is managed by `NSSplitViewController` automatically. Its content area gets ambient tinting similar to (but architecturally distinct from) the sidebar.

---

## Window Management with Liquid Glass

### Window Corner Radii

macOS 26 dynamically adjusts window corner radii based on toolbar configuration:

| Toolbar Configuration | Corner Radius |
|----------------------|---------------|
| No toolbar (titlebar-only) | ~16pt |
| Compact toolbar | ~20pt |
| Standard toolbar | ~26pt |

These radii are system-managed. Do not attempt to override them with custom clipping.

### Window Style Configuration

```swift
WindowGroup {
    ContentView()
}
.windowStyle(.automatic) // Full Liquid Glass (default on macOS 26)
.windowToolbarStyle(.unified(showsTitle: false))
.defaultSize(width: 1200, height: 800)
.windowResizeAnchor(.top)
```

### Window Scene Types

| Scene | Purpose | Instance Behavior |
|-------|---------|-------------------|
| `WindowGroup` | Standard document or content windows | Multi-instance. Each open creates a new window. |
| `Window` | Utility or auxiliary windows | Single-instance, opened by ID. |
| `Settings` | Preferences window (Cmd+Comma) | Single-instance, system-managed. |
| `MenuBarExtra` | Menu bar utility or popover | Always available in the menu bar. |

### WindowGroup (Multi-Instance)

```swift
WindowGroup("Document", id: "document", for: Document.ID.self) { $documentID in
    DocumentView(documentID: documentID)
}
.defaultSize(width: 800, height: 600)
```

### Window (Single-Instance)

```swift
Window("Activity Monitor", id: "activity") {
    ActivityView()
}
.defaultSize(width: 500, height: 400)
.keyboardShortcut("0", modifiers: [.command, .option])
```

Open it programmatically with `@Environment(\.openWindow)`:

```swift
@Environment(\.openWindow) private var openWindow

Button("Show Activity") {
    openWindow(id: "activity")
}
```

---

## Settings Scene Pattern

The `Settings` scene creates the standard macOS preferences window, accessible via Cmd+Comma. It automatically receives Liquid Glass window treatment.

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }

        Settings {
            TabView {
                GeneralSettingsView()
                    .tabItem { Label("General", systemImage: "gear") }
                AppearanceSettingsView()
                    .tabItem { Label("Appearance", systemImage: "paintpalette") }
                AdvancedSettingsView()
                    .tabItem { Label("Advanced", systemImage: "gearshape.2") }
            }
            .frame(width: 450, height: 250)
        }
    }
}
```

The tab bar in Settings windows adopts glass styling automatically. Each tab item renders as a glass-backed segment.

---

## MenuBarExtra Pattern

`MenuBarExtra` creates a menu bar item with either a menu or a popover window. The `.window` style produces a Liquid Glass popover.

```swift
@main
struct StatusApp: App {
    var body: some Scene {
        MenuBarExtra("MyApp", systemImage: "chart.bar") {
            StatusContentView()
                .frame(width: 300, height: 180)
        }
        .menuBarExtraStyle(.window) // Glass popover instead of plain menu
    }
}
```

### Agent App Configuration

For apps that live exclusively in the menu bar (no Dock icon):

1. Set `LSUIElement = YES` in `Info.plist` to hide the Dock icon.
2. Always include an explicit Quit button in the popover content, since there is no Dock context menu to quit from.

```swift
struct StatusContentView: View {
    var body: some View {
        VStack {
            // Main content
            StatusDashboard()

            Divider()

            Button("Quit MyApp") {
                NSApplication.shared.terminate(nil)
            }
            .keyboardShortcut("q")
        }
        .padding()
    }
}
```

---

## Keyboard Shortcuts and Menu System

### Custom Command Menus

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            CommandMenu("Symbol") {
                Button("Random") {
                    selectedSymbol?.chooseRandom()
                }
                .keyboardShortcut("r")

                Divider()

                Button("Reset All") {
                    resetSymbols()
                }
                .keyboardShortcut("r", modifiers: [.command, .shift])
            }
            CommandGroup(after: .undoRedo) {
                Button("Custom Edit Action") { }
                    .keyboardShortcut("e", modifiers: [.command, .option])
            }
        }
    }
}
```

### Standard macOS Keyboard Shortcuts

Always respect these system conventions. Do not reassign them to custom actions.

| Shortcut | Action |
|----------|--------|
| Cmd+N | New window / document |
| Cmd+O | Open |
| Cmd+S | Save |
| Cmd+Shift+S | Save As |
| Cmd+Z | Undo |
| Cmd+Shift+Z | Redo |
| Cmd+Q | Quit |
| Cmd+W | Close window |
| Cmd+Comma | Open Settings |
| Cmd+H | Hide application |
| Cmd+M | Minimize window |
| Cmd+Option+H | Hide others |
| Cmd+A | Select all |
| Cmd+C / Cmd+V / Cmd+X | Copy / Paste / Cut |
| Cmd+F | Find |
| Cmd+G / Cmd+Shift+G | Find next / previous |

---

## focusedSceneValue for Menu Commands

Menu bar commands need to communicate with the focused window's state. `focusedSceneValue` is the correct mechanism for scene-wide state sharing with menus.

### Step 1: Define a FocusedValues Extension

```swift
struct FocusedDocumentKey: FocusedValueKey {
    typealias Value = Binding<Document>
}

extension FocusedValues {
    var document: Binding<Document>? {
        get { self[FocusedDocumentKey.self] }
        set { self[FocusedDocumentKey.self] = newValue }
    }
}
```

### Step 2: Publish from the Scene's Root View

```swift
struct DocumentView: View {
    @State private var document: Document

    var body: some View {
        EditorView(document: $document)
            .focusedSceneValue(\.document, $document)
    }
}
```

### Step 3: Consume in Commands

```swift
struct DocumentCommands: Commands {
    @FocusedBinding(\.document) var document

    var body: some Commands {
        CommandMenu("Document") {
            Button("Bold") {
                document?.applyBold()
            }
            .keyboardShortcut("b")
            .disabled(document == nil)
        }
    }
}
```

### focusedSceneValue vs. focusedValue

| Modifier | Scope | Use When |
|----------|-------|----------|
| `.focusedSceneValue()` | Entire scene (window) | Menu commands, toolbar actions. Preferred for macOS menus. |
| `.focusedValue()` | Specific focused view only | A particular text field or control must be focused. |

**Critical:** Use `focusedSceneValue` for menu bar commands. Using `focusedValue` causes the binding to be `nil` unless the exact view publishing it has keyboard focus, which leads to menus appearing permanently disabled.

---

## Multi-Window State Management

macOS apps often have multiple windows open simultaneously. State must be partitioned correctly between global (shared across all windows) and per-window (local to each window instance).

### App-Level vs. Window-Level State

```swift
@Observable
class AppState {
    var userPreferences = UserPreferences()
    var recentDocuments: [Document] = []
}

@main
struct MyApp: App {
    @State private var appState = AppState() // Shared across all windows

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appState) // Every window reads the same AppState
        }

        WindowGroup("Editor", id: "editor", for: Document.ID.self) { $docID in
            EditorView(documentID: docID)
                .environment(appState)
        }

        Settings {
            SettingsView()
                .environment(appState)
        }
    }
}
```

### Per-Window Navigation State

Navigation state (selected items, scroll position, expanded sections) must remain local to each window. SwiftUI handles this automatically when `@State` is declared inside the view hierarchy rather than at the `App` level.

```swift
struct ContentView: View {
    // Per-window: each window gets its own navigation state
    @State private var selectedItem: Item.ID?
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    // Shared: injected from App via environment
    @Environment(AppState.self) private var appState

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            SidebarView(selection: $selectedItem)
        } detail: {
            if let selectedItem {
                DetailView(itemID: selectedItem)
            }
        }
    }
}
```

### Opening Windows Programmatically

```swift
struct SidebarView: View {
    @Environment(\.openWindow) private var openWindow

    var body: some View {
        List(documents) { doc in
            Button(doc.title) {
                openWindow(id: "editor", value: doc.id)
            }
        }
    }
}
```

---

## Custom Glass Controls

When building custom floating tool palettes or control surfaces that live outside the standard toolbar, use `GlassEffectContainer` and `.glassEffect()` to match the system glass appearance.

### Floating Tool Palette

```swift
struct FloatingToolPalette: View {
    @Namespace private var namespace

    var body: some View {
        GlassEffectContainer(spacing: 16) {
            Button("Pencil", systemImage: "pencil") {
                selectTool(.pencil)
            }
            .glassEffect(.regular, in: .rect(cornerRadius: 12))
            .glassEffectID("pencil", in: namespace)

            Button("Eraser", systemImage: "eraser") {
                selectTool(.eraser)
            }
            .glassEffect(.regular, in: .rect(cornerRadius: 12))
            .glassEffectID("eraser", in: namespace)

            Button("Lasso", systemImage: "lasso") {
                selectTool(.lasso)
            }
            .glassEffect(.regular, in: .rect(cornerRadius: 12))
            .glassEffectID("lasso", in: namespace)
        }
    }
}
```

### macOS Button Tinting Rule

On macOS, glass buttons may appear visually heavy when they carry an unexpected accent tint. Practitioners report that `.tint(.clear)` on secondary glass buttons produces a cleaner neutral appearance:

```swift
Button("Action", systemImage: "star") { }
    .glassEffect(.regular, in: .capsule)
    .tint(.clear) // Practitioner workaround for tint bleed — not official Apple guidance
```

Reserve colored tints for the single primary action in a group. The `.tint(.clear)` pattern is not documented in WWDC sessions — test on your target macOS version.

### Selection State in Glass Groups

Use `.glassEffectID` with a namespace to enable animated selection transitions within a glass container:

```swift
@Namespace private var toolNamespace
@State private var activeTool: Tool = .pencil

GlassEffectContainer(spacing: 8) {
    ForEach(Tool.allCases) { tool in
        Button(tool.name, systemImage: tool.icon) {
            withAnimation { activeTool = tool }
        }
        .glassEffect(
            activeTool == tool ? .prominent : .regular,
            in: .rect(cornerRadius: 10)
        )
        .glassEffectID(tool.id, in: toolNamespace)
    }
}
```

---

## Scroll Edge Effects on macOS

macOS and iOS have different default behaviors for how toolbars respond to scroll position.

### Platform Defaults

| Platform | Default Style | Visual Effect |
|----------|--------------|---------------|
| macOS | `.hard` | Strong separation with a visible dividing line between toolbar and content. |
| iOS | `.soft` | Translucent blend where content fades under the toolbar glass. |

### Overriding Scroll Edge Style

```swift
List {
    ForEach(items) { item in
        ItemRow(item: item)
    }
}
.scrollEdgeEffectStyle(.hard, for: .top)  // macOS default: crisp divider
.scrollEdgeEffectStyle(.soft, for: .top)  // Override: translucent toolbar look
```

### When to Override

- Use `.soft` when you want the toolbar to feel more integrated with the scrolling content (e.g., media browsers, canvas-style interfaces).
- Keep `.hard` (the default) for document-oriented apps where a clear toolbar boundary aids readability.
- On macOS, `.automatic` resolves to `.hard` for ALL edges (top and bottom). On iOS, `.automatic` resolves to `.soft` for all edges. Override explicitly if needed.

```swift
ScrollView {
    LazyVStack { /* ... */ }
}
.scrollEdgeEffectStyle(.soft, for: .top)    // Translucent top toolbar
.scrollEdgeEffectStyle(.hard, for: .bottom) // Crisp bottom bar
```
