# Flow YAML Structure and Selector Strategies

Maestro flows are declarative YAML files specifying sequential test steps across mobile (iOS/Android) and web (Chromium) targets. The execution engine handles timing, element settling, and automatic polling without boilerplate sleep statements.

---

## Flow Header and Configuration

A flow begins with an optional configuration block separated from commands by `---`. If a subflow contains no header metadata, the leading `---` can be omitted.

```yaml
appId: com.example.demo         # Target mobile package ID or bundle ID
# Or for web:
# url: https://example.com      # Target web starting URL (CDP/Selenium)
name: "Checkout Smoke Flow"     # Human-readable flow title in reports
tags:
  - smoke
  - checkout
env:
  DEFAULT_USER: "testuser@example.com"
  BASE_URL: "https://api.example.com"
onFlowStart:
  - clearState
  - clearKeychain
onFlowComplete:
  - runFlow: subflows/cleanup.yaml
---
- launchApp
- assertVisible: "Welcome"
```

### Configuration Keys

- **`appId`**: Target application package ID (Android) or bundle identifier (iOS).
  - *iOS Discovery*: Run `xcrun simctl listapps booted` (or for a specific device: `xcrun simctl listapps "$UDID"`). Alternatively inspect `Info.plist` (`CFBundleIdentifier`) or `app.json` (`expo.ios.bundleIdentifier`).
  - *Android Discovery*: Run `adb shell pm list packages -3` (third-party installed apps). Alternatively inspect `app/build.gradle` (`applicationId`) or `app.json` (`expo.android.package`).
- **`url`**: Target starting URL for Web automation via Chromium CDP/Selenium (mutually exclusive with `appId`).
- **`name`**: Human-readable flow name rendered in CLI output and JUnit/HTML reports.
- **`tags`**: List of categorization tags for filtering runs via `--include-tags` or `--exclude-tags`.
- **`env`**: Map of environment variables accessible via `${VAR_NAME}` in commands (CLI `-e` overrides header values).
- **`onFlowStart`**: Sequence of commands executed prior to the main flow. If any start command fails, the flow terminates immediately.
- **`onFlowComplete`**: Sequence executed after the flow finishes, running even if steps failed.
- **`properties`** / **`ext`**: Custom key-value metadata preserved in execution manifests.

---

## Selector Hierarchy and Strategy

Maestro locators find elements within the accessibility tree exposed by XCUITest (iOS), UIAutomator (Android), or Chrome CDP (Web). Always prioritize resilient identifiers over fragile visual coordinates:

| Priority | Selector Type | Resilience | Usage Pattern |
|---|---|---|---|
| 1 | `id` | Highest | Accessibility identifier (`iOS`) or resource ID (`Android`). Immune to text copy changes and translations. |
| 2 | `css` | High (Web) | Standard CSS selector for web elements (e.g. `button.submit`, `#login-btn`). |
| 3 | `text` + Relational | High | Disambiguates duplicate labels by spatial relation (`below`, `above`, `childOf`, `containsChild`). |
| 4 | Visible `text` / Regex | Medium | User-facing copy. **Full-string regex by default** with case insensitivity. |
| 5 | `traits` & State Filters | Medium | Filters elements by trait (`TEXT`, `SQUARE`) or state (`enabled`, `selected`, `checked`, `focused`). |
| 6 | `index` | Low | Zero-based screen order index (sorted top-to-bottom, left-to-right). |
| 7 | `point` / `relativePoint` | Lowest | Fractional or percentage coordinate (`"50%,80%"`). Breaks across varying aspect ratios. |

### Critical Selector Semantics & Rules

1. **Full-String Regex Matching on `text:`**:
   Maestro evaluates `text:` as a **full-string regex match with case insensitivity (`IGNORE_CASE`)**.
   - `text: "Log In"` will **FAIL** on `"Log In to your Account"`.
   - To match substrings or partial text, **always use regex wildcards**: `text: ".*Log In.*"`.
   - Maestro normalizes embedded newline characters (`\n`) to single spaces (` `) before matching.
2. **Text Resolution Priority**:
   When resolving `text: "..."`, Maestro checks attributes in this order:
   1. `text` (Android text attribute or iOS `value`/`label`)
   2. `hintText` (placeholder / hint text)
   3. `accessibilityText` (`content-description` on Android, accessibility text on iOS)
   4. `error` (input field error validation message)
3. **Android Resource ID Splitting**:
   Matching `id: "btn_submit"` matches both short name `btn_submit` and fully-qualified `com.example.app:id/btn_submit`.
4. **Invalid Selector Keys (2.11.0 Rule)**:
   Do **not** place `start:` or `end:` inside element selectors (e.g. `tapOn: { start: ... }`). Those keys belong strictly to `swipe:`.

### Selector Property Inventory

```yaml
- tapOn:
    id: "resource_or_accessibility_id"
    text: ".*Regex Text.*"            # Full-string regex with IGNORE_CASE
    label: "Accessibility Label"
    css: "button.submit"              # Web automation CSS selector
    traits: TEXT                      # Trait filter: TEXT, SQUARE, LONG_TEXT
    width: 100                        # Dimension matching (px)
    height: 50
    tolerance: 10                     # Dimension tolerance (+/- px)
    enabled: true                     # State filter: enabled/disabled
    selected: true                    # State filter: selected/unselected
    checked: true                     # State filter: checked/unchecked
    focused: true                     # State filter: focused/unfocused
    below: "Anchor Heading"           # Spatial relation: below anchor
    above: "Anchor Footer"            # Spatial relation: above anchor
    leftOf: "Right Button"            # Spatial relation: left of anchor
    rightOf: "Left Button"            # Spatial relation: right of anchor
    childOf:                          # Hierarchical parent anchor
      id: "card_container"
    containsChild:                    # Direct child selector
      text: "Item Title"
    containsDescendants:              # All descendant selectors must match
      - text: "Price: $10"
      - id: "buy_icon"
    index: 0                          # 0-based coordinate index
    relativePoint: "90%,10%"          # Relative tap offset inside element
    retryTapIfNoChange: true          # Auto-retries tap if view hierarchy did not change
    waitUntilVisible: true            # Waits for element to appear before tapping
    waitToSettleTimeoutMs: 2000       # Wait for element to settle after scrolling
    optional: true                    # Skips command without failing if element absent
```

---

## Comprehensive Command Inventory

### 1. Interaction Commands

- **`tapOn`**: Taps matching element, coordinate point, or text:
  ```yaml
  - tapOn: "Log In"
  - tapOn:
      id: "submit_button"
      retryTapIfNoChange: true
  - tapOn:
      point: "50%,80%"
      repeat: 2
      delay: 200
  ```
- **`doubleTapOn`** / **`longPressOn`**: Double-tap or press-and-hold gestures on elements or points.
- **`inputText: "string"`**: Types text into the currently focused field:
  ```yaml
  - inputText: "user@example.com"
  - inputText: ${output.generatedEmail}
  ```
- **`eraseText: N`**: Deletes `N` characters (or clears entire field if count omitted).
- **`hideKeyboard`**: Dismisses soft keyboard (`hideKeyboard: { optional: true }` avoids failing if keyboard is not displayed).
- **`pressKey: KeyCode`**: Emits hardware key event. Supported values:
  - Common: `ENTER`, `BACKSPACE`, `BACK`, `HOME`, `ESCAPE`, `TAB`, `POWER`, `LOCK`, `VOLUME_UP`, `VOLUME_DOWN`
  - Android TV / Media: `REMOTE_UP`, `REMOTE_DOWN`, `REMOTE_LEFT`, `REMOTE_RIGHT`, `REMOTE_CENTER`, `REMOTE_PLAY_PAUSE`, `REMOTE_STOP`, `REMOTE_NEXT`, `REMOTE_PREVIOUS`, `REMOTE_REWIND`, `REMOTE_FAST_FORWARD`, `REMOTE_MENU`, `TV_INPUT`
- **`back`**: Dispatches platform back navigation (Android back button event or iOS navigation swipe).
- **`copyTextFrom` & `pasteText`**: Extracts text from element into clipboard and updates `maestro.copiedText`, then pastes into focused field:
  ```yaml
  - copyTextFrom:
      id: "otp_code"
  - tapOn:
      id: "otp_input"
  - pasteText
  ```
- **`setClipboard: "string"`**: Directly populates device clipboard and sets `maestro.copiedText`.

### 2. Navigation, Scrolling & Gestures

- **`scroll`**: Standard vertical downward scroll gesture.
- **`scrollUntilVisible`**: Continuously scrolls a scrollable container until the target element appears:
  ```yaml
  - scrollUntilVisible:
      element:
        id: "terms_and_conditions"
      direction: DOWN               # Direction: DOWN, UP, LEFT, RIGHT
      timeout: 15000                # Timeout in ms (default 15000)
      speed: 40                     # Scroll fling speed percentage (0-100)
      visibilityPercentage: 100     # Required percentage visible (0-100)
      centerElement: true           # Centers target element in viewport
  ```
- **`swipe`**: Performs gesture in 4 modes:
  ```yaml
  # 1. Directional
  - swipe:
      direction: LEFT
      duration: 400

  # 2. Element-anchored
  - swipe:
      from:
        id: "carousel_card"
      direction: UP

  # 3. Coordinate percentage
  - swipe:
      start: "50%,80%"
      end: "50%,20%"
      duration: 350
  ```

### 3. Synthetic Random Data Input Commands

Generate and type realistic test data natively without external scripts:

```yaml
- inputRandomText: { length: 12 }    # Types random alphanumeric string
- inputRandomNumber: { length: 6 }   # Types random numeric digits (e.g. OTP)
- inputRandomEmail                   # Types realistic synthetic email
- inputRandomPersonName              # Types full person name
- inputRandomCityName                # Types realistic city name
- inputRandomCountryName             # Types country name
- inputRandomColorName               # Types color string
```

### 4. Device Control, Environment & Application State

- **`launchApp`**: Launches application with clean state, keychain, permissions, and extra arguments:
  ```yaml
  - launchApp:
      appId: com.example.demo
      clearState: true              # Wipes app storage / cache
      clearKeychain: true           # Wipes iOS Keychain
      stopApp: true                 # Terminates existing instance before launch
      permissions:
        all: allow
        notifications: allow
        camera: deny
        location: in-use            # Options: allow, deny, unset, in-use, always
      arguments:
        test_mode: "mock"
  ```
- **`stopApp` & `killApp`**:
  - `stopApp`: Graceful background termination.
  - `killApp`: Immediate SIGKILL process termination.
- **`clearState` & `clearKeychain`**: Standalone state purge commands.
- **`setPermissions`**: Modifies runtime permissions dynamically during test execution:
  ```yaml
  - setPermissions:
      appId: com.example.demo
      permissions:
        location: always
        notifications: allow
  ```
- **`setLocation` & `travel`**:
  ```yaml
  - setLocation:
      latitude: "37.7749"
      longitude: "-122.4194"

  - travel:
      points:
        - "37.7749,-122.4194"
        - "37.7752,-122.4178"
      speed: 15.0                   # Meters per second
  ```
- **`setOrientation`**: Rotates display (`PORTRAIT`, `LANDSCAPE_LEFT`, `LANDSCAPE_RIGHT`, `UPSIDE_DOWN`).
- **`setDarkMode` & `toggleDarkMode`**:
  ```yaml
  - setDarkMode: enabled            # Strictly lowercase 'enabled' or 'disabled'
  - toggleDarkMode
  ```
- **`setAirplaneMode` & `toggleAirplaneMode`**:
  ```yaml
  - setAirplaneMode: enabled        # Strictly lowercase 'enabled' or 'disabled'
  - toggleAirplaneMode
  ```
- **`addMedia`**: Pushes image or video files from host into simulator/emulator gallery:
  ```yaml
  - addMedia:
      - fixtures/avatar.jpg
      - fixtures/receipt.png
  ```
- **`openLink`**: Opens standard URLs, deep links, or app schemes in browser or app:
  ```yaml
  # Simple deep link
  - openLink: "myapp://order/12345"

  # Open URL in external browser with optional auto-verification
  - openLink:
      link: "https://example.com/verify"
      browser: true                 # Opens in external browser rather than app
      autoVerify: true              # Handles Android App Links / iOS Universal Links verification
  ```

### 5. Media & Telemetry Capture

- **`takeScreenshot: <path>`**: Captures viewport image saved relative to `--test-output-dir` or current directory.
- **`startRecording: <path>` & `stopRecording`**: Renders full MP4 video of flow execution.

### 6. Synchronization Primitives

Avoid arbitrary sleep statements. Use built-in synchronization:

```yaml
# Wait for animations and layout reflows to settle
- waitForAnimationToEnd:
    timeout: 5000

# Wait up to custom timeout for appearance or disappearance
- extendedWaitUntil:
    visible:
      id: "payment_complete_banner"
    timeout: 15000

- extendedWaitUntil:
    notVisible:
      id: "loading_spinner"
    timeout: 20000
```

### 7. Assertions Reference

- **`assertVisible` & `assertNotVisible`**: Polls for element presence or absence (default poll timeout ~7000ms).
- **`assertTrue: ${expression}`**: Evaluates JavaScript boolean expression; fails if false, null, or undefined:
  ```yaml
  - assertTrue: ${output.status === 200}
  - assertTrue: ${output.items.length > 0}
  ```
- **`assertScreenshot`**: Visual regression pixel comparison against baseline image:
  ```yaml
  - assertScreenshot:
      path: baselines/home_screen.png
      thresholdPercentage: 0.5%
      cropOn:
        id: "hero_banner"
  ```
- **`assertDarkMode` & `assertLightMode`**: Asserts device appearance mode.

#### AI-Powered Multimodal Assertions

Maestro 2.x supports multimodal vision models for semantic visual verification without accessibility locators:

- **`assertWithAI`**: Natural language visual check:
  ```yaml
  - assertWithAI: "The shopping cart contains 3 distinct items and total matches $45.00"
  ```
- **`assertNoDefectsWithAI`**: Automatically checks for overlapping text, broken image icons, or clipped layout defects:
  ```yaml
  - assertNoDefectsWithAI
  ```
- **`extractTextWithAI`**: Extracts unstructured visual text from screen and assigns it to an environment variable:
  ```yaml
  - extractTextWithAI:
      query: "Extract the 6-digit confirmation code"
      outputVariable: CONFIRMATION_CODE
  - inputText: ${CONFIRMATION_CODE}
  ```

---

## Flow Control, Loops & Conditional Execution

### 1. Conditional Execution (`runFlow: when:`)

Universal branching primitive supporting platform, visibility, and JS expressions:

```yaml
# Platform-specific subflow
- runFlow:
    when:
      platform: Android            # Values: Android, iOS, Web
    file: subflows/android_setup.yaml

# Conditional on element visibility
- runFlow:
    when:
      visible: "Rate our App"
    commands:
      - tapOn: "Not Now"

# Conditional on JavaScript expression
- runFlow:
    when:
      true: ${output.hasPromoCode === true}
    commands:
      - tapOn: "Apply Promo"
```

### 2. Loops (`repeat: times:` & `repeat: while:`)

```yaml
# Fixed iteration count
- repeat:
    times: 5                       # Accepts integer or ${expression}
    commands:
      - swipe:
          direction: LEFT

# While condition remains true
- repeat:
    while:
      visible: "Load More"
    commands:
      - tapOn: "Load More"
```

### 3. Bounded Retries (`retry: maxRetries:`)

Retries a sequence of commands up to `maxRetries` times if an assertion or step within fails:

```yaml
- retry:
    maxRetries: 3
    commands:
      - tapOn: "Refresh Feed"
      - assertVisible: "Latest News"
```

### 4. Scripts & Scoped Variables

- **`defineVariables`**: Defines scoped flow variables inline:
  ```yaml
  - defineVariables:
      BASE_URL: "https://staging.example.com"
  ```
- **`evalScript`**: Evaluates single JavaScript expression inline:
  ```yaml
  - evalScript: ${output.timestamp = Date.now()}
  ```
- **`runScript`**: Executes modular `.js` files located relative to calling flow:
  ```yaml
  - runScript:
      file: scripts/auth.js
      env:
        ROLE: "admin"
  ```

---

## Related References

- [CLI and Artifacts](cli-and-artifacts.md) — Running tests and dumping hierarchy.
- [GraalJS Scripting](../guides/graaljs.md) — JavaScript execution, HTTP helper, and faker.
- [Mobile Flakiness](../troubleshooting/mobile-flakiness.md) — Fixing selector failures and keyboard races.
