# TC-CHT-08: Composer Keyboard Shortcuts (`Shift+Enter` vs `Enter`)

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-08`
- **Purpose:** Verify that pressing `Enter` in the Copilot composer triggers message submission and prevents default newline insertion, while pressing `Shift+Enter` cleanly inserts a newline and auto-expands the composer height up to 190px without dispatching the message.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/08-gherkin-result-case-keyboard-shortcuts-navigation/`

---

## 2. Tester Brief
Standard messaging ergonomics require distinguishing between message transmission and multiline composition.
1. When a user presses plain `Enter` (without `Shift`):
   - `ev.preventDefault()` is invoked.
   - Text is trimmed. If non-empty, `chatLiveSend()` is called.
2. When a user presses `Shift+Enter`:
   - Default browser behavior is preserved (or newline inserted).
   - `chatLiveSend` is NOT called.
   - The textarea expands its height dynamically up to `190px`.
3. Whitespace-only input: Pressing `Enter` on whitespace does not send empty bubbles.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/chat.js` & `assets/radar.js`.
- **Target Elements:** `#chatInput` or `#aiHelpInput`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Composer Keyboard Shortcuts

  Scenario Outline: Differentiating between message submission and multiline prompt expansion
    Given the user has typed text into the chat composer
    When the user triggers a keydown event with key "Enter" and shiftKey set to <ShiftKeyStatus>
    Then the message dispatch status should be <ShouldDispatch>
    And default newline prevention should be <DefaultPrevented>

    Examples:
      | ShiftKeyStatus | ShouldDispatch | DefaultPrevented | Purpose              |
      | false          | true           | true             | Submit prompt        |
      | true           | false          | false            | Insert multiline text|
```

---

## 5. Visual Checks
- **Composer Height:**
  - On `Shift+Enter`, textarea height expands (e.g. from ~40px to ~72px, capped at 190px).
- **Screenshot Points:**
  - `01_multiline_expanded_composer.png` (Textarea expanded over multiple lines).

---

## 6. Data and Network Checks
- **Keyboard Event Inspection:**
  - Plain `Enter`: `ev.key === "Enter" && !ev.shiftKey`.
  - `Shift+Enter`: `ev.key === "Enter" && ev.shiftKey`.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/08-gherkin-result-case-keyboard-shortcuts-navigation/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-keys');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const keyCheck = await js(String.raw`(() => {
  const inp = document.getElementById("chatInput") || document.getElementById("aiHelpInput");
  if (!inp) return { found: false };

  // Test 1: Shift+Enter
  let sentOnShift = false;
  const origSend = window.chatLiveSend;
  window.chatLiveSend = () => { sentOnShift = true; };

  inp.value = "Line 1";
  const shiftEv = new KeyboardEvent("keydown", { key: "Enter", shiftKey: true, bubbles: true, cancelable: true });
  inp.dispatchEvent(shiftEv);

  // Test 2: Plain Enter
  let sentOnPlain = false;
  window.chatLiveSend = () => { sentOnPlain = true; };

  inp.value = "Single line prompt";
  const plainEv = new KeyboardEvent("keydown", { key: "Enter", shiftKey: false, bubbles: true, cancelable: true });
  inp.dispatchEvent(plainEv);

  window.chatLiveSend = origSend;

  return {
    found: true,
    sentOnShift,
    shiftPrevented: shiftEv.defaultPrevented,
    sentOnPlain,
    plainPrevented: plainEv.defaultPrevented
  };
})()`);

cliLog('Keyboard Shortcuts Result: ' + JSON.stringify(keyCheck));
if (keyCheck.sentOnShift || !keyCheck.sentOnPlain || !keyCheck.plainPrevented) {
  throw new Error('Keyboard shortcuts failed Shift+Enter vs Enter behavioral checks');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-keys', { keep: false })`.
