# AppKit Bridging for Liquid Glass on macOS

SwiftUI provides first-class Liquid Glass support through `.glassEffect()`, glass button styles, and `NavigationSplitView`. However, certain scenarios demand dropping into AppKit for full control over glass rendering, toolbar customization, window management, and event handling. This reference defines when to bridge, how to bridge correctly, and the patterns that prevent the most common pitfalls.

## When to Bridge to AppKit

Use AppKit when you need any of the following:

- **`NSGlassEffectView` with custom corner radius or tint** not achievable through the SwiftUI `.glassEffect()` modifier
- **Full `NSToolbar` customization** including user reordering, display mode switching (icon-only, label-only, icon-and-label), and size modes
- **Custom window management** beyond what `.windowStyle()` provides (e.g., programmatic window positioning, custom title bar content, non-standard chrome)
- **`NSVisualEffectView` fallback** for pre-Tahoe (macOS < 26) deployment targets
- **Advanced drag-and-drop** using file promises and the `NSDragging` protocol family
- **Precise mouse event handling** or custom cursor management
- **Advanced responder chain access** for custom key handling or first-responder manipulation
- **`NSTextView`** for rich text editing (attributed strings, text attachments, custom layout managers)
- **`NSView.LayoutRegion`** for corner avoidance in windows with large corner radii

Stay in pure SwiftUI when:

- Standard toolbar items via `.toolbar { }` suffice
- `NavigationSplitView` provides the sidebar pattern you need
- `.glassEffect()` gives you the glass look you want
- `.backgroundExtensionEffect()` handles your layout needs
- Button styles (`.glass`, `.glassProminent`) are enough
- You do not need to support macOS versions prior to Tahoe

> **Rule of thumb:** Start in SwiftUI. Bridge only the specific view or subsystem that requires AppKit. Never wrap an entire window in `NSViewRepresentable` when only one control needs it.

> **Critical constraint:** `NSGlassEffectView` has no `.state` property. When the hosting `NSWindow` is not the key window, glass renders significantly more opaque. There is no public API to force active glass on inactive windows (unlike `NSVisualEffectView.state = .active`). This is unresolved as of macOS 26.4 and breaks HUD-style floating windows. See `pitfalls-and-solutions.md` pitfall #30.

## NSViewRepresentable for NSGlassEffectView

The most common bridge: wrapping `NSGlassEffectView` so you can set corner radius and tint color beyond what the SwiftUI modifier exposes.

```swift
import SwiftUI
import AppKit

struct GlassEffectRepresentable: NSViewRepresentable {
    var cornerRadius: CGFloat = 12
    var tintColor: NSColor? = nil

    func makeNSView(context: Context) -> NSGlassEffectView {
        let glassView = NSGlassEffectView()
        glassView.cornerRadius = cornerRadius
        if let tint = tintColor {
            glassView.tintColor = tint
        }
        return glassView
    }

    func updateNSView(_ nsView: NSGlassEffectView, context: Context) {
        nsView.cornerRadius = cornerRadius
        nsView.tintColor = tintColor
    }
}
```

### Usage in SwiftUI

```swift
ZStack {
    GlassEffectRepresentable(cornerRadius: 20, tintColor: .systemBlue.withAlphaComponent(0.15))
        .frame(width: 300, height: 200)

    VStack {
        Image(systemName: "sparkles")
            .font(.largeTitle)
        Text("Custom Glass")
    }
}
```

## NSGlassEffectContainerView Bridge

When you need multiple glass regions grouped together, use `NSGlassEffectContainerView`. This container manages the shared backdrop and compositing for its children.

```swift
struct GlassContainerRepresentable: NSViewRepresentable {
    struct GlassRegion {
        var frame: CGRect
        var cornerRadius: CGFloat
        var tintColor: NSColor?
    }

    var regions: [GlassRegion]

    func makeNSView(context: Context) -> NSGlassEffectContainerView {
        let container = NSGlassEffectContainerView()
        for region in regions {
            let child = NSGlassEffectView()
            child.frame = region.frame
            child.cornerRadius = region.cornerRadius
            child.tintColor = region.tintColor
            container.addSubview(child)
        }
        return container
    }

    func updateNSView(_ nsView: NSGlassEffectContainerView, context: Context) {
        // Remove existing children and rebuild
        nsView.subviews.forEach { $0.removeFromSuperview() }
        for region in regions {
            let child = NSGlassEffectView()
            child.frame = region.frame
            child.cornerRadius = region.cornerRadius
            child.tintColor = region.tintColor
            nsView.addSubview(child)
        }
    }
}
```

> **Important:** `NSGlassEffectContainerView` does NOT propagate `cornerRadius` to its children. You must set `cornerRadius` on each child `NSGlassEffectView` individually. Failing to do so results in children rendering with the default radius, breaking visual consistency.

## Correct NSViewRepresentable Coordinator Pattern

The most common bug in AppKit bridging: capturing the parent view (a value type) inside the coordinator. Because SwiftUI recreates the struct on every state change, the coordinator ends up holding a stale copy.

### WRONG -- capturing self

```swift
// DO NOT DO THIS
struct BrokenTableView: NSViewRepresentable {
    var events: [String]

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self) // Captures a stale value-type copy
    }

    class Coordinator: NSObject {
        var parent: BrokenTableView // Stale after first SwiftUI update
        init(parent: BrokenTableView) { self.parent = parent }
    }
}
```

### CORRECT -- passing only data

```swift
struct EventsTableView: NSViewRepresentable {
    var events: [String]

    func makeCoordinator() -> Coordinator {
        Coordinator(events: events) // Pass data, NOT self
    }

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        let tableView = NSTableView()
        let column = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("Event"))
        column.title = "Event"
        tableView.addTableColumn(column)
        tableView.delegate = context.coordinator
        tableView.dataSource = context.coordinator
        scrollView.documentView = tableView
        return scrollView
    }

    func updateNSView(_ nsView: NSScrollView, context: Context) {
        context.coordinator.events = events // Sync data every update cycle
        (nsView.documentView as? NSTableView)?.reloadData()
    }

    class Coordinator: NSObject, NSTableViewDelegate, NSTableViewDataSource {
        var events: [String]

        init(events: [String]) {
            self.events = events
        }

        func numberOfRows(in tableView: NSTableView) -> Int {
            events.count
        }

        func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
            let cell = NSTextField(labelWithString: events[row])
            return cell
        }
    }
}
```

### Coordinator Rules

1. **Never capture the parent view** (a value type) in a coordinator
2. **Pass only mutable data** the coordinator needs -- individual properties, not the whole struct
3. **Update coordinator data in `updateNSView`** so the coordinator always has fresh state
4. **Use the coordinator for AppKit delegate conformance** (`NSTableViewDelegate`, `NSToolbarDelegate`, etc.)

## NSToolbar Bridge Pattern

When the SwiftUI `.toolbar { }` modifier is insufficient -- for example, you need user-customizable toolbar items, display mode control, or the new `.glass` bezel style on individual buttons:

```swift
struct AppKitToolbar: NSViewRepresentable {
    static let customItem = NSToolbarItem.Identifier("customAction")

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            let toolbar = NSToolbar(identifier: "MyToolbar")
            toolbar.delegate = context.coordinator
            toolbar.allowsUserCustomization = true
            toolbar.displayMode = .iconOnly
            window.toolbar = toolbar
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        // Toolbar updates handled through coordinator state if needed
    }

    class Coordinator: NSObject, NSToolbarDelegate {
        func toolbarDefaultItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] {
            [
                .toggleSidebar,
                .sidebarTrackingSeparator,
                .flexibleSpace,
                AppKitToolbar.customItem
            ]
        }

        func toolbarAllowedItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] {
            [
                .toggleSidebar,
                .sidebarTrackingSeparator,
                .flexibleSpace,
                .space,
                AppKitToolbar.customItem
            ]
        }

        func toolbar(
            _ toolbar: NSToolbar,
            itemForItemIdentifier identifier: NSToolbarItem.Identifier,
            willBeInsertedIntoToolbar flag: Bool
        ) -> NSToolbarItem? {
            switch identifier {
            case AppKitToolbar.customItem:
                let item = NSToolbarItem(itemIdentifier: identifier)
                item.label = "Action"
                item.toolTip = "Perform custom action"

                let button = NSButton()
                button.bezelStyle = .glass // NEW in macOS 26 -- Liquid Glass bezel
                button.image = NSImage(systemSymbolName: "star.fill", accessibilityDescription: "Action")
                button.target = self
                button.action = #selector(customAction(_:))
                item.view = button

                return item
            default:
                return nil
            }
        }

        @objc func customAction(_ sender: Any?) {
            // Handle action
        }
    }
}
```

### Toolbar Integration in a SwiftUI View

```swift
struct ContentView: View {
    var body: some View {
        NavigationSplitView {
            SidebarView()
        } detail: {
            DetailView()
        }
        .background {
            AppKitToolbar()
                .frame(width: 0, height: 0) // Invisible -- only installs the toolbar
        }
    }
}
```

## SwiftUI .toolbar vs NSToolbar Comparison

| Feature | SwiftUI `.toolbar` | NSToolbar (AppKit) |
|---|---|---|
| User customization | `.toolbar(id:)` + `customizationBehavior` | `allowsUserCustomization = true` |
| Display modes | Not controllable | `.iconOnly`, `.iconAndLabel`, `.labelOnly` |
| Size modes | Not exposed | `sizeMode` property |
| Placement | Predefined placements (`.principal`, `.automatic`, etc.) | Arbitrary via delegate ordering |
| Glass bezel on buttons | Automatic for standard items | `bezelStyle = .glass` on `NSButton` |
| Badges | `.badge(Int)` modifier | `NSItemBadge` |
| User reordering | Limited (via `customizationBehavior`) | Full drag-and-drop reordering |
| Overflow handling | Automatic | Configurable via `visibilityPriority` |
| Programmatic item insertion | Not supported | `insertItem(withItemIdentifier:at:)` |

## NSWindow Delegate for Glass Windows

Glass appearance transitions (brightening, dimming) are automatic when a window gains or loses main status. Use the window delegate when you need to coordinate additional behavior with these transitions:

```swift
class WindowDelegate: NSObject, NSWindowDelegate {
    func windowDidBecomeMain(_ notification: Notification) {
        // Glass automatically brightens when the window gains focus.
        // Use this callback to start animations, resume updates, or
        // synchronize non-glass UI elements with the active appearance.
    }

    func windowDidResignMain(_ notification: Notification) {
        // Glass automatically dims when the window loses focus.
        // Use this to pause expensive rendering, reduce update frequency,
        // or visually de-emphasize custom (non-glass) overlays.
    }

    func windowWillResize(_ sender: NSWindow, to frameSize: NSSize) -> NSSize {
        // Enforce minimum size to prevent glass regions from collapsing
        return NSSize(
            width: max(frameSize.width, 400),
            height: max(frameSize.height, 300)
        )
    }
}
```

### Installing a Window Delegate from SwiftUI

```swift
struct WindowAccessor: NSViewRepresentable {
    var delegate: NSWindowDelegate

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            view.window?.delegate = delegate
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}
}
```

## NSView.LayoutRegion for Corner Avoidance

macOS 26 windows have larger corner radii as part of the Liquid Glass design language. Content placed in corners may be clipped. Use `NSView.LayoutRegion` to constrain subviews within safe areas that respect the new corner geometry.

```swift
// AppKit: avoid new window corner radii clipping content
class CornerAwareViewController: NSViewController {
    override func viewDidLayout() {
        super.viewDidLayout()

        let safeArea = view.layoutGuide(for: .safeArea(cornerAdaptation: .horizontal))

        // Constrain a button to respect corner-safe insets
        let button = NSButton(title: "Action", target: self, action: #selector(doAction))
        button.bezelStyle = .glass
        button.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(button)

        NSLayoutConstraint.activate([
            safeArea.leadingAnchor.constraint(equalTo: button.leadingAnchor),
            safeArea.trailingAnchor.constraint(greaterThanOrEqualTo: button.trailingAnchor),
            safeArea.bottomAnchor.constraint(equalTo: button.bottomAnchor)
        ])
    }

    @objc func doAction() {}
}
```

### Corner Adaptation Modes

| Mode | Behavior |
|---|---|
| `.horizontal` | Insets leading and trailing edges to avoid corners |
| `.vertical` | Insets top and bottom edges to avoid corners |
| `.all` | Insets all edges |

> In SwiftUI, use `.safeAreaPadding()` or `.ignoresSafeArea()` to achieve similar behavior. The AppKit `LayoutRegion` API is primarily needed when you host raw `NSView` subclasses that manage their own Auto Layout constraints.

## Hybrid Architecture Pattern

The recommended architecture for apps that need both SwiftUI views and AppKit-level control: use SwiftUI for all views and glass effects, with an AppKit shell for window configuration, toolbar management, and system-level integration.

```swift
@main
struct MyApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView() // SwiftUI views with .glassEffect()
        }
        .windowStyle(.automatic) // Liquid Glass chrome on Tahoe
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // AppKit-level setup that cannot be done from SwiftUI:
        // - Custom NSToolbar installation
        // - NSWindow appearance overrides
        // - Menu bar customization
        // - Global event monitors
    }

    func applicationSupportsSecureRestorableState(_ app: NSApplication) -> Bool {
        true
    }
}
```

### When to Use Each Layer

| Layer | Responsibilities |
|---|---|
| **SwiftUI** | All view hierarchy, `.glassEffect()`, navigation, state management, standard toolbar items, animations |
| **AppKit (via bridge)** | `NSGlassEffectView` with custom properties, `NSToolbar` with user customization, `NSWindow` delegate, `NSVisualEffectView` fallback, `NSTextView`, drag-and-drop |
| **AppDelegate** | App lifecycle, global menu bar, Dock menu, Apple Events, URL handling, global hotkeys |

### Pre-Tahoe Fallback Pattern

When your deployment target includes macOS versions before Tahoe (macOS 26):

```swift
struct AdaptiveGlassView: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView {
        if #available(macOS 26, *) {
            let glassView = NSGlassEffectView()
            glassView.cornerRadius = 12
            return glassView
        } else {
            let effectView = NSVisualEffectView()
            effectView.material = .sidebar
            effectView.blendingMode = .behindWindow
            effectView.state = .active
            return effectView
        }
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        if #available(macOS 26, *) {
            guard let glassView = nsView as? NSGlassEffectView else { return }
            glassView.cornerRadius = 12
        }
        // NSVisualEffectView needs no updates for basic usage
    }
}
```

> **Key difference:** `NSVisualEffectView` uses material-based blurring (vibrancy). `NSGlassEffectView` uses the new Liquid Glass compositing pipeline with specular highlights and depth-aware tinting. They are not interchangeable, but `NSVisualEffectView` is the closest visual fallback for older systems.
