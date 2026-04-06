# macOS Alerts, Sheets, Dialogs & Modality — Definitive Reference

> **Scope:** macOS only. Exact button placement rules, text formatting, modality hierarchy.
> **Sources:** Apple HIG, NSAlert Class Reference, AppKit Release Notes macOS 11, AppCoda, Stack Overflow, Reddit.

---

## 1. Alert Types (NSAlert.Style)

| Style | Icon | Sound | Use When |
|---|---|---|---|
| `.informational` | App icon | None | Neutral information |
| `.warning` | App icon (same as informational) | None | Non-critical issue requiring acknowledgment |
| `.critical` | Stop sign (red badge on app icon) | Sosumi | Serious problem, may be unrecoverable |

**Critical finding:** "Currently, there is no visual difference between informational and warning alerts." — Apple NSAlert Class Reference. Only `.critical` is visually distinct.

---

## 2. Button Placement Rules

Buttons placed **right to left** in the order added:

| Position | Added | Keyboard | Return Code |
|---|---|---|---|
| Rightmost | 1st `addButton` | Return = default | `NSAlertFirstButtonReturn` |
| Second from right | 2nd `addButton` | Escape = cancel | `NSAlertSecondButtonReturn` |
| Third from right | 3rd `addButton` | — | `NSAlertThirdButtonReturn` |

- Maximum 4 buttons per alert
- First button = default (blue, Return key)
- Alert with no buttons gets automatic "OK"

### Destructive Buttons (macOS 11+)

```swift
alert.addButton(withTitle: "Cancel")     // 1st → rightmost → default (blue)
alert.addButton(withTitle: "Delete")     // 2nd → left of Cancel → red
alert.buttons[1].hasDestructiveAction = true
```

**Critical rule:** Destructive button must NOT be first — `hasDestructiveAction` styling is suppressed on the first button.

---

## 3. Alert Text Formatting

| Property | Typography | Purpose |
|---|---|---|
| `messageText` | Bold, larger | Primary question/problem — one sentence |
| `informativeText` | Regular, smaller | Consequences, recovery steps — 1-3 sentences |

- Restate the specific action ("Delete 'Project Alpha'?") not "Are you sure?"
- Don't repeat message text in informative text

---

## 4. Suppression Checkbox

```swift
alert.showsSuppressionButton = true
alert.suppressionButton?.title = "Don't show this warning again"
```

**Persistence is YOUR responsibility.** NSAlert does NOT persist state. Store in UserDefaults after dismissal.

Never offer suppression on irreversible destructive actions.

---

## 5. Sheets

### What Sheets Are

Document-modal dialog attached to parent window. Slides down from title bar. Blocks parent window only — other app windows remain accessible.

### Presenting

```swift
// Sheet (window-modal) — preferred
alert.beginSheetModal(for: window) { response in ... }

// App-modal (blocks entire app) — use sparingly
let response = alert.runModal()
```

### When to Use

- Dialog relates to a specific document/window
- User needs to see parent content while deciding
- Task is window-specific (Save, Print, "Save before closing?")

### When NOT to Use

- Decision affects entire app
- App-wide critical error (use `runModal`)
- Not tied to any specific window

---

## 6. Modality Levels

| Level | Scope | Presentation | API |
|---|---|---|---|
| **Window-Modal** | Single window | Sheet from title bar | `beginSheetModal(for:)` |
| **App-Modal** | Entire app | Free-floating centered dialog | `runModal()` |
| **System-Modal** | Entire system | Above all apps | Not available to third-party apps |

**Preference:** Window-modal > App-modal. Use app-modal only when response is required before app can do anything.

---

## 7. System Panels

### Open Panel (NSOpenPanel)

| Property | Purpose |
|---|---|
| `canChooseFiles` | Select files (default: true) |
| `canChooseDirectories` | Select directories (default: false) |
| `allowsMultipleSelection` | Multi-select (default: false) |
| `allowedContentTypes` | Restrict file types |
| `directoryURL` | Initial directory |
| `prompt` | Button label (default: "Open") |
| `accessoryView` | Custom view below browser |

Present as sheet in document-based apps: `panel.beginSheetModal(for: window)`

### Save Panel (NSSavePanel)

NSOpenPanel subclasses NSSavePanel. Additional properties: `nameFieldStringValue`, `canCreateDirectories`, `isExtensionHidden`.

### Print Dialog

```swift
let op = NSPrintOperation(view: myView)
op.runOperation()  // presents sheet from window context
```

Customize via `panel.addAccessoryController()` and `panel.options` mask.

---

## 8. Confirmation Patterns

### Destructive Action

1. Message: restate specific action ("Delete 'Annual Report.pdf'?")
2. Informative: state consequence ("You can't undo this action.")
3. Cancel first (rightmost, blue, Return key)
4. Destructive second (left, red via `hasDestructiveAction`)

### Data Loss on Close

- Sheet attached to document window
- "Do you want to save changes to 'Untitled'?"
- Buttons: Save (default), Don't Save, Cancel

---

## 9. Decision Tree

```
Interrupt needed?
├── No → Inline status (badge, label, error text)
└── Yes → Tied to specific window?
    ├── Yes → SHEET (beginSheetModal)
    └── No → Blocks entire app?
        ├── Yes → APP-MODAL (runModal)
        └── No → Notification or inline message
```

---

## 10. Do's and Don'ts

### Do
- Use sheets for document-specific interactions
- Add Cancel as first button when destructive alternative exists
- Restate specific action in message text
- Use `hasDestructiveAction = true` (macOS 11+)
- Persist suppression state to UserDefaults manually
- Present Open/Save panels as sheets in document-based apps

### Don't
- Don't use alerts for inline-displayable errors
- Don't use `.critical` for mere warnings (alert fatigue)
- Don't make destructive button the default (rightmost)
- Don't assume suppression persists automatically
- Don't use "OK" for destructive buttons — use the action verb
- Don't present sheets for app-wide decisions

---

## 11. Sources

1. Apple HIG — Alerts, Sheets, Modality
2. NSAlert Class Reference (AppKit)
3. NSAlert.Style documentation
4. NSPrintPanel documentation
5. Apple File System Programming Guide — Open/Save Panels
6. AppKit Release Notes macOS 11 (hasDestructiveAction)
7. AppCoda — macOS Alerts tutorial
8. Stack Overflow — NSAlert destructive button
9. Reddit r/MacOS, r/UXDesign — destructive action patterns
