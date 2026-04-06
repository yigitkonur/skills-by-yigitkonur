# macOS Accessibility

Accessibility on macOS is a platform expectation, not an optional feature. Every app distributed through the Mac App Store or in enterprise environments operates within macOS's assistive technology stack. Users who depend on VoiceOver, keyboard navigation, or display accommodations cannot use an app that ignores these requirements. This document covers every dimension of macOS accessibility with exact APIs, testing procedures, and a binary audit checklist.

---

## 1. VoiceOver Requirements

### The Accessibility Object Model

macOS represents every UI as a tree of accessibility elements. At the root is a system-wide element. Below it are application elements, then window and menu bar elements, then individual controls. VoiceOver traverses this tree using the `NSAccessibility` protocol.

Every object in the tree exposes its identity through four core attributes:

| Attribute | Protocol property | What VoiceOver reads |
|---|---|---|
| **Label** | `accessibilityLabel: String?` | The name of the element ("Close", "Search field") |
| **Value** | `accessibilityValue: Any?` | The current state ("On", "75%", selected text content) |
| **Hint** | `accessibilityHelp: String?` | What activating the element does ("Opens the preferences window") |
| **Role** | `accessibilityRole: NSAccessibility.Role?` | What kind of element it is ("button", "slider", "text field") |

VoiceOver announces them in this order: label, value, role, hint.

### Labels

- Provide a label for every interactive element and every image that conveys meaning.
- Labels must be concise. One to three words for controls, a full descriptive phrase for images.
- Do not include the role in the label ("Close button" is wrong — the role is announced separately).
- Do not repeat visible text. If a button's title is already "Save", the `accessibilityLabel` should be `nil` and the system will use the title.
- Decorate-only images should set `accessibilityElement` to `false` (AppKit) or `.accessibilityHidden(true)` (SwiftUI).

```swift
// AppKit — image with semantic content
imageView.setAccessibilityLabel("Product photo: white leather sneaker with black heel detail")

// AppKit — decorative image: hide it
imageView.setAccessibilityElement(false)

// SwiftUI
Image("heroImage")
    .accessibilityLabel("San Francisco skyline at dusk")

Image(decorative: "patternTile") // automatically hidden
```

### Values

Use `accessibilityValue` when the element's current state differs from its label and that state matters to the user.

```swift
// AppKit slider
override var accessibilityValue: Any? {
    return "Volume: \(Int(slider.doubleValue)) percent"
}

// SwiftUI
Slider(value: $volume, in: 0...100)
    .accessibilityValue("\(Int(volume)) percent")
```

### Hints

Hints explain the result of an action. Apply them only when the outcome is non-obvious from the label.

- Written as an imperative sentence: "Opens the color picker."
- Must end with a period.
- Keep under 40 words.

```swift
// AppKit
button.setAccessibilityHelp("Opens the export panel where you can choose a file format.")

// SwiftUI
Button("Export") { ... }
    .accessibilityHint("Opens the export panel where you can choose a file format.")
```

| Situation | Use label only | Add hint |
|---|---|---|
| Static image | Provide descriptive label | Not needed |
| Button with obvious action | Label alone | Not needed |
| Button whose result is ambiguous | Label the element | Explain the outcome |
| Slider or stepper | Label the control | Describe what adjusting it does |

### Roles and Subroles

Every accessible element must declare a role. Roles tell VoiceOver how to announce the element and which actions are available (press, increment, decrement, pick).

**Primary role protocols (adopt one per control type):**

| Protocol | Use for |
|---|---|
| `NSAccessibilityButton` | Push buttons, icon buttons |
| `NSAccessibilityCheckBox` | Checkboxes |
| `NSAccessibilityRadioButton` | Radio buttons |
| `NSAccessibilitySlider` | Sliders |
| `NSAccessibilityStaticText` | Non-editable text |
| `NSAccessibilityNavigableStaticText` | Text blocks a user navigates character-by-character |
| `NSAccessibilityImage` | Images |
| `NSAccessibilityProgressIndicator` | Progress bars |
| `NSAccessibilityStepper` | Steppers |
| `NSAccessibilitySwitch` | Toggle switches |
| `NSAccessibilityTable` | Tables |
| `NSAccessibilityOutline` | Outline/tree views |
| `NSAccessibilityList` | Lists |
| `NSAccessibilityRow` | Table or outline rows |
| `NSAccessibilityGroup` | Logical groupings |
| `NSAccessibilityContainsTransientUI` | Views with transient overlays |

Using a specific role protocol instead of the generic `NSAccessibility` gives Xcode compile-time enforcement of required methods.

**Subroles** refine a role when needed:
- `NSAccessibility.Subrole.closeButton` for a window close button
- `NSAccessibility.Subrole.tableRow` for a row in a table
- `NSAccessibility.Subrole.toggle` for a button that toggles between two states

### VoiceOver Navigation

VoiceOver navigates elements sequentially (VO + Right Arrow / Left Arrow) and hierarchically (VO + Shift + Down Arrow to enter a group, VO + Shift + Up Arrow to exit). For navigation to be logical:

- Return a meaningful `accessibilityChildren` array from container views.
- Ensure every child's `accessibilityParent` points back to its container.
- Order children in `accessibilityChildren` to match visual reading order (top-to-bottom, leading-to-trailing).
- Hide decorative subviews from the tree: `setAccessibilityElement(false)`.

### The VoiceOver Rotor

The rotor (VO + U, or VO + Command + Left/Right Arrow) lets users jump to specific element types without navigating linearly.

**Default rotor items on macOS:**
- Headings
- Links
- Form Controls (buttons, text fields, checkboxes)
- Window Spots (toolbars, panels)
- Characters (when inside a text view)
- Content Chooser (app-specific items like Mail messages or Calendar events)

**Key rotor shortcuts:**

| Action | Shortcut |
|---|---|
| Open rotor menus | VO + U |
| Cycle rotor categories | VO + Command + Left/Right Arrow |
| Move within rotor list | VO + Command + Up/Down Arrow |
| Filter list by typing | Type letters/numbers |
| Clear filter | Delete |
| Select and jump to item | Return or Space |
| Exit rotor | Escape |

Apps cannot add custom rotor items for native macOS apps using a public API (the Web Rotor can be customized for web content via VoiceOver Utility → Web → Web Rotor). For native apps, structure the accessibility hierarchy correctly so that the standard rotor categories capture all key elements.

---

## 2. Custom Controls

Standard AppKit controls (`NSButton`, `NSSlider`, `NSTextField`, etc.) inherit full VoiceOver support automatically. Custom-drawn controls — anything that subclasses `NSView` and paints its own UI — require explicit implementation.

### Implementation Steps

**Step 1: Adopt the correct role-specific protocol.**

```swift
// Swift
class VolumeKnob: NSView, NSAccessibilitySlider {
    // Protocol enforces: accessibilityLabel, accessibilityValue,
    // accessibilityPerformIncrement, accessibilityPerformDecrement
}
```

```objc
// Objective-C
@interface VolumeKnob : NSView <NSAccessibilitySlider>
@end
```

**Step 2: Implement required properties.**

```swift
override var isAccessibilityElement: Bool { true }
override var accessibilityRole: NSAccessibility.Role? { .slider }
override var accessibilityLabel: String? { "Volume" }
override var accessibilityValue: Any? { "\(Int(knobValue * 100)) percent" }

override var accessibilityFrame: NSRect {
    guard let window = self.window else { return .zero }
    return window.convertToScreen(convert(bounds, to: nil))
}

override var accessibilityParent: Any? { superview }
```

**Step 3: Implement actions.**

```swift
override func accessibilityPerformIncrement() -> Bool {
    knobValue = min(1.0, knobValue + 0.05)
    NSAccessibility.post(element: self, notification: .valueChanged)
    return true
}

override func accessibilityPerformDecrement() -> Bool {
    knobValue = max(0.0, knobValue - 0.05)
    NSAccessibility.post(element: self, notification: .valueChanged)
    return true
}
```

**Step 4: Post notifications when state changes.**

Any time the control's state changes programmatically (not triggered by an assistive action), post the appropriate notification:

```swift
// Value changed (slider, progress, stepper)
NSAccessibility.post(element: self, notification: .valueChanged)

// Focus moved
NSAccessibility.post(element: self, notification: .focusedUIElementChanged)

// Selected items changed (tables, outlines)
NSAccessibility.post(element: self, notification: .selectedChildrenChanged)

// Row expanded/collapsed (outlines)
NSAccessibility.post(element: self, notification: .rowExpanded)
NSAccessibility.post(element: self, notification: .rowCollapsed)

// Title or label changed
NSAccessibility.post(element: self, notification: .titleChanged)
```

### Virtual Elements (NSAccessibilityElement)

When a single `NSView` renders multiple logical items (a canvas with draggable objects, a custom list drawn with Core Graphics), each logical item must be represented as a separate `NSAccessibilityElement` — a lightweight proxy object that does not have its own view.

```swift
// Create a proxy element
let element = NSAccessibilityElement.accessibilityElement(
    withRole: .button,
    frame: frameInScreenCoordinates,
    label: "Play",
    parent: self
)

// Or build it manually
let element = NSAccessibilityElement()
element.setAccessibilityRole(.listItem)
element.setAccessibilityLabel("Item 3: Rename project")
element.setAccessibilityParent(self)
element.setAccessibilityFrameInParentSpace(itemFrame) // moves with parent

// Register with parent
self.setAccessibilityChildren([element])

// Post notifications on the element itself
NSAccessibility.post(element: element, notification: .valueChanged)
```

**Use `accessibilityFrameInParentSpace` (not `accessibilityFrame`) for virtual elements.** This ensures the element's hit region tracks the parent view when the window moves or scrolls.

### Common Mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| `isAccessibilityElement` returns `false` on a custom control | VoiceOver skips the control entirely | Return `true` for any control the user must interact with |
| Role is `nil` | VoiceOver announces "unknown" | Always return a valid `NSAccessibility.Role` |
| `accessibilityLabel` is `nil` or empty | VoiceOver reads nothing meaningful | Provide a concise descriptive label |
| `accessibilityFrame` in view coordinates, not screen coordinates | Hit testing fails; VoiceOver cannot focus the element | Convert via `window.convertToScreen(convert(bounds, to: nil))` |
| Not posting notifications after state changes | Screen reader never hears updates | Call `NSAccessibility.post(element:notification:)` for every state change |
| Virtual elements not added to `accessibilityChildren` | Elements are invisible to the accessibility tree | Set `setAccessibilityChildren` on the parent |
| Decorative elements exposed to accessibility tree | Noisy, confusing VoiceOver experience | Set `setAccessibilityElement(false)` on decorative subviews |
| Providing a generic "button" label for every button | User cannot distinguish controls | Write specific, descriptive labels per element |

---

## 3. Display Accommodations

All four display accommodations are accessed through `NSWorkspace.shared` properties and are triggered by a single notification.

### Detection Notification

All four settings fire the same notification:

```swift
NSWorkspace.shared.notificationCenter.addObserver(
    self,
    selector: #selector(displayOptionsDidChange(_:)),
    name: NSWorkspace.accessibilityDisplayOptionsDidChangeNotification,
    object: NSWorkspace.shared
)

@objc func displayOptionsDidChange(_ notification: Notification) {
    applyDisplayAccommodations()
}
```

**Important:** The notification is posted on `NSWorkspace.shared.notificationCenter`, not `NotificationCenter.default`. Using the wrong notification center means the observer never fires.

### Reduce Motion

| | |
|---|---|
| **Setting path** | System Settings → Accessibility → Display → Reduce Motion |
| **Detection API** | `NSWorkspace.shared.accessibilityDisplayShouldReduceMotion: Bool` |
| **What users experience** | Animations are vestibularly uncomfortable or disorienting |

**Required app response:** When `true`, replace or disable animations entirely. Do not merely slow them down.

```swift
func applyAnimation(to view: NSView) {
    if NSWorkspace.shared.accessibilityDisplayShouldReduceMotion {
        // Snap directly to the final state — no animation
        view.frame = destinationFrame
    } else {
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            view.animator().frame = destinationFrame
        }
    }
}
```

Animations to eliminate when Reduce Motion is on:
- Sliding transitions between panels or views
- Parallax effects
- Auto-playing video or animated content
- Spinning loading indicators (replace with a static progress bar)
- Page-curl or zoom effects on window open/close

### Reduce Transparency

| | |
|---|---|
| **Setting path** | System Settings → Accessibility → Display → Reduce Transparency |
| **Detection API** | `NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency: Bool` |
| **What users experience** | Translucent sidebar/toolbar backgrounds are hard to read; blurs cause visual noise |

**Required app response:** Replace all translucent or blurred surfaces with opaque alternatives.

```swift
func configureBackground() {
    if NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency {
        // Use a solid, fully opaque background
        contentView.wantsLayer = true
        contentView.layer?.backgroundColor = NSColor.windowBackgroundColor.cgColor
        // Disable NSVisualEffectView blending
        visualEffectView.blendingMode = .withinWindow
        visualEffectView.material = .underWindowBackground
        visualEffectView.isEmphasized = false
        visualEffectView.alphaValue = 1.0
    } else {
        visualEffectView.material = .sidebar
    }
}
```

When using `NSVisualEffectView`, set its `material` to a non-blending value or hide it entirely and substitute an opaque `NSColor.windowBackgroundColor` fill.

### Increase Contrast

| | |
|---|---|
| **Setting path** | System Settings → Accessibility → Display → Increase Contrast |
| **Detection API** | `NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast: Bool` |
| **What users experience** | Low-contrast UI elements (separators, placeholder text, subtle borders) disappear |

**Required app response:** Strengthen borders, darken separator lines, increase the contrast of any UI element that relies on a subtle color difference.

```swift
func configureListItem(_ view: NSBox) {
    if NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast {
        view.boxType = .custom
        view.borderColor = NSColor.labelColor
        view.borderWidth = 1.0
        view.fillColor = NSColor.controlBackgroundColor
    } else {
        view.boxType = .custom
        view.borderColor = NSColor.separatorColor
        view.borderWidth = 0.5
        view.fillColor = NSColor.controlBackgroundColor.withAlphaComponent(0.5)
    }
}
```

Tip: Use macOS semantic colors (`NSColor.labelColor`, `NSColor.separatorColor`, `NSColor.controlColor`) for default states. The system automatically adjusts these for Increase Contrast mode.

### Bold Text

| | |
|---|---|
| **Setting path** | System Settings → Accessibility → Display → Bold Text |
| **Detection API** | `NSWorkspace.shared.accessibilityDisplayShouldUseBoldText: Bool` |
| **What users experience** | Text with thin stroke weights is hard to read |

**Required app response:** Replace light or thin font weights with regular or semibold equivalents.

```swift
func labelFont(size: CGFloat) -> NSFont {
    let weight: NSFont.Weight = NSWorkspace.shared.accessibilityDisplayShouldUseBoldText
        ? .semibold
        : .regular
    return NSFont.systemFont(ofSize: size, weight: weight)
}
```

For custom fonts with named variants:

```swift
func customFont(size: CGFloat) -> NSFont {
    let name = NSWorkspace.shared.accessibilityDisplayShouldUseBoldText
        ? "Montserrat-SemiBold"
        : "Montserrat-Regular"
    return NSFont(name: name, size: size) ?? NSFont.systemFont(ofSize: size)
}
```

**Important:** `NSWorkspace.shared.accessibilityDisplayShouldUseBoldText` has no separate change notification on macOS — query it inside the unified `displayOptionsDidChange` handler.

### Complete Accommodation Handler

```swift
func applyDisplayAccommodations() {
    let ws = NSWorkspace.shared
    let reduceMotion      = ws.accessibilityDisplayShouldReduceMotion
    let reduceTransparency = ws.accessibilityDisplayShouldReduceTransparency
    let increaseContrast  = ws.accessibilityDisplayShouldIncreaseContrast
    let boldText          = ws.accessibilityDisplayShouldUseBoldText

    updateAnimations(disable: reduceMotion)
    updateTranslucency(opaque: reduceTransparency)
    updateContrast(high: increaseContrast)
    updateFontWeight(bold: boldText)
}
```

---

## 4. Color Accessibility

### Contrast Ratios (WCAG 2.2)

macOS apps are expected to meet WCAG 2.2 Level AA as a minimum. App Store Connect explicitly evaluates contrast compliance.

| Content type | Minimum ratio | Notes |
|---|---|---|
| Normal text (< 18 pt, or < 14 pt bold) | **4.5 : 1** | Text against its immediate background |
| Large text (≥ 18 pt, or ≥ 14 pt bold) | **3 : 1** | Includes headings |
| UI component borders and icons | **3 : 1** | WCAG SC 1.4.11 Non-Text Contrast |
| Decorative elements | No requirement | Purely visual, conveys no information |
| Logotypes | No requirement | Brand name text in logos |

**Contrast formula:**
```
ratio = (L1 + 0.05) / (L2 + 0.05)

where L = 0.2126 × R_lin + 0.7152 × G_lin + 0.0722 × B_lin
and R_lin = (R_sRGB / 255)^2.2  (approximate linearization)
```

Do not round: 4.499 : 1 does not meet the 4.5 : 1 threshold.

**Testing:** Accessibility Inspector (Xcode) reports the contrast ratio for any selected text element. Run checks in both Light and Dark appearance modes.

### Increase Contrast Mode

When `NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast` is `true`, the system raises contrast for system colors automatically. Your custom colors must also respond. Test in this mode separately — a UI that passes 4.5 : 1 in normal mode may fall below it in Increase Contrast mode if you have conditional color logic.

### Semantic Colors (Color Blindness Safety)

The most reliable color blindness accommodation is to use macOS semantic system colors. These are defined to be distinguishable under common color vision deficiencies and automatically adapt to Dark Mode and Increase Contrast.

**Essential semantic colors:**

| Color | `NSColor` property | Use for |
|---|---|---|
| Label (primary text) | `NSColor.labelColor` | All primary text |
| Secondary label | `NSColor.secondaryLabelColor` | Supporting text |
| Tertiary label | `NSColor.tertiaryLabelColor` | Placeholder, hint text |
| Separator | `NSColor.separatorColor` | Dividers, borders |
| Control background | `NSColor.controlBackgroundColor` | Input field backgrounds |
| Window background | `NSColor.windowBackgroundColor` | Main window surfaces |
| Selected content | `NSColor.selectedContentBackgroundColor` | Highlighted rows |
| Control accent | `NSColor.controlAccentColor` | Interactive highlights |

### Color Blindness Types and macOS Color Filters

**Prevalence:** ~8% of men and ~0.5% of women have some form of color vision deficiency (~300 million people globally).

| Type | Description |
|---|---|
| Deuteranomaly / Deuteranopia | Red-green (most common; green weakness or absence) |
| Protanomaly / Protanopia | Red-green (red weakness or absence) |
| Tritanomaly / Tritanopia | Blue-yellow (rarer) |
| Achromatopsia | Complete (sees only grayscale) |

**macOS color filter options** (System Settings → Accessibility → Display → Color Filters):
- Greyscale
- Red/Green filter (Protanopia simulation)
- Green/Red filter (Deuteranopia simulation)
- Blue/Yellow filter (Tritanopia simulation)
- Color Tint (adjustable)

Use these filters during design review to verify that information is still legible.

### Color Blindness Design Rules

1. **Never convey information by color alone.** If a red border means "error", add an error icon or the word "Error" as a label.
2. **Add redundant cues:** icons, patterns, shapes, or text labels alongside color-coded states.
3. **Avoid red/green combinations** for critical distinctions (most common deficiency type).
4. **Test with Greyscale filter** — if the UI is still usable in monochrome, color blindness users will manage.
5. **Use the system's semantic status colors** (`NSColor.systemRed`, `NSColor.systemGreen`, etc.) alongside descriptive labels. Do not rely on these colors alone.

---

## 5. Target Sizes

### macOS Minimum Click Targets

The Apple HIG specifies a minimum clickable area of **44 × 44 points** for controls across Apple platforms. For macOS, where pointer precision is higher than touch, this minimum still applies but the acceptable range extends down toward 22 × 22 pt for small utility controls (window chrome buttons, toolbar items) provided they are well-separated and carry visible labels or tooltips.

**Practical guidance:**

| Control type | Minimum size | Notes |
|---|---|---|
| Primary action buttons | 44 × 44 pt | Never go below this for main actions |
| Toolbar buttons | 28 × 28 pt minimum (44 preferred) | System toolbar items are 28 pt minimum |
| Icon-only controls | 44 × 44 pt tap area (visual size can be smaller) | Use `contentInsets` / hit-test override |
| Close/minimize/zoom (traffic lights) | ~15 pt visual, ~22 pt hit area | System-provided; do not replicate at smaller sizes |
| Text links inline in paragraphs | Exempt from size requirement | WCAG 2.5.5 inline exception applies |

**WCAG 2.5.5 (AAA)** specifies 44 × 44 CSS px as the target size for interactive controls. Inline text links within sentences are exempt. Essential targets whose size cannot change are also exempt (e.g., map controls).

### Increasing Hit Area Without Changing Visual Size

Override `hitTest(_:)` in AppKit to expand the interactive region without changing the visible appearance:

```swift
override func hitTest(_ point: NSPoint) -> NSView? {
    // Expand the hit area by 8 pt on each side
    let expandedBounds = bounds.insetBy(dx: -8, dy: -8)
    return expandedBounds.contains(point) ? self : nil
}
```

---

## 6. Keyboard Navigation

### Two Modes on macOS

macOS has two keyboard navigation modes:

| Mode | Scope | How to enable |
|---|---|---|
| **Tab Navigation (default)** | Text fields, buttons, and form controls only | On by default |
| **Full Keyboard Access** | Every UI element including lists, toolbars, and window controls | System Settings → Keyboard → Keyboard Navigation |

Apps must support Tab Navigation at minimum. Supporting Full Keyboard Access for complex custom UIs is required for WCAG 2.1 Level AA compliance (SC 2.1.1 Keyboard).

### Focus Management Requirements

1. **Logical Tab Order:** Tab focus must follow visual reading order. Override `nextKeyView` to set explicit order when auto-layout order is incorrect.

   ```swift
   // AppKit
   searchField.nextKeyView = filterPopup
   filterPopup.nextKeyView = resultsTable
   resultsTable.nextKeyView = searchField // wraps
   ```

2. **Visible Focus Ring:** Every focused control must show a visible focus indicator. Standard AppKit controls draw the system blue focus ring automatically. Custom controls must draw their own.

   ```swift
   // Custom control focus ring
   override func drawFocusRingMask() {
       let path = NSBezierPath(roundedRect: bounds, xRadius: 4, yRadius: 4)
       path.fill()
   }

   override var focusRingMaskBounds: NSRect { bounds }

   override var needsPanelToBecomeKey: Bool { true }
   override var acceptsFirstResponder: Bool { true }
   ```

3. **WCAG 2.4.7 (Focus Visible):** Focus indicators must be visible for all keyboard-operable components. The indicator must persist as long as the element has focus (not time-limited). The form of the indicator is not specified by WCAG, but the macOS system focus ring satisfies the requirement.

4. **Keyboard Actions per Control Type:**

   | Control | Key action |
   |---|---|
   | Button (standard) | Space bar or Return to activate |
   | Default button (blue) | Return activates from anywhere in window |
   | Checkbox | Space bar to toggle |
   | Radio button group | Arrow keys to move within group |
   | Dropdown / pop-up button | Space or Return to open; arrows to navigate; Return or Space to select |
   | Slider | Left/Right arrows to adjust value |
   | Number stepper | Up/Down arrows |
   | Table / outline | Arrow keys to navigate rows; Space to select; Return or Space to activate |
   | Tab bar | Left/Right arrows to switch tabs |
   | Text field | Type to enter; Tab to leave |

5. **Keyboard Shortcuts:** Provide `keyEquivalent` for frequently used actions. Every menu item must be keyboard-reachable.

   ```swift
   let menuItem = NSMenuItem(title: "Save", action: #selector(save), keyEquivalent: "s")
   menuItem.keyEquivalentModifierMask = .command
   ```

6. **Escape Key:** Dismiss any modal, popover, or sheet on Escape.

7. **No Keyboard Traps:** Focus must never be trapped within a control or panel. The user must always be able to move focus away using Tab, Shift-Tab, Escape, or arrow keys.

### Full Keyboard Access Navigation

Under Full Keyboard Access, macOS highlights every focusable element with a blue border. Toolbar items, sidebar items, and window controls become Tab-focusable. Space activates any focused control. To support this mode in custom controls, `acceptsFirstResponder` must return `true`.

---

## 7. Dynamic Type on macOS

### The Status of Dynamic Type on macOS

macOS does not implement iOS-style Dynamic Type. Calls to `NSFont.preferredFont(forTextStyle:)` return a fixed size regardless of the user's text size preference. The user-facing text size setting (macOS 14 Sonoma and later) is stored in a system preferences domain, not surfaced through a public Swift/AppKit API.

### macOS 14+ Text Size Setting

**Location:** System Settings → Accessibility → Display → Text Size (or the Control Center slider in macOS 15+).

**Underlying storage:** `com.apple.universalaccess` preference domain, key `FontSizeCategory`.

**Values and corresponding point sizes:**

| Preference value | Approx. pt size | Notes |
|---|---|---|
| `XXXS` | 9 pt | |
| `XXS` | 10 pt | |
| `XS` | 11 pt | |
| `DEFAULT` | 11 pt | System default |
| `S` | 12 pt | |
| `M` | 13 pt | |
| `L` | 14 pt | |
| `XL` | 15 pt | |
| `XXL` | 16 pt | |
| `XXXL` | 17 pt | |
| `AX1` | 20 pt | Accessibility size |
| `AX2` | 24 pt | Accessibility size |
| `AX3` | 29 pt | Accessibility size |
| `AX4` | 35 pt | Accessibility size |
| `AX5` | 42 pt | Accessibility size |

**Observing changes in code:**

```swift
// WARNING: Reading com.apple.universalaccess may require an entitlement.
// Apple's review guidelines disallow this for most App Store apps.
// Use this approach only for enterprise or developer tools.

extension UserDefaults {
    @objc var FontSizeCategory: [String: Any]? {
        dictionary(forKey: "FontSizeCategory")
    }
}

let uaDefaults = UserDefaults(suiteName: "com.apple.universalaccess")!
var fontSizeObservation: NSKeyValueObservation?

fontSizeObservation = uaDefaults.observe(\.FontSizeCategory, options: .new) { _, change in
    guard let global = change.newValue?["global"] as? String else { return }
    // Map global string to NSFont size
    self.applyFontSize(forCategory: global)
}
```

### Recommended Approach for App Store Apps

For apps distributed through the App Store, the safest approach is:

1. **Use semantic system fonts** (`NSFont.systemFont(ofSize:weight:)`) for all text. The system applies some level of size adaptation for standard fonts.
2. **Support the accessibility text size by building flexible layouts.** Avoid fixed-height containers, clipping views, or pixel-precise text positioning.
3. **Verify layouts at both ends of the scale** using the Simulator or device. Open System Settings → Accessibility → Display → Text Size and drag to maximum; then test the app.

### SwiftUI Dynamic Type (macOS)

SwiftUI on macOS supports `@Environment(\.dynamicTypeSize)` for layouts that should adapt:

```swift
@Environment(\.dynamicTypeSize) private var dynamicTypeSize

var body: some View {
    Group {
        if dynamicTypeSize.isAccessibilitySize {
            VStack { contentItems }
        } else {
            HStack { contentItems }
        }
    }
}
```

SwiftUI's `Text` views using built-in font styles (`.title`, `.body`, `.caption`) respond to the user's text size setting automatically on macOS 14+.

---

## 8. Testing

### Accessibility Inspector

**Location:** Xcode → Open Developer Tool → Accessibility Inspector (or: Xcode → Xcode menu → Open Developer Tool → Accessibility Inspector).

**What it does:**
- Displays the accessibility attributes of any element on screen in real time.
- Shows: role, label, value, hint, frame, enabled state, actions, parent, and children.
- Reports contrast ratios for text elements.
- Runs automated audits.

**Testing workflow:**

1. Launch your app.
2. Launch Accessibility Inspector.
3. Choose your app from the target picker (top-left of the Inspector window).
4. Hover over any UI element. The Inspector updates instantly with that element's attributes.
5. Check:
   - `accessibilityLabel` is present and meaningful.
   - `accessibilityRole` matches the control type.
   - `accessibilityValue` is current and human-readable.
   - `accessibilityHelp` is present for non-obvious controls.
   - `accessibilityFrame` is correctly positioned over the visible control.
6. Run the audit: Accessibility Inspector → Window → Accessibility Verifier (or the triangle/play button in the Audit tab). The Verifier scans the full accessibility tree and reports missing labels, empty roles, and other structural issues.
7. Review each finding, fix in Xcode, rebuild, and re-run.

**Contrast ratio check:**
- Select any text element in the Inspector.
- The Audit tab's "Contrast" entry shows the computed ratio.
- Compare against the thresholds: 4.5 : 1 for normal text, 3 : 1 for large text and non-text UI.

### VoiceOver Testing

**Enable VoiceOver:** Command + F5, or System Settings → Accessibility → VoiceOver → Enable VoiceOver. Press Command + F5 again to disable.

**Essential keyboard shortcuts:**

| Action | Shortcut |
|---|---|
| VoiceOver modifier (VO) | Control + Option |
| Next element | VO + Right Arrow |
| Previous element | VO + Left Arrow |
| Interact with element (enter group) | VO + Shift + Down Arrow |
| Stop interacting (exit group) | VO + Shift + Up Arrow |
| Activate (press) focused element | VO + Space |
| Open rotor menus | VO + U |
| Read from beginning | VO + A |
| Pause/resume reading | Control |
| Read current element | VO + F3 |

**Testing steps:**

1. Start at the top of your app window (Command + Option + Shift + Down Arrow to interact with the window).
2. Navigate with VO + Right Arrow through every interactive element.
3. Confirm VoiceOver announces: element name, element type (role), and current state (value) for each control.
4. Activate each button, checkbox, and slider using VO + Space and verify the state change is announced.
5. Open the rotor (VO + U). Verify Form Controls lists all interactive elements. Navigate to each using the rotor.
6. Enter any text field. Verify keyboard input is possible and VoiceOver announces characters as they are typed.
7. Trigger any dynamic state changes (loading spinner, alert, selection change). Verify VoiceOver announces the change without requiring the user to navigate back to it.
8. Test with VoiceOver speaking rate reduced (VO + Command + Shift + Down Arrow decreases rate) to confirm all announcements are complete before the next begins.

### Simulating Display Accommodations in Xcode Tests

```swift
// Simulate accessibility flags during UI tests
let app = XCUIApplication()
app.launchArguments = [
    "-UIAccessibilityReduceMotionEnabled",  "YES",
    "-UIAccessibilityReduceTransparencyEnabled", "YES",
    "-UIAccessibilityIncreaseContrastEnabled", "YES",
    "-UIAccessibilityBoldTextEnabled", "YES"
]
app.launch()
```

For macOS, manually toggle each setting during testing. Use `defaults write` to script it in CI:

```bash
# Enable Reduce Motion
defaults write com.apple.universalaccess reduceMotion -bool true

# Enable Increase Contrast
defaults write com.apple.universalaccess increaseContrast -bool true

# Re-launch app, test, restore
defaults delete com.apple.universalaccess reduceMotion
defaults delete com.apple.universalaccess increaseContrast
```

---

## 9. Audit Checklist

Use this checklist before every release. All items must be "Yes" for the app to be considered accessible.

### VoiceOver

- [ ] Every interactive control has a non-empty `accessibilityLabel`.
- [ ] Every control's `accessibilityRole` matches its function (button, slider, checkbox, etc.).
- [ ] Controls with changing state provide an accurate `accessibilityValue` at all times.
- [ ] Hints (`accessibilityHelp`) are present for any control whose action is non-obvious, and absent for obvious ones.
- [ ] Decorative images and purely visual elements have `setAccessibilityElement(false)` set.
- [ ] The accessibility hierarchy is a proper tree (no cycles; each child's parent points back to its container).
- [ ] Tab order through VO + Right Arrow matches the visual reading order of the window.
- [ ] All dynamic content changes (loading states, alerts, selection changes) post the appropriate `NSAccessibility` notification.

### Custom Controls

- [ ] Every custom-drawn control adopts the appropriate role-specific protocol (`NSAccessibilityButton`, `NSAccessibilitySlider`, etc.).
- [ ] `accessibilityFrame` is in screen coordinates (converted via `window.convertToScreen`), not view coordinates.
- [ ] Virtual elements (drawn without a view) use `accessibilityFrameInParentSpace` and are registered in the parent's `accessibilityChildren`.
- [ ] Action methods (`accessibilityPerformPress`, `accessibilityPerformIncrement`, etc.) return `true` and trigger the corresponding behavior.

### Display Accommodations

- [ ] App subscribes to `NSWorkspace.accessibilityDisplayOptionsDidChangeNotification` on `NSWorkspace.shared.notificationCenter` and refreshes UI on receipt.
- [ ] When `accessibilityDisplayShouldReduceMotion` is `true`, all non-essential animations are disabled (not slowed; disabled).
- [ ] When `accessibilityDisplayShouldReduceTransparency` is `true`, all translucent or blurred surfaces use opaque equivalents.
- [ ] When `accessibilityDisplayShouldIncreaseContrast` is `true`, borders, separators, and UI element contrast are strengthened.
- [ ] When `accessibilityDisplayShouldUseBoldText` is `true`, fonts with light or thin weight are replaced by regular or semibold equivalents.

### Color

- [ ] All normal text (< 18 pt, or < 14 pt bold) meets a minimum contrast ratio of 4.5 : 1 against its background, in both Light and Dark appearance modes.
- [ ] All large text (≥ 18 pt, or ≥ 14 pt bold) meets a minimum contrast ratio of 3 : 1.
- [ ] All UI component borders, icons, and non-text indicators meet a minimum contrast ratio of 3 : 1 (WCAG SC 1.4.11).
- [ ] No information is conveyed by color alone. Every color-coded state also uses a label, icon, pattern, or shape as a redundant cue.
- [ ] App tested with macOS Color Filters → Greyscale: all information remains legible.
- [ ] Semantic system colors (`NSColor.labelColor`, `NSColor.separatorColor`, etc.) are used for standard UI elements rather than hardcoded color values.

### Target Sizes

- [ ] All primary action buttons have a clickable area of at least 44 × 44 points.
- [ ] All icon-only toolbar controls have a hit area of at least 28 × 28 points (44 × 44 preferred).
- [ ] Custom controls that are smaller than 44 × 44 points visually override `hitTest(_:)` to expand the interactive region.

### Keyboard Navigation

- [ ] All interactive controls are reachable with the Tab key in a logical order.
- [ ] Every focused control shows a visible focus ring (system focus ring, or custom equivalent).
- [ ] Keyboard focus is never trapped — the user can always Tab or Escape out of any control or panel.
- [ ] Standard keyboard actions are respected per control type (Space for buttons, arrows for sliders/lists, Return for default button, Escape for dismissal).
- [ ] All frequently used actions have menu items with keyboard shortcuts (`keyEquivalent`).

### Dynamic Type / Text Size

- [ ] Layouts do not use fixed-height containers that clip text at large type sizes.
- [ ] App tested with System Settings → Accessibility → Display → Text Size at maximum setting.
- [ ] SwiftUI `Text` views use system font styles (`.body`, `.title`, etc.) that respond to the text size setting.

### Testing

- [ ] Accessibility Inspector audit passes with zero reported issues.
- [ ] Manual VoiceOver walkthrough completed, confirming every control is announced correctly.
- [ ] Contrast ratios verified in Accessibility Inspector for both Light and Dark modes.
- [ ] All four display accommodations manually toggled and verified (Reduce Motion, Reduce Transparency, Increase Contrast, Bold Text).

---

## 10. Sources

All claims in this document are sourced from the following:

| Source | Used for |
|---|---|
| [NSAccessibilityProtocol — Apple Developer Documentation](https://developer.apple.com/documentation/appkit/nsaccessibilityprotocol) | VoiceOver attribute APIs, roles, required vs optional properties |
| [NSAccessibilityElementProtocol — Apple Developer Documentation](https://developer.apple.com/documentation/AppKit/NSAccessibilityElementProtocol) | Custom control implementation, virtual elements |
| [Implementing Accessibility for Custom Controls — Apple Library Archive](https://developer.apple.com/library/archive/documentation/Accessibility/Conceptual/AccessibilityMacOSX/ImplementingAccessibilityforCustomControls.html) | Role-specific protocol list, notification posting, NSAccessibilityElement |
| [Accessibility Programming Guide — macOS Model — Apple Library Archive](https://developer.apple.com/library/archive/documentation/Accessibility/Conceptual/AccessibilityMacOSX/OSXAXmodel.html) | Accessibility object model hierarchy |
| [NSWorkspace.accessibilityDisplayOptionsDidChangeNotification — Apple](https://developer.apple.com/documentation/appkit/nsworkspace/accessibilitydisplayshouldreducemotion) | Reduce Motion API |
| [NSWorkspace.accessibilityDisplayShouldIncreaseContrast — Apple](https://developer.apple.com/documentation/appkit/nsworkspace/accessibilitydisplayshouldincreasecontrast) | Increase Contrast API |
| [NSWorkspace.accessibilityDisplayShouldReduceTransparency — Apple](https://developer.apple.com/documentation/appkit/nsworkspace/accessibilitydisplayshouldreducetransparency) | Reduce Transparency API |
| [Testing System Accessibility Features — Apple Developer Documentation](https://developer.apple.com/documentation/accessibility/testing-system-accessibility-features-in-your-app) | Bold text API (`accessibilityDisplayShouldUseBoldText`), accommodation detection |
| [Use the VoiceOver rotor on Mac — Apple Support](https://support.apple.com/en-ca/guide/voiceover/mchlp2719/mac) | Rotor keyboard shortcuts and navigation items |
| [Change VoiceOver Rotor Items — Apple Support](https://support.apple.com/guide/voiceover/change-what-the-voiceover-rotor-shows-vo15219/mac) | Rotor customization |
| [Sufficient Contrast Evaluation Criteria — App Store Connect Help](https://developer.apple.com/help/app-store-connect/manage-app-accessibility/sufficient-contrast-evaluation-criteria/) | App Store contrast requirements, audit workflow |
| [WCAG 2.2 SC 1.4.3 Contrast (Minimum) — W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) | Contrast ratio formula, normal vs large text thresholds |
| [WCAG 2.5.5 Target Size — W3C](https://www.w3.org/WAI/WCAG21/Understanding/target-size) | 44 × 44 minimum click target requirement and exemptions |
| [WCAG 2.4.7 Focus Visible — W3C](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) | Focus indicator requirements |
| [Preparing Your App for VoiceOver — CreateWithSwift](https://www.createwithswift.com/preparing-your-app-for-voice-over-labels-values-and-hints/) | Label/value/hint best practices with SwiftUI examples |
| [How to Respond to macOS 14 Text Size Setting — Stack Overflow](https://stackoverflow.com/questions/77937271/how-to-respond-to-the-new-text-size-setting-in-macos-14-sonoma) | Dynamic Type on macOS: preference domain, KVO, font size table |
| [macOS accessibility display accommodations — GitHub Gist (dagronf)](https://gist.github.com/dagronf/8c3e1dcc0f8175365f3055bacd9c99fa) | NSWorkspace notification center requirement |
| [macOS Increase Contrast — Stack Overflow](https://stackoverflow.com/questions/49268981/how-to-support-the-increase-contrast-option-under-the-accessibility-display) | Contrast detection code pattern |
| [Keyboard Access on Mac — Deque University](https://dequeuniversity.com/mac/keyboard-access-mac) | Full Keyboard Access enabling, Tab navigation scope |
| [Using the Keyboard to Navigate on macOS — tempertemper.net](https://www.tempertemper.net/blog/using-the-keyboard-to-navigate-on-macos) | Per-control keyboard interaction patterns |
| [Color Blindness Design — Litmus](https://www.litmus.com/blog/how-to-design-for-colorblindness) | Color blindness prevalence, safe design rules |
| [macOS Color Filters — AbilityNet](https://mcmw.abilitynet.org.uk/how-to-change-the-colours-on-the-screen-in-macos-13-ventura) | Color filter types and system settings path |
| [Dynamic Type in iOS/macOS — codakuma.com](https://codakuma.com/dynamic-type/) | DynamicTypeSize API, isAccessibilitySize, ViewThatFits patterns |
| [Bold Text with Custom Fonts — blog.kevin-hirsch.com](https://www.blog.kevin-hirsch.com/accessibility-bold-text-with-custom-fonts/) | Bold text detection, font descriptor approach |
| [macOS Accessibility Testing — MagicPod](https://blog.magicpod.com/accessibility-testing-on-mac-guide-to-creating-inclusive-web-experiences) | Accessibility Inspector + VoiceOver testing workflow |
