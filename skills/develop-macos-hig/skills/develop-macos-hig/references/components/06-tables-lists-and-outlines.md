# macOS Data Display Components: Tables, Lists, Outlines, Collections, and Browsers

Definitive reference for UI experts building macOS productivity apps. Every spec is sourced; where Apple's public documentation is inaccessible (JS-rendered), the value is cross-checked from Apple API snippet text, practitioner implementations, and community confirmation.

---

## 1. Tables (NSTableView / SwiftUI Table)

### 1.1 Row Heights

NSTableView exposes row sizing through two overlapping systems: `rowSizeStyle` (macOS 10.7+) for system-managed presets, and `rowHeight` (legacy + custom mode fallback).

**`rowSizeStyle` presets (NSTableView.RowSizeStyle)**

| Style | Row height | Notes |
|---|---|---|
| `.small` | ~17 pt | Dense data; rare in modern apps |
| `.medium` | ~22 pt | Standard for most macOS utility apps |
| `.large` | ~30 pt | Comfortable for touch-proximate or accessibility contexts |
| `.custom` | set via `rowHeight` | You own the height; default `rowHeight` = 16.0 pt |
| `.default` | resolves to `.medium` | Applied when the app does not explicitly set a style |

Source: Apple Developer Documentation snippets — "The table will use a row height specified for a medium table" for `.default`; `rowHeight` property: "The default row height is 16.0. The value in this property is used only if the table's rowSizeStyle is set to NSTableView.RowSizeStyle.custom."

**Dynamic / automatic row heights**

Available macOS 10.13+. Enable via Interface Builder (Size Inspector checkbox "Uses Automatic Row Heights") or code:

```swift
tableView.usesAutomaticRowHeights = true
```

When enabled, `tableView(_:heightOfRow:)` delegate return values are ignored. The table derives height from each cell view's Auto Layout constraints.

**Important regressions:**
- macOS 13.0 (Ventura): row-height cache not cleared on `reloadData()`, causing incorrect scroll offsets. Workaround: `noteHeightOfRows(withIndexesChanged:)` or set `UserDefaults.standard.set(false, forKey: "NSTableViewCanEstimateRowHeights")`. Fixed in 13.1.
- macOS 15.3: heights can become non-integral, causing subpixel text rendering. Mitigation: round returned heights to nearest integer.

**Manual dynamic height (delegate)**

```swift
func tableView(_ tableView: NSTableView, heightOfRow row: Int) -> CGFloat {
    // Keep a spare off-screen cell view for measurement
    cellView.bounds.size.width = tableView.bounds.size.width
    cellView.needsLayout = true
    cellView.layoutSubtreeIfNeeded()
    let height = cellView.fittingSize.height
    return max(height, tableView.rowHeight)
}
```

Never call `noteHeightOfRowsWithIndexesChanged:` from within `tableView:heightOfRow:` — that causes a recursive layout loop.

### 1.2 Column Headers

| Spec | Value |
|---|---|
| Default header height (pre-El Capitan / ≤ macOS 10.10) | 17 pt |
| System-drawn header height (macOS 10.11+) | Slightly taller; system-controlled |
| How to customize | Subclass `NSTableHeaderView`, override `frame` property; or set `tableView.headerView.frame.size.height = desiredHeight` in `awakeFromNib` |
| Minimum practical height | 17 pt |

Source: Stack Overflow #32712561 — pre-El Capitan header = 17 pt, El Capitan introduced a larger system-drawn header.

**Column behavior:**
- Columns are defined by `NSTableColumn` objects added to `NSTableView.tableColumns`
- Minimum width: `NSTableColumn.minWidth` (default 10 pt); set per column
- Maximum width: `NSTableColumn.maxWidth` (default CGFloat.greatestFiniteMagnitude)
- User resize: controlled by `NSTableColumn.resizingMask` (.noResizing, .userResizingMask, .autoresizingMask)
- Column reordering: `NSTableView.allowsColumnReordering` (default true)
- Column hide/show: `NSTableColumn.isHidden`

### 1.3 Sorting

NSTableView does not sort data automatically. The developer must respond to sort requests:

1. Assign `sortDescriptorPrototype` to each `NSTableColumn`
2. Implement `tableView(_:sortDescriptorsDidChange:)` on the delegate
3. Re-sort the data source array and call `reloadData()`

The table draws a sort indicator arrow in the header of the sorted column automatically once `sortDescriptors` is set on the table. The arrow cycles: first click → ascending, second click → descending, third click → no sort (removes descriptor).

SwiftUI `Table` uses the same pattern:
```swift
Table(items, sortOrder: $sortOrder) {
    TableColumn("Name", value: \.name)
    TableColumn("Date", value: \.date)
}
.onChange(of: sortOrder) { items.sort(using: $0) }
```

### 1.4 Selection

**`NSTableView.selectionHighlightStyle`:**

| Style | Behavior | Typical use |
|---|---|---|
| `.regular` | Full-row blue/accent highlight | Main content lists |
| `.sourceList` | Sidebar-style gradient highlight (matches system accent) | Source lists / sidebars |
| `.none` | No visual highlight | Custom selection rendering |

Source: Apple Documentation snippet — "NSTableView.SelectionHighlightStyle.sourceList: The source list style of NSTableView. On 10.5, a light blue gradient is used to highlight selected rows."

**Selection modes:**

| Property | Default | Effect |
|---|---|---|
| `allowsEmptySelection` | true | User can deselect all |
| `allowsMultipleSelection` | false | Enable for multi-select |

Keyboard modifiers for selection (standard macOS):
- Click: select single row, deselect others
- Shift+Click: extend selection range
- Command+Click: toggle individual row in/out of selection
- Arrow Up/Down: move selection
- Shift+Arrow: extend selection

### 1.5 Alternating Row Colors

```swift
tableView.usesAlternatingRowBackgroundColors = true
```

The colors come from `NSColor.alternatingContentBackgroundColors` — an array of system colors. Apple documentation explicitly states: "You should not assume the array will contain only two colors." The colors adapt to the current appearance (light/dark mode) automatically.

SwiftUI equivalent:
```swift
Table(items) { ... }
    .tableStyle(.inset(alternatesRowBackgrounds: true))
```

### 1.6 Cell-Based vs. View-Based

| Aspect | Cell-based (legacy) | View-based (current) |
|---|---|---|
| Cell type | NSCell subclasses | NSView / NSTableCellView subclasses |
| Animation support | Limited | Full Core Animation |
| Auto Layout | Not supported in cells | Fully supported |
| Recommended since | macOS 10.7 (deprecated path) | macOS 10.7+ |
| Row height | Fixed via `rowHeight` | Fixed or automatic via constraints |

Prefer view-based. Cell-based is only relevant when maintaining very old codebases.

---

## 2. Outline Views (NSOutlineView)

NSOutlineView subclasses NSTableView and adds hierarchical display with disclosure triangles.

### 2.1 Core Specs

| Spec | Value | Source |
|---|---|---|
| Default row height | 22 pt (inherits NSTableView `.medium`) | NSOutlineView docs |
| `indentationPerLevel` | **20 pt** (default) | Apple Developer Documentation |
| Disclosure triangle visual size | ~10 pt × 10 pt | System metric |
| Disclosure triangle hit area | Full indentation width | System behavior |

The disclosure triangle (disclosure button) is drawn by the system at the leading edge of each expandable row. Its position is offset by the current indentation level. You cannot directly resize the triangle but can suppress it:
```swift
outlineView.indentationMarkerFollowsCell = true  // triangle indents with cell content
outlineView.indentationMarkerFollowsCell = false // triangle stays at column edge
```

### 2.2 Expand / Collapse

```swift
// Programmatic control
outlineView.expandItem(item)
outlineView.expandItem(item, expandChildren: true)  // recursive
outlineView.collapseItem(item)

// Check state
outlineView.isItemExpanded(item)
```

Keyboard behavior:
- Arrow Right: expand selected row (if collapsed)
- Arrow Left: collapse selected row (if expanded), or move to parent
- Space: toggle disclosure state of focused row
- Return: begin inline editing (if editable column)
- Arrow Up/Down: move selection

### 2.3 Data Source

NSOutlineView requires its data source to answer:
- `outlineView(_:numberOfChildrenOfItem:)` — return count for `nil` (root) and each item
- `outlineView(_:child:ofItem:)` — return child at index
- `outlineView(_:isItemExpandable:)` — return whether the item has children
- `outlineView(_:objectValueFor:byItem:)` — cell-based only; view-based uses `viewForTableColumn:row:`

### 2.4 Source List / Sidebar Style

For sidebar navigation panels (Mail sidebar, Finder sidebar):

```swift
outlineView.selectionHighlightStyle = .sourceList
```

This applies the vibrancy-aware gradient selection used in system apps. Pair with a window panel configured as a sidebar (`.sourceList` style) for the correct visual treatment.

Row height for sidebar source lists is typically 22 pt (`.medium`). Some Apple apps use 24–26 pt for more breathing room but 22 pt is the system default.

### 2.5 Sorting in Outline Views

NSOutlineView supports the same `sortDescriptorPrototype` mechanism as NSTableView. Sorting in hierarchical data typically sorts only within each parent node, not across the tree — the developer controls this in the `outlineView(_:sortDescriptorsDidChange:)` callback.

---

## 3. List Views (SwiftUI List)

SwiftUI `List` on macOS renders using NSTableView internally but exposes a declarative API.

### 3.1 Row Specs

| Spec | Value / Notes |
|---|---|
| Default row height | System-managed; approximately 22 pt for text-only rows |
| Minimum row height | `defaultMinListRowHeight` environment key (no built-in floor beyond system minimum) |
| Custom row height | Apply `.padding(.vertical, X)` to row content — smallest vertical padding across columns determines height |
| Alternating rows | `.listStyle(.bordered(alternatesRowBackgrounds: true))` or via Table |

Row height in SwiftUI List is content-driven. There is no direct equivalent of `rowSizeStyle`; instead, use padding modifiers:

```swift
List(items) { item in
    Text(item.name)
        .padding(.vertical, 6)  // adds 6 pt top + 6 pt bottom = ~24 pt effective row
}
```

### 3.2 Selection

```swift
List(items, selection: $selectedItem) { item in
    Text(item.name).tag(item.id)
}
```

- Single selection: `@State var selectedItem: Item.ID?`
- Multiple selection: `@State var selectedItems: Set<Item.ID>`
- `.listStyle(.sidebar)` on macOS applies source-list appearance

### 3.3 Swipe Actions

macOS List supports swipe actions (macOS 12+):

```swift
List {
    ForEach(items) { item in
        Text(item.name)
            .swipeActions(edge: .trailing) {
                Button(role: .destructive) { delete(item) } label: {
                    Label("Delete", systemImage: "trash")
                }
            }
    }
}
```

Note: Swipe actions on macOS are subtle — they appear when a row is right-swiped or on contextual menu equivalent interactions. They are more prominent on iOS; on macOS, consider pairing with a context menu.

### 3.4 NSTableView Swipe Actions (AppKit)

Available macOS 10.11+ via `NSTableViewDelegate`:

```swift
func tableView(_ tableView: NSTableView,
               rowActionsForRow row: Int,
               edge: NSTableView.RowActionEdge) -> [NSTableViewRowAction]
```

The same API is available on NSOutlineView. Actions appear when the user swipes left on a row.

---

## 4. Collection Views (NSCollectionView / SwiftUI LazyVGrid)

### 4.1 NSCollectionView Fundamentals

NSCollectionView on macOS differs meaningfully from UICollectionView on iOS:

| Aspect | macOS NSCollectionView | iOS UICollectionView |
|---|---|---|
| Item type | `NSCollectionViewItem` (NSView subclass) | `UICollectionViewCell` |
| Selection indicator | **Not built-in; must custom-implement** | Built-in selected state |
| Dequeue method | `makeItem(withIdentifier:for:)` | `dequeueReusableCell(withReuseIdentifier:for:)` |
| Layout in IB | Grid layout IB settings are **ignored**; configure in code | IB settings respected |

Source: AppCoda macOS Collection View tutorial — "macOS does not provide a built-in visual selection indicator; you must implement it."

### 4.2 Item Selection

```swift
// Enable selection
collectionView.isSelectable = true
collectionView.allowsEmptySelection = true
collectionView.allowsMultipleSelection = true

// Custom selection visual in NSCollectionViewItem
override var isSelected: Bool {
    didSet {
        view.layer?.backgroundColor = isSelected
            ? NSColor.selectedControlColor.cgColor
            : NSColor.clear.cgColor
    }
}
```

### 4.3 Layout Types

**NSCollectionViewFlowLayout** — sequential, wrap-around flow:

```swift
let layout = NSCollectionViewFlowLayout()
layout.itemSize = NSSize(width: 150, height: 150)      // explicit item size
layout.minimumInteritemSpacing = 10                     // horizontal gap
layout.minimumLineSpacing = 10                          // vertical gap between rows
layout.sectionInset = NSEdgeInsets(top: 10, left: 10,
                                   bottom: 10, right: 10)
```

Item size defaults to `NSZeroSize` — you must either set `itemSize` or implement `collectionView(_:layout:sizeForItemAt:)` in the delegate. If neither is done, items render at zero size (invisible).

For size-per-item control via delegate:
```swift
func collectionView(_ collectionView: NSCollectionView,
                    layout: NSCollectionViewLayout,
                    sizeForItemAt indexPath: IndexPath) -> NSSize {
    return NSSize(width: 150, height: 150)
}
```

**NSCollectionViewGridLayout** — strict grid (macOS-only, no iOS equivalent):

```swift
let layout = NSCollectionViewGridLayout()
layout.minimumItemSize = NSSize(width: 100, height: 100)
layout.maximumItemSize = NSSize(width: 200, height: 200)
layout.maximumNumberOfColumns = 4   // 0 = unlimited
layout.maximumNumberOfRows = 0      // 0 = unlimited
layout.minimumInteritemSpacing = 10
layout.minimumLineSpacing = 10
```

Grid layout constrains items to uniform sizing within the min/max range. The layout selects item size to fill available width while respecting `maximumNumberOfColumns`.

**Important:** NSCollectionViewGridLayout settings configured in Interface Builder are silently ignored. Always configure programmatically.

### 4.4 Section Headers/Footers

```swift
func collectionView(_ collectionView: NSCollectionView,
                    layout: NSCollectionViewLayout,
                    referenceSizeForHeaderInSection section: Int) -> NSSize {
    return NSSize(width: collectionView.bounds.width, height: 30)
}
```

Supplementary views must be registered:
```swift
collectionView.register(HeaderView.self,
    forSupplementaryViewOfKind: NSCollectionView.elementKindSectionHeader,
    withIdentifier: NSUserInterfaceItemIdentifier("header"))
```

### 4.5 SwiftUI LazyVGrid (and performance trade-offs)

```swift
LazyVGrid(columns: [
    GridItem(.adaptive(minimum: 120)),
], spacing: 10) {
    ForEach(items) { item in
        ItemView(item: item)
    }
}
```

**Performance reality (community consensus, 2024–2026):** For grids with 1,000+ items or complex per-item views, SwiftUI `LazyVGrid` has notable performance problems on macOS — memory growth, janky scrolling, and long layout pauses. Multiple practitioners (r/SwiftUI, r/swift) report switching to `NSCollectionView` via `NSViewRepresentable` for production use. For simple, bounded lists (< ~500 items), `LazyVGrid` is acceptable.

---

## 5. Column Browser (NSBrowser)

NSBrowser provides the column-navigation pattern used in macOS Finder's column view, Mail's mailbox list, and file-picking panels.

### 5.1 Core Specs

| Spec | Value / Notes |
|---|---|
| Column width | User-resizable per column |
| Minimum column width | `minColumnWidth` property — documented in points (labeled "pixels" in older docs; treat as points on modern hardware) |
| Column resizing type | `.noColumnResizing`, `.userColumnResizing`, `.automaticColumnResizing` via `columnResizingType` |
| Column content width utility | `columnWidth(forColumnContentWidth:)` — calculates full column width from content width |
| Autosave column widths | `columnsAutosaveName` — if set, column widths persist automatically in user defaults |
| Scroll behavior | Each column has its own scroll view; selecting a row navigates into the next column |
| Last column (leaf) | Displays file/item detail or nothing if the selection is a leaf node |

### 5.2 Column Resizing Types

```swift
browser.columnResizingType = .userColumnResizing  // user can drag column dividers
browser.columnResizingType = .noColumnResizing     // fixed widths
browser.columnResizingType = .automaticColumnResizing  // auto-size to content
```

When `automaticColumnResizing` is set and the user double-clicks a column divider, the column resizes to fit the widest visible item.

### 5.3 Data Source

Two modes:

1. **Passive (delegate-based):** Implement `browser(_:numberOfChildrenOfItem:)` and `browser(_:child:ofItem:)`. Simpler but less flexible.
2. **Active (action-based):** Each column is backed by an NSMatrix of cells. Used in very old code.

Prefer the delegate-based passive mode for new code.

### 5.4 Navigation Pattern

NSBrowser displays a hierarchical path. The current selection path is accessible via `browser.path()`. Set programmatically: `browser.setPath("/Applications/Utilities")`.

Key behavior:
- Clicking an item with children loads the next column
- Clicking a leaf item shows it in the last column (or triggers selection)
- Back/forward navigation: not built-in; implement with a path history array
- Keyboard: Arrow Left/Right to navigate between columns, Arrow Up/Down within a column

---

## 6. Selection Patterns (Cross-Component)

### 6.1 Selection Modes

| Mode | API | Components |
|---|---|---|
| Single select | `allowsMultipleSelection = false` | NSTableView, NSOutlineView, NSCollectionView |
| Multiple select | `allowsMultipleSelection = true` | All above |
| Empty selection allowed | `allowsEmptySelection = true/false` | All above |
| SwiftUI single | `selection: $selectedID` (optional scalar) | List, Table |
| SwiftUI multiple | `selection: $selectedIDs` (Set) | List, Table |

### 6.2 Keyboard Selection

| Key | Behavior |
|---|---|
| Arrow Up/Down | Move selection one row |
| Shift+Arrow | Extend contiguous selection |
| Command+A | Select all rows |
| Command+Click | Toggle row in/out of selection (multi-select mode) |
| Shift+Click | Extend selection to clicked row |
| Space | Toggle disclosure (outline) or scroll (table) |
| Return / Enter | Begin inline editing (if editable) |
| Escape | Cancel editing |
| Tab | Move to next editable cell |
| Shift+Tab | Move to previous editable cell |

### 6.3 Selection Highlight Styles

NSTableView and NSOutlineView offer three visual styles for selected rows:

- `.regular`: Full-width opaque highlight using the system accent color. Standard for main content lists.
- `.sourceList`: Gradient highlight with vibrancy, matching the sidebar aesthetic. Use when the table lives inside a sidebar panel. The selection remains visible in inactive windows (dimmed).
- `.none`: No automatic highlight. You must draw selection feedback in the cell view or row view.

For `.sourceList`, also configure the parent window panel as `.sourceList` style for correct vibrancy layering.

---

## 7. Inline Editing and Drag-to-Reorder

### 7.1 Inline Editing Rules

Inline editing activates when the user double-clicks a cell (or presses Return on a selected row) and the backing `NSTextField` is editable.

To enable editing in a view-based table column:

```swift
// In the NSTableCellView subclass, configure the text field:
textField.isEditable = true
textField.isBordered = false   // shows border only when editing
textField.drawsBackground = false
textField.delegate = self      // to receive editing events
```

Or in Interface Builder: select the NSTextField inside the cell view, set "Editable" to true.

**Editing lifecycle:**

| Event | Delegate method |
|---|---|
| Will begin editing | `control(_:textShouldBeginEditing:)` |
| Did begin editing | `controlTextDidBeginEditing(_:)` |
| Text changed | `controlTextDidChange(_:)` |
| Did end editing | `controlTextDidEndEditing(_:)` |
| Validation | `control(_:isValidObject:)` |

To commit edits on Enter and cancel on Escape, NSTextField handles this automatically. To detect which key ended editing:

```swift
func control(_ control: NSControl,
             textView: NSTextView,
             doCommandBy commandSelector: Selector) -> Bool {
    if commandSelector == #selector(NSResponder.insertNewline(_:)) {
        // Commit
        return true
    }
    if commandSelector == #selector(NSResponder.cancelOperation(_:)) {
        // Cancel — revert to original value
        return true
    }
    return false
}
```

**Column editability toggle:**

```swift
tableColumn.isEditable = true  // applies to cell-based tables
```

For view-based tables, editability is set on the NSTextField inside the cell view, not on the column.

**Dynamic row height during editing:**

If a cell's text field grows while the user types, call:

```swift
NSAnimationContext.beginGrouping()
NSAnimationContext.current.duration = 0
tableView.noteHeightOfRows(withIndexesChanged: IndexSet(integer: row))
NSAnimationContext.endGrouping()
```

This re-queries `tableView(_:heightOfRow:)` for the affected row and animates the resize with zero duration.

### 7.2 Drag-to-Reorder Rows

Three `NSTableViewDataSource` methods are required:

**Step 1 — Write to pasteboard:**

```swift
func tableView(_ tableView: NSTableView,
               pasteboardWriterForRow row: Int) -> NSPasteboardWriting? {
    let item = NSPasteboardItem()
    item.setString("\(row)", forType: NSPasteboard.PasteboardType("private.table-row"))
    return item
}
```

**Step 2 — Validate drop:**

```swift
func tableView(_ tableView: NSTableView,
               validateDrop info: NSDraggingInfo,
               proposedRow row: Int,
               proposedDropOperation operation: NSTableView.DropOperation) -> NSDragOperation {
    // Only allow row reordering (not into a row)
    if operation == .above {
        return .move
    }
    return []
}
```

**Step 3 — Accept drop:**

```swift
func tableView(_ tableView: NSTableView,
               acceptDrop info: NSDraggingInfo,
               row: Int,
               dropOperation: NSTableView.DropOperation) -> Bool {
    var sourceIndexes = [Int]()
    info.enumerateDraggingItems(options: [], for: tableView,
                                classes: [NSPasteboardItem.self],
                                searchOptions: [:]) { item, _, _ in
        if let str = (item.item as? NSPasteboardItem)?
               .string(forType: NSPasteboard.PasteboardType("private.table-row")),
           let index = Int(str) {
            sourceIndexes.append(index)
        }
    }
    // Rearrange data source, then animate
    tableView.beginUpdates()
    for sourceRow in sourceIndexes.sorted(by: >) {
        // move in your model array
        tableView.moveRow(at: sourceRow, to: row)
    }
    tableView.endUpdates()
    return true
}
```

**Critical rule:** Do not call `tableView.reloadData()` synchronously inside `acceptDrop` — it terminates the drag animation mid-flight and produces visual glitches. Use `moveRow(at:to:)` + `beginUpdates/endUpdates` instead.

NSCollectionView drag reorder uses the same pattern adapted to `NSCollectionViewDataSource` — `collectionView(_:pasteboardWriterForItemAt:)`, `collectionView(_:validateDrop:proposedIndexPath:dropOperation:)`, and `collectionView(_:acceptDrop:indexPath:dropOperation:)`.

---

## 8. Decision Tree: Which Component to Use

### Primary question: Is the data flat or hierarchical?

```
Is the data hierarchical (parent/child relationships)?
├── Yes → Does the user need to navigate columns one level at a time?
│         ├── Yes → NSBrowser (column view)
│         └── No  → NSOutlineView (expandable tree)
└── No  → Is the layout grid-based or list-based?
           ├── Grid (equal-size items, variable column count)
           │     → NSCollectionView / LazyVGrid
           └── List (rows, possibly multi-column)
                   → Does the app target macOS only or needs max performance?
                     ├── Yes → NSTableView
                     └── No  → SwiftUI Table or SwiftUI List
```

### Secondary criteria

| Criterion | Best choice |
|---|---|
| Multi-column sortable data | NSTableView or SwiftUI Table |
| Sidebar navigation (Mail, Finder sidebar) | NSOutlineView with `.sourceList` highlight |
| File/folder column navigation | NSBrowser |
| Photo grid, icon grid, media browser | NSCollectionView (AppKit) or LazyVGrid (SwiftUI, < 500 items) |
| Simple single-column list, settings-like | SwiftUI List |
| 10,000+ rows, heavy sorting | NSTableView (AppKit) — SwiftUI Table struggles at scale |
| Hierarchical data with optional columns | NSOutlineView |
| Drag-to-reorder required | NSTableView or NSOutlineView (most mature drag API) |
| Cross-platform (macOS + iOS) | SwiftUI Table / SwiftUI List (compile on both) |

### Framework choice: SwiftUI vs AppKit

| Scenario | Recommendation |
|---|---|
| < ~1,000 rows, no heavy customization | SwiftUI Table or List is acceptable |
| > ~5,000 rows or complex per-row views | NSTableView via AppKit or NSViewRepresentable wrapper |
| Strict macOS-native appearance required | NSTableView / NSOutlineView |
| Cross-platform target (macOS + iPadOS) | SwiftUI Table |
| Heavy customization (custom cell views, drag) | AppKit |

Community consensus (r/SwiftUI, r/swift, 2024–2026): SwiftUI on macOS is "not there yet" for high-complexity tables and grids. Multiple teams report reverting from SwiftUI Table to NSTableView for performance reasons after hitting scale.

---

## 9. Do's and Don'ts

### Tables (NSTableView)

**Do:**
- Use `.medium` rowSizeStyle as default — matches system apps
- Enable `usesAlternatingRowBackgroundColors` for data-dense tables (Finder list view, spreadsheet-like layouts)
- Set `selectionHighlightStyle = .sourceList` when the table lives in a sidebar or source panel
- Use `beginUpdates / endUpdates` (or `performBatchUpdates`) for animated row changes
- Implement `noteHeightOfRowsWithIndexesChanged:` outside the delegate's `heightOfRow:` method
- Validate `rowSizeStyle` actually produces the intended height on each major OS version

**Don't:**
- Call `reloadData()` inside `acceptDrop` — it breaks drag animation
- Call `noteHeightOfRowsWithIndexesChanged:` from inside `tableView:heightOfRow:` — causes recursive loop
- Assume `alternatingContentBackgroundColors` returns exactly two colors
- Use cell-based NSTableView for new code — it's a deprecated path
- Ignore the Ventura 13.0 / macOS 15.3 row-height regression if using automatic row heights

### Outline Views (NSOutlineView)

**Do:**
- Use `indentationPerLevel` (default 20 pt) as-is unless the tree is very deep
- Enable `usesAutomaticRowHeights` for rich tree cells with variable content
- Return `true` from `outlineView(_:isGroupItem:)` for section headers — they render with a distinct style
- Test expand-all / collapse-all with `expandItem(nil, expandChildren: true)`

**Don't:**
- Mix cell-based and view-based rows in the same outline view
- Perform expensive operations in `outlineView(_:numberOfChildrenOfItem:)` — called frequently during layout

### Collection Views (NSCollectionView)

**Do:**
- Always configure `NSCollectionViewFlowLayout.itemSize` or implement the delegate method — items are invisible at NSZeroSize
- Configure `NSCollectionViewGridLayout` entirely in code, not IB
- Implement custom selection highlighting in `NSCollectionViewItem.isSelected` didSet
- Register supplementary views before the collection view loads

**Don't:**
- Use `LazyVGrid` in SwiftUI for large datasets (1,000+ items) on macOS — performance degrades
- Rely on IB layout settings for `NSCollectionViewGridLayout` — silently ignored

### Inline Editing

**Do:**
- Show a visible border on the text field when editing begins (`isBordered = false` at rest, use drawing to indicate focus)
- Commit on Return, cancel on Escape — NSTextField does this automatically
- Use `controlTextDidEndEditing` to persist the edit to the model

**Don't:**
- Trigger editing on single click for destructive or irreversible actions — double-click is the macOS standard
- Leave `isEditable = true` on read-only columns

### NSBrowser

**Do:**
- Set `columnsAutosaveName` to a stable identifier — column widths persist in user defaults automatically
- Use `columnResizingType = .userColumnResizing` unless you have a specific reason to lock widths
- Handle the case where a leaf item is selected and no further column is needed

**Don't:**
- Use NSBrowser for flat lists — it is designed for hierarchical navigation
- Configure columns to be too narrow (< 100 pt effective width) — column headers become unreadable

---

## 10. Sources

| Claim | Source |
|---|---|
| `rowHeight` default = 16.0 pt, used only in `.custom` mode | Apple Developer Documentation snippet: `https://developer.apple.com/documentation/AppKit/NSTableView/rowHeight` |
| `rowSizeStyle.default` resolves to `.medium` | Apple Developer Documentation snippet: "The table will use a row height specified for a medium table" |
| `indentationPerLevel` default = 20 pt | Apple Developer Documentation — NSOutlineView doc extracted via scraper |
| NSTableHeaderView default height ≤ 10.10 = 17 pt | Stack Overflow #32712561 (backward compatibility of header height, El Capitan) |
| `usesAutomaticRowHeights` macOS 10.13+ | Stack Overflow #7504546 (view-based NSTableView dynamic heights, Clifton Labrum answer) |
| Ventura 13.0 row-height regression and workarounds | christiantietze.de/posts/2022/11/nstableview-variable-row-heights-broken-macos-ventura-13-0/ |
| macOS 15.3 non-integral height regression | Same source (2025-02-27 update) |
| `alternatingContentBackgroundColors` — "do not assume only two colors" | Apple Developer Documentation snippet |
| `SelectionHighlightStyle.sourceList` description | Apple Developer Documentation snippet |
| NSCollectionView no built-in selection indicator | AppCoda macOS Programming Tutorial: Working with Collection View |
| NSCollectionViewGridLayout IB settings ignored | AppCoda macOS Programming Tutorial |
| Drag reorder: 3 methods, `moveRow(at:to:)`, no `reloadData` in `acceptDrop` | Stack Overflow #2121907 (drag-drop reorder rows NSTableView) |
| SwiftUI LazyVGrid performance problems > 1,000 items | r/SwiftUI 2024-07-05 (SwiftUI mac performance), r/swift 2026-03-16 (Poor performance of LazyVGrid) |
| SwiftUI Table row height via padding | Stack Overflow #69998770 (SwiftUI Table rowHeight on macOS) |
| SwiftUI alternating rows `.tableStyle(.inset(alternatesRowBackgrounds: true))` | Stack Overflow #69998770 |
| NSBrowser `minColumnWidth`, `columnResizingType` | Apple Developer Documentation — NSBrowser reference |
| NSBrowser `columnsAutosaveName` persists widths in user defaults | Apple Developer Documentation |
| NSOutlineView keyboard navigation (arrows, Space, Return) | Apple Developer Documentation extracted via scraper |
| `allowsMultipleSelection` default = false | Apple Developer Documentation — NSOutlineView doc extracted |
| NSCollectionViewFlowLayout `itemSize` default = NSZeroSize | AppCoda tutorial; Apple Developer Documentation: "if you do not provide an estimated size or implement the delegate method..." |

---

## Appendix: NSCollectionViewCompositionalLayout (macOS 10.15+)

The modern declarative layout system for `NSCollectionView`. Replaces subclassing `NSCollectionViewFlowLayout` for all layouts with irregular structure, orthogonal sections, or adaptive per-section configuration.

**Availability:** Layout macOS 10.15+, Orthogonal scrolling macOS 11.0+, `visibleItemsInvalidationHandler` macOS 12.0+.

### Architecture: Item → Group → Section → Layout

| Element | Role | Size descriptor |
|---|---|---|
| `NSCollectionLayoutItem` | Leaf — maps to one cell | `NSCollectionLayoutSize` |
| `NSCollectionLayoutGroup` | Positions items (horizontal/vertical/custom) | `NSCollectionLayoutSize` |
| `NSCollectionLayoutSection` | Groups + spacing + insets + supplementary | Wraps a group |
| `NSCollectionViewCompositionalLayout` | Full layout | Wraps sections |

### NSCollectionLayoutDimension Factories

| Factory | Meaning |
|---|---|
| `.fractionalWidth(_ f)` | f × container width |
| `.fractionalHeight(_ f)` | f × container height |
| `.absolute(_ pts)` | Fixed points |
| `.estimated(_ pts)` | Initial estimate, refined after layout |

### Standard Patterns

**List:** Full-width rows — `.fractionalWidth(1.0)` item + vertical group.

**Grid:** N columns — `.fractionalWidth(1.0/N)` items + horizontal group.

**Adaptive:** Section provider closure reads `layoutEnvironment.container.effectiveContentSize.width` to choose column count at runtime.

**Orthogonal scrolling (macOS 11.0+):** Horizontally scrolling carousel within vertical layout via `section.orthogonalScrollingBehavior`:

| Case | Behavior |
|---|---|
| `.none` | No orthogonal scrolling (default) |
| `.continuous` | Free scroll |
| `.continuousGroupLeadingBoundary` | Snaps to group leading edge |
| `.groupPaging` | Pages by group width |
| `.groupPagingCentered` | Pages by group, centered |
| `.paging` | Pages by container width |

### Supplementary Items (Headers/Footers)

```swift
let headerSize = NSCollectionLayoutSize(
    widthDimension: .fractionalWidth(1.0), heightDimension: .absolute(44))
let header = NSCollectionLayoutBoundarySupplementaryItem(
    layoutSize: headerSize,
    elementKind: NSCollectionView.elementKindSectionHeader,
    alignment: .top)
section.boundarySupplementaryItems = [header]
```

### Decoration Items (Section Backgrounds)

Register on the **layout** (not collection view):

```swift
layout.register(BackgroundView.self, forDecorationViewOfKind: "bg")
let bg = NSCollectionLayoutDecorationItem.background(elementKind: "bg")
bg.zIndex = -1
section.decorationItems = [bg]
```

### macOS vs iOS Differences

| Aspect | macOS | iOS |
|---|---|---|
| Orthogonal scrolling | macOS 11.0+ | iOS 13.0 |
| Item class | `NSCollectionViewItem` (controller) | `UICollectionViewCell` |
| `UICollectionLayoutListConfiguration` | **Not available** | iOS 14+ |
| `visibleItemsInvalidationHandler` | macOS 12.0+ | iOS 13.0+ |
| Coordinate origin | Lower-left (flipped) | Upper-left |

### Known Bugs

- **FB14638771 (macOS 14.6):** Orthogonal sections use nested NSScrollView; parent `documentVisibleRect` is incorrect.
- **macOS 13.x:** `pinToVisibleBounds = true` + orthogonal scrolling offsets header origin.

### Decision Tree

- Uniform grid, simple → **NSCollectionViewGridLayout**
- Per-item size variation, delegate callbacks → **NSCollectionViewFlowLayout**
- Per-section variance, orthogonal, adaptive, decoration → **NSCollectionViewCompositionalLayout** (modern default)
- SwiftUI, <500 items → **LazyVGrid**

**Sources:** Apple Developer Documentation (NSCollectionViewCompositionalLayout, NSCollectionLayoutSection, NSCollectionLayoutBoundarySupplementaryItem, NSCollectionViewDiffableDataSource), WWDC19 session 215.
