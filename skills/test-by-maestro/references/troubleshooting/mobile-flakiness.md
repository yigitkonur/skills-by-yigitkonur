# Troubleshooting Mobile Flakiness and Timing Failures

Mobile UI testing involves asynchronous animations, soft keyboard shifts, lazy-loaded lists, and dynamic accessibility trees. Diagnosing failures systematically eliminates test flakiness without resorting to arbitrary sleep delays.

---

## Hierarchy-First Diagnostic Workflow

When a selector fails with element-not-found or timeout errors, never guess selector modifications. Inspect the live accessibility tree directly from the running simulator or device:

### 1. Terminal Hierarchy Inspection
```bash
# Dump complete formatted JSON view hierarchy
maestro hierarchy

# Target explicit device
maestro --device "$DEVICE_UDID" hierarchy

# Dump tabular CSV summary (element_num,depth,attributes,parent_num)
maestro hierarchy --compact
```

### 2. Interactive AI Agent Inspection via MCP (`maestro mcp`)
When automating via AI coding agents:
- Use MCP `inspect_screen`: Returns compact hierarchy (`ui_schema` and `elements`) with token-efficient keys (`b`=bounds, `txt`=text, `rid`=id, `a11y`=accessibility label, `hint`=placeholder).
- Use MCP `open_maestro_viewer`: Opens live Server-Sent Events (SSE) stream in browser to see the device screen and command execution in real-time.

### What to Inspect in the Hierarchy Dump:
1. **Identifiers**: Check whether `id` (`resource-id` on Android, `accessibilityIdentifier` on iOS) matches your locator exactly.
2. **Text Resolution & Regex Anchors**: Remember that Maestro's `text:` matcher is a **full-string regex match (case-insensitive)**. If the screen has `"Log In to Your Account"`, `text: "Log In"` will fail. Always use `text: ".*Log In.*"` for partial copy.
3. **Element Coordinates & Bounds**: Verify that the element's frame is within the screen bounds (e.g. `frame: {{x, y}, {w, h}}`).
4. **Accessibility Grouping**: In React Native and native containers, setting `accessible={true}` on a parent view collapses child elements into a single node, hiding individual child IDs.
5. **Modal Scrims & Invisible Overlays**: Transparent backdrops can intercept touch events, preventing taps from reaching underlying buttons.

---

## Selector Validation Rules & Invariants (2.11.0)

1. **No Coordinates in Element Selectors**:
   In Maestro 2.11.0, passing `start:` or `end:` inside element selectors (e.g. `tapOn: { start: ... }`) is strictly rejected. `start` and `end` are valid exclusively for `swipe:`.
2. **Scroll Speed Bounds**:
   In `scrollUntilVisible`, `speed:` must be an integer between 0 and 100. Negative values or values exceeding 100 trigger deserialization errors.

---

## Soft Keyboard Race Conditions and Input Focus

The on-screen soft keyboard is a primary source of mobile test flakiness:

### 1. Obscured Action Buttons
When typing into text inputs, the soft keyboard may push or obscure buttons at the bottom of the screen.

```yaml
# Correct: Explicitly dismiss keyboard before proceeding
- tapOn:
    id: "email_input"
- inputText: "user@example.com"
- hideKeyboard:
    optional: true
- tapOn:
    id: "submit_button"
```

Using `optional: true` ensures the step succeeds even if the keyboard has already dismissed automatically.

### 2. Focus Before Input
Always tap the input element to guarantee focus before typing:

```yaml
# Ensure element is focused before sending text
- tapOn:
    id: "search_input"
- inputText: "query string"
```

---

## Animations, Screen Transitions, and Rendering

Maestro automatically retries locators for up to 7 seconds, but rapid screen transitions or layout animations can cause race conditions.

### 1. Wait for Animations to End
When screens animate in with slide or fade transitions, use `waitForAnimationToEnd` before asserting elements:

```yaml
- tapOn: "Open Details"
- waitForAnimationToEnd:
    timeout: 5000
- assertVisible: "Details Header"
```

### 2. Disable Looping Animations in CI
Continuous looping animations (such as unconstrained pulse effects or looping video banners) can prevent the iOS XCUITest driver from detecting that the application is idle.
- In `.maestro/config.yaml`, set `platform.ios.disableAnimations: true` and `platform.android.disableAnimations: true`.
- Or perform a settle swipe if cold boot accessibility tree needs stabilization:
  ```yaml
  - launchApp
  - swipe:
      direction: DOWN
      duration: 150
  ```

---

## Duplicate Elements and List Items

When multiple elements share identical labels (e.g. repeated "Delete" buttons in a list), avoid fragile ordinal index selectors (`index: 0`, `index: 1`).

### 1. Use Relational Selectors
Anchor the target element relative to a unique neighbor:

```yaml
# Tap Delete button within a specific item row
- tapOn:
    text: "Delete"
    below: "Product Title #42"

# Target button as child of a specific container
- tapOn:
    text: "Remove"
    childOf:
      id: "cart_item_42"
```

### 2. Off-Screen List Items
Modern mobile lists (`FlatList`, `RecyclerView`) unmount views outside the viewport. Elements that are scrolled off-screen do not exist in the accessibility hierarchy.

Use `scrollUntilVisible` to locate off-screen items:

```yaml
- scrollUntilVisible:
    element:
      id: "item_99"
    direction: DOWN
    timeout: 15000
    speed: 40
- tapOn:
    id: "item_99"
```

---

## System Permission Dialogs and Alerts

System permission sheets (Camera, Location, Notifications) appear asynchronously and block interaction with the underlying app.

### 1. Pre-Grant Permissions
Avoid runtime alerts completely by granting permissions at launch or via `setPermissions`:

```yaml
- launchApp:
    permissions:
      all: allow
```

### 2. Handle Optional Alerts Gracefully
If testing runtime permission prompts:

```yaml
- tapOn:
    text: "Allow While Using App"
    optional: true

- tapOn:
    text: "Allow"
    optional: true
```

Or condition the action on visibility:

```yaml
- runFlow:
    when:
      visible: "Allow While Using App"
    commands:
      - tapOn: "Allow While Using App"
```

---

## Related References

- [Flows and Selectors](../commands/flows-and-selectors.md) — Selector priority, regex rules, and command syntax.
- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Dumping hierarchy, MCP tools, and inspecting logs.
- [Expo and State](expo-and-state.md) — State hydration, permissions, and Keychain token issues.
