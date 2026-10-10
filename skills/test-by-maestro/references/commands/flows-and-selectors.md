# Flow YAML Structure and Selector Strategies

Maestro flows are declarative YAML files specifying sequential test steps across mobile (iOS/Android) and web (Chromium) targets. The engine handles timing, element settling, and polling without boilerplate sleep statements.

Verified against Maestro `2.11.0` source (`maestro-orchestra` YAML classes) and `docs.maestro.dev`. Run `maestro check-syntax` for structure, but remember it does **not** catch everything `runFlow` rejects (see the header rule below).

---

## Flow Header and Configuration

**Every flow file, including subflows loaded by `runFlow`, must start with a configuration section** containing `appId` (mobile) or `url` (web), followed by `---`. A file that begins directly with `- tapOn: ...` fails at run time with `Config Section Required` (and a header holding only `name:` fails with `Config Field Required`) even though `maestro check-syntax` accepts the bare command list.

```yaml
appId: com.example.demo         # Target mobile package ID or bundle ID
# Or for web:
# url: https://example.com      # Target web starting URL
name: "Checkout Smoke Flow"     # Human-readable flow title in reports
tags:
  - smoke
  - checkout
env:
  DEFAULT_USER: "testuser@example.com"
  BASE_URL: ${BASE_URL || "https://api.example.com"}   # overridable with -e BASE_URL=...
onFlowStart:
  - clearState
  - clearKeychain
onFlowComplete:
  - runFlow: ../subflows/cleanup.yaml
---
- launchApp
- assertVisible: "Welcome"
```

### Configuration Keys

- **`appId`**: Android package ID or iOS bundle identifier.
  - *iOS discovery*: `xcrun simctl listapps booted`, or `CFBundleIdentifier` in `Info.plist`, or `expo.ios.bundleIdentifier` in `app.json`.
  - *Android discovery*: `adb shell pm list packages -3`, or `applicationId` in `app/build.gradle`, or `expo.android.package`.
- **`url`**: Starting URL for Web flows. May coexist with `appId` (then `url` wins); it is an error only when both are missing.
- **`name`**: Flow name in CLI output and reports; also the key used by `executionOrder.flowsOrder` (falls back to the file name without extension when absent).
- **`tags`**: Categories for `--include-tags` / `--exclude-tags`.
- **`env`**: String variables available as `${VAR}`. A plain header value **wins over** CLI `-e`; use the `KEY: ${KEY || "default"}` idiom to let `-e` override.
- **`onFlowStart`**: Commands before the body. If one fails, the body is skipped but `onFlowComplete` still runs.
- **`onFlowComplete`**: Commands after the flow; a failure here fails the flow.
- **`properties`**: String map emitted as `<property>` elements on the JUnit `<testcase>` (`junitId` and `junitClassname` are reserved). Unknown header keys are collected silently in a catch-all `ext` and have no documented effect.

---

## Selector Hierarchy and Strategy

Maestro locators query the accessibility tree exposed by XCUITest (iOS), UIAutomator (Android), or Chrome (Web). Prefer resilient identifiers over coordinates:

| Priority | Selector Type | Resilience | Usage Pattern |
|---|---|---|---|
| 1 | `id` | Highest | `accessibilityIdentifier` (iOS) / resource ID (Android). Immune to copy changes and translations. Also a regex. |
| 2 | `css` | High (Web only) | CSS selector, e.g. `button.submit`. |
| 3 | `text` + relational | High | Disambiguate duplicates with `below`, `above`, `leftOf`, `rightOf`, `childOf`, `containsChild`. |
| 4 | Visible `text` / regex | Medium | User-facing copy. **Full-string regex, case-insensitive.** |
| 5 | `traits` and state filters | Medium | `traits` (`TEXT`, `SQUARE`, `LONG_TEXT`) or `enabled`/`selected`/`checked`/`focused`. |
| 6 | `index` | Low | 0-based (top-to-bottom, then left-to-right); a negative index counts from the end. |
| 7 | `point` | Lowest | `"50%,80%"` or absolute `"100,200"`; combined with a selector it is relative to that element. |

### Critical Selector Semantics

1. **`text:` is a full-string regex with `IGNORE_CASE`** (also `DOT_MATCHES_ALL`/`MULTILINE`; a literal equal string also matches).
   - `text: "Log In"` fails on `"Log In to your Account"`; use `text: ".*Log In.*"`.
   - Escape regex metacharacters (`$ [ ( .`) in literal copy, e.g. `"Price: \\$10"`.
   - Embedded newlines are retried with spaces.
2. **What `text:` matches**: an element matches if **any** of its `text`, `hintText`, `accessibilityText`, or `error` (Android) values matches (a union; there is no priority order). On iOS, `text` includes the `accessibilityLabel`.
3. **Android `id:`** matches the short name `btn_submit` and the qualified `com.example.app:id/btn_submit`.
4. **`start:` / `end:` are rejected in element selectors** since 2.11.0 (`tapOn: {start: ...}`); they belong to `swipe:` only.
5. **`label:` is not a matcher.** It renames the command in console output and reports (useful for masking secrets), on any command.

### Selector Property Inventory

```yaml
- tapOn:
    id: "resource_or_accessibility_id"
    text: ".*Regex Text.*"            # Full-string regex, IGNORE_CASE
    css: "button.submit"              # Web only
    traits: TEXT                      # TEXT, SQUARE, LONG_TEXT
    width: 100                        # Dimension match (px)
    height: 50
    tolerance: 10                     # +/- px for width/height
    enabled: true                     # State filters
    selected: true
    checked: true
    focused: true
    below: "Anchor Heading"           # Spatial relations (selector or text)
    above: "Anchor Footer"
    leftOf: "Right Button"
    rightOf: "Left Button"
    childOf:
      id: "card_container"
    containsChild:
      text: "Item Title"
    containsDescendants:
      - text: "Price: \\$10"
      - id: "buy_icon"
    index: 0
    point: "90%,10%"                  # Tap offset inside the matched element
    retryTapIfNoChange: true          # Re-tap if the hierarchy did not change
    waitToSettleTimeoutMs: 2000       # Best-effort cap (max 30000) on settling before the next command
    label: "Tap the pay button"       # Report label, not a selector
    optional: true                    # Do not fail if the element is absent
```

`waitUntilVisible: true` exists in source but is undocumented: after the tap, if the hierarchy did not change and the element is not visible, Maestro waits up to ~10 s and re-taps. `tapOn` already waits for the element to exist.

---

## Command Inventory

Commands with platform limits are marked. Unsupported commands often "pass" without effect, which gives a false green.

### 1. Interaction Commands

- **`tapOn`**: element, text, or coordinate.
  ```yaml
  - tapOn: "Log In"
  - tapOn:
      id: "submit_button"
      retryTapIfNoChange: true
  - tapOn:
      point: "50%,80%"
      repeat: 2
      delay: 200                    # ms between repeats (default 100)
  ```
- **`doubleTapOn`** / **`longPressOn`**: same selectors; `doubleTapOn` accepts `delay`.
- **`inputText: "string"`**: types into the focused field (tap the field first). Also `inputRandomText`/`inputRandomNumber` (take `length`), `inputRandomEmail`, `inputRandomPersonName`, `inputRandomCityName`, `inputRandomCountryName`, `inputRandomColorName`.
- **`eraseText: N`**: deletes up to `N` characters; **omitted = 50 characters** (documented max 100). For longer fields, repeat the step or pass an explicit count.
- **`hideKeyboard`**: fails only if the keyboard is **still visible** after the attempt, never because it was absent. `optional: true` downgrades that failure to a warning. On Android it always sends the Back key (like `back`), even with no keyboard, which can navigate away. On web it is a no-op.
- **`pressKey: <name>`**: names are the **descriptions**, case-insensitive, with spaces. Underscored enum names are rejected (`Unknown key name`).
  - Single word: `Enter`, `Backspace`, `Back`, `Home`, `Lock`, `Escape`, `Power`, `Tab` (`Back`, `Power`, `Tab` are Android-only per docs).
  - Volume: `Volume Up`, `Volume Down`.
  - TV remote: `Remote Dpad Up|Down|Left|Right|Center`, `Remote Media Play Pause|Stop|Next|Previous|Rewind|Fast Forward`, `Remote System Navigation Up|Down`, `Remote Button A|B`, `Remote Menu`, `TV Input`, `TV Input HDMI 1|2|3`.
- **`back`**: Android and Web only. **On iOS it is a no-op** (no edge swipe is emitted); use a visible Back button selector or a swipe.
- **`copyTextFrom` / `pasteText` / `setClipboard`**: these use Maestro's **in-memory** `maestro.copiedText`, not the device clipboard. `pasteText` types `copiedText` into the focused field.
  ```yaml
  - copyTextFrom:
      id: "otp_code"
  - tapOn:
      id: "otp_input"
  - pasteText
  ```

### 2. Navigation, Scrolling and Gestures

- **`scroll`**: vertical downward scroll.
- **`scrollUntilVisible`**: swipes from the screen center toward the edge until the element appears. It is **not** container-aware (it can miss bottom sheets or nested scroll views).
  ```yaml
  - scrollUntilVisible:
      element:
        id: "terms_and_conditions"
      direction: DOWN               # DOWN, UP, LEFT, RIGHT
      timeout: 20000                # default 20000 ms
      speed: 40                     # 0-100, default 40
      visibilityPercentage: 100
      centerElement: true           # keep scrolling until the element is >30% away from the viewport edge (a few attempts)
  ```
- **`swipe`**: four forms; default `duration` 400 ms.
  ```yaml
  - swipe: { direction: LEFT, duration: 400 }            # 1. direction
  - swipe: { from: { id: "carousel_card" }, direction: UP }   # 2. anchored to an element (optional `point`)
  - swipe: { start: "50%,80%", end: "50%,20%" }          # 3. relative percentages
  - swipe: { start: "200,1600", end: "200,400" }         # 4. absolute pixels
  ```

### 3. Device Control, Environment and App State

- **`launchApp`**:
  ```yaml
  - launchApp:
      appId: com.example.demo
      clearState: true              # wipes app storage
      clearKeychain: true           # iOS: wipes the ENTIRE simulator keychain
      stopApp: true                 # default true; false brings a backgrounded app forward
      permissions:                  # omitted block = all permissions allowed
        all: allow
        notifications: allow
        camera: deny
      arguments:
        test_mode: "mock"           # string/bool/int/double
  ```
  Permission values: `allow`, `deny`, `unset` work on both platforms. `always`, `inuse`, `never` (location) and `photos: limited` are **iOS only**; on Android any other value silently **revokes** the permission. For cross-platform flows branch: `location: ${maestro.platform == "android" ? "allow" : "always"}`.
- **`stopApp`**: force-stops the app (`am force-stop` on Android).
- **`killApp`**: Android only, `am kill` (system-style process death for a *backgrounded* app); an alias of `stopApp` on iOS; no effect on Web.
- **`clearState`**, **`clearKeychain`** (iOS): standalone purge commands.
- **`setPermissions`**: `allow`/`deny` are the documented values; `always` and similar iOS-only values revoke on Android.
  ```yaml
  - setPermissions:
      appId: com.example.demo
      permissions:
        notifications: allow
  ```
- **`setLocation`** / **`travel`**:
  ```yaml
  - setLocation: { latitude: "37.7749", longitude: "-122.4194" }
  - travel:
      points: ["37.7749,-122.4194", "37.7752,-122.4178"]
      speed: 15.0                   # meters per second
  ```
- **`setOrientation`**: `PORTRAIT`, `LANDSCAPE_LEFT`, `LANDSCAPE_RIGHT`, `UPSIDE_DOWN` (not Web).
- **`setDarkMode: enabled|disabled`**, **`toggleDarkMode`**, **`assertDarkMode`**, **`assertLightMode`** (2.9.0+).
- **`setAirplaneMode: enabled|disabled`**, **`toggleAirplaneMode`**: **Android only**; on iOS and Web the command passes with no effect.
- **`addMedia`**: PNG, JPEG, JPG, GIF, MP4; paths relative to the flow.
  ```yaml
  - addMedia:
      - fixtures/avatar.jpg
  ```
- **`openLink`**:
  ```yaml
  - openLink: "myapp://order/12345"
  - openLink:
      link: "https://example.com/verify"
      browser: true                 # Android only: force Google Chrome
      autoVerify: true              # Android only: skip the app-chooser dialog
  ```

### 4. Media Capture

- **`takeScreenshot: <path>`**: written to `<flow artifact bundle>/takeScreenshot/<path>.png` (`.png` is appended; with no bundle, relative to the current directory). `artifacts/checkout` therefore lands in `<test-output-dir>/<session>/<flow>/takeScreenshot/artifacts/checkout.png`. `cropOn` is supported. An undefined variable in the path silently becomes `undefined.png`.
- **`startRecording: <path>`** / **`stopRecording`**: records only between the two commands to `<bundle>/startRecording/<path>.mp4`; `stopRecording` is required to finalize the file.

### 5. Synchronization

```yaml
- waitForAnimationToEnd:
    timeout: 5000
- extendedWaitUntil:
    visible:
      id: "payment_complete_banner"
    timeout: 15000
- extendedWaitUntil:
    notVisible:
      id: "loading_spinner"
    timeout: 20000
```

### 6. Assertions

- **`assertVisible`** / **`assertNotVisible`**: poll for the element. Docs say 7 s; source uses 17 s for non-optional lookups and 7 s for optional ones.
- **`assertTrue: ${expression}`**: JavaScript truthiness; `false`, `0`, `""`, `null`, `undefined`, `NaN` all fail.
- **`assertScreenshot`**: baseline comparison; `thresholdPercentage` is a number 0-100 (default 95). The baseline is found next to the flow first, then under `<artifacts>/takeScreenshot/`.
  ```yaml
  - assertScreenshot:
      path: baselines/home_screen.png
      thresholdPercentage: 98
      cropOn:
        id: "hero_banner"
  ```

#### AI Commands (experimental)

`assertWithAI`, `assertNoDefectsWithAI`, and `extractTextWithAI` need a Maestro Cloud login (`maestro login` or `MAESTRO_CLOUD_API_KEY`) because screenshots are analysed by Maestro's backend. **They default to `optional: true`, so a failed AI assertion does not fail the run** unless you write `optional: false`; a failed `extractTextWithAI` leaves the variable unset and the flow continues.

```yaml
- assertWithAI:
    assertion: "The cart shows 3 items"
    optional: false
- assertNoDefectsWithAI:             # flags text that is cut off, overlapping, or not centered
    optional: false
- extractTextWithAI:
    query: "The 6-digit confirmation code"
    outputVariable: CONFIRMATION_CODE   # default variable name is aiOutput
- inputText: ${CONFIRMATION_CODE}
```

---

## Flow Control, Loops and Conditions

### 1. `runFlow`

Takes exactly one of `file` or `commands`, plus optional `when`, `env`, `label`, `optional`. Paths are relative to the declaring flow. The target file needs its own `appId` header and may declare its own `env`, `onFlowStart`, and `onFlowComplete`, which run inside the subflow.

```yaml
- runFlow:
    file: ../subflows/login-user.yaml
    env:
      USER_EMAIL: ${ADMIN_EMAIL}

- runFlow:
    when:
      platform: Android              # Android, iOS, Web (case-insensitive)
    commands:
      - tapOn: "Not Now"

- runFlow:
    when:
      visible: "Rate our App"
    file: ../subflows/dismiss-rating.yaml

- runFlow:
    when:
      true: ${output.hasPromoCode === true}
    commands:
      - tapOn: "Apply Promo"
```

### 2. Loops

```yaml
- repeat:
    times: 5                         # integer or ${expression}
    commands:
      - swipe: { direction: LEFT }

- repeat:
    while:
      visible: "Load More"
    commands:
      - tapOn: "Load More"
```

`times` and `while` may be combined; with neither, `times` is effectively unbounded.

### 3. Bounded Retries

`maxRetries` is capped at 3 (default 1); `maxRetries: 2` means up to 3 attempts. Only Maestro command failures are retried, and retry also accepts `file`/`env`. Retries can hide real flakiness; do not use them to paper over bad selectors.

```yaml
- retry:
    maxRetries: 2
    commands:
      - tapOn: "Refresh Feed"
      - assertVisible: "Latest News"
```

### 4. Scripts and Variables

There is **no `defineVariables` YAML command**. Set variables with the header `env:`, `runFlow.env`, `runScript.env`, or `evalScript`:

```yaml
- evalScript: ${output.timestamp = Date.now()}
- runScript:
    file: scripts/auth.js            # relative to this flow
    env:
      ROLE: "admin"
```

Built-in variables: `MAESTRO_FILENAME` (file stem, no extension), `MAESTRO_DEVICE_UDID`, `MAESTRO_SHARD_ID`/`MAESTRO_SHARD_INDEX` when sharding, and any `MAESTRO_*` shell variable. All env values are strings.

### 5. Labels and Optional Steps

Every command accepts `label:` (shown in console and reports; use it to mask secrets) and `optional: true`.

---

## Related References

- [CLI and Artifacts](cli-and-artifacts.md) — Running tests and dumping hierarchy.
- [GraalJS Scripting](../guides/graaljs.md) — JavaScript execution, HTTP helper, and faker.
- [Mobile Flakiness](../troubleshooting/mobile-flakiness.md) — Fixing selector failures and keyboard races.
