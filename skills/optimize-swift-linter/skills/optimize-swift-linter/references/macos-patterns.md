# macOS-Specific Patterns

Drawn from: CotEditor (87/100), AeroSpace (84/100), Gifski (83/100), stats (82/100),
NetNewsWire (80/100), Maccy (79/100), Rectangle (76/100), Loop (77/100), Ice (67/100),
and sindresorhus libraries.

---

## 1. App Architecture

**Use `@main` + `App` protocol for new projects. Fall back to `AppDelegate` only when you need deep lifecycle hooks SwiftUI doesn't expose.**

```swift
@main
struct MyApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    var body: some Scene {
        WindowGroup { ContentView() }
        Settings { SettingsView() }
    }
}

// AppDelegate for things SwiftUI can't reach
class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ app: NSApplication) -> Bool { false }
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular) // or .accessory for menu-bar-only
    }
}
```

- `WindowGroup` — multi-window document-style apps
- `Window` — single fixed window (macOS 13+)
- `MenuBarExtra` — menu bar apps (macOS 13+)
- `Settings` — preferences window (macOS 13+)

---

## 2. AppKit Integration with SwiftUI

**SwiftUI first; drop to AppKit only for NSTextView, NSTableView, custom drawing, or system APIs with no SwiftUI equivalent.**

```swift
// Wrap AppKit view for use in SwiftUI
struct RichTextView: NSViewRepresentable {
    @Binding var text: NSAttributedString

    func makeNSView(context: Context) -> NSScrollView {
        let textView = NSTextView()
        textView.isRichText = true
        let scroll = NSScrollView()
        scroll.documentView = textView
        return scroll
    }
    func updateNSView(_ nsView: NSScrollView, context: Context) { /* sync state */ }
    func makeCoordinator() -> Coordinator { Coordinator($text) }
}

// Embed SwiftUI in AppKit hierarchy (stats/Loop pattern)
let hostingView = NSHostingView(rootView: ContentView())
existingNSView.addSubview(hostingView)
```

**Hybrid pattern (Loop/Ice):** AppKit owns window + event loop; SwiftUI renders each panel as `NSHostingController`. This gives pixel-perfect control over window chrome while keeping UI declarative.

---

## 3. Menu Bar Apps

**macOS 13+: use `MenuBarExtra` for simple cases. Use `NSStatusItem` + `NSPopover` for full control or backward compatibility.**

```swift
// SwiftUI (macOS 13+)
MenuBarExtra("App", systemImage: "circle.fill") {
    MenuBarContentView()
}
.menuBarExtraStyle(.window) // popover-like panel; omit for plain menu

// AppKit — max control, works on macOS 11+
class StatusBarController {
    private var statusItem: NSStatusItem!
    private var popover = NSPopover()

    init() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.image = NSImage(systemSymbolName: "circle.fill", accessibilityDescription: nil)
        statusItem.button?.action = #selector(toggle)
        statusItem.button?.target = self
        popover.contentViewController = NSHostingController(rootView: ContentView())
        popover.behavior = .transient
    }

    @objc func toggle() {
        if popover.isShown { popover.performClose(nil) }
        else { popover.show(relativeTo: statusItem.button!.bounds, of: statusItem.button!, preferredEdge: .minY) }
    }
}
```

For menu-bar-only apps: set `LSUIElement = YES` in Info.plist (or `NSApp.setActivationPolicy(.accessory)`).

---

## 4. Window Management

**Use `NSWindowController` for document windows. Use `openWindow(id:)` for SwiftUI-managed multi-window flows.**

```swift
// SwiftUI multi-window (macOS 13+)
@Environment(\.openWindow) private var openWindow
Button("Open Inspector") { openWindow(id: "inspector") }

// In App body:
Window("Inspector", id: "inspector") { InspectorView() }
    .defaultSize(width: 300, height: 500)
    .windowResizability(.contentSize)

// NSWindowController (AppKit) — Rectangle/AeroSpace pattern for system-level control
class PanelController: NSWindowController {
    convenience init() {
        let window = NSPanel(
            contentRect: .zero, styleMask: [.nonactivatingPanel, .borderless],
            backing: .buffered, defer: false
        )
        window.level = .floating
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        self.init(window: window)
    }
}
```

- Window restoration: set `restorationClass` on `NSWindowController`, implement `NSWindowRestoration`
- Full-screen: `window.collectionBehavior = [.fullScreenPrimary]`

---

## 5. System APIs

### IOKit / SMC (stats pattern)

**IOKit is C-based; wrap it in a Swift actor for safe async access.**

```swift
// Open SMC connection
var connection: io_connect_t = 0
let service = IOServiceGetMatchingService(kIOMainPortDefault,
    IOServiceMatching("AppleSMC"))
IOServiceOpen(service, mach_task_self_, 0, &connection)
IOObjectRelease(service)

// Read SMC key (simplified — stats uses SMCKit or direct struct calls)
// Use IOConnectCallStructMethod for sensor reads
```

### Accessibility API (Ice/AeroSpace)

**Requires runtime permission. Never assume access; always check and prompt.**

```swift
// Check permission
let trusted = AXIsProcessTrustedWithOptions(
    [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary
)

// Get frontmost app's windows
let app = AXUIElementCreateApplication(pid)
var value: CFTypeRef?
AXUIElementCopyAttributeValue(app, kAXWindowsAttribute as CFString, &value)
let windows = value as! [AXUIElement]
```

### NSWorkspace Notifications

```swift
NSWorkspace.shared.notificationCenter.addObserver(
    forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main
) { note in
    let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication
}
```

---

## 6. Keyboard Shortcuts

**Use [sindresorhus/KeyboardShortcuts](https://github.com/sindresorhus/KeyboardShortcuts) for global hotkeys. Avoid Carbon directly.**

```swift
// Define shortcut identifiers
extension KeyboardShortcuts.Name {
    static let togglePanel = Self("togglePanel", default: .init(.p, modifiers: [.command, .shift]))
}

// Register handler
KeyboardShortcuts.onKeyDown(for: .togglePanel) { [weak self] in
    self?.togglePanel()
}

// SwiftUI recorder widget (in Settings view)
KeyboardShortcuts.Recorder("Toggle Panel", name: .togglePanel)
```

For local key events in SwiftUI: `.onKeyPress(.space) { ... }` (macOS 14+).
For NSView: override `keyDown(with:)` and call `interpretKeyEvents([event])`.

---

## 7. Auto-Updates with Sparkle

**Use `SPUStandardUpdaterController`. Never ship without Sparkle for direct-distribution apps.**

```swift
// Package.swift
.package(url: "https://github.com/sparkle-project/Sparkle", from: "2.0.0")

// AppDelegate
import Sparkle
class AppDelegate: NSObject, NSApplicationDelegate {
    private let updaterController = SPUStandardUpdaterController(
        startingUpdater: true, updaterDelegate: nil, userDriverDelegate: nil
    )
}

// SwiftUI menu integration
CheckForUpdatesView(updater: appDelegate.updaterController.updater)
// (Sparkle ships this view; just add it to your Help menu)
```

Info.plist keys: `SUFeedURL` (your appcast URL), `SUPublicEDKey` (for EdDSA signing).
Sign updates: `sign_update` tool ships with Sparkle. Required — Sparkle 2 rejects unsigned items.

---

## 8. Sandboxing & Entitlements

**Don't sandbox utilities that need system access (AeroSpace, stats, Rectangle). Sandbox App Store builds.**

Key entitlements:
```xml
<!-- Network client (most apps need this) -->
<key>com.apple.security.network.client</key><true/>

<!-- User-selected file access -->
<key>com.apple.security.files.user-selected.read-write</key><true/>

<!-- Downloads folder (temporary exception) -->
<key>com.apple.security.temporary-exception.files.absolute-path.read-write</key>
<array><string>/Users/</string></array>
```

Security-scoped bookmarks for persistent file access outside sandbox:
```swift
let bookmark = try url.bookmarkData(
    options: .withSecurityScope, includingResourceValuesForKeys: nil, relativeTo: nil)
// Persist bookmark in UserDefaults
// Later: url.startAccessingSecurityScopedResource()
```

---

## 9. macOS Distribution

**Direct distribution: notarize + staple + distribute via DMG or Homebrew Cask. App Store: sandbox required.**

```bash
# Notarize (Xcode 15+ — xcrun notarytool)
rtk xcrun notarytool submit MyApp.dmg --keychain-profile "AC_PASSWORD" --wait
rtk xcrun stapler staple MyApp.dmg

# Create DMG (use create-dmg tool)
rtk create-dmg --volname "MyApp" --app-drop-link 660 185 MyApp.dmg MyApp.app
```

Homebrew Cask formula: provide SHA256, version, and download URL in `Casks/my-app.rb`.
Mac App Store: requires sandbox, no Sparkle, entitlements reviewed — expect 1-2 week review cycles.

---

## 10. Preferences / Settings

**Use [sindresorhus/Defaults](https://github.com/sindresorhus/Defaults) over raw `UserDefaults`. Use [sindresorhus/Settings](https://github.com/sindresorhus/Settings) for the Settings window.**

```swift
// Define keys with types
import Defaults
extension Defaults.Keys {
    static let launchAtLogin = Key<Bool>("launchAtLogin", default: false)
    static let accentColor = Key<Color>("accentColor", default: .blue)
}

// Read/write
Defaults[.launchAtLogin] = true
let color = Defaults[.accentColor]

// SwiftUI Settings window with tabs (sindresorhus/Settings)
import Settings
let settingsController = SettingsWindowController(panes: [
    GeneralSettingsPane(),
    AdvancedSettingsPane(),
])
```

Plain `@AppStorage` is fine for simple `Bool`/`String`/`Int` values with no type safety needs.

---

## 11. Launch at Login

**macOS 13+: use `SMAppService`. For older targets or convenience, use [sindresorhus/LaunchAtLogin](https://github.com/sindresorhus/LaunchAtLogin-Modern).**

```swift
import ServiceManagement

// Register
try SMAppService.mainApp.register()

// Unregister
try SMAppService.mainApp.unregister()

// Check status
let isEnabled = SMAppService.mainApp.status == .enabled
```

LaunchAtLogin-Modern wraps this and provides a SwiftUI toggle: `LaunchAtLogin.Toggle()`.
Requires no special entitlement for sandboxed apps; helper-based approach is gone in macOS 13+.

---

## 12. Dock Integration

**Use `NSDockTile` for badges and progress. Use [sindresorhus/DockProgress](https://github.com/sindresorhus/DockProgress) for animated progress arcs.**

```swift
// Badge
NSApp.dockTile.badgeLabel = "3"
NSApp.dockTile.display()

// DockProgress (Gifski uses this)
import DockProgress
DockProgress.style = .squircle(color: .controlAccentColor)
DockProgress.progress = 0.42  // 0.0–1.0; set to 1 or reset to hide
```

Override `applicationDockMenu(_:)` in `NSApplicationDelegate` to add items to the Dock right-click menu.

---

## 13. File System

**Use `NSOpenPanel` and `NSSavePanel` for user-initiated file access. Use `FileCoordinator` for shared documents.**

```swift
// Open panel (async, macOS 12+)
let panel = NSOpenPanel()
panel.allowedContentTypes = [.pdf, .plainText]
panel.allowsMultipleSelection = false
let response = await panel.begin()
if response == .OK, let url = panel.url { /* use url */ }

// Save panel
let save = NSSavePanel()
save.nameFieldStringValue = "export.pdf"
let response = await save.begin()

// Recent documents
NSDocumentController.shared.noteNewRecentDocumentURL(url)
```

Drag and drop: conform view to `DropDelegate` (SwiftUI) or implement `NSDraggingDestination` (AppKit).
UTType: always use typed `UTType` constants (`UTType.pdf`, `UTType.plainText`) over string literals.

---

## 14. macOS SwiftUI Specifics

**macOS SwiftUI has unique modifiers and scenes not available on iOS — know them.**

```swift
// Commands (menu bar items)
.commands {
    CommandGroup(replacing: .newItem) { }
    CommandMenu("Tools") {
        Button("Analyze") { analyze() }.keyboardShortcut("a", modifiers: [.command, .shift])
    }
}

// NavigationSplitView (macOS sidebar pattern)
NavigationSplitView {
    List(items, selection: $selection) { Label($0.name, systemImage: $0.icon) }
} detail: {
    DetailView(item: selection)
}

// Table (macOS-only, sortable columns)
Table(rows, sortOrder: $sortOrder) {
    TableColumn("Name", value: \.name)
    TableColumn("Size", value: \.size) { Text($0.size.formatted()) }
}

// Other key macOS-only modifiers
.windowResizability(.contentSize)      // window fits content
.defaultSize(width: 800, height: 600)  // initial window size
.windowToolbarStyle(.unified)          // toolbar style
.presentedWindowStyle(.titleBar)       // or .hiddenTitleBar
```

Avoid `NavigationStack` on macOS — it's an iOS pattern. Use `NavigationSplitView` instead.

---

## 15. Reference Codebases by Pattern

| Pattern | Study This Repo | Why |
|---------|----------------|-----|
| NSTextView / rich text editing | **CotEditor** | 17k commits, full NSTextView stack |
| Tiling window management / AXUIElement | **AeroSpace** | Pure SPM, accessibility API mastery |
| Menu bar popover, Sparkle, quality bar | **Gifski** | sindresorhus code standards |
| IOKit / SMC / hardware sensors | **stats** | every system sensor covered |
| Multi-target (iOS + macOS shared) | **NetNewsWire** | proven shared-module structure |
| Clipboard monitoring / pasteboard | **Maccy** | `NSPasteboard` polling patterns |
| Rectangle / window snapping | **Rectangle** | `NSWindow` manipulation at scale |
| SwiftUI + AppKit hybrid panels | **Loop** | `NSHostingController` inside AppKit |
| Menu bar icon management | **Ice** | advanced `NSStatusItem` tricks |
| `Defaults`, `Settings`, `KeyboardShortcuts` | **sindresorhus repos** | drop-in macOS utility libraries |
| Global keyboard shortcuts | **KeyboardShortcuts** (sindresorhus) | best-in-class global hotkey API |
| Launch at login (modern) | **LaunchAtLogin-Modern** (sindresorhus) | `SMAppService` wrapper |
