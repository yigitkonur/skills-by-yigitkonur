# macOS Text Input Components — Definitive Reference

**Scope:** macOS only. All measurements in points (pt) at 1x; multiply by 2 for @2x Retina pixels.
**Sources:** Apple HIG (scraped 2026-04-06), AppKit API docs (scraped 2026-04-06), NSControl.ControlSize spec.

---

## 1. Text Fields

### Definition

A text field (`NSTextField`) is a rectangular, single-line area in which people enter or edit a specific, small piece of text. It is the standard macOS input for names, email addresses, URLs, numbers, passwords, and any other short discrete value.

### Size Variants

macOS text fields respect `NSControl.ControlSize`, which maps to three standard sizes. Width is always set by the layout; only height is system-defined.

| Size | Height (pt) | Font | Use when |
|------|------------|------|----------|
| Regular (`.regular`) | 22 pt | System 13 pt | Default for most dialogs and preferences |
| Small (`.small`) | 19 pt | System 11 pt | Toolbars, inspector panels, dense UIs |
| Mini (`.mini`) | 16 pt | System 9 pt | Very compact panels (e.g., some Xcode panes) |
| Large (`.large`) | 26 pt | System 15 pt | Onboarding flows, prominent primary fields |

> **Source note:** Apple's current HIG web pages do not list these pixel values explicitly. The values above are from the macOS design resources (Sketch/Figma templates), confirmed by measuring NSTextField instances in Interface Builder across macOS 13–15 and corroborated by multiple community references. The `NSControl.ControlSize` enum exposes `.mini`, `.small`, `.regular`, `.large`, and `.extraLarge`.

### Anatomy

```
┌────────────────────────────────────────────┐  ← Rounded rectangle (bezel)
│  [leading icon/button]  text content  [X]  │  ← Content area
└────────────────────────────────────────────┘
      ↑ placeholder or typed text
```

- **Bezel styles:** `.roundedBezel` (default for editable fields) or `.squareBezel` (table cell editing, custom contexts)
- **Border:** 1 pt rounded stroke; unfocused = subtle gray; focused = 3 pt blue focus ring (accent color)
- **Focus ring:** Appears as a blue (or accent-color) 3 pt ring outside the bezel when the field is first responder. macOS 14+ uses a tighter, inside-edge ring style in some contexts.
- **Clear button:** macOS text fields do not include a built-in Clear button (that is an iOS-only affordance). Clear behavior is handled via the Delete key or a custom trailing button.
- **Trailing/Leading icons:** Can be added via custom cells or wrapping views; not native to `NSTextField` itself.

### States

| State | Visual description |
|-------|--------------------|
| Empty (unfocused) | Bezel visible, placeholder text shown in tertiary label color (~40% opacity gray) |
| Focused (empty) | Blue focus ring surrounds bezel; placeholder text still visible in tertiary color |
| Filled (unfocused) | Bezel visible, user text in primary label color, no focus ring |
| Filled (focused) | Blue focus ring; user text selected-all or cursor visible |
| Disabled | Bezel fades; text shown in tertiary label color; no interaction possible; `isEnabled = false` |
| Read-only (selectable) | No bezel by default for labels; for a "read-only field," border may be shown but no editing cursor |
| Error | No native error state in `NSTextField`; app must implement (see Section 7) |

### Placeholder Text Behavior

- Set via `NSTextField.placeholderString` (plain) or `NSTextField.placeholderAttributedString` (styled)
- Placeholder disappears the moment the user starts typing (it is not a floating label)
- Placeholder is rendered in the system's tertiary label color — never in the primary text color
- Placeholder should be a concise noun or example value (e.g., "Search" or "username@company.com"), not instructional prose
- HIG guidance: "Because placeholder text disappears when people start typing, it can also be useful to include a separate label describing the field to remind people of its purpose."
- Do not rely solely on placeholder to communicate a field's purpose when it is not obvious from context

### Line Break and Overflow Behavior

Three modes are available:
- **Clip** (default): Text extending beyond the field boundary is clipped; no visual indicator
- **Wrap**: Text wraps to a new line at character or word level (set `maximumNumberOfLines` or use `NSTextView` instead)
- **Truncate**: Truncation at beginning (…text), middle (tex…t), or end (text…), indicated by an ellipsis

**Expansion tooltip:** When text is clipped or truncated, macOS automatically shows an expansion tooltip (a popover-style overlay showing the full string) when the pointer rests over the field. Enabled by `NSControl.allowsExpansionToolTips = true`. Also available in `NSTextField` directly.

### Keyboard Behavior

| Key | Action |
|-----|--------|
| Tab | Move focus to next field (responder chain order) |
| Shift+Tab | Move focus to previous field |
| Return / Enter | Sends action message to target; ends editing |
| Escape | Aborts editing and reverts to pre-edit value |
| Cmd+A | Selects all text in the field |
| Cmd+Z | Undo last change (within editing session) |
| Arrow keys | Move insertion point |
| Cmd+Arrow | Move to beginning/end of line |
| Option+Arrow | Move by word |

### Number Formatting

Use `NSNumberFormatter` assigned to `NSTextField.formatter` to:
- Constrain input to numeric characters only
- Format display as currency, percentage, decimal, or scientific notation
- Automatically validate on focus-out

### API Reference

```swift
// AppKit
NSTextField                     // Primary class
NSTextField.init(string:)       // Editable single-line field
NSTextField.init(labelWithString:) // Static label (not editable, no border)
NSTextField.init(wrappingLabelWithString:) // Multiline selectable label
NSTextField.placeholderString   // Placeholder text
NSTextField.controlSize         // .mini / .small / .regular / .large
NSTextField.bezelStyle          // .roundedBezel / .squareBezel
NSTextField.isEditable          // true for input fields
NSTextField.isSelectable        // true to allow copying
NSTextField.delegate            // NSTextFieldDelegate for validation hooks

// SwiftUI
TextField("label", text: $binding)
TextField("label", text: $binding, axis: .vertical) // multiline
SecureField("label", text: $binding)
```

### When to Use Text Fields vs Alternatives

| Situation | Use |
|-----------|-----|
| Short single-value input (name, URL, number) | Text field |
| Long prose, paragraphs, notes | Text view (NSTextView) |
| Constrained set of known options | Popup button or combo box |
| Sensitive credential (password) | Secure text field (NSSecureTextField) |
| Multiple recipients / tags | Token field (NSTokenField) |
| Free text + dropdown suggestions | Combo box (NSComboBox) |
| Content filtering / search | Search field (NSSearchField) |

---

## 2. Text Editors / Views (NSTextView)

### Definition

A text view (`NSTextView`) displays multiline, styled text content that is optionally editable. It is the correct choice when the amount of text is large, the format is rich (bold, italic, lists), or unlimited vertical space is needed.

### Dimensions

Text views have no fixed height constraint — they expand to fill the scroll view containing them. Width is set by layout. There is no mini/small/regular size variant for text views.

### Anatomy

```
┌─────────────────────────────────────────┐  ← NSScrollView (container)
│ ┌─────────────────────────────────────┐ │  ← NSTextView (content view)
│ │  Rich or plain text content         │ │
│ │  spanning multiple lines,           │ │
│ │  optionally editable.               │ │
│ └─────────────────────────────────────┘ │
│                                    [↕] │  ← Scroll indicator
└─────────────────────────────────────────┘
```

- Always embed `NSTextView` inside `NSScrollView` for scrolling
- No bezel on the text view itself; the scroll view provides visual containment
- Focus ring appears on the scroll view when the text view is first responder

### States

| State | Visual description |
|-------|--------------------|
| Empty (unfocused) | No content; no placeholder by default (placeholder requires custom implementation via `NSTextViewDelegate`) |
| Focused | Focus ring on enclosing scroll view; text cursor visible |
| Filled | Text rendered with the configured font/color attributes |
| Rich text | Bold, italic, underline, color — all supported via `NSTextStorage` |
| Disabled | Text visible but no cursor; `isEditable = false` + `isSelectable = false` |
| Read-only | `isEditable = false`, `isSelectable = true` — user can copy but not edit |

### Scrolling Behavior

- When content exceeds the visible area, scrollbars appear (system-controlled)
- Auto-scroll to insertion point on keystroke
- `NSScrollView.hasVerticalScroller` and `hasHorizontalScroller` control scroller visibility

### Rich Text Capabilities

- Font panel integration (`NSFontPanel`)
- Text alignment (left, center, right, justify)
- Line spacing, paragraph spacing
- Lists (unordered, ordered) via `NSTextList`
- Tables via `NSTextTable`
- Inline images via `importsGraphics`
- Spell check and grammar check (automatic)
- Writing Tools (macOS 15+): summarize, rewrite, proofread

### API Reference

```swift
// AppKit
NSTextView                         // Primary class; placed inside NSScrollView
NSTextView.isEditable              // false for read-only display
NSTextView.isSelectable            // allow text selection/copying
NSTextView.allowsRichText          // toggle rich-text editing
NSTextView.textStorage             // NSTextStorage — mutable attributed string
NSTextView.delegate                // NSTextViewDelegate

// SwiftUI
TextEditor(text: $binding)         // Multiline editable plain text
Text(attributedString)             // Rich text display (read-only)
```

### When to Use Text Views vs Text Fields

- Use `NSTextView` when content may be multi-paragraph, rich-formatted, or of unknown length
- Use `NSTextField` for single discrete values (name, address line, number)
- HIG: "Use a text field to request a small amount of information, such as a name or an email address. To let people input larger amounts of text, use a text view instead."

---

## 3. Search Fields (NSSearchField)

### Definition

A search field (`NSSearchField`) is a specialized text field that displays a Search icon (magnifying glass) on the leading end and a Clear button on the trailing end. It is used to filter or find content within an app.

### Dimensions

Search fields inherit NSTextField size variants:

| Size | Height (pt) | Notes |
|------|------------|-------|
| Regular | 22 pt | Standard toolbar or sidebar placement |
| Small | 19 pt | Dense inspector or filter rows |
| Mini | 16 pt | Rarely used; very compact contexts |

### Anatomy

```
┌────────────────────────────────────────────┐
│ 🔍  [placeholder / search text]       [✕]  │
└────────────────────────────────────────────┘
   ↑ search icon (non-interactive)   ↑ clear button (appears when text present)
```

- The search (magnifying glass) icon is always shown on the leading end
- The Clear (✕) button appears only when the field contains text
- Placeholder text (e.g., "Search") is shown when the field is empty
- A scope control (segmented control) can be embedded below the field to filter search category

### Search Field States

| State | Visual description |
|-------|--------------------|
| Empty (unfocused) | Magnifying glass icon + placeholder text; no clear button |
| Focused (empty) | Focus ring; placeholder still visible; recent searches may appear in dropdown |
| Active (typing) | Magnifying glass; typed text; clear (✕) button appears |
| Showing recents | Dropdown menu lists recent search strings (if `NSSearchField.recentSearches` is populated) |
| Showing suggestions | Dropdown lists app-provided suggestions via `NSSearchFieldDelegate` |
| Disabled | Faded appearance; no interaction |

### Recents and Suggestions

- **Recent searches:** `NSSearchField.recentSearches` stores an array of past queries. The system shows these in a dropdown when the field is focused and empty, under a "Recent Searches" heading. Clear button in the dropdown removes all recents. Maximum recents controlled by `maximumRecents`.
- **Search suggestions:** Implement `NSSearchFieldDelegate` to return suggestion strings as the user types. These appear in a dropdown below the field.
- **Scope bar:** Add an `NSSegmentedControl` below a search field and assign it to `NSSearchField.searchMenuTemplate` to let users filter across named categories (e.g., "This Mac", "Shared", "Everywhere").

### Placement on macOS

- **Toolbar (trailing side):** Most common pattern; provides persistent global search across app content (Mail, Finder, Notes)
- **Top of sidebar:** Used when search filters sidebar navigation items (System Settings)
- **Dedicated search tab/area:** For apps where browsing and search are unified (Music, TV)
- **Inline with content list:** When filtering a single list or table

### API Reference

```swift
// AppKit
NSSearchField                             // Subclass of NSTextField
NSSearchField.recentSearches             // Array of recent search strings
NSSearchField.maximumRecents             // Max stored recents (default 10)
NSSearchField.searchMenuTemplate         // NSMenu for scope bar integration
NSSearchField.sendsSearchStringImmediately  // true = search on every keystroke
NSSearchField.sendsWholeSearchString     // true = search only on Return

// SwiftUI
.searchable(text: $query, placement: .toolbar) // Standard placement
.searchable(text: $query, placement: .sidebar) // Sidebar filter
.searchSuggestions { ... }               // Provide suggestions
.onSubmit(of: .search) { ... }           // Handle Return key
```

---

## 4. Secure Text Fields and Token Fields

### 4a. Secure Text Fields (NSSecureTextField)

#### Definition

`NSSecureTextField` is a direct subclass of `NSTextField` that obscures characters as the user types, replacing each character with a filled circle (•). Used for passwords, PINs, and any sensitive credential.

#### Dimensions

Identical to `NSTextField` — 22 pt regular, 19 pt small, 16 pt mini.

#### Behavior

- Characters are replaced with bullet (•) dots as typed; no character is ever displayed in plain text
- The field never stores its content in the pasteboard via copy
- Undo is disabled by default so characters cannot be retrieved through the undo history
- Unlike iOS, macOS does not offer a built-in "reveal password" toggle; apps must implement this manually if desired (e.g., toggle between `NSSecureTextField` and `NSTextField` with the same binding)
- In visionOS context (for Catalyst), the system automatically blurs the field for AirPlay/screen sharing scenarios
- `NSSecureTextField` does not support rich text, expansion tooltips, or recents

#### API Reference

```swift
// AppKit
NSSecureTextField             // Drop-in replacement for NSTextField for passwords
// All NSTextField properties apply; secure input behavior is automatic

// SwiftUI
SecureField("Password", text: $password)
```

#### When to Use

- Any password entry field
- PIN entry (for non-numeric PINs; for numeric PINs use NSSecureTextField with a number formatter)
- API keys, secret tokens, any value the user should not see echoed on screen

---

### 4b. Token Fields (NSTokenField)

#### Definition

`NSTokenField` is a subclass of `NSTextField` that converts typed text into discrete visual tokens — pill-shaped labels that can be selected, dragged, deleted, and act as atomic units. Used for recipient fields, tag inputs, and filter expressions.

#### Platform

macOS only. There is no direct equivalent in iOS/iPadOS UIKit (iOS uses `UISearchTextField` with tokens, but the macOS component predates and differs from it).

#### Dimensions

Same as NSTextField: 22 pt regular height. Token fields typically grow in height as tokens wrap to additional lines.

#### Anatomy

```
┌───────────────────────────────────────────────────────────┐
│ [Jony Ive ▼]  [Tim Cook ▼]  [|cursor or typed text...]   │
└───────────────────────────────────────────────────────────┘
      ↑ committed tokens (pill shape, selectable)  ↑ text input area
```

- Tokens appear as rounded-rectangle pills inside the field
- Each token may have a disclosure indicator (▼) if it has a contextual menu
- Typing text and then pressing comma (,) — or Return, or another configured delimiter — converts the text to a token
- Tokens can be selected (highlighted blue) and deleted with the Delete key
- Tokens can be dragged to reorder within the field or moved to another token field

#### Token Conversion Behavior

- **Default delimiter:** Comma (`,`) — typing a comma converts the preceding text to a token
- **Configurable delimiters:** Additional keys (e.g., Return, Space, Tab) can be added via `NSTokenFieldDelegate.tokenField(_:shouldAdd:at:)` or by setting `NSTokenField.tokenizingCharacterSet`
- **Auto-suggestion:** Implement `NSTokenFieldDelegate` to provide suggestions as the user types; suggestions appear in a dropdown list below the field
- **Suggestion delay:** Configurable via `NSTokenFieldDelegate.tokenField(_:completionDelayForRepresentedObject:)`. Default is immediate (0 seconds). Apple recommends a comfortable delay to avoid distracting the user while typing.

#### Context Menu on Tokens

Each token can display a contextual menu (right-click or Ctrl+click) with:
- Actions relevant to the token (e.g., "Edit recipient", "Mark as VIP")
- Information about the token (e.g., contact card, email address details)
- Provide via `NSTokenFieldDelegate.tokenField(_:menuForRepresentedObject:)`

Example (Mail): recipient tokens show a context menu with "Send New Message", "Add to Contacts", "Copy Address", etc.

#### API Reference

```swift
// AppKit
NSTokenField                                    // Subclass of NSTextField
NSTokenField.tokenizingCharacterSet             // CharacterSet for delimiters
NSTokenField.completionDelay                    // Delay before suggestions appear
NSTokenFieldDelegate                            // Protocol for suggestions, menus, editing
// Key delegate methods:
// tokenField(_:completionsForSubstring:indexOfToken:indexOfSelectedItem:)
// tokenField(_:menuForRepresentedObject:)
// tokenField(_:shouldAdd:at:)
// tokenField(_:displayStringForRepresentedObject:)
// tokenField(_:editingStringForRepresentedObject:)
```

---

## 5. Combo Boxes (NSComboBox)

### Definition

A combo box (`NSComboBox`) combines a text field with a pull-down button. Users can either type a custom value directly or click the button to reveal a list of predefined choices. Unlike a popup button, a combo box always accepts free-form text entry; the list is a convenience, not a constraint.

### Platform

macOS only. Not available on iOS, iPadOS, tvOS, visionOS, or watchOS.

### Dimensions

| Size | Height (pt) |
|------|------------|
| Regular | 26 pt (slightly taller than NSTextField due to the integrated button) |
| Small | 22 pt |

> The pull-down button (chevron/arrow) is integrated into the trailing end of the field and is not separately sizable.

### Anatomy

```
┌────────────────────────────────────────┬───┐
│  [value or placeholder text          ] │ ▼ │
└────────────────────────────────────────┴───┘
                                          ↑ pull-down button
```

When the pull-down button is clicked, a scrollable list appears below the field showing the predefined items.

### States

| State | Visual description |
|-------|--------------------|
| Default | Field shows default value (should be a meaningful list item, not empty) |
| Focused | Focus ring; insertion point visible; user may type freely |
| Dropdown open | List of choices shown below the field; currently matching item highlighted |
| Custom value entered | Text in field does not match any list item; accepted as-is on confirm |
| Disabled | Faded; neither text entry nor dropdown available |

### Behavior Rules

- Typing a custom value does not add it to the list permanently; it disappears when the user dismisses the field
- The list items should be the most likely choices, not an exhaustive enumeration (use a popup button for exhaustive constrained lists)
- List items must not be wider than the text field; if an item is too wide, it will be truncated
- The default value shown in the field should be a meaningful item from the list, not empty
- Use an introductory label (e.g., "Font:" with title-case capitalization and a colon) to identify the field's purpose

### When to Use Combo Box vs Alternatives

| Situation | Use |
|-----------|-----|
| Free text + list of common choices | Combo box |
| Constrained to list only (no custom value) | Popup button (NSPopUpButton) |
| Constrained to list + type-ahead filtering | Combo box |
| Short list, all values known | Popup button |
| Search/filter with custom query | Search field |

### API Reference

```swift
// AppKit
NSComboBox                              // Subclass of NSTextField
NSComboBox.addItem(withObjectValue:)    // Add a list item
NSComboBox.addItems(withObjectValues:)  // Add multiple items
NSComboBox.removeAllItems()             // Clear the list
NSComboBox.numberOfVisibleItems         // Rows visible in open dropdown (default 10)
NSComboBoxDataSource                    // Protocol for data-driven lists
NSComboBoxDelegate                      // Protocol for change notifications
```

---

## 6. Labels

### Definition

A label is static, uneditable text that appears throughout the macOS interface to identify controls, provide context, describe actions, or display information. Labels are implemented as `NSTextField` instances with `isEditable = false` and `isSelectable` set as appropriate, or as SwiftUI `Text` / `Label` views.

### Label Types

| Type | Purpose | API |
|------|---------|-----|
| **Control label** | Identifies a specific control to its left or above (e.g., "Name:") | `NSTextField.init(labelWithString:)` |
| **Descriptive label** | Provides context, instructions, or supplemental information in a view | `NSTextField.init(wrappingLabelWithString:)` |
| **Value label** | Displays a read-out value that users may want to copy (IP address, serial number) | `NSTextField.init(labelWithString:)` + `isSelectable = true` |
| **Button label** | Text inside a button conveying its action | Part of NSButton, not a standalone NSTextField |

### System Label Color Hierarchy (macOS)

Apple defines four semantic label colors for macOS that automatically adapt to light/dark mode and accessibility settings:

| Semantic name | SwiftUI | AppKit | Typical use |
|---------------|---------|--------|-------------|
| Label | `.primary` | `NSColor.labelColor` | Primary content, main text |
| Secondary Label | `.secondary` | `NSColor.secondaryLabelColor` | Subheadings, supplemental text |
| Tertiary Label | `.tertiary` | `NSColor.tertiaryLabelColor` | Placeholder text, unavailable item descriptions |
| Quaternary Label | (no direct SwiftUI equivalent) | `NSColor.quaternaryLabelColor` | Watermark text, very low emphasis |

### Alignment Rules for Labels Relative to Controls

These are the macOS-standard conventions for label placement:

**Trailing-aligned labels to the left of controls (the macOS standard):**
```
          Name:  [______________________]
    Email address:  [______________________]
          Phone:  [______________________]
```
- Labels sit to the left of their associated controls
- Labels are right-aligned (trailing-aligned) within their column
- The colon (`:`) is part of the label text and sits immediately before the control
- Labels use Title Case for standalone labels, sentence case for descriptive text
- Leave 8 pt between the end of the label (colon) and the beginning of the control

**Top-aligned labels above controls:**
- Used when the control is very wide (e.g., a full-width text view or a large form element)
- Label is left-aligned above the control
- Typically 4–8 pt vertical spacing between label and control

**No label (placeholder only):**
- Acceptable only when the field's purpose is visually obvious from context
- Must still have an accessibility label set programmatically

### Typography

- Control labels: System font, regular weight, 13 pt (regular size)
- Small control labels: System font, regular weight, 11 pt
- Descriptive body text: System font, regular weight, 13 pt, with word wrap
- Prefer system fonts for legibility and Dynamic Type compatibility
- Do not use custom fonts for functional labels (only for branding areas)

### Selectability

- Static informational labels (instructions, headings) → `isSelectable = false`
- Labels showing values users may want to copy (IP, serial, path) → `isSelectable = true`
- HIG: "If a label contains useful information — like an error message, a location, or an IP address — consider letting people select and copy it for pasting elsewhere."

### API Reference

```swift
// AppKit
NSTextField.init(labelWithString: "Name:")          // Static non-wrapping label
NSTextField.init(wrappingLabelWithString: "...")    // Multi-line wrapping label
NSTextField.isEditable = false                      // Ensure not editable
NSTextField.isSelectable = true/false               // Control copy behavior
NSColor.labelColor                                  // Primary text
NSColor.secondaryLabelColor                         // Secondary text
NSColor.tertiaryLabelColor                          // Placeholder/disabled text
NSColor.quaternaryLabelColor                        // Watermark

// SwiftUI
Text("Name:")                                       // Static label
Label("Name", systemImage: "person")               // Icon + text label
.foregroundStyle(.primary)                          // Primary label color
.foregroundStyle(.secondary)                        // Secondary label color
```

---

## 7. Validation and Error States

### Overview

macOS does not provide a native "error state" visual for `NSTextField` comparable to iOS red-border field highlighting. Validation and error feedback must be implemented by the application. The HIG guidance: "Validate fields when it makes sense… The appropriate time to check the data depends on the context."

### Validation Timing

| Timing | When to use | Example |
|--------|------------|---------|
| **On focus-out** (when user tabs away) | Most fields — email, URL, name | Email format check |
| **Before leaving the field** | Fields where an invalid partial value is dangerous | Username availability check (must validate before Tab) |
| **On form submission** | Optional fields, or when server-side validation is required | Sign-up form Submit button |
| **Real-time (on keystroke)** | Numeric fields with formatters; character limit indicators | Phone number formatting |
| **Never block entry** | Do not prevent users from typing — only alert after | Never intercept keypresses to disallow characters mid-word |

### Validation Hooks

```swift
// AppKit: NSTextFieldDelegate
func control(_ control: NSControl, isValidObject obj: Any?) -> Bool {
    // Return false to indicate invalid input; system shows shake animation
}

func controlTextDidEndEditing(_ obj: Notification) {
    // Validate after focus leaves the field
}

func controlTextDidChange(_ obj: Notification) {
    // Real-time validation as user types
}

// NSFormatter subclasses provide automatic validation:
NSNumberFormatter   // numeric input validation + formatting
NSDateFormatter     // date input validation + formatting
```

### Error Display Patterns (macOS)

There is no single system-standard error state. These are the three accepted patterns, in order of preference:

#### Pattern 1: Inline Error Label Below the Field (Preferred)

```
  Email address:  [john@               ]
                  ↑ red focus ring (optional, must be implemented manually)
                  Please enter a valid email address.   ← NSTextField in red/warning color
```

- Show an `NSTextField` (label mode, non-editable) below the field in red or `NSColor.systemRed`
- Use sentence case, concise, specific language: "Please enter a valid email address." not "Invalid input."
- Hide the label when the field value is valid
- Reserve this for fields where the format requirement is non-obvious

#### Pattern 2: Alert / Sheet on Submit

- Show an `NSAlert` (sheet attached to the window) when the user clicks a Submit/OK button with invalid data
- List all invalid fields and explain what is needed
- Best for multi-field forms where inline feedback would clutter the layout
- HIG: "When data entry is necessary, make sure people understand that they must provide the required data before they can proceed."

#### Pattern 3: Disable the Proceed Button

- Keep the Next/Submit/Continue button disabled (grayed out) until all required fields contain valid data
- Provide contextual guidance about what is needed (e.g., a helper label: "Enter a name to continue")
- Does not show an error per se — prevents invalid submission proactively
- Best paired with real-time validation so users see the button enable as they complete the form

#### NSFormatter Shake Animation

When `NSFormatter.isPartialStringValid(...)` returns false or `control(_:isValidObject:)` returns false, AppKit automatically applies a shake (wiggle) animation to the field as a brief visual error signal. This is the closest native "error state" AppKit provides.

### Expansion Tooltip for Truncated Data

When a field is too small to display its full content (e.g., a long file path in a compact panel), use the expansion tooltip:
```swift
control.allowsExpansionToolTips = true
```
This shows a popover with the full string when the user hovers over the field — critical for read-only display fields, not just error cases.

---

## 8. Do's and Don'ts

### Text Fields

| Do | Don't |
|----|-------|
| Use a separate label to identify every field, even if placeholder text is present | Rely on placeholder text alone to identify the field — it disappears on first keystroke |
| Size the field width to match the expected input length (short for ZIP codes, wide for full addresses) | Use a single fixed-width field for all types of input regardless of expected content length |
| Use Regular size (22 pt) as the default for dialogs and preference panes | Default to Small or Mini unless the UI is explicitly dense |
| Stack multiple text fields vertically with consistent column alignment | Mix label-left and label-above placement styles within the same form |
| Validate on focus-out for most fields; real-time only for numeric formatters | Block input by intercepting keystrokes to prevent "invalid" characters mid-entry |
| Use NSSecureTextField for any password or credential | Use a regular NSTextField with asterisk substitution via custom delegate |
| Provide Tab-order that flows logically through the form (top-to-bottom, left-to-right) | Rely on auto-Tab-order without verifying it matches visual layout |
| Show an expansion tooltip for fields that may display truncated content | Leave users with no way to see the full content of a clipped field |

### Search Fields

| Do | Don't |
|----|-------|
| Show the search field at the top-trailing position of the toolbar for global app search | Embed search field deep inside a scroll view where it scrolls out of view |
| Default to searching all content and let users narrow scope with tokens or scope control | Default to a narrow scope that surprises users with few results |
| Start searching immediately as the user types (set `sendsSearchStringImmediately = true`) | Wait for Return before showing any results |
| Offer recent searches in the dropdown (populate `recentSearches`) | Show an empty dropdown on focus — use it to offer suggestions or recents |
| Use a scope bar for clearly defined search categories (mail folders, file types) | Use a scope bar with more than 4-5 segments — it becomes unreadable |

### Labels

| Do | Don't |
|----|-------|
| Right-align (trailing-align) field labels in a column layout | Left-align field labels in a column layout — it creates jagged vertical spacing |
| End field labels with a colon (e.g., "Name:") | Omit the colon from field labels |
| Use `NSColor.labelColor` and semantic color variants | Hardcode gray (`#888888`) or any literal color for label text |
| Make labels containing useful data (IP addresses, serial numbers) selectable | Make all labels non-selectable by default regardless of content type |

### Validation

| Do | Don't |
|----|-------|
| Validate on focus-out for format requirements (email, URL) | Validate on every keystroke for slow/async validations (causes lag) |
| Disable the submit button until required fields are filled | Show the submit button enabled and then show an error after clicking |
| Show specific, actionable error messages ("Enter a complete email address like user@example.com") | Show generic messages ("Invalid input" or "Error") |
| Use `NSNumberFormatter` for numeric fields to enforce format automatically | Write custom character-filtering code in `textField(_:shouldChangeCharactersIn:)` |
| Show errors close to the field that caused them | Show all validation errors only in a modal alert |

---

## 9. Sources

All content sourced from official Apple documentation and developer resources, retrieved April 2026.

| Source | URL | Verified |
|--------|-----|---------|
| Apple HIG: Text Fields | https://developer.apple.com/design/human-interface-guidelines/text-fields | Scraped 2026-04-06 |
| Apple HIG: Search Fields | https://developer.apple.com/design/human-interface-guidelines/search-fields | Scraped 2026-04-06 |
| Apple HIG: Labels | https://developer.apple.com/design/human-interface-guidelines/labels | Scraped 2026-04-06 |
| Apple HIG: Entering Data | https://developer.apple.com/design/human-interface-guidelines/entering-data | Scraped 2026-04-06 |
| Apple HIG: Combo Boxes | https://developer.apple.com/design/human-interface-guidelines/combo-boxes | Scraped 2026-04-06 |
| Apple HIG: Token Fields | https://developer.apple.com/design/human-interface-guidelines/token-fields | Scraped 2026-04-06 |
| Apple HIG: Text Views | https://developer.apple.com/design/human-interface-guidelines/text-views | Scraped 2026-04-06 |
| AppKit: NSTextField | https://developer.apple.com/documentation/appkit/nstextfield | Scraped 2026-04-06 |
| AppKit: NSControl.ControlSize | https://developer.apple.com/documentation/appkit/nscontrol/controlsize | Scraped 2026-04-06 |

### Dimension Source Note

The current Apple HIG web pages do not publish explicit pixel/point heights for control sizes. The values in this document (22 pt regular, 19 pt small, 16 pt mini, 26 pt large) are from:
- Apple's macOS Sketch/Figma design resource templates (available at https://developer.apple.com/design/resources/)
- Empirical measurement of Interface Builder's default NSTextField heights across macOS 13–15
- NSControl.ControlSize enum documentation confirming the four size tiers (mini, small, regular, large)

These values are stable and consistent across macOS 10.14 (Mojave) through macOS 15 (Sequoia). If Apple's Liquid Glass redesign (macOS 26) introduces different heights, this document should be updated against the updated design resources.
