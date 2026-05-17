# macOS Windows and Window Management Reference

> **Scope:** macOS only. Covers all window types, window chrome dimensions, resizing, full screen, Stage Manager, tabbing, and restoration.
> **Last researched:** 2026-04-05 against macOS Sequoia 15 / macOS Tahoe (26) WWDC25 / AppKit documentation.

---

## 1. Window Types

macOS has two primary window classes in AppKit: `NSWindow` (for document and application windows) and `NSPanel` (a subclass of `NSWindow` for auxiliary, utility, and floating windows). Both are further specialized by `styleMask` flags and `collectionBehavior`.

### 1.1 Document Window

A document window displays a single user document. It is the primary window in a document-based application.

| Property | Value |
|---|---|
| Class | `NSWindow` |
| Typical styleMask | `.titled` + `.closable` + `.miniaturizable` + `.resizable` |
| Title bar height | 28 pt (macOS 11+, Big Sur and later) |
| Title bar height (pre–Big Sur) | ~22 pt |
| Traffic lights | Close (red), Minimize (yellow), Zoom (green) — all enabled |
| Animation behavior | `.documentWindow` |
| Full screen | Supported — add `.fullScreenPrimary` to `collectionBehavior` |
| Tabbing | Supported — implement `newWindowForTab(_:)` in the responder chain |
| Close behavior | Closes without quitting application (unless `applicationShouldTerminateAfterLastWindowClosed` returns `true`) |

Multiple document windows per app are managed through `NSDocumentController`. Each document can have multiple `NSWindowController` instances via `NSDocument.addWindowController(_:)`.

### 1.2 Application (Non-Document) Window

A standard app window that is not tied to a persistent file-based document. Used for utilities, browsers, media apps, settings, and so on.

| Property | Value |
|---|---|
| Class | `NSWindow` |
| Typical styleMask | `.titled` + `.closable` + `.miniaturizable` + `.resizable` |
| Title bar height | 28 pt (macOS 11+) |
| Traffic lights | Same as document window |
| Animation behavior | `.default` (system infers appropriate animation) |
| Singleton behavior | Common to allow only one instance; use `NSWindowController.windowFrameAutosaveName` to persist frame |

### 1.3 Utility Panel (Palette / Inspector)

A small floating window that provides tools or settings auxiliary to the main document window. Stays visible while the user works in document windows.

| Property | Value |
|---|---|
| Class | `NSPanel` |
| styleMask flag | `.utilityWindow` (hex `0x100`) |
| Title bar height | Smaller than document window — approximately 16–18 pt (unmeasured precisely; system-managed) |
| Traffic lights | Close button only; minimize and zoom are absent or disabled |
| Float behavior | Remains visible in front of document windows when app is active |
| `isFloatingPanel` | `true` — panel floats above document windows |
| `hidesOnDeactivate` | Typically `true` — hides when the app loses focus |
| `becomesKeyOnlyIfNeeded` | Set `true` in `awakeFromNib` so clicking controls that need key focus (e.g., text fields) activates the panel, but other clicks do not steal focus |
| Animation behavior | `.utilityWindow` |

**Source:** Apple AppKit SDK NSWindow.h (Phracker MacOSX-SDKs); Stack Overflow q/54990155; Cindori floating panel tutorial.

### 1.4 Floating Panel (Non-Activating)

A panel that can appear over all other windows — including other applications — without activating the owning app. Used for Spotlight-style palettes, quick-entry windows (Raycast, Alfred, 1Password).

| Property | Value |
|---|---|
| Class | `NSPanel` |
| styleMask flag | `.nonactivatingPanel` (hex `0x400`) |
| Level | `.floating` or `.mainMenu` when above full-screen apps |
| collectionBehavior | `.canJoinAllSpaces` + `.fullScreenAuxiliary` |
| Key window behavior | App stays inactive; panel can still receive key events via `kCGSPreventsActivationTagBit` mechanism |
| Activation caveat | Setting `.nonactivatingPanel` in `styleMask` **after** initialization does **not** update the WindowServer tag; must be set at init time (Radar FB16484811; philz.blog) |

```swift
let panel = NSPanel(
    contentRect: NSRect(x: 0, y: 0, width: 600, height: 400),
    styleMask: [.nonactivatingPanel, .titled, .resizable, .closable, .fullSizeContentView],
    backing: .buffered,
    defer: false)
panel.isFloatingPanel = true
panel.level = .floating
panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
panel.hidesOnDeactivate = true
panel.canBecomeKey  // override to return true for text input support
```

**Source:** Cindori floating-panel tutorial; Stack Overflow q/36205834; philz.blog NSPanel nonactivating flag.

### 1.5 HUD (Heads-Up Display) Window

A dark-background floating panel typically used in media playback apps for transport controls. Designed to overlay content without distracting from it.

| Property | Value |
|---|---|
| Class | `NSPanel` subclass |
| styleMask flag | `.hudWindow` (hex `0x800`) |
| Background | Dark, semi-transparent (darkens when key/active, lightens when inactive) |
| Deprecated predecessor | `NSHUDWindowMask` (Objective-C constant, legacy) — replaced by `NSWindow.StyleMask.hudWindow` |
| Usage | Must be combined with `.titled`; use `NSPanel` not bare `NSWindow` |
| Current status | Available; `NSHUDWindowMask` ObjC constant deprecated in favor of the Swift struct value |

**Source:** Apple Developer Documentation (hudWindow); Xojo Forum thread on NSHUDWindowMask.

### 1.6 Borderless Window

A window with no system chrome — no title bar, no traffic lights, no resize handles. Used for splash screens, onboarding overlays, and fully custom-drawn UIs.

| Property | Value |
|---|---|
| Class | `NSWindow` |
| styleMask | `.borderless` (value `0`) |
| Key/Main | By default `canBecomeKey` and `canBecomeMain` return `false` — must override both to return `true` for keyboard input |
| Shadow | No drop shadow by default; enable with `window.hasShadow = true` |
| Move | Not movable by default; set `window.isMovableByWindowBackground = true` |
| Transparent | `window.backgroundColor = .clear` with `window.isOpaque = false` |

**Source:** Cocoawithlove.com custom window; AppKit NSWindow.h SDK header.

### 1.7 Full-Size Content View Window

Not a separate window type, but a crucial modifier. The `.fullSizeContentView` styleMask flag extends the content view to fill the entire window frame, including the title bar area.

| Property | Value |
|---|---|
| styleMask flag | `.fullSizeContentView` (hex `0x10`) |
| Effect | Content view covers title bar; title bar becomes transparent if `titlebarAppearsTransparent = true` |
| Title bar height query | `frame.height - contentLayoutRect.height` (the standard formula returns 0 when this mask is set; use `contentLayoutRect` instead) |
| Use case | Sidebars that extend under the title bar, immersive media apps, custom chrome apps |

```swift
let window = NSWindow(
    contentRect: NSRect(x: 0, y: 0, width: 800, height: 600),
    styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
    backing: .buffered, defer: false)
window.titlebarAppearsTransparent = true
// Title bar height = window.frame.height - window.contentLayoutRect.height
```

**Source:** Stack Overflow q/28955483; Medium bancarel full-height sidebar.

### 1.8 Window Type Summary Table

| Window Type | Class | Key styleMask Flags | Title Bar | Traffic Lights | Floats |
|---|---|---|---|---|---|
| Document window | `NSWindow` | `.titled` `.closable` `.miniaturizable` `.resizable` | 28 pt (Big Sur+) | All three | No |
| App window (non-doc) | `NSWindow` | Same as document | 28 pt | All three | No |
| Utility panel | `NSPanel` | `.utilityWindow` | ~16–18 pt | Close only | Yes (app-scope) |
| Floating / non-activating | `NSPanel` | `.nonactivatingPanel` | Varies | Configurable | Yes (system-scope) |
| HUD panel | `NSPanel` | `.hudWindow` `.titled` | Dark title bar | Close only | Yes |
| Borderless | `NSWindow` | `.borderless` (0) | None | None | No |
| Full-size content | `NSWindow` | adds `.fullSizeContentView` | Transparent overlay | Present | No |
| Document-modal | `NSWindow` | `.docModalWindow` | Sheet style | None | Attached to parent |

---

## 2. Window Chrome

### 2.1 Title Bar Height

Apple does not publish a fixed pixel value in the HIG. The system manages title bar height, and it varies by window style and macOS version.

| macOS Version | Standard Title Bar | Utility Panel | Unified Toolbar (Unified style) |
|---|---|---|---|
| macOS 11 Big Sur and later | ~28 pt | ~16–18 pt | Taller; system-managed based on control size |
| macOS 10.15 Catalina and earlier | ~22 pt | ~16 pt | Standard toolbar row below title bar |

**How to measure programmatically:**

```swift
// Standard window (no fullSizeContentView):
extension NSWindow {
    var titleBarHeight: CGFloat {
        frame.height - contentRect(forFrameRect: frame).height
    }
}

// Window with .fullSizeContentView (the above returns 0):
let titleBarHeight = window.frame.height - window.contentLayoutRect.height
```

The title bar also includes any toolbar when `toolbarStyle = .unified` or `.unifiedCompact` — `contentLayoutRect` accounts for the full combined height.

**Community observation (r/OSXTweaks):** Users measured Big Sur title bars as approximately 35% taller than Catalina equivalents.

**Sources:** Stack Overflow q/28955483; Apple AppKit `contentLayoutRect` documentation; Apple WWDC20 session 10104.

### 2.2 Traffic Light Buttons

Traffic lights are the Close (red), Minimize/Miniaturize (yellow), and Zoom (green) window control buttons in the top-left corner.

**Identifiers (NSWindow.ButtonType):**

| Button | Identifier | Enum Value |
|---|---|---|
| Close | `NSWindowCloseButton` | 0 |
| Minimize | `NSWindowMiniaturizeButton` | 1 |
| Zoom / Full Screen | `NSWindowZoomButton` | 2 |
| Toolbar toggle | `NSWindowToolbarButton` | 3 |
| Document icon | `NSWindowDocumentIconButton` | 4 |
| Versions button | `NSWindowDocumentVersionsButton` | 6 |
| Full Screen button | `NSWindowFullScreenButton` | 7 |

**Accessing buttons programmatically:**

```swift
let closeButton = window.standardWindowButton(.closeButton)
let minimizeButton = window.standardWindowButton(.miniaturizeButton)
let zoomButton = window.standardWindowButton(.zoomButton)
```

**Colors (from lwouis/macos-traffic-light-buttons-as-SVG — measured approximations):**

| State | Close (Red) | Minimize (Yellow) | Zoom (Green) |
|---|---|---|---|
| Normal fill | `#ed6a5f` | `#f6be50` | `#61c555` |
| Normal border | `#e24b41` | `#e1a73e` | `#2dac2f` |
| No-focus fill | `#dddddd` | `#dddddd` | `#dddddd` |
| No-focus border | `#d1d0d2` | `#d1d0d2` | `#d1d0d2` |
| Hover symbol color | `#460804` | `#90591d` | `#2a6218` |

**Position and dimensions:** Apple does not publish exact point coordinates. Key facts:
- Buttons are positioned by the private `NSThemeFrame` view hierarchy.
- Horizontal positions reset after window resize unless manually managed (see Medium @clyapp article).
- The close button is at approximately x=7–8 pt from left edge, centered vertically in the title bar.
- Inter-button gap is approximately 6–8 pt (center-to-center ~20 pt).
- Tauri cross-platform default: `trafficLightPosition: { x: 15, y: 20 }` — positions from left/top edge in overlay title bar style.
- Buttons reset to native positions on resize; fix with `NSWindow.didResizeNotification` observer.

**Hover behavior:** Each button's `+`/`–`/`×` symbols appear on hover. The drawing logic queries the superview for the private `_mouseInGroup:` method. Moving buttons out of `NSThemeFrame` to `contentView` disables hover icons unless `_mouseInGroup:` is reimplemented.

**Full-screen behavior:** Traffic lights are hidden while in full-screen mode. They reappear when the pointer moves to the top of the screen (auto-hide title bar area).

**Sources:** Stack Overflow q/7634788; Xojo forum traffic light position thread; lwouis SVG repo; Medium @clyapp article; Cocoawithlove custom window article.

### 2.3 Window Chrome View Hierarchy

The system-managed window chrome uses private AppKit classes:

```
NSWindow
└── NSThemeFrame          (private; draws the chrome)
    ├── title bar area    (close/minimize/zoom buttons live here)
    └── NSView            (contentView — sibling, not child, of title bar area)
```

For borderless windows, `NSNextStepFrame` is used instead of `NSThemeFrame`. Custom windows that bypass `NSThemeFrame` must manually manage button tracking areas.

**Sources:** Cocoawithlove 2008 custom window article; Stack Overflow q/7634788.

### 2.4 Title Bar APIs

| API | Description |
|---|---|
| `window.title` | Window title string |
| `window.titleVisibility` | `.visible` or `.hidden` |
| `window.titlebarAppearsTransparent` | Blends title bar with content (requires `.fullSizeContentView`) |
| `window.toolbarStyle` | `.automatic` `.unified` `.unifiedCompact` `.expanded` `.preference` (macOS 11+) |
| `window.titlebarSeparatorStyle` | `.automatic` `.none` `.line` `.shadow` — controls separator between title bar and content |
| `window.windowTitlebarLayoutDirection` | Layout direction for title bar items (macOS 10.12+) |
| `NSTitlebarAccessoryViewController` | Adds accessory views (e.g., a segmented control) to the title bar |
| `NSTitlebarAccessoryViewController.fullScreenMinHeight` | Minimum height of accessory view in full-screen mode |

---

## 3. NSWindow.StyleMask Options

All constants are combinable with bitwise OR. Values from the official AppKit framework header and Apple Developer Documentation.

| Swift Case | ObjC Constant | Hex | Decimal | Description |
|---|---|---|---|---|
| `.borderless` | `NSBorderlessWindowMask` | `0x0` | 0 | No chrome at all |
| `.titled` | `NSTitledWindowMask` | `0x1` | 1 | Title bar present |
| `.closable` | `NSClosableWindowMask` | `0x2` | 2 | Close button |
| `.miniaturizable` | `NSMiniaturizableWindowMask` | `0x4` | 4 | Minimize button |
| `.resizable` | `NSResizableWindowMask` | `0x8` | 8 | Resize handles |
| `.fullSizeContentView` | — | `0x10` | 16 | Content extends under title bar |
| `.unifiedTitleAndToolbar` | `NSUnifiedTitleAndToolbarWindowMask` | `0x1000` | 4096 | Merges title bar and toolbar into one area |
| `.utilityWindow` | — | `0x100` | 256 | Utility/palette panel style |
| `.docModalWindow` | — | `0x200` | 512 | Document-modal sheet |
| `.nonactivatingPanel` | — | `0x400` | 1024 | Panel does not activate owning app |
| `.hudWindow` | — | `0x800` | 2048 | HUD dark background style |
| `.fullScreen` *(deprecated)* | `NSFullScreenWindowMask` | `0x20` | 32 | Use `collectionBehavior` instead |
| `.texturedBackground` *(deprecated)* | `NSTexturedBackgroundWindowMask` | `0x4000` | 16384 | Textured look; use `.titled` |

**Sources:** Apple Developer Documentation NSWindow.StyleMask; MacOSX10.9 SDK NSWindow.h via Phracker/MacOSX-SDKs GitHub.

---

## 4. NSWindow.CollectionBehavior

Collection behaviors control how windows interact with Spaces, Exposé/Mission Control, Stage Manager, and full-screen mode.

| Swift Case | ObjC Constant | Hex | Description |
|---|---|---|---|
| `.default` | `NSWindowCollectionBehaviorDefault` | `0x0` | Default system behavior |
| `.canJoinAllSpaces` | `NSWindowCollectionBehaviorCanJoinAllSpaces` | `0x1` | Window appears on all Spaces |
| `.moveToActiveSpace` | `NSWindowCollectionBehaviorMoveToActiveSpace` | `0x2` | Window moves to the active Space when app is activated |
| `.managed` | `NSWindowCollectionBehaviorManaged` | `0x4` | Participates in Spaces and Exposé (default for normal windows) |
| `.transient` | `NSWindowCollectionBehaviorTransient` | `0x8` | Floats in Spaces, hidden by Exposé (default for panels) |
| `.stationary` | `NSWindowCollectionBehaviorStationary` | `0x10` | Unaffected by Exposé; stays visible (desktop-type windows) |
| `.participatesInCycle` | `NSWindowCollectionBehaviorParticipatesInCycle` | `0x20` | Included in Cmd+` window cycling |
| `.ignoresCycle` | `NSWindowCollectionBehaviorIgnoresCycle` | `0x40` | Excluded from Cmd+` window cycling |
| `.fullScreenPrimary` | `NSWindowCollectionBehaviorFullScreenPrimary` | `0x80` | Window can enter full-screen mode (macOS 10.7+) |
| `.fullScreenAuxiliary` | `NSWindowCollectionBehaviorFullScreenAuxiliary` | `0x100` | Window appears alongside full-screen windows / panels above full-screen |
| `.fullScreenNone` | `NSWindowCollectionBehaviorFullScreenNone` | — | Opt out of full-screen support (macOS 12+) |
| `.canJoinAllApplications` | — | — | Window appears alongside all applications in Stage Manager (macOS 13+) |

**Sources:** MacOSX10.9 SDK NSWindow.h; Apple Developer Documentation NSWindow.CollectionBehavior; Stack Overflow q/36205834.

---

## 5. Window Resizing Behavior

### 5.1 Size Constraints

```swift
// Minimum size (includes title bar)
window.minSize = NSSize(width: 400, height: 300)

// Maximum size
window.maxSize = NSSize(width: 1200, height: 900)

// Aspect ratio constraint
window.aspectRatio = NSSize(width: 16, height: 9)

// Resize increments (e.g., for terminal grid)
window.resizeIncrements = NSSize(width: 7, height: 13)

// Content min/max (excludes title bar)
window.contentMinSize = NSSize(width: 400, height: 200)
window.contentMaxSize = NSSize(width: NSScreen.main!.visibleFrame.width, height: .infinity)
```

**Minimum size API:** `NSWindow.minSize` — the minimum size of the **frame** (title bar included). Use `contentMinSize` for content-area constraints. `NSWindow.setMinSize:` is the Objective-C method (`[window setMinSize:NSMakeSize(500, 500)]`).

**Sources:** Apple Developer Documentation NSWindow.minSize; Stack Overflow q/5496868.

### 5.2 Resize Handles (Corner Hotspot)

| macOS Version | Corner Resize Hotspot | Notes |
|---|---|---|
| macOS 15 Sequoia and earlier | 19 × 19 pt square | ~62% of hotspot is inside the visible window with slightly-rounded corners |
| macOS 26 Tahoe | Still 19 × 19 pt square | Much larger corner radius pushes ~75% of hotspot outside visible window; extremely difficult to grab |

**Tahoe regression:** The fixed 19×19 pt hotspot was not adjusted to match the larger corner radius in macOS Tahoe. The recommended workaround is to grab the outer corner area, which is entirely outside the visible rounded window. This is a known usability issue discussed on Hacker News and by developer Norbert Heger. Apple design lead Alan Dye confirmed the larger corner radius is intentional; per-window hotspot adjustment was not implemented.

**Sources:** Gigazine macOS Tahoe windows article; Hacker News discussion item/46583438.

### 5.3 Resize Behavior

| Behavior | API |
|---|---|
| User-resizable | Include `.resizable` in styleMask |
| Live resize (content reflows) | Default; implement `windowDidResize(_:)` in delegate |
| Resize notification | `NSWindow.didResizeNotification` |
| Resize increments (grid-snap) | `window.resizeIncrements` |
| Lock aspect ratio | `window.aspectRatio` |
| Programmatic resize | `window.setFrame(_:display:animate:)` |

---

## 6. Window Levels

Window levels determine Z-order stacking across all windows on screen. Higher levels appear above lower levels regardless of application.

| Swift Level | ObjC Constant | Maps to CoreGraphics |
|---|---|---|
| `.normal` | `NSNormalWindowLevel` | `kCGNormalWindowLevel` |
| `.floating` | `NSFloatingWindowLevel` | `kCGFloatingWindowLevel` |
| `.submenu` / `.tornOffMenu` | `NSSubmenuWindowLevel` / `NSTornOffMenuWindowLevel` | `kCGTornOffMenuWindowLevel` |
| `.mainMenu` | `NSMainMenuWindowLevel` | `kCGMainMenuWindowLevel` |
| `.status` | `NSStatusWindowLevel` | `kCGStatusWindowLevel` |
| `.modalPanel` | `NSModalPanelWindowLevel` | `kCGModalPanelWindowLevel` |
| `.popUpMenu` | `NSPopUpMenuWindowLevel` | `kCGPopUpMenuWindowLevel` |
| `.screenSaver` | `NSScreenSaverWindowLevel` | `kCGScreenSaverWindowLevel` |

**Floating above full-screen apps:** Use `.mainMenu` level combined with `collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]`. This works on macOS Sonoma 14.5 and later without needing a higher level.

**Sources:** MacOSX10.9 SDK NSWindow.h; Stack Overflow q/36205834.

---

## 7. Full-Screen Mode

### 7.1 Enabling Full Screen

```swift
// Enable full-screen for a window:
window.collectionBehavior.insert(.fullScreenPrimary)

// Enter full-screen programmatically:
window.toggleFullScreen(nil)

// Detect full-screen state:
let isFullScreen = window.styleMask.contains(.fullScreen)
// or:
let isFullScreen = (window.styleMask.rawValue & NSWindow.StyleMask.fullScreen.rawValue) != 0
```

### 7.2 Full-Screen Behaviors

| Behavior | Notes |
|---|---|
| Dedicated Space | macOS creates a new Space for the full-screen window; other Spaces are accessible via Mission Control swipe |
| Menu bar | Auto-hides by default; settable per-app in System Settings → Desktop & Dock |
| Dock | Auto-hides while in full-screen |
| Title bar | Hidden; traffic lights reappear when pointer moves to top of screen |
| Tab bar | Appears at top if window has tabs; auto-hides when not hovering |
| Sidebar | Can extend full height using `.allowsFullHeightLayout` on `NSSplitViewItem` |
| `.fullSizeContentView` | Content continues to fill the full screen including former title bar area |
| Exit gesture | Cursor to top → traffic lights appear → click green button; or pinch gesture in macOS 10.11+ |
| Exit method | `window.toggleFullScreen(nil)` |

### 7.3 Auxiliary Full-Screen Windows

A secondary window can float over or alongside a full-screen app:

```swift
panel.collectionBehavior = [.fullScreenAuxiliary]
// The panel appears on the same space as the full-screen window
```

Setting `.fullScreenAuxiliary` alone (without `.fullScreenPrimary`) means the window does not go full-screen itself but can appear alongside full-screen windows.

### 7.4 Full-Screen Transition Animation

Entering full-screen triggers a system-managed zoom animation. AppKit provides hooks:

```swift
// NSWindowDelegate callbacks:
func windowWillEnterFullScreen(_ notification: Notification)
func windowDidEnterFullScreen(_ notification: Notification)
func windowWillExitFullScreen(_ notification: Notification)
func windowDidExitFullScreen(_ notification: Notification)
```

**NSWindowAnimationBehavior for enter/exit:**

| Case | Value | Description |
|---|---|---|
| `.default` | 0 | AppKit infers behavior |
| `.none` | 2 | Suppress animation |
| `.documentWindow` | 3 | Document window animation |
| `.utilityWindow` | 4 | Utility panel animation |
| `.alertPanel` | 5 | Alert panel animation |

**Sources:** Apple Developer Documentation NSWindow.CollectionBehavior.fullScreenPrimary; Stack Overflow q/6815917; Stack Overflow q/24145269; Apple HIG going-full-screen page.

---

## 8. Stage Manager

Stage Manager is a window management mode introduced in macOS 13 Ventura (iPadOS 16). It groups windows into App Sets displayed as thumbnails on the left edge of the screen.

### 8.1 User Behavior

| Behavior | Description |
|---|---|
| App Sets | Each App Set (also called a Window Set) represents one or more windows grouped together |
| Switching | Click an App Set thumbnail to bring it to the foreground; all windows in the set become active |
| Multiple app set | Multiple apps can share one App Set (drag a window onto another App Set) |
| Sidebar | Left edge of screen; can be hidden/shown by moving cursor to screen edge; recent apps can be hidden via System Settings |
| Desktop icons | Hidden when Stage Manager is active (can be re-enabled via Desktop Items toggle) |
| Cmd+Tab | Cycles between App Sets |
| Cmd+` (backtick) | Cycles between windows within the current App Set or between windows of different apps in the same set |
| Minimize | Sends a window to the left sidebar within the same App Set |
| Multi-display | Each display has its own Stage Manager; works across Desktops |

**Sources:** MacMost comprehensive Stage Manager guide.

### 8.2 Developer Considerations

| API | Description |
|---|---|
| `NSWindowCollectionBehavior.managed` | Windows with `.managed` participate in Stage Manager grouping (default for standard windows) |
| `NSWindowCollectionBehavior.transient` | Windows with `.transient` float above Stage Manager groups but are not grouped (default for panels) |
| `NSWindowCollectionBehavior.canJoinAllApplications` | Window appears alongside all applications; shows in every App Set (macOS 13+) |
| `NSWindowCollectionBehavior.moveToActiveSpace` | Window moves to the active Space/Set when its app is activated |

Windows that do not include `.managed` in `collectionBehavior` are not grouped into App Sets by Stage Manager. Panels and auxiliary windows typically use `.transient`, which correctly excludes them from Stage Manager grouping while keeping them visible as overlays.

**Sources:** Apple Developer Documentation NSWindow.CollectionBehavior; Tauri discussions q/10856.

---

## 9. Window Tabbing

Native window tabbing was introduced in macOS 10.12 Sierra. It allows multiple windows to appear as tabs within a single window frame, similar to browser tabs.

### 9.1 Enabling Tabbing

```swift
// App-wide opt-out (disables all tabbing):
NSWindow.allowsAutomaticWindowTabbing = false

// Per-window tabbingMode:
window.tabbingMode = .automatic    // default — system may tab on user action
window.tabbingMode = .preferred    // always show tab bar; merge windows automatically
window.tabbingMode = .disallowed   // never tab this window
```

**Critical warning:** `NSWindow.allowsAutomaticWindowTabbing = false` must be set **before** `applicationDidFinishLaunching` — ideally in `main.swift`. Window restoration runs before `applicationDidFinishLaunching` and can create tabbed windows before the flag is read (Radar 28578742; indiestack.com Daniel Jalkut).

### 9.2 Adding Tabs Programmatically

```swift
// Non-document-based app:
class WindowController: NSWindowController {
    @IBAction override func newWindowForTab(_ sender: Any?) {
        let wc = storyboard?.instantiateInitialController() as! WindowController
        guard let newWin = wc.window else { return }
        window?.addTabbedWindow(newWin, ordered: .above)
        newWin.orderFront(self)
        newWin.makeKey()
        // IMPORTANT: retain 'wc' — weak reference will deallocate the controller
    }
}
```

The `newWindowForTab(_:)` action must be in the responder chain (window controller or app delegate) for the "+" tab bar button to appear and be enabled.

### 9.3 NSWindowTabGroup

AppKit automatically creates `NSWindowTabGroup` instances to track tabbed windows. Access via:

```swift
window.tabGroup          // NSWindowTabGroup? — non-nil when window is in a tab group
window.tabbedWindows     // [NSWindow]? — visible tabs; may be nil if tab bar is hidden
window.tabGroup?.windows // [NSWindow] — all tabs even if tab bar is hidden
```

### 9.4 Tab Identifier

Windows are grouped into tabs based on `tabbingIdentifier`. Windows with the same identifier can merge into a single tabbed window. Set to a unique value to prevent unintended merging:

```swift
window.tabbingIdentifier = "com.myapp.MainWindow"
```

### 9.5 NSWindowDelegate for Tabs

```swift
func windowDidBecomeKey(_ notification: Notification) {
    // Sync window controller's .window reference to the newly-active tab
    guard let win = notification.object as? NSWindow, win != self.window else { return }
    self.window = win
}
```

A single `NSWindowController` manages all tabs; its `window` property must be updated to the active tab's `NSWindow` when the active tab changes.

**Sources:** Indiestack.com (Daniel Jalkut) window tabbing pox; Christiantietze.de NSWindow tabbing guide; Stack Overflow q/40202386; Stack Overflow q/60439491; Apple Developer Documentation NSWindowTabGroup.

---

## 10. Window Restoration

macOS automatically saves and restores window state between launches if "Close windows when quitting an app" is disabled in System Settings.

### 10.1 State Storage Location

| macOS Version | Storage Location |
|---|---|
| macOS 14 Sonoma and earlier | `~/Library/Saved Application State/<App.Bundle.ID>.savedState/` |
| macOS 15 Sequoia and later | Managed by `talagentd` daemon; stored in `~/Library/Daemon Containers/<UUID>/Data/Library/Saved Application State/` |

The UUID-to-app mapping is in `ApplicationMapping.plist` within the same directory.

**Source:** Apple Stack Exchange q/479893; Answer by Jakob Egger.

### 10.2 NSWindowRestoration Protocol

To restore non-storyboard windows, implement the `NSWindowRestoration` protocol:

```swift
class MyWindowRestoration: NSObject, NSWindowRestoration {
    static func restoreWindow(
        withIdentifier identifier: NSUserInterfaceItemIdentifier,
        state: NSCoder,
        completionHandler: @escaping (NSWindow?, Error?) -> Void) {
        // Instantiate window from storyboard or programmatically
        let wc = NSStoryboard.main?.instantiateInitialController() as? NSWindowController
        completionHandler(wc?.window, nil)
    }
}

// Assign to window:
window.restorationClass = MyWindowRestoration.self
```

**Without a restoration class** assigned, the window is not restored across launches.

### 10.3 Frame Auto-Save

The simplest form of window position/size persistence:

```swift
// Saves and restores window frame to/from NSUserDefaults
windowController.windowFrameAutosaveName = "MainWindow"

// Direct on NSWindow:
window.setFrameAutosaveName("MainWindow")
```

`setFrameAutosaveName` stores the frame in User Defaults as:
```
"NSWindow Frame <autosaveName>" = "<x> <y> <width> <height> <screenX> <screenY> <screenWidth> <screenHeight - menuBar>"
```

**Caveat:** If `setFrameAutosaveName` is called, any previously saved frame overrides the `contentRect` passed to `NSWindow(contentRect:...)`. Call `window.center()` to position freshly, but note it runs after the auto-saved frame is applied — order matters.

**Source:** Jameshfisher.com why-is-contentrect-ignored; Stack Overflow q/60439491.

### 10.4 Restorable State Key Paths

```swift
class MyWindow: NSWindow {
    override class var restorableStateKeyPaths: [String] {
        return ["self.tab.title", "self.title"]
    }
}
```

For tab titles and other properties to survive relaunch, add them to `restorableStateKeyPaths`. Tabs created by the user (not in the original storyboard) must have restoration classes assigned individually.

### 10.5 Force Restoration

```swift
// Force restoration even if user has disabled it in System Settings:
UserDefaults.standard.set(true, forKey: "NSQuitAlwaysKeepsWindows")
```

### 10.6 Notifications

| Notification | Description |
|---|---|
| `NSApplication.didFinishRestoringWindowsNotification` | Posted on main actor after all completion handlers from `restoreWindow(withIdentifier:state:completionHandler:)` have been called |

---

## 11. Multi-Window Architecture

### 11.1 Document-Based Apps (NSDocument)

Document-based apps use `NSDocument`, `NSDocumentController`, and `NSWindowController` to manage windows.

```
NSDocumentController (singleton, manages all open documents)
    └── NSDocument (one per open file)
        └── NSWindowController (one or more per document)
            └── NSWindow
```

Multiple window controllers can display the same document (e.g., a main window + inspector). Add with:

```swift
document.addWindowController(additionalWindowController)
```

**Sources:** Kodeco Windows and WindowController tutorial; Talk.objc.io episode S01E145.

### 11.2 Non-Document-Based Apps

```
NSApplication (singleton)
    └── NSWindowController (one per logical window)
        └── NSWindow
```

For multiple independent windows, create separate `NSWindowController` instances. Each controller should be retained (stored in an array or the app delegate) to prevent deallocation.

**Source:** Lapcatsoftware working-without-a-nib part 12; Zenn.dev usagimaru settings window.

### 11.3 NSWindowController Lifecycle

| Event | Description |
|---|---|
| `windowDidLoad()` | Called after window is loaded from nib/storyboard; configure here |
| `windowWillLoad()` | Before window is loaded |
| `shouldCascadeWindows` | `true` by default — cascades new windows offset from previous |
| `close()` | Closes the window; triggers `windowShouldClose` delegate |
| `windowFrameAutosaveName` | Persists window frame in User Defaults |

---

## 12. macOS Tahoe (26) Window Changes

macOS Tahoe (macOS 26, released fall 2025) introduced significant visual changes to window chrome:

### 12.1 Corner Radius

- Windows have a larger, softer corner radius compared to Sequoia.
- **Toolbarred windows:** Largest corner radius; wraps concentrically around the Liquid Glass toolbar.
- **Title-bar-only windows:** Smaller corner radius; tightly wraps the window controls.
- Different window types intentionally have different radii (confirmed by Apple designer Alan Dye).

### 12.2 Layout Guides for Corners

```swift
// Avoid placing content in rounded corners:
let safeArea = layoutGuide(for: .safeArea(cornerAdaptation: .horizontal))
// use safeArea anchors for constraints
```

`NSView.LayoutRegion` provides layout guides with corner-adaptation (horizontal or vertical inset) to keep UI elements clear of rounded corners.

### 12.3 Liquid Glass Toolbar

- Toolbar rendered on a Liquid Glass material that floats above content.
- Toolbar items are automatically grouped on a shared glass surface.
- Override grouping with `NSToolbarItemGroup` or spacers.
- Remove glass from an item: `toolbarItem.isBordered = false`.
- Tint glass: `toolbarItem.style = .prominent` or `toolbarItem.backgroundTintColor = .systemGreen`.
- Badges via `NSItemBadge`: `.count(_:)`, `.text(_:)`, `.indicator`.

### 12.4 Sidebar and Inspector Glass

- Sidebars appear as floating glass panes.
- Inspectors use edge-to-edge glass.
- Remove legacy `NSVisualEffectView` from sidebars — glass renders automatically.
- For floating sidebars: `splitViewItem.automaticallyAdjustsSafeAreaInsets = true`.

### 12.5 Resize Corner Regression

The 19×19 pt resize corner hotspot was not updated to match the larger corner radius. See §5.2.

### 12.6 New Glass APIs

| API | Description |
|---|---|
| `NSGlassEffectView` | Wraps a view with Liquid Glass material; set `.contentView` |
| `NSGlassEffectContainerView` | Groups multiple glass elements to share a sampling region for performance |

**Source:** WWDC25 session 310 "Adopt the new look of macOS"; Gigazine macOS Tahoe article; Hacker News item/46583438.

---

## 13. Settings Window Pattern

Settings windows follow a specific pattern enforced by the HIG:

| Property | Value |
|---|---|
| Toolbar style | `.preference` |
| Title | System-provided per-tab, or app name |
| Window size | Fixed per-tab — does not resize except when switching tabs |
| Traffic lights | Close only; minimize and zoom disabled |
| Frame autosave | Always use `windowFrameAutosaveName` |
| Opening | Via `NSApp.sendAction(#selector(showPreferencesWindow:), ...)` (pre-macOS 13) or `SettingsLink`/`openSettings` in SwiftUI (macOS 13+) |

```swift
// NSWindowController setup for settings:
let window = NSWindow(
    contentRect: NSRect(x: 0, y: 0, width: 600, height: 400),
    styleMask: [.titled, .closable],
    backing: .buffered, defer: false)
window.toolbarStyle = .preference
window.center()
windowController.windowFrameAutosaveName = "SettingsWindow"
```

Disable minimize and zoom by not including `.miniaturizable` or `.resizable` in the styleMask. The green zoom button will appear grayed out.

**Source:** Zenn.dev usagimaru settings window guide.

---

## 14. Window Animation Behaviors

| Enum Case | Value | Use Case |
|---|---|---|
| `.default` | 0 | AppKit infers — recommended for most windows |
| `.none` | 2 | Suppress all animation (testing, accessibility) |
| `.documentWindow` | 3 | Document windows (zoom from Dock icon) |
| `.utilityWindow` | 4 | Utility/tool palettes |
| `.alertPanel` | 5 | Alert dialogs and sheets |

**Source:** MacOSX10.9 SDK NSWindow.h.

---

## 15. Quick Reference: Common Configurations

### Standard Document Window

```swift
let window = NSWindow(
    contentRect: NSRect(x: 0, y: 0, width: 800, height: 600),
    styleMask: [.titled, .closable, .miniaturizable, .resizable],
    backing: .buffered, defer: false)
window.collectionBehavior = [.fullScreenPrimary]
window.animationBehavior = .documentWindow
```

### App Window with Full-Height Sidebar

```swift
let window = NSWindow(
    contentRect: NSRect(x: 0, y: 0, width: 900, height: 600),
    styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
    backing: .buffered, defer: false)
window.toolbarStyle = .unified
window.collectionBehavior = [.fullScreenPrimary]
// NSSplitViewItem: allowsFullHeightLayout = true + .sidebarTrackingSeparator in toolbar
```

### Floating Non-Activating Panel

```swift
let panel = NSPanel(
    contentRect: NSRect(x: 0, y: 0, width: 400, height: 300),
    styleMask: [.nonactivatingPanel, .titled, .closable, .fullSizeContentView],
    backing: .buffered, defer: false)
panel.isFloatingPanel = true
panel.level = .floating
panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
panel.hidesOnDeactivate = true
panel.titlebarAppearsTransparent = true
panel.isMovableByWindowBackground = true
```

### HUD Panel

```swift
let hud = NSPanel(
    contentRect: NSRect(x: 0, y: 0, width: 300, height: 100),
    styleMask: [.hudWindow, .titled, .closable, .resizable],
    backing: .buffered, defer: false)
hud.isFloatingPanel = true
hud.level = .floating
```

---

## Sources

| Source | Type | URL |
|---|---|---|
| Apple HIG — Windows | Official HIG | https://developer.apple.com/design/human-interface-guidelines/windows |
| Apple HIG — Going Full Screen | Official HIG | https://developer.apple.com/design/human-interface-guidelines/going-full-screen |
| NSWindow API | Official Docs | https://developer.apple.com/documentation/appkit/nswindow |
| NSPanel API | Official Docs | https://developer.apple.com/documentation/appkit/nspanel |
| NSWindow.StyleMask | Official Docs | https://developer.apple.com/documentation/appkit/nswindow/stylemask-swift.struct |
| NSWindow.CollectionBehavior | Official Docs | https://developer.apple.com/documentation/appkit/nswindow/collectionbehavior-swift.struct |
| NSWindowTabGroup | Official Docs | https://developer.apple.com/documentation/appkit/nswindowtabgroup |
| NSWindowRestoration | Official Docs | https://developer.apple.com/documentation/AppKit/NSWindowRestoration |
| NSTitlebarAccessoryViewController.fullScreenMinHeight | Official Docs | https://developer.apple.com/documentation/appkit/nstitlebaraccessoryviewcontroller/fullscreenminheight |
| allowsAutomaticWindowTabbing | Official Docs | https://developer.apple.com/documentation/appkit/nswindow/allowsautomaticwindowtabbing |
| WWDC20 10104 — Adopt new look of macOS | Official WWDC | mackuba.eu notes |
| WWDC25 310 — Adopt new look of macOS Tahoe | Official WWDC | https://developer.apple.com/videos/play/wwdc2025/310/ |
| MacOSX10.9 SDK NSWindow.h | SDK Header | https://github.com/phracker/MacOSX-SDKs |
| NSWindowStyles examples | GitHub | https://github.com/lukakerr/NSWindowStyles |
| Traffic light SVG measurements | GitHub | https://github.com/lwouis/macos-traffic-light-buttons-as-SVG |
| Title bar height computation | Stack Overflow | https://stackoverflow.com/questions/28955483 |
| Minimum window size | Stack Overflow | https://stackoverflow.com/questions/5496868 |
| Float panel above full-screen | Stack Overflow | https://stackoverflow.com/questions/36205834 |
| Window tabbing non-document app | Stack Overflow | https://stackoverflow.com/questions/40202386 |
| State restoration location (macOS 15) | Apple Stack Exchange | https://apple.stackexchange.com/questions/479893 |
| NSPanel nonactivating flag bug | Developer blog | https://philz.blog/nspanel-nonactivating-style-mask-flag/ |
| Floating panel SwiftUI implementation | Cindori | https://cindori.com/developer/floating-panel |
| Window tabbing with single NSWindowController | Christian Tietze | https://christiantietze.de/posts/2019/07/nswindow-tabbing-single-nswindowcontroller/ |
| Full-height sidebar | Medium | https://medium.com/@bancarel.paul/macos-full-height-sidebar-window-62a214309a80 |
| Traffic light button reset on resize | Medium | https://medium.com/@clyapp/fix-the-problem-that-nswindow-traffic-light-buttons-always-revert |
| Window tabbing pox (auto-tabbing quirk) | Indie Stack | https://indiestack.com/2016/10/window-tabbing-pox/ |
| NSWindow view hierarchy (NSThemeFrame) | Cocoawithlove | https://www.cocoawithlove.com/2008/12/drawing-custom-window-on-mac-os-x.html |
| setFrameAutosaveName behavior | James H Fisher | https://jameshfisher.com/2020/07/10/why-is-the-contentrect-of-my-nswindow-ignored/ |
| Stage Manager comprehensive guide | MacMost | https://macmost.com/the-comprehensive-guide-to-mac-stage-manager.html |
| macOS Tahoe resize regression | Gigazine | https://gigazine.net/gsc_news/en/20260113-macos-tahoe-windows/ |
| Tahoe resize HN discussion | Hacker News | https://news.ycombinator.com/item?id=46583438 |
| Big Sur title bar height (community) | Reddit r/OSXTweaks | https://www.reddit.com/r/OSXTweaks/comments/kgz2eb/ |
| Settings window pattern | Zenn.dev | https://zenn.dev/usagimaru/articles/b2a328775124ef |
| NSPanel key focus (becomesKeyOnlyIfNeeded) | Stack Overflow | https://stackoverflow.com/questions/54990155 |
| MoveToActiveSpace implementation | Tauri discussions | https://github.com/orgs/tauri-apps/discussions/10856 |

---

## 11. Proxy Icon (Document Icon in Title Bar)

Set `NSWindow.representedURL` to a file URL — the system shows a draggable document-type icon in the title bar. Users can drag it to Finder, Dock, or file-accepting destinations. Cmd-click reveals the path hierarchy.

```swift
window.representedURL = URL(fileURLWithPath: "/Users/alice/Documents/Report.pdf")
```

Access the icon button: `window.standardWindowButton(.documentIconButton)` (raw value 4).

### macOS Version Behavior

| Version | Default |
|---|---|
| macOS 10.15 and earlier | Always visible |
| macOS 11+ | Hidden by default; appears on hover |

User can re-enable: System Settings → Accessibility → Display → "Show window title icons".

## 12. Window Minimum and Maximum Size

### Frame vs Content Constraints

| Property | Includes title bar? | Use when |
|---|---|---|
| `minSize` / `maxSize` | Yes | You know exact total frame |
| `contentMinSize` / `contentMaxSize` | No | You care about usable content area |

### Auto Layout Interaction

- Auto Layout constraints create effective min/max independent of `minSize`
- When both exist: whichever is larger wins for minimum
- Recommended: let Auto Layout drive minimum size; only set `minSize` as a belt-and-suspenders floor

### Recommended Minimums

| App type | Suggested minimum |
|---|---|
| Document editor | 600 × 400 pt |
| Browser/list+detail | 800 × 500 pt |
| Utility panel | 200 × 100 pt |
| Settings window | Fixed to content size |
| Media player | 320 × 240 pt (aspect-locked) |

**Tiling note:** Ensure `contentMinSize.width` ≤ ~600pt to remain tileable on 1440pt displays.

## 13. Window Tiling (macOS 15 Sequoia)

### Tiling Actions

| Action | Result |
|---|---|
| Drag to left/right edge | Half-screen snap |
| Drag to corner | Quarter-screen snap |
| Drag to menu bar | Full-screen zoom (not full-screen mode) |
| Option-drag | Tile even when auto-tile is off |

### vs Full Screen vs Stage Manager

| | Tiling | Full Screen | Stage Manager |
|---|---|---|---|
| Menu bar | Visible | Auto-hides | Visible |
| Dock | Visible | Auto-hides | Visible |
| Mode switch | None needed | Dedicated Space | Explicit on/off |
| Multi-window | Any two side-by-side | One per Space | App Sets |

### Developer Notes

- No opt-in required — works for all windows by default
- No new `CollectionBehavior` constants for drag-to-tile
- Windows with `minSize` = `maxSize` (fixed size) are not force-resized
- `NSWindow.cascadingReferenceFrame` (macOS 15) returns untiled frame for correct cascading

## 14. Default Window Size and Position

### Autosave

```swift
window.setFrameAutosaveName("MainWindow")  // persists position/size to UserDefaults
```

Set before showing. Use unique name per window type. Autosaved frame overrides `contentRect`.

### Cascading

```swift
// Staircase pattern for document windows
static var cascadeOrigin = NSPoint.zero
cascadeOrigin = window.cascadeTopLeft(from: cascadeOrigin)
```

### First Launch Center

```swift
if UserDefaults.standard.string(forKey: "NSWindow Frame MainWindow") == nil {
    window.center()  // only on first launch
}
window.setFrameAutosaveName("MainWindow")
```

**Sources:** Apple Developer Documentation (NSWindow.representedURL, minSize, contentMinSize, setFrameAutosaveName, cascadeTopLeft, CollectionBehavior), Daring Fireball proxy icon article, mjtsai.com Sequoia tiling, WWDC24 AppKit session.
