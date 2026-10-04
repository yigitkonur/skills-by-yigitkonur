# Troubleshooting Mobile Flakiness and Timing Failures

Mobile UI testing involves asynchronous animations, soft keyboard shifts, lazy-loaded lists, and dynamic accessibility trees. Diagnosing failures systematically eliminates test flakiness without resorting to arbitrary sleep delays.

## Hierarchy-First Diagnostic Workflow

When a selector fails with element-not-found or timeout errors, never guess selector modifications. Inspect the live accessibility tree directly from the running simulator or device:

```bash
# Dump the complete view hierarchy
maestro hierarchy

# Dump tabular CSV summary
maestro hierarchy --compact
```

### What to Inspect in the Hierarchy Dump

1. **Accessibility Identifiers**: Locate the target element and check whether `id` matches your locator exactly.
2. **Element Visibility and Bounds**: Verify that the element's coordinate frame is inside the visible screen bounds (e.g. `frame: {{x, y}, {w, h}}`).
3. **Accessibility Grouping**: In React Native and native containers, setting `accessible={true}` on a parent view collapses child elements into a single node, hiding individual child IDs.
4. **Active Modals and Overlays**: Transparent scrims or invisible modal backdrops can intercept touch events, preventing taps from reaching underlying buttons.

## Soft Keyboard Race Conditions and Input Focus

The on-screen soft keyboard is a primary source of mobile test flakiness.

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

## Animations, Screen Transitions, and Rendering

Maestro automatically retries locators for up to 7 seconds, but rapid screen transitions or layout animations can cause race conditions.

### 1. Wait for Animations to End
When screens animate in with slide or fade transitions, use `waitForAnimationToEnd` before asserting elements:

```yaml
- tapOn: "Open Details"
- waitForAnimationToEnd
- assertVisible: "Details Header"
```

### 2. Avoid Continuous Background Animations
Continuous looping animations (such as unconstrained pulse effects or looping video banners) can prevent the iOS XCUITest driver from detecting that the application is idle. If tests freeze on iOS cold boot, disable looping animations in your test build or add a brief settle swipe:

```yaml
- launchApp
# Brief swipe to settle cold boot accessibility tree
- swipe:
    direction: DOWN
    duration: 100
```

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
- tapOn:
    id: "item_99"
```

## System Permission Dialogs and Alerts

System permission sheets (Camera, Location, Notifications) appear asynchronously and block interaction with the underlying app.

Handle optional system dialogs cleanly using `optional: true`:

```yaml
# Handle potential permission prompt without failing if absent
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

## Related References

- [Flows and Selectors](../commands/flows-and-selectors.md) — Selector priority and command syntax.
- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Dumping hierarchy and inspecting logs.
- [Expo and State](expo-and-state.md) — State hydration and Keychain token issues.
