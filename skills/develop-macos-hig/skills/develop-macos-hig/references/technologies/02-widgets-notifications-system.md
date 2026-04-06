# macOS System Integration Reference

> Scope: macOS only. iOS/iPadOS dimensions and behaviors are excluded unless explicitly noted as shared API surface. All dimensions are in points at @2x (Retina) unless stated otherwise.

---

## 1. Widgets

### 1.1 Widget Families Available on macOS

WidgetKit (introduced WWDC 2020) supports the following widget families on macOS. Not all families are available on every platform.

| Family | API Enum Case | macOS Support | Grid Slot |
|---|---|---|---|
| Small | `WidgetFamily.systemSmall` | macOS 11+ | 1×1 |
| Medium | `WidgetFamily.systemMedium` | macOS 11+ | 2×1 |
| Large | `WidgetFamily.systemLarge` | macOS 11+ | 2×2 |
| Extra Large | `WidgetFamily.systemExtraLarge` | macOS 14 Sonoma+ (desktop) | 4×2 |

Accessory families (`.accessoryCircular`, `.accessoryRectangular`, `.accessoryInline`, `.accessoryCorner`) are watchOS/iOS Lock Screen only — not available on macOS.

### 1.2 Widget Placement on macOS

**macOS Ventura and earlier:** Widgets appeared exclusively in the Notification Center sidebar (accessible by clicking the clock in the menu bar).

**macOS 14 Sonoma and later:** Widgets can be placed directly on the desktop. They sit behind open windows by default and can be configured to remain visible or fade. The widget gallery is accessed by right-clicking the desktop and choosing "Edit Widgets."

Widgets on the desktop are organized in a grid anchored to screen edges. The system determines exact on-screen pixel dimensions based on display resolution and scale factor. The grid slot proportions (1×1, 2×1, 2×2, 4×2) remain consistent.

### 1.3 Exact Widget Dimensions (Points)

Apple does not publish a single canonical dimension table for macOS widgets in the public HIG — dimensions are determined at runtime via `context.displaySize` inside `TimelineProvider`. The values below represent the dimensions reported by the WidgetKit runtime on macOS as documented by practitioners and confirmed against Apple's Xcode canvas presets:

| Family | Approximate macOS Dimensions (points) | Notes |
|---|---|---|
| systemSmall | ~170 × 170 | Square; exact value varies slightly by display configuration |
| systemMedium | ~329 × 170 | Wide rectangle; 2× width of small |
| systemLarge | ~329 × 345 | Tall rectangle; approximately 2× height of medium |
| systemExtraLarge | ~620 × 345 | Only on macOS 14+ desktop; twice the width of large |

**Critical note:** Always use `context.displaySize` (available inside `getTimeline(in:completion:)` and `getSnapshot(in:completion:)`) rather than hardcoding dimensions. The system passes the exact rendered size at call time.

```swift
func getTimeline(in context: Context, completion: @escaping (Timeline<Entry>) -> Void) {
    let size = context.displaySize  // Use this, not hardcoded values
    // ...
}
```

### 1.4 Widget Design Rules

**Interaction constraints:**
- Widgets are non-scrollable. Every piece of content must be visible within the widget's fixed frame.
- Prior to macOS 14 / iOS 17 (WWDC 2023): Tapping a widget opens the containing app. Widgets can use `Link` or `widgetURL` modifiers to pass a deep-link URL to the app on tap.
- macOS 14 / iOS 17 and later (interactive widgets): Widgets may embed `Button` and `Toggle` SwiftUI controls backed by `AppIntent`. These controls execute actions without launching the app to the foreground. The app process is launched in the background to perform the intent.

**Content rules:**
- Display timely, at-a-glance information — not interactive forms, text entry, or scrolling lists.
- Content must render correctly at all three standard sizes the developer declares support for.
- Images should be pre-rendered; avoid heavy computation in the widget view.
- Use system colors and dynamic type to respect user accessibility settings (Dark Mode, Increased Contrast, text size).
- Keep text minimal. Widgets are glanceable, not document viewers.
- The system may desaturate widget content on the macOS desktop in certain Focus modes or when behind windows.

**Tap targets (interactive widgets):**
- Minimum interactive region: follow standard SwiftUI tap target guidance (44×44 points minimum).
- Each `Button` or `Toggle` must be backed by an `AppIntent` that completes quickly — intents that take more than a few seconds will time out.

**Link / deep-link:**
```swift
// Entire widget taps to a URL
.widgetURL(URL(string: "myapp://content/item-id")!)

// Specific regions tap to different URLs
Link(destination: URL(string: "myapp://detail/1")!) {
    Text("View Detail")
}
```

### 1.5 Widget Timeline Behavior

Widgets use a **timeline provider** pattern. The app declares future timeline entries; the system renders and caches them, swapping views at the declared dates.

**Protocol:**
```swift
struct MyProvider: TimelineProvider {
    func placeholder(in context: Context) -> MyEntry { ... }
    func getSnapshot(in context: Context, completion: @escaping (MyEntry) -> Void) { ... }
    func getTimeline(in context: Context, completion: @escaping (Timeline<MyEntry>) -> Void) { ... }
}
```

**Methods:**
- `placeholder(in:)` — Returns a placeholder entry rendered while the widget loads. Must be fast; use static/mock data.
- `getSnapshot(in:completion:)` — Returns a single "preview" entry shown in the widget gallery. Must be fast.
- `getTimeline(in:completion:)` — Returns an array of `TimelineEntry` values plus a `TimelineReloadPolicy`. This is the primary data-fetch method.

**Reload policies (`TimelineReloadPolicy`):**
| Policy | Behavior |
|---|---|
| `.atEnd` | System calls `getTimeline` again after the last entry's date passes |
| `.after(date:)` | System calls `getTimeline` again after the specified date |
| `.never` | System never automatically requests a new timeline; use `WidgetCenter.shared.reloadTimelines(ofKind:)` from the app |

**Background refresh budget:**
- The system enforces a daily refresh budget per widget instance. Budgets are not publicly specified but are approximately 40–70 refreshes per day per widget across all instances.
- Budget is consumed faster when the widget is frequently visible and when the device is actively used.
- Exceeding budget causes the system to delay refreshes until budget replenishes.
- Use `WidgetCenter.shared.reloadTimelines(ofKind:)` from the host app when new data is available (e.g., after a push notification or foreground data sync) to avoid wasting background budget.

**WWDC 2024 additions:**
- `ControlWidget` API for interactive controls in the Control Center.
- Relevant contexts for widget priority.
- `supplementalActivityFamily` for watchOS.

---

## 2. Notifications

### 2.1 Notification Types and Visual Specs

macOS supports two user-facing notification presentation styles, configured per app by the user in System Settings > Notifications.

#### Banner (Transient)
- Slides in from the top-right corner of the display.
- **Auto-dismisses after approximately 5 seconds** (the exact duration is controlled by the `com.apple.notificationcenterui bannerTime` default; users can modify it via Terminal).
- Action buttons are hidden by default; they appear on hover.
- Does not require user interaction.
- Queued in Notification Center after dismissal.
- Suitable for informational updates that do not require immediate action.

#### Alert (Persistent)
- Appears in the same top-right position as banners.
- **Remains on screen until the user explicitly dismisses it** by clicking X, performing an action, or clicking on it.
- Action buttons are always visible without hover.
- Suitable for time-sensitive or action-required notifications (calendar invites, communication app messages, critical alerts).

#### Visual distinction summary:

| Property | Banner | Alert |
|---|---|---|
| Position | Top-right corner | Top-right corner |
| Auto-dismiss | ~5 seconds | No |
| Action buttons | Hover to reveal | Always visible |
| User interaction required | No | Yes |
| Notification Center archival | Yes | Yes |

#### Additional presentation types:
- **Badge:** A numeric badge on the app's Dock icon. Does not produce a banner or alert. Configured via `UNNotificationContent.badge` (an `NSNumber`).
- **Sound:** Played alongside banner/alert. Configured via `UNNotificationContent.sound`.
- **Critical alerts:** Bypass Do Not Disturb and mute settings. Require the `com.apple.developer.critical-alerts` entitlement (Apple approval needed). Set via `UNNotificationSound.critical...` variants.

### 2.2 Notification Content (`UNNotificationContent`)

| Property | Type | Description |
|---|---|---|
| `title` | `String` | Primary bold text line. Required for meaningful display. |
| `subtitle` | `String` | Secondary text below title. Optional. |
| `body` | `String` | Main message text. Displayed in full only on expansion. |
| `badge` | `NSNumber?` | Dock icon badge count. `0` clears the badge. |
| `sound` | `UNNotificationSound?` | Sound played on delivery. `.default`, `.defaultCritical`, or custom. |
| `userInfo` | `[AnyHashable: Any]` | Custom payload dictionary. Not shown to user. |
| `attachments` | `[UNNotificationAttachment]` | Images, audio, video. Displayed as thumbnail in notification. |
| `categoryIdentifier` | `String` | Links to a registered `UNNotificationCategory`. |
| `threadIdentifier` | `String` | Groups related notifications together in Notification Center. |
| `summaryArgument` | `String` | Text used in grouped summary line (e.g., "5 more from Alice"). |
| `summaryArgumentCount` | `Int` | Item count represented by this notification in a group. |
| `launchImageName` | `String` | Launch image name (iOS only; no effect on macOS). |

### 2.3 Notification Actions (`UNNotificationAction`)

Actions appear as buttons in the notification. Registered per category via `UNNotificationCategory`.

**Action types:**
- **Standard action** — Launches app in foreground (`UNNotificationActionOptions.foreground`).
- **Destructive action** — Displayed with visual emphasis (red text on iOS; similar treatment on macOS) to signal a destructive operation. Use `UNNotificationActionOptions.destructive`.
- **Authentication-required action** — Requires device authentication before the app receives the callback. Use `UNNotificationActionOptions.authenticationRequired`.
- **Text input action** (`UNTextInputNotificationAction`) — Presents a text field allowing the user to type a reply inline without opening the app (e.g., Mail quick reply).

**Registration pattern:**
```swift
let replyAction = UNTextInputNotificationAction(
    identifier: "REPLY_ACTION",
    title: "Reply",
    options: [],
    textInputButtonTitle: "Send",
    textInputPlaceholder: "Type a message...")

let deleteAction = UNNotificationAction(
    identifier: "DELETE_ACTION",
    title: "Delete",
    options: [.destructive])

let category = UNNotificationCategory(
    identifier: "MESSAGE_CATEGORY",
    actions: [replyAction, deleteAction],
    intentIdentifiers: [],
    options: [.customDismissAction])

UNUserNotificationCenter.current().setNotificationCategories([category])
```

### 2.4 Notification Categories (`UNNotificationCategory`)

Categories define the set of actions available for a notification type and configure category-level behavior.

**Category options (`UNNotificationCategoryOptions`):**
| Option | Effect |
|---|---|
| `.customDismissAction` | App receives a callback when the user dismisses without acting |
| `.allowInCarPlay` | Category may be shown in CarPlay |
| `.hiddenPreviewsShowTitle` | Shows title even when notification previews are hidden |
| `.hiddenPreviewsShowSubtitle` | Shows subtitle when previews are hidden |
| `.allowAnnouncement` | Enables Siri/VoiceOver spoken announcements |

### 2.5 Authorization and Delivery

**Requesting permission:**
```swift
UNUserNotificationCenter.current().requestAuthorization(
    options: [.alert, .sound, .badge]) { granted, error in
    // Handle result
}
```

**Authorization options:**
- `.alert` — Show banner or alert.
- `.sound` — Play sound.
- `.badge` — Update Dock badge.
- `.provisional` — Deliver quietly to Notification Center without prompting user; user can later opt in or out.
- `.criticalAlert` — Bypass DND (requires entitlement).
- `.announcement` — Allow Siri to announce in AirPods.

**Provisional notifications:**
- Granted without a user-visible permission dialog.
- Notifications are delivered silently to Notification Center only (no banner, no sound, no badge).
- User sees an option in Notification Center to "Keep" or "Turn Off" the notifications.

---

## 3. Notification Center

### 3.1 Notification Center Behavior (macOS)

Notification Center is accessed by clicking the clock/date in the top-right of the menu bar (or swiping right with two fingers from the right edge of the trackpad).

**Delivery and archival:**
- Banners and alerts are archived in Notification Center after delivery or dismissal.
- Notifications persist until the user explicitly clears them or the app removes them programmatically.
- The system respects active Focus modes: notifications may be suppressed or delivered to Notification Center only based on the user's Focus configuration.
- Do Not Disturb (a Focus mode) prevents banner/alert display; notifications accumulate silently in Notification Center.

### 3.2 Notification Grouping

**Automatic app grouping:** The system groups all notifications from an app under a single expandable row in Notification Center by default.

**Thread-level grouping:** Assign `threadIdentifier` on `UNMutableNotificationContent` to sub-group notifications within an app. Notifications sharing a `threadIdentifier` are collapsed together with a count badge.

```swift
let content = UNMutableNotificationContent()
content.title = "New message from Alice"
content.threadIdentifier = "conversation-alice-id"   // stable, unique per logical thread
content.summaryArgument = "Alice"                    // displayed as "5 more from Alice"
content.summaryArgumentCount = 1
```

**User control:**
- Users can configure per-app notification grouping in System Settings > Notifications > [App] > Notification Grouping.
- Options: Automatic (system decides), By App (all from app), Off (no grouping).

### 3.3 Removing Delivered Notifications Programmatically

```swift
// Remove specific notifications by identifier
UNUserNotificationCenter.current().removeDeliveredNotifications(
    withIdentifiers: ["notification-id-1", "notification-id-2"])

// Remove all delivered notifications from this app
UNUserNotificationCenter.current().removeAllDeliveredNotifications()
```

---

## 4. Share Extensions

### 4.1 Overview

Share extensions appear when a user clicks a Share button in a toolbar or chooses Share from a context menu. On macOS, the share sheet is an `NSSharingServicePicker`. The extension runs as a separate process hosted by the system, not the app.

**Extension point:** `com.apple.share-services`

**Principal class options:**
- `SLComposeServiceViewController` — Provides the standard compose UI (title, content preview, optional configuration items). Use this for social-style sharing.
- Custom `NSViewController` — Full custom UI for non-compose sharing scenarios.

### 4.2 Info.plist Configuration

```xml
<key>NSExtension</key>
<dict>
    <key>NSExtensionPointIdentifier</key>
    <string>com.apple.share-services</string>
    <key>NSExtensionPrincipalClass</key>
    <string>$(PRODUCT_MODULE_NAME).ShareViewController</string>
    <key>NSExtensionAttributes</key>
    <dict>
        <key>NSExtensionActivationRule</key>
        <dict>
            <key>NSExtensionActivationSupportsImageWithMaxCount</key>
            <integer>1</integer>
            <key>NSExtensionActivationSupportsWebURLWithMaxCount</key>
            <integer>1</integer>
            <key>NSExtensionActivationSupportsText</key>
            <true/>
        </dict>
    </dict>
</dict>
```

### 4.3 Activation Rule Keys (`NSExtensionActivationRule`)

| Key | Value Type | Description |
|---|---|---|
| `NSExtensionActivationSupportsImageWithMaxCount` | Integer | Maximum number of images the extension handles |
| `NSExtensionActivationSupportsMovieWithMaxCount` | Integer | Maximum number of video files |
| `NSExtensionActivationSupportsFileWithMaxCount` | Integer | Maximum number of generic files |
| `NSExtensionActivationSupportsWebURLWithMaxCount` | Integer | Maximum number of web URLs |
| `NSExtensionActivationSupportsWebPageWithMaxCount` | Integer | Maximum number of web pages |
| `NSExtensionActivationSupportsText` | Boolean | Extension handles plain text |
| `NSExtensionActivationSupportsAttachmentsWithMaxCount` | Integer | Maximum total attachments |
| `NSExtensionActivationSupportsAttachmentsWithMinCount` | Integer | Minimum required attachments |
| `NSExtensionActivationDictionaryVersion` | Integer | Activation dict version (1 or 2); v2 for stricter matching |
| `NSExtensionActivationUsesStrictMatching` | Boolean | Enables strict type matching |

**Advanced predicate (for App Store distribution — `TRUEPREDICATE` is rejected):**
```xml
<key>NSExtensionActivationRule</key>
<string>SUBQUERY(extensionItems, $item,
    SUBQUERY($item.attachments, $attachment,
        ANY $attachment.registeredTypeIdentifiers UTI-CONFORMS-TO "public.image"
    ).@count == $item.attachments.@count
).@count == 1</string>
```

### 4.4 UI Constraints

- **Width:** Fixed by the system; the extension cannot increase its width.
- **Height:** Can grow using Auto Layout or by setting `preferredContentSize`. Keep height restrained — avoid making users scroll.
- **Navigation:** Use `pushConfigurationViewController(_:)` / `popConfigurationViewController()` for configuration sub-screens. Do not present additional modal view controllers.
- **Sandbox:** Extensions run in a strict sandbox. Network access requires declaring the appropriate entitlement. Shared data between the extension and the host app requires an App Group.
- **Completion:** Call `extensionContext?.completeRequest(returningItems:)` or `extensionContext?.cancelRequest(withError:)` to finish.

---

## 5. Spotlight Integration (CoreSpotlight)

### 5.1 Overview

CoreSpotlight enables app content to appear in macOS Spotlight search results. Indexed items are private (on-device only). Available: macOS 10.13+.

**Framework:** `CoreSpotlight`  
**Key classes:** `CSSearchableItem`, `CSSearchableItemAttributeSet`, `CSSearchableIndex`

### 5.2 Indexing Workflow

```swift
import CoreSpotlight
import UniformTypeIdentifiers

func indexContent(title: String, description: String, id: String, thumbnail: NSImage?) {
    // 1. Create attribute set
    let attributeSet = CSSearchableItemAttributeSet(contentType: UTType.text)
    attributeSet.title = title
    attributeSet.contentDescription = description
    attributeSet.keywords = ["keyword1", "keyword2"]

    // Optional thumbnail
    if let thumbnail = thumbnail,
       let tiffData = thumbnail.tiffRepresentation,
       let bitmap = NSBitmapImageRep(data: tiffData) {
        attributeSet.thumbnailData = bitmap.representation(using: .png, properties: [:])
    }

    // 2. Create searchable item
    let item = CSSearchableItem(
        uniqueIdentifier: id,
        domainIdentifier: "com.yourapp.content-domain",
        attributeSet: attributeSet)

    // Optional: set expiration
    item.expirationDate = Date().addingTimeInterval(60 * 60 * 24 * 30)  // 30 days

    // 3. Index
    CSSearchableIndex.default().indexSearchableItems([item]) { error in
        if let error = error { print("Indexing error: \(error)") }
    }
}
```

### 5.3 `CSSearchableItemAttributeSet` Key Properties

| Category | Properties |
|---|---|
| **Identity** | `title`, `contentDescription`, `keywords`, `domainIdentifier` |
| **Visual** | `thumbnailData` (PNG Data), `thumbnailURL` |
| **Content type** | `contentType` (UTType), `contentURL` |
| **Documents** | `pageCount`, `creator`, `fonts` |
| **Location** | `latitude`, `longitude`, `altitude`; set `supportsNavigation = 1` to show directions button |
| **Communication** | `supportsPhoneCall = 1`, `phoneNumbers`, `emailAddresses` |
| **Media** | `duration`, `composer`, `tempo`, `sampleRate` |
| **Time** | `startDate`, `endDate`, `dueDate`, `completionDate` |

**Thumbnail guidance:**
- Supply PNG data via `thumbnailData`.
- No strict pixel dimension is enforced by the API, but Apple recommends keeping thumbnails appropriate for the search result preview — approximately 90×90 points at @2x (180×180 px) is a common practical size.
- Oversized thumbnails waste memory; undersized thumbnails appear blurry.

### 5.4 Handling Search Result Selection

When a user selects your app's Spotlight result, the system delivers an `NSUserActivity` to your app delegate:

```swift
// macOS: In AppDelegate or SceneDelegate
func application(_ application: NSApplication,
                 continue userActivity: NSUserActivity,
                 restorationHandler: @escaping ([NSUserActivityRestoring]) -> Void) -> Bool {
    guard userActivity.activityType == CSSearchableItemActionType,
          let id = userActivity.userInfo?[CSSearchableItemActivityIdentifier] as? String else {
        return false
    }
    // Navigate to the content identified by `id`
    return true
}
```

Declare `NSUserActivityTypes` in your app's `Info.plist` including `CSSearchableItemActionType` (`com.apple.corespotlightitem`).

### 5.5 Deletion and Updates

```swift
// Delete specific items
CSSearchableIndex.default().deleteSearchableItems(
    withIdentifiers: ["item-id-1"]) { error in ... }

// Delete entire domain
CSSearchableIndex.default().deleteSearchableItems(
    withDomainIdentifiers: ["com.yourapp.content-domain"]) { error in ... }

// Update: re-index with same uniqueIdentifier; system replaces existing entry
```

### 5.6 Spotlight Extension (CSIndexExtensionRequestHandler)

For apps with large content libraries that need background indexing without the main app running, implement a CoreSpotlight index extension using `CSIndexExtensionRequestHandler`. This extension type runs on demand by the system.

---

## 6. Services Menu

### 6.1 Overview

The Services menu (in every app's application menu under [AppName] > Services) exposes functionality from other installed apps. A macOS app can both **provide** services (appear in other apps' Services menus) and **consume** services.

Services are macOS-only. They operate via pasteboard (clipboard) data exchange.

### 6.2 Providing a Service — Info.plist Registration

Add an `NSServices` array to your app's `Info.plist`. Each dictionary in the array defines one service entry:

```xml
<key>NSServices</key>
<array>
    <dict>
        <!-- Menu item text (localizable via ServicesMenu.strings) -->
        <key>NSMenuItem</key>
        <dict>
            <key>default</key>
            <string>Encrypt Selection</string>
        </dict>

        <!-- Optional keyboard shortcut (⌘ + this character) -->
        <key>NSKeyEquivalent</key>
        <dict>
            <key>default</key>
            <string>E</string>
        </dict>

        <!-- Selector invoked when user selects the service -->
        <key>NSMessage</key>
        <string>encryptSelection</string>

        <!-- Port name matching NSRegisterServicesProvider / NSApp.setServicesProvider -->
        <key>NSPortName</key>
        <string>MyApp</string>

        <!-- Data types this service can READ from the pasteboard -->
        <key>NSSendTypes</key>
        <array>
            <string>NSStringPboardType</string>
        </array>

        <!-- Data types this service WRITES back to the pasteboard (omit if read-only) -->
        <key>NSReturnTypes</key>
        <array>
            <string>NSStringPboardType</string>
        </array>

        <!-- Optional: file type UTIs this service accepts -->
        <!-- <key>NSSendFileTypes</key> -->

        <!-- Context conditions for menu visibility -->
        <key>NSRequiredContext</key>
        <dict/>

        <!-- Prevent sandboxed apps from invoking this service -->
        <key>NSRestricted</key>
        <false/>

        <!-- Human-readable description -->
        <key>NSServiceDescription</key>
        <string>Encrypts the selected text using ROT-13.</string>

        <!-- Optional: timeout in milliseconds -->
        <key>NSTimeout</key>
        <string>3000</string>
    </dict>
</array>
```

### 6.3 Key Reference

| Key | Type | Required | Description |
|---|---|---|---|
| `NSMenuItem` | Dictionary (key: `default`) | Yes | Menu item text; localizable |
| `NSMessage` | String | Yes | Selector name (without `:userData:error:` suffix in plist) |
| `NSPortName` | String | Yes | Must match registration identifier |
| `NSSendTypes` | Array of String | Conditional | Pasteboard types to read; required if service reads data |
| `NSReturnTypes` | Array of String | Conditional | Pasteboard types to write; omit for read-only services |
| `NSSendFileTypes` | Array of UTI String | Optional | File UTIs; replaces `NSSendTypes` for file-based services |
| `NSKeyEquivalent` | Dictionary (key: `default`) | No | Single-character keyboard shortcut |
| `NSRequiredContext` | Dictionary or Array | No | Conditions for visibility in the menu |
| `NSRestricted` | Boolean | No | Prevents sandboxed apps from calling (default `false`) |
| `NSServiceDescription` | String | No | Human-readable description |
| `NSTimeout` | String (numeric ms) | No | How long the system waits for a response |
| `NSUserData` | String | No | Arbitrary developer data passed to the handler |

### 6.4 Service Handler Implementation

```swift
// Register the service provider
NSApp.setServicesProvider(self)

// Handler method — must match NSMessage value + pattern
@objc func encryptSelection(_ pboard: NSPasteboard,
                             userData: String?,
                             error: AutoreleasingUnsafeMutablePointer<NSString?>?) {
    guard let input = pboard.string(forType: .string) else {
        error?.pointee = "No string data on pasteboard" as NSString
        return
    }
    let encrypted = rot13(input)
    pboard.clearContents()
    pboard.setString(encrypted, forType: .string)
}
```

**Selector signature:** `methodName:userData:error:` — the method name in the plist (`NSMessage`) matches the first component.

### 6.5 Service Discovery and Installation

- **In an app:** Services are active when the app is installed in an Applications folder. The system scans at login.
- **Standalone:** Create a `.service` bundle and place it in `~/Library/Services`, `/Library/Services`, or `/Network/Library/Services`.
- **Force rescan:** Call `NSUpdateDynamicServices()` or use the `pbs` command-line tool after installation.
- **Debugging:** Set `NSDebugServices` default to log why services appear or not.
- **macOS 10.6+:** Service menu items no longer support slash (`/`) as submenu delimiter. App name is auto-appended for disambiguation.

---

## 7. Menu Bar Extras (Status Items)

### 7.1 Overview

A menu bar extra (status item) is an icon in the right portion of the macOS menu bar that provides persistent access to app functionality even when the app is not frontmost. Implemented via `NSStatusItem` / `NSStatusBar`.

Available: macOS 10.0+. The modern SwiftUI equivalent is `MenuBarExtra` (macOS 13+).

### 7.2 Creating an NSStatusItem

```swift
// Classic AppKit
let statusBar = NSStatusBar.system
let statusItem = statusBar.statusItem(withLength: NSStatusItem.squareLength)

// Set a template image (preferred)
if let button = statusItem.button {
    button.image = NSImage(named: "MenuBarIcon")
    button.image?.isTemplate = true  // Enables automatic light/dark adaptation
    button.toolTip = "My App"
}

// Attach a menu
let menu = NSMenu()
menu.addItem(NSMenuItem(title: "Open", action: #selector(openApp), keyEquivalent: ""))
menu.addItem(.separator())
menu.addItem(NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
statusItem.menu = menu
```

**SwiftUI MenuBarExtra (macOS 13+):**
```swift
@main
struct MyApp: App {
    var body: some Scene {
        MenuBarExtra("My App", image: "MenuBarIcon") {
            ContentView()
        }
        .menuBarExtraStyle(.window)  // or .menu
    }
}
```

### 7.3 Sizing and Icon Guidelines

| Property | Value | Notes |
|---|---|---|
| Status bar height (thickness) | ~22 points (macOS default) | Retrieved via `NSStatusBar.system.thickness` |
| Recommended icon size | `NSStatusBar.system.thickness` × `NSStatusBar.system.thickness` | Square; typically 18×18 pt drawn in a 22×22 pt frame |
| `NSStatusItem.squareLength` | Equal to `NSStatusBar.system.thickness` | Use for icon-only items |
| `NSVariableStatusItemLength` | Dynamic; fits content | Use when displaying text or variable content |

**Image design rules:**
- Use **template images** (`isTemplate = true`): monochrome black + transparent PNG. The system colorizes automatically for light/dark mode, active/inactive state, and High Contrast.
- Do NOT use full-color images as the icon — they will not adapt to appearance changes correctly.
- Keep the icon at 18×18 points (36×36 px @2x) centered in the 22-point tall frame.
- Provide a 2x asset in the asset catalog (`@2x` suffix).
- Include an accessibility label: `button.setAccessibilityLabel("My App status")`

### 7.4 Interaction Behavior

| Gesture | Behavior |
|---|---|
| Left click | Opens attached menu (if `statusItem.menu` is set) or invokes button action |
| Right click | Opens attached menu (same as left if menu is set) |
| Click with no menu | Invokes the button's `action` selector |
| Click + drag | Not a standard pattern; avoid |

**Popover pattern (non-menu):**
```swift
statusItem.button?.action = #selector(togglePopover)
statusItem.button?.target = self

@objc func togglePopover() {
    if popover.isShown {
        popover.performClose(nil)
    } else {
        if let button = statusItem.button {
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
        }
    }
}
```

### 7.5 Design Guidelines (HIG)

- Menu bar extras appear in the trailing (right) portion of the menu bar. The system controls ordering; the user can reorder using Cmd+drag.
- An app does not need a main window to have a menu bar extra (agent apps with `LSUIElement = YES` in Info.plist).
- Avoid menu bar extras for functionality that belongs in the app's main window. Reserve this pattern for persistent status monitoring, quick actions, or background services.
- Do not display a menu bar extra unless the app has a meaningful reason for persistent presence.
- Prefer short menus (fewer than ~10 items). Long menus degrade discoverability.
- Show the current state of the app in the icon or title (e.g., recording indicator, network status symbol).
- Avoid animating the menu bar icon continuously — it is distracting.

---

## 8. Quick Actions (Finder Integration)

### 8.1 Overview

Quick Actions are custom actions that appear in the Finder context menu under "Quick Actions," in the Finder Preview pane, and (on supported hardware) on the Touch Bar. They are implemented as:

1. **Automator Quick Action workflows** (`.workflow` bundles)
2. **Shortcuts marked "Use as Quick Action"** targeting Finder
3. **Quick Look Preview Extensions** (for custom preview rendering in Finder's preview pane)

Managed by the user in: System Settings > Privacy & Security > Extensions > Finder

### 8.2 Automator Quick Actions

- Built in Automator as a "Quick Action" workflow.
- Declare the accepted input type (e.g., Image Files, PDF Files, Any File).
- Common built-in examples: "Convert Image," "Create PDF," "Trim Audio/Video."
- Stored in `~/Library/Services/` or distributed inside an app bundle.
- Appear in Finder context menu under Quick Actions when files of the declared type are selected.

### 8.3 Shortcuts Quick Actions

- Create a Shortcut and enable "Use as Quick Action" targeting "Finder."
- The shortcut receives selected files as input via the `Shortcut Input` variable.
- Appears in Quick Actions menu alongside Automator workflows.

### 8.4 Quick Look Preview Extension (`QLPreviewingController`)

A Quick Look extension enables Finder (and other host apps) to display rich previews of custom file types in the preview pane and the Quick Look panel (Space bar).

**Protocol:** `QLPreviewingController`

**Key guidelines:**
- The main preview view is provided by a `NSViewController` subclass that conforms to `QLPreviewingController`.
- **Do not** present additional view controllers over the preview controller; the host controls the presentation.
- For view-controller-based previews: implement `preparePreviewOfFile(at:completionHandler:)`.
- For data-based previews: implement `providePreview(for:completionHandler:)`.
- Thumbnail generation: implement `prepareThumbnailOfFile(at:withSize:completionHandler:)` in a separate `QLThumbnailProvider` subclass.
- Available: macOS 10.15+ (replaces the deprecated Quick Look Plug-In format from macOS 10.13).

**Extension point:** `com.apple.quicklook.preview`

**Info.plist file type registration:**
```xml
<key>QLSupportedContentTypes</key>
<array>
    <string>com.yourcompany.myformat</string>  <!-- custom UTType -->
</array>
```

**Design constraints:**
- Keep preview rendering fast — the host may time out slow extensions.
- The preview view size is determined by the host; use Auto Layout.
- Support dark mode; use system materials and colors.
- Do not include interactive elements that could confuse users expecting a read-only preview — unless the extension explicitly supports editing.

---

## 9. Do's and Don'ts

### Widgets

| Do | Don't |
|---|---|
| Use `context.displaySize` for layout | Hardcode pixel dimensions |
| Supply content for all declared family sizes | Declare a family and show a broken layout |
| Use `widgetURL` or `Link` for taps | Try to intercept individual taps without AppIntent |
| Back interactive controls with fast `AppIntent` | Use AppIntent for long-running tasks |
| Refresh via `WidgetCenter.reloadTimelines` after push | Poll on a tight schedule and exhaust the budget |
| Test with WidgetKit Simulator | Assume Xcode canvas shows production-accurate sizes |

### Notifications

| Do | Don't |
|---|---|
| Request only the permission options you use | Request all options speculatively |
| Use `threadIdentifier` to group related notifications | Send dozens of ungrouped notifications |
| Use `.provisional` for onboarding | Bombard users with alerts immediately on install |
| Register categories with actions | Use generic notifications that require app launch for every action |
| Use destructive action option for delete/remove operations | Mark non-destructive actions as destructive |

### Menu Bar Extras

| Do | Don't |
|---|---|
| Use template images (monochrome) | Use full-color icons that don't adapt to appearance |
| Keep the icon at 18×18 pt (drawn), 22×22 pt (frame) | Use oversized or undersized icons |
| Provide an accessibility label on the button | Leave the icon unlabeled for assistive technology |
| Limit menu to essential actions | Replicate the entire app menu in the status item |
| Show meaningful state in the icon | Animate the icon continuously without user-triggered activity |

### Services

| Do | Don't |
|---|---|
| Use stable pasteboard type names or UTIs | Use private, undocumented pasteboard types |
| Implement the handler method with the correct signature | Use a selector that doesn't match `NSMessage` |
| Call `NSUpdateDynamicServices()` after installation | Expect the menu to update without a rescan |
| Localize the `NSMenuItem` text via `ServicesMenu.strings` | Hardcode English-only menu text |

### Spotlight (CoreSpotlight)

| Do | Don't |
|---|---|
| Provide `title`, `contentDescription`, and `keywords` | Index items with only a title and no description |
| Use a stable `uniqueIdentifier` that survives app updates | Use random UUIDs that cause duplicate entries |
| Set `expirationDate` for time-sensitive content | Let stale content persist indefinitely in the index |
| Handle `CSSearchableItemActionType` activity type in your app delegate | Ignore the activity type and fail to deep-link |
| Provide thumbnail data for visual content | Skip thumbnails for content types where they matter |

---

## 10. Sources

| Topic | Source | URL |
|---|---|---|
| Widget families and macOS support | Apple Developer Documentation — WidgetFamily | `developer.apple.com/documentation/widgetkit/widgetfamily` |
| Widget systemExtraLarge macOS 14 | Apple Developer Documentation — WidgetFamily.systemExtraLarge | `developer.apple.com/documentation/widgetkit/widgetfamily/systemextralarge` |
| Widget interactivity (Button/Toggle) | Apple Developer Documentation — Adding interactivity to widgets | `developer.apple.com/documentation/widgetkit/adding-interactivity-to-widgets-and-live-activities` |
| Widget timeline behavior | Apple Developer Documentation — TimelineProvider | `developer.apple.com/documentation/widgetkit/timelineprovider` |
| Widget dimensions at runtime | Stack Overflow — How to retrieve widget sizes | `stackoverflow.com/questions/64077115` |
| Notification content properties | Apple Developer Documentation — UNNotificationContent | `developer.apple.com/documentation/usernotifications/unnotificationcontent` |
| Notification banner vs alert timing | Stack Overflow — Local notification dismissed in few seconds | `stackoverflow.com/questions/64553966` |
| Notification banner timing user control | AppleInsider — How to make Mac notifications show longer | `appleinsider.com/articles/21/06/15/how-to-make-mac-notifications-show-longer-or-leave-faster` |
| Notification grouping | Hacking with Swift — threadIdentifier and summaryArgument | `hackingwithswift.com/example-code/system/how-to-group-user-notifications-using-threadidentifier-and-summaryargument` |
| Share extension activation rules | Apple Developer Documentation — App Extension Keys | `developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/AppExtensionKeys.html` |
| Share extension activation rule keys | Apple Developer Documentation — NSExtensionActivationRule | `developer.apple.com/documentation/bundleresources/information-property-list/nsextension/nsextensionattributes/nsextensionactivationrule` |
| Share extension design | Apple Developer Documentation — Share extension programming guide | `developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/Share.html` |
| CoreSpotlight indexing | Darjeeling Steve — Indexing App Content | `darjeelingsteve.com/articles/Indexing-App-Content-with-Core-Spotlight.html` |
| CoreSpotlight handler | Hacking with Swift — Core Spotlight indexing | `hackingwithswift.com/example-code/system/how-to-use-core-spotlight-to-index-content-in-your-app` |
| CoreSpotlight thumbnail | Apple Developer Documentation — thumbnailData | `developer.apple.com/documentation/corespotlight/cssearchableitemattributeset/thumbnaildata` |
| Services menu Info.plist keys | Apple Developer Documentation — Cocoa Keys / NSServices | `developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CocoaKeys.html` |
| Services menu registration pattern | Apple Developer Documentation — Providing a Service | `developer.apple.com/library/archive/documentation/Cocoa/Conceptual/SysServices/Articles/providing.html` |
| NSStatusItem / NSStatusBar API | Apple Developer Documentation — NSStatusBar | `developer.apple.com/documentation/appkit/nsstatusbar` |
| Menu bar extra implementation | 8th Light — Tutorial: Add a Menu Bar Extra | `8thlight.com/insights/tutorial-add-a-menu-bar-extra-to-a-macos-app` |
| Quick Actions in Finder | PCRisk — Beginner's guide to Quick Actions | `pcrisk.com/blog/mac/13965-a-beginners-guide-to-creating-and-using-quick-actions-on-a-mac` |
| Quick Look extension design | Apple Developer Documentation — QLPreviewingController | `developer.apple.com/documentation/quicklook/qlpreviewingcontroller` |
| macOS Sonoma widget desktop sizes | Ars Technica — macOS 14 Sonoma review | `arstechnica.com/gadgets/2023/09/macos-14-sonoma-the-ars-technica-review/` |
| Widget development overview | AppleInsider — Getting started with WidgetKit | `appleinsider.com/inside/xcode/tips/getting-started-with-widgetkit-making-your-first-macos-widget` |
| WWDC 2024 WidgetKit updates | Apple Developer Documentation — WidgetKit updates | `developer.apple.com/documentation/updates/widgetkit` |
| HIG Widgets page | Apple Human Interface Guidelines — Widgets | `developer.apple.com/design/human-interface-guidelines/widgets` |
| HIG Notifications page | Apple Human Interface Guidelines — Notifications | `developer.apple.com/design/human-interface-guidelines/notifications` |
| HIG Managing Notifications | Apple Human Interface Guidelines — Managing notifications | `developer.apple.com/design/human-interface-guidelines/managing-notifications` |
| HIG Activity Views (share sheets) | Apple Human Interface Guidelines — Activity views | `developer.apple.com/design/human-interface-guidelines/activity-views` |
| HIG Searching / Spotlight | Apple Human Interface Guidelines — Searching | `developer.apple.com/design/human-interface-guidelines/searching` |
| HIG Menu Bar | Apple Human Interface Guidelines — The menu bar | `developer.apple.com/design/human-interface-guidelines/the-menu-bar` |
