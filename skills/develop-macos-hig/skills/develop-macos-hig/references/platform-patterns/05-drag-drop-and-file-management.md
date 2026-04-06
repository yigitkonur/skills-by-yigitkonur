# macOS Drag and Drop & File Management — Definitive Reference

> Scope: macOS only. Target: UI engineers and designers building or auditing AppKit drag-and-drop implementations.
> Sources: Apple Developer Documentation (AppKit), Apple HIG (2008 PDF), WWDC 2016/2023 session notes, macOS system defaults analysis (Eclectic Light Company / Mojave), practitioner articles (Buckleyisms, Cocoanetics), MacRumors/Apple Discussions community records.

---

## 1. Drag Initiation

### Threshold and Timing

macOS does **not** publish a single canonical pixel threshold for drag initiation in its current HIG. The system handles initiation through the AppKit event pipeline — the threshold is an internal hysteresis guard built into `NSWindow`'s event handling, not a configurable value. In practice:

- Drag initiation fires after the mouse moves a few pixels during a mouse-down, but the exact distance is system-controlled and not developer-overridable.
- The developer triggers a drag by calling `beginDraggingSessionWithItems:event:source:` from within `mouseDragged:` (or equivalent gesture recognizer) — the `event` parameter must be the originating `mouseDown` event, not the drag event.
- **No time-based threshold** is required; the session starts as soon as the call is made with a valid mouseDown event.

```swift
// In NSView subclass:
override func mouseDragged(with event: NSEvent) {
    let item = NSDraggingItem(pasteboardWriter: myItem)
    item.setDraggingFrame(draggingRect, contents: draggingImage)
    beginDraggingSession(with: [item], event: originalMouseDownEvent, source: self)
}
```

**Key rule:** Save the original `mouseDown` event and pass it to `beginDraggingSession`. If you pass the `mouseDragged` event, the system rejects it.

### Visual Feedback During Initiation

- The drag image lifts from the source and begins tracking the cursor immediately.
- The source view may optionally dim or mark the dragged item as "being moved" (the system does not do this automatically).
- No spinner or delay animation is shown at initiation.

---

## 2. Drag Image

### Appearance

| Property | Specification |
|---|---|
| Translucency | macOS renders drag images semi-transparent. The exact alpha is not published in HIG, but system behavior targets approximately 50–70% opacity — enough to see content beneath the dragged image. |
| Size | The drag image should match the visual size of the source item. The system does not scale it automatically. |
| Shadow | AppKit adds a subtle drop shadow to the drag image automatically when using the standard compositing path. |
| Retina | Use `contentsScale` on `NSDraggingImageComponent` to supply @2x content on HiDPI displays. |

### Multi-Item Drag Stacking (Flocking)

When multiple items are dragged simultaneously, AppKit uses `NSDraggingFormation` to arrange them:

| Formation Constant | Description |
|---|---|
| `NSDraggingFormationDefault` | System decides (typically a stack/pile for 2+ items) |
| `NSDraggingFormationNone` | Items move independently, no visual grouping |
| `NSDraggingFormationPile` | Items stacked as a pile (fan-out effect) |
| `NSDraggingFormationStack` | Items arranged in a tight stack |

The formation can be changed dynamically in `draggingEntered:` or `draggingUpdated:` by setting `sender.draggingFormation`. This allows drop targets to re-form items into a list layout when dragging over, for example, a list view.

The count badge on the drag image (showing how many items are dragged) is shown automatically for multi-item drags. Set `numberOfValidItemsForDrop` on `NSDraggingInfo` in `draggingUpdated:` to update it when only some items are accepted.

### Custom Drag Image Composition

Use `NSDraggingItem.setImageComponentsProvider:` to provide an array of `NSDraggingImageComponent` objects. Each component has:
- `contents`: an `NSImage`, `NSView`, or `NSColor`
- `bounds`: position and size relative to the drag image
- `contentsScale`: for HiDPI

This replaces the deprecated `draggedImage` property (deprecated macOS 10.13+).

### Animation

- **`animatesToDestination`** (on `NSDraggingSession`): When `true` (default), the drag image animates back to its origin on cancel, or forward to the drop point on success. Set to `false` only when your view renders its own drop animation.
- On a failed drop (no valid target, drop outside any window), the image slides back to the source with a rubber-band animation.

---

## 3. Drop Targets

### Zone Highlighting

Drop zone highlighting is the responsibility of the destination view. AppKit does not apply automatic highlighting — the developer implements it in the `NSDraggingDestination` protocol:

```swift
func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {
    isHighlighted = true       // your property
    needsDisplay = true        // triggers redraw
    return validateDrop(sender)
}

func draggingExited(_ sender: NSDraggingInfo?) {
    isHighlighted = false
    needsDisplay = true
}
```

**Recommended visual treatment:**
- Draw a rounded-rect border (system accent color, ~2pt line width) around the drop zone.
- Optionally fill the zone with a very low-opacity tint of the accent color.
- For icon-type drop targets (e.g., a folder icon), use a highlight ring, not a full fill.
- macOS system components (Finder, Mail) use an accent-colored border inset by about 2–4 pt from the view edge.

### Insertion Indicators

For list-type views (NSTableView, NSCollectionView, NSOutlineView), when a dragged item would be inserted **between** existing items, draw an insertion indicator — a thin horizontal line with round caps at the insertion point.

The 2008 Apple HIG specifies: "An insertion indicator should appear in a list where a dragged item would be inserted if the user releases the mouse button."

`NSTableView` handles this automatically when you implement `validateDrop:proposedRow:proposedDropOperation:` and return `NSTableViewDropAbove`:

```swift
func tableView(_ tableView: NSTableView,
               validateDrop info: NSDraggingInfo,
               proposedRow row: Int,
               proposedDropOperation: NSTableView.DropOperation) -> NSDragOperation {
    tableView.setDropRow(row, dropOperation: .above)  // draws insertion line
    return .move
}
```

For custom views, draw the insertion indicator manually as a 2pt horizontal line in the accent color.

### Acceptance Validation

The full validation lifecycle:

| Phase | Method | Return |
|---|---|---|
| Item enters | `draggingEntered:` | `NSDragOperation` (or `.none` to reject) |
| Item moves within | `draggingUpdated:` | `NSDragOperation` (re-validate each move) |
| Item exits | `draggingExited:` | `void` — remove highlight |
| Pre-drop | `prepareForDragOperation:` | `Bool` — `false` aborts |
| Perform drop | `performDragOperation:` | `Bool` — `false` signals failure |
| Cleanup | `concludeDragOperation:` | `void` — finalize UI |

Register the view to receive drags:
```swift
registerForDraggedTypes([.fileURL, .string, NSFilePromiseReceiver.readableDraggedTypes].flatMap { $0 })
```

---

## 4. Cursor Badges

The cursor badge is a small overlay icon on the arrow cursor that communicates the operation the drop will perform. It is driven entirely by the `NSDragOperation` returned from the destination (and negotiated with the source).

| Badge | Operation Constant | Visual | Modifier Key |
|---|---|---|---|
| No badge (move) | `NSDragOperationMove` | Plain arrow cursor | No modifier |
| Green plus (+) | `NSDragOperationCopy` | Arrow + green circle with + | Option key held |
| Link badge | `NSDragOperationLink` | Arrow + curved arrow | Option+Command held |
| Forbidden (–) | `NSDragOperationNone` | Arrow + red circle with – | N/A — target rejects |
| Generic | `NSDragOperationGeneric` | Arrow + rectangle | App-defined |

**Critical rule confirmed by Cocoanetics (practitioner, widely cited):**
> "NSDragOperationCopy adds a green plus, NSDragOperationMove shows nothing [no badge], NSDragOperationLink shows a link badge, NSDragOperationNone shows the forbidden badge."

The source specifies which operations are permitted via `draggingSession(_:sourceOperationMaskForDraggingContext:)`. The destination then selects from that set. The cursor badge reflects the **intersection** — what the destination will do.

**Modifier key override:** Users can hold Option to request Copy or Option+Command to request Link, as long as the source permits those operations. The source can disable modifier override by returning `true` from `ignoreModifierKeysForDraggingSession:`.

---

## 5. Spring-Loaded Folders

### Behavior

Spring-loaded folders allow a user dragging an item to navigate into nested folders by hovering over them during a drag without dropping. The folder "springs" open after the hover delay.

1. User drags item over a closed folder.
2. After the delay, the folder opens (bounces open with a brief animation).
3. User can continue into subfolders (each level applies the same delay).
4. User drops the item in the desired location.
5. If the user moves away without dropping, the folder closes.

**Spacebar shortcut:** Pressing Space while hovering over a folder during a drag instantly springs it open, bypassing the delay. This is the single most important usability tip for power users and is documented in MacRumors forum references and macOS documentation.

### Timing

| Parameter | Value |
|---|---|
| Default delay | **0.5 seconds** |
| Adjustable range | 0 to ~2 seconds (user-configurable slider in System Settings > Accessibility > Pointer Control) |
| Defaults key | `com.apple.springing.delay` (NSGlobalDomain) |
| Instant trigger | Space bar during hover |

Confirmed by:
- Eclectic Light Company's global defaults analysis (Mojave): "standard 0.5"
- dotfiles references: `defaults write NSGlobalDomain com.apple.springing.delay -float 0.5`
- MacRumors forum: "0.5–1 sec is ok for me"
- Stack Exchange answer: `defaults write -g com.apple.springing.delay -float <seconds> && killall -HUP Finder`

### API

```swift
// Enable spring loading on a custom drop target view:
// (NSView inherits spring loading support via NSDraggingDestination)
// Return NSSpringLoadingHighlightStandard or NSSpringLoadingHighlightEmphasized
// from springLoadingHighlightChanged:

func springLoadingHighlightChanged(_ sender: NSDraggingInfo) {
    switch sender.springLoadingHighlight {
    case .standard:
        drawStandardHighlight()
    case .emphasized:
        drawEmphasizedHighlight()   // folder is about to spring
    case .none:
        removeHighlight()
    @unknown default: break
    }
}
```

The `NSSpringLoadingDestination` protocol provides: `springLoadingActivated(_:draggingInfo:)`, `springLoadingHighlightChanged(_:)`, `springLoadingEntered(_:)`, `springLoadingUpdated(_:)`, `springLoadingExited(_:)`.

---

## 6. Pasteboard (Clipboard)

### Standard Types

All pasteboard type constants live under `NSPasteboard.PasteboardType`. Modern macOS uses Swift extensions on `NSPasteboard.PasteboardType`; the underlying strings are Uniform Type Identifiers.

| Constant | Type String | Use Case |
|---|---|---|
| `.string` | `public.utf8-plain-text` | Plain text |
| `.rtf` | `com.apple.flat-rtf` | Rich text |
| `.rtfd` | `com.apple.rtfd` | Rich text with attachments |
| `.html` | `public.html` | Web content |
| `.tabularText` | `public.utf8-tab-separated-values` | Spreadsheet rows |
| `.URL` | `public.url` | Generic URL |
| `.fileURL` | `public.file-url` | File reference (local file) |
| `.pdf` | `com.adobe.pdf` | PDF data |
| `.png` | `public.png` | PNG image |
| `.tiff` | `public.tiff` | TIFF image |
| `.color` | `com.apple.cocoa.pasteboard.color` | NSColor data |
| `.sound` | `com.apple.cocoa.pasteboard.sound` | NSSound data |

### Custom Types

Define a custom type using a reverse-DNS identifier:

```swift
extension NSPasteboard.PasteboardType {
    static let myCustomItem = NSPasteboard.PasteboardType("com.example.myapp.customitem")
}

// Adopt NSPasteboardWriting and NSPasteboardReading on your model objects
class MyItem: NSObject, NSPasteboardWriting, NSPasteboardReading {
    func writableTypes(for pasteboard: NSPasteboard) -> [NSPasteboard.PasteboardType] {
        return [.myCustomItem, .string]   // offer multiple representations
    }
    func pasteboardPropertyList(forType type: NSPasteboard.PasteboardType) -> Any? {
        switch type {
        case .myCustomItem: return try? JSONEncoder().encode(self)
        case .string: return title
        default: return nil
        }
    }
    static func readableTypes(for pasteboard: NSPasteboard) -> [NSPasteboard.PasteboardType] {
        return [.myCustomItem]
    }
    static func readingOptions(forType type: NSPasteboard.PasteboardType,
                               pasteboard: NSPasteboard) -> NSPasteboard.ReadingOptions {
        return .asData
    }
    required init?(pasteboardPropertyList propertyList: Any,
                   ofType type: NSPasteboard.PasteboardType) {
        // decode
    }
}
```

### Multiple Representations

A single dragged item should offer multiple pasteboard types ordered from richest to most generic. The destination picks the best type it can handle. Example ordering:
1. Custom private type (most fidelity for same-app drops)
2. `NSPasteboardTypeRTFD` or custom rich format
3. `NSPasteboardTypeString` (fallback, universally accepted)
4. `NSPasteboardTypeFileURL` (if the item corresponds to a file)

### Clipboard vs Drag Pasteboard

- Clipboard: `NSPasteboard.general`
- Drag: `NSDraggingInfo.draggingPasteboard` — a separate pasteboard instance, not `.general`
- Both have the same API. The drag pasteboard is released after the drop completes.

---

## 7. File Promises

### What They Are

A **file promise** (`NSFilePromiseProvider`) is a pasteboard representation that commits to producing a file at drop time, rather than serializing the file content during drag initiation. Use when:

- The file doesn't exist yet (e.g., exporting from a canvas app on drop)
- File generation is expensive and shouldn't block the drag
- The file format depends on the drop destination (e.g., different image format for different apps)

Key principle from Apple docs: "Avoid loading or performing any actions on the file until the promise completes."

### Provider (Drag Source)

```swift
// 1. Create a provider with a UTI conforming to public.data or public.directory
let provider = NSFilePromiseProvider(fileType: UTType.png.identifier, delegate: self)

// 2. Add it to the dragging item
let item = NSDraggingItem(pasteboardWriter: provider)
item.setDraggingFrame(frame, contents: thumbnail)

// 3. Implement delegate
func filePromiseProvider(_ filePromiseProvider: NSFilePromiseProvider,
                          fileNameForType fileType: String) -> String {
    return "MyExport.png"   // base filename, not full path
}

func filePromiseProvider(_ filePromiseProvider: NSFilePromiseProvider,
                          writePromiseTo url: URL,
                          completionHandler: @escaping (Error?) -> Void) {
    // Write the file to `url` (the system provides the final path + filename)
    do {
        try imageData.write(to: url)
        completionHandler(nil)
    } catch {
        completionHandler(error)
    }
}
```

### Receiver (Drop Destination)

```swift
// Register to receive promises
registerForDraggedTypes(NSFilePromiseReceiver.readableDraggedTypes)

func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
    sender.enumerateDraggingItems(for: self, classes: [NSFilePromiseReceiver.self],
                                   options: [:]) { item, _, _ in
        if let receiver = item.item as? NSFilePromiseReceiver {
            receiver.receivePromisedFiles(atDestination: destinationURL,
                                          options: [:],
                                          operationQueue: .main) { fileURL, error in
                // file is now at fileURL
            }
        }
    }
    return true
}
```

### When to Combine with File URL

For items that already exist as files, prefer `NSPasteboardTypeFileURL` directly. Use `NSFilePromiseProvider` when the file needs to be generated. Many apps offer both — the file URL for same-machine drops (faster) and a promise for cross-machine or cross-app drops.

---

## 8. Undo and Error Recovery

### Undo for Drag Move

macOS does not provide automatic undo for drag operations. The application must register undo actions manually.

**Pattern for a move operation:**

```swift
func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
    guard let item = extractItem(from: sender) else { return false }

    // Capture state for undo
    let originalIndex = item.originalIndex
    let originalContainer = item.originalContainer

    // Perform the move
    model.move(item, to: destinationContainer, at: destinationIndex)

    // Register undo action
    undoManager?.registerUndo(withTarget: self) { target in
        target.model.move(item, back: originalContainer, at: originalIndex)
    }
    undoManager?.setActionName("Move \(item.name)")

    return true
}
```

**Source-side cleanup for move:**
After a successful move (when `endedAtOperation:` delivers `.move`), the source must delete its copy:

```swift
func draggingSession(_ session: NSDraggingSession,
                     endedAt screenPoint: NSPoint,
                     operation: NSDragOperation) {
    if operation == .move {
        removeSourceItems()   // source is responsible for deletion
        // Also register undo here for the deletion side
    }
}
```

### Drag Cancellation

A drag is cancelled when:
- The user releases the mouse over no valid drop target
- The user presses Escape during a drag
- `performDragOperation:` returns `false`

On cancellation, the drag image slides back to the source (`animatesToDestination` = true by default). No data is modified. No undo entry is needed.

`draggingSession(_:endedAtPoint:operation:)` fires with `operation == .none` on cancellation. Clean up any transient drag state here.

### Error Recovery

If `performDragOperation:` fails (returns `false`):
1. The drag image animates back (if `animatesToDestination` is true).
2. Present an error to the user via `NSAlert` or inline error state.
3. Do not leave partial data on the destination pasteboard.
4. If the source was already modified in anticipation of a successful drop, revert it.

---

## 9. File Management Patterns

### Document Types and UTI Registration

Document types are declared in `Info.plist` under `CFBundleDocumentTypes`. Each entry maps a UTI to a role (Editor, Viewer, Shell) and specifies icon files.

```xml
<key>CFBundleDocumentTypes</key>
<array>
  <dict>
    <key>CFBundleTypeName</key><string>My Document</string>
    <key>LSItemContentTypes</key>
    <array><string>com.example.myapp.mydocument</string></array>
    <key>CFBundleTypeRole</key><string>Editor</string>
    <key>CFBundleTypeIconFile</key><string>MyDocumentIcon</string>
  </dict>
</array>
```

Custom UTIs must declare conformance to `public.data` or `public.composite-content` in `UTExportedTypeDeclarations`.

### Recent Documents

`NSDocumentController` manages the "Open Recent" menu automatically for document-based apps. Key API:

| Method / Property | Description |
|---|---|
| `recentDocumentURLs` | Array of recently opened document URLs |
| `maximumRecentDocumentCount` | Read-only; returns the user's system setting (5, 10, 15, 20, 30, or 50) |
| `noteNewRecentDocumentURL(_:)` | Call this to add a URL to the recent list (called automatically by `NSDocument`) |
| `clearRecentDocuments(_:)` | Action method wired to "Clear Menu" item |
| `openRecentDocument(_:)` | Action method that opens the selected recent document |

The system caps the recent list length at `maximumRecentDocumentCount`. The user controls this in System Settings > General > Recent Items. Value 0 means "don't track."

For **non-document-based apps**, call `NSDocumentController.shared.noteNewRecentDocumentURL(url)` manually after opening a file.

**Sandbox gotcha:** In sandboxed apps, `recentDocumentURLs` requires a security-scoped bookmark to resolve the URL when reopening. Use `NSApp.application(_:open:)` or the system's open panel, which grants the entitlement automatically.

### Quick Look Integration

Quick Look lets users preview files with Space bar in Finder. Apps add Quick Look support via:

1. **Thumbnail extension** (QLThumbnailProvider) — generates thumbnails shown in Finder icon view
2. **Preview extension** (QLPreviewProvider) — renders the full preview panel content

For in-app Quick Look (e.g., a file browser panel):

```swift
// In AppDelegate or responder chain:
override func acceptsPreviewPanelControl(_ panel: QLPreviewPanel!) -> Bool {
    return true  // claim control when your view is key
}

override func beginPreviewPanelControl(_ panel: QLPreviewPanel!) {
    panel.delegate = self
    panel.dataSource = self
}

override func endPreviewPanelControl(_ panel: QLPreviewPanel!) {
    panel.delegate = nil
    panel.dataSource = nil
}

// QLPreviewPanelDataSource
func numberOfPreviewItems(in panel: QLPreviewPanel!) -> Int {
    return selectedURLs.count
}

func previewPanel(_ panel: QLPreviewPanel!, previewItemAt index: Int) -> QLPreviewItem! {
    return selectedURLs[index] as NSURL
}
```

Open Quick Look from a menu item or keyboard shortcut (`Space` is standard, but you must connect it):

```swift
QLPreviewPanel.shared().makeKeyAndOrderFront(nil)
```

### Finder Integration

| Pattern | Implementation |
|---|---|
| Custom file icons | Register custom UTI with icon in Info.plist; Finder uses it automatically |
| Context menu extensions | Finder Sync Extension (FIFinder­Sync­Controller) |
| Share extension | NSExtension with `com.apple.share-services` extension point |
| Drag source to Finder | Use `NSPasteboardTypeFileURL` for existing files; `NSFilePromiseProvider` for generated files |
| Drop from Finder | Register for `.fileURL`; read URL from `NSDraggingInfo.draggingPasteboard` |
| Tags / Spotlight metadata | Set `NSURLTagNamesKey` or write Spotlight metadata via `MDItem` API |

---

## 10. Do's and Don'ts

### Do

- **Register for `NSFilePromiseReceiver.readableDraggedTypes` alongside `.fileURL`** — Finder and many apps use file promises, not bare file URLs, for drags from app to app.
- **Call `draggingUpdated:` efficiently** — it fires every mouse-move event. Keep it fast; defer heavy validation to `prepareForDragOperation:`.
- **Support `NSDragOperationMove` for intra-app reordering** — return `.move` from both source and destination, and delete the source copy in `draggingSession(_:endedAt:operation:)`.
- **Provide undo for all destructive drag operations** — move and delete operations must be undoable. Copy is not destructive and does not require undo.
- **Use `numberOfValidItemsForDrop`** to update the badge count when only some of the dragged items are valid. Set it in `draggingUpdated:`.
- **Draw your drop zone highlight yourself** — AppKit does not apply it automatically. Use system accent color.
- **Handle Escape / drag cancellation** — clean up any provisional state in `draggingSession(_:endedAt:operation:)` when operation is `.none`.
- **Support spring loading** — implement `NSSpringLoadingDestination` on folder-like views so users can navigate during a drag.
- **Use the Space shortcut to advertise spring loading** — mention it in your Help content; it is not discoverable.
- **Test with large multi-item drags** — `NSDraggingFormation` can cause performance issues with custom image component providers when there are many items.

### Don't

- **Don't call `beginDraggingSession` with the `mouseDragged` event** — always pass the `mouseDown` event.
- **Don't perform expensive work in `draggingEntered:`** — this fires on first entry; defer reads to `prepareForDragOperation:`.
- **Don't write data to the destination before `performDragOperation:` returns `true`** — if you bail in `prepareForDragOperation:`, you've already dirtied state.
- **Don't skip `concludeDragOperation:`** — use it for final UI cleanup (e.g., removing drop highlight, updating selection to dropped items).
- **Don't use the deprecated `dragImage:at:offset:event:pasteboard:source:slideBack:` method** — replaced by `beginDraggingSessionWithItems:event:source:` since macOS 10.7.
- **Don't write files synchronously in `NSFilePromiseProvider`'s delegate** — write on a background queue and call the completion handler when done.
- **Don't use `kUTType...` constants from MobileCoreServices** — deprecated. Use `UTType` from the `UniformTypeIdentifiers` framework (macOS 11+) or `NSPasteboard.PasteboardType` string literals.
- **Don't leave stale data on the drag pasteboard** — the drag pasteboard is automatically cleared after the session, but do not hold long-lived references to it.
- **Don't forget to deregister drag types** — call `unregisterDraggedTypes()` when the view no longer needs to accept drags (e.g., when an edit mode ends).
- **Don't show a drop highlight for rejected types** — `draggingEntered:` should return `.none` and not set `isHighlighted` when the payload is not acceptable.

---

## Sources

| Source | Type | Weight |
|---|---|---|
| Apple Developer Documentation — NSDraggingDestination, NSDraggingSource, NSDraggingItem, NSDraggingSession, NSDraggingFormation, NSDraggingInfo, NSFilePromiseProvider, NSFilePromiseProviderDelegate, NSFilePromiseReceiver, NSPasteboard.PasteboardType, NSDocumentController | Official API docs | 0.9 |
| Apple HIG 2008 PDF (acko.net archive) | Official design guidelines | 0.9 |
| WWDC 2016 "What's New in Cocoa" (session 203 PDF) — NSFilePromiseProvider introduction | Official session | 0.8 |
| WWDC 2023 "What's New in AppKit" (session 10054) — NSTextInsertionIndicator | Official session | 0.8 |
| Apple Developer Documentation — Supporting Drag and Drop Through File Promises | Official sample article | 0.9 |
| Apple Developer Documentation — Supporting Table View Drag and Drop Through File Promises | Official sample article | 0.9 |
| Apple Developer Documentation — NSDocumentController, maximumRecentDocumentCount | Official API docs | 0.9 |
| Eclectic Light Company — "Global defaults in macOS Mojave" (Howard Oakley, 2019) | Practitioner / reverse-engineered defaults | 0.7 |
| Stack Exchange (apple.stackexchange.com) — spring-loaded folder delay terminal command | Community verified | 0.6 |
| MacRumors Forums — spring-loaded delay 0.5–1 sec range | Community | 0.5 |
| Cocoanetics (via Rssing archive) — cursor badge NSDragOperation mapping | Practitioner | 0.6 |
| Buckleyisms — "How to Actually Implement File Dragging From Your App on Mac" (2018) | Practitioner | 0.6 |
| Apple Discussions — spring-loaded 1 second default behavior | Community | 0.5 |
| macOS system defaults dotfiles (pmmmwh, marlosirapuan Gist, marslo.github.io) — `com.apple.springing.delay` default 0.5 | Community verified | 0.5 |
