# Flow YAML Structure and Selector Strategies

Maestro flows are declarative YAML files specifying sequential test steps. The execution engine handles timing, element settling, and automatic retries without boilerplate sleep statements.

## Flow Header and Configuration

A flow begins with an optional configuration block separated from commands by `---`:

```yaml
appId: com.example.demo
env:
  DEFAULT_USER: "testuser@example.com"
  BASE_URL: "https://api.example.com"
tags:
  - smoke
  - checkout
onFlowStart:
  - clearState
onFlowComplete:
  - runFlow: subflows/cleanup.yaml
---
- launchApp
- assertVisible: "Welcome"
```

### Configuration Keys

- **`appId`**: Target application package ID (Android) or bundle identifier (iOS).
  - *iOS Discovery*: Run `xcrun simctl listapps booted` (or for a specific device: `xcrun simctl listapps "$UDID"`). Alternatively inspect `Info.plist` (`CFBundleIdentifier`) or `app.json` (`expo.ios.bundleIdentifier`).
  - *Android Discovery*: Run `adb shell pm list packages` or `adb shell pm list packages -3` (third-party installed apps). Alternatively inspect `app/build.gradle` (`applicationId`) or `app.json` (`expo.android.package`).
- **`env`**: Map of environment variables accessible via `${VAR_NAME}` in commands.
- **`tags`**: List of categorization tags for filtering runs via `--include-tags` or `--exclude-tags`.
- **`onFlowStart`**: Sequence of commands executed prior to the main flow. If a start hook fails, the main flow is skipped.
- **`onFlowComplete`**: Sequence executed after the flow finishes, running even if steps failed.

## Selector Hierarchy and Strategy

Maestro locators find elements within the accessibility tree. Always prioritize stable selectors over fragile visual coordinates:

| Priority | Selector Type | Resilience | Usage Pattern |
|---|---|---|---|
| 1 | `id` | Highest | Accessibility identifier (`iOS`) or resource ID (`Android`). Immune to text copy changes and translations. |
| 2 | `text` + Relational | High | Disambiguates duplicate labels by spatial relation (`below`, `above`, `childOf`). |
| 3 | Visible `text` / Regex | Medium | Human-readable user-facing copy. Vulnerable to i18n and marketing copy changes. |
| 4 | State Filters | Medium | Filters elements by runtime state (`enabled`, `selected`, `checked`, `focused`). |
| 5 | `index` | Low | Zero-based screen order index. Fragile if lists or cards reorder. |
| 6 | `point` | Lowest | Percentage coordinate (`"50%,80%"`). Breaks across varying aspect ratios. |

### Selector Examples

#### 1. ID Selectors (Recommended)

```yaml
- tapOn:
    id: "submit_order_button"
```

#### 2. Relational Selectors

Disambiguate matching elements using spatial relationships:

```yaml
# Tap button located below a specific heading
- tapOn:
    text: "Add to Cart"
    below: "Product Details"

# Tap action button inside a specific list card
- tapOn:
    text: "Delete"
    childOf:
      id: "cart_item_card"

# Target a card containing specific descendant text
- tapOn:
    containsChild: "Order #1042"
```

#### 3. Regular Expression Matching

Use regular expressions for dynamic or partially matched strings:

```yaml
- assertVisible: ".*Order confirmed.*"
- tapOn: "Welcome, .*"
```

#### 4. Element State Modifiers

Combine element identity with state checks:

```yaml
# Tap button only when active
- tapOn:
    id: "checkout_button"
    enabled: true

# Assert checkbox is checked
- assertVisible:
    id: "terms_checkbox"
    checked: true

# Wait for input field to gain focus
- extendedWaitUntil:
    visible:
      id: "email_input"
      focused: true
    timeout: 5000
```

## Core Command Inventory

### Interaction Commands

- **`tapOn`**: Taps matching element or point. Supports `optional: true` to avoid failing if element is missing.
- **`doubleTapOn`** / **`longPressOn`**: Double-tap or long-press interactions.
- **`inputText: "string"`**: Types text into the currently focused text field.
- **`eraseText: N`**: Deletes `N` characters from active field (or clears all if count omitted).
- **`hideKeyboard`**: Dismisses soft keyboard (`optional: true` prevents error if keyboard is not up).
- **`pressKey: Key`**: Emits hardware key event (`Enter`, `Backspace`, `Home`, `Lock`).
- **`back`**: Triggers back navigation (Android back button or iOS navigation gesture).
- **`openLink: "scheme://path"`**: Opens a deep link or URL in the device.

### Navigation and Scrolling

- **`scroll`**: Performs a standard vertical scroll downward.
- **`scrollUntilVisible`**: Continuously scrolls a container until the target element appears:

```yaml
- scrollUntilVisible:
    element:
      id: "footer_legal_notice"
    direction: DOWN
    timeout: 10000
```

- **`swipe`**: Performs gesture across coordinates or directions (`UP`, `DOWN`, `LEFT`, `RIGHT`).

### Media and Telemetry Commands

Capture visual and video evidence during test execution:

- **`takeScreenshot: <path>`**: Captures an immediate screen image and saves it to `<path>.png` (relative to current working directory or `--test-output-dir`).
- **`startRecording: <path>`**: Starts continuous video recording of the device screen to `<path>.mp4`.
- **`stopRecording`**: Stops the active video recording and finalizes the output file.

```yaml
# Capture screenshot at key milestone or before sensitive action
- takeScreenshot: artifacts/home_screen

# Record critical user journey
- startRecording: artifacts/checkout_flow
- tapOn: "Checkout"
- assertVisible: "Payment Method"
- stopRecording
```

### Assertions

- **`assertVisible`**: Asserts element is visible. Automatically polls for up to 7 seconds before failing.
- **`assertNotVisible`**: Asserts element is absent or dismissed from view.
- **`assertTrue: ${expression}`**: Evaluates JavaScript boolean expression; fails if false.

### Waiting and Timing

Avoid arbitrary sleep statements. Use built-in synchronization primitives:

```yaml
# Wait for animation transitions to settle
- waitForAnimationToEnd

# Wait up to custom timeout for slow network or state changes
- extendedWaitUntil:
    visible:
      id: "payment_success_banner"
    timeout: 15000
```

### Flow Composition and Scripts

- **`runFlow`**: Invokes subflows with parameter passing:

```yaml
- runFlow:
    file: subflows/login.yaml
    env:
      USERNAME: "user@example.com"
```

- **`runScript`**: Executes synchronous GraalJS logic from external `.js` files.

## Related References

- [CLI and Artifacts](cli-and-artifacts.md) — Running tests and dumping hierarchy.
- [GraalJS Scripting](../guides/graaljs.md) — JavaScript execution and variable interpolation.
- [Mobile Flakiness](../troubleshooting/mobile-flakiness.md) — Fixing selector failures and keyboard races.
