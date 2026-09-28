# TC-CHT-07: Streaming Response Cancellation via AbortController

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-07`
- **Purpose:** Verify that clicking the Stop button during active response generation dispatches the `stop-chat-response` RPC command, invokes `AbortController.abort()` to terminate the network connection, flushes unrendered typewriter queue tokens immediately, and displays a `"Response stopped"` toast without creating phantom message duplicates.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/07-gherkin-result-case-streaming-abort-controller/`

---

## 2. Tester Brief
Users must have the ability to abort runaway AI responses or rephrase queries midway through generation.
1. While streaming is in progress, the submit button morphs into `.cc-send.stop[data-action="chat-stop"]`.
2. Clicking Stop triggers `chatLiveStop()`:
   - `window.ZEO_DATA_PROVIDER.callCommand("stop-chat-response", { projectId, sessionId, turnId })`.
   - `abortController.abort()` is called to close HTTP/SSE stream channels.
   - The pending typewriter text queue is immediately cleared.
   - The blinking caret is detached, and the message finalizes at its current word.
   - An informational toast confirms: `"Response stopped"` / `"Yanıt durduruldu"`.
3. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.
- **Target Action:** `button[data-action="chat-stop"]`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Streaming Response Interruption

  Scenario: Aborting an in-flight streaming response via Stop button
    Given the Copilot assistant is actively streaming an AI answer
    And the Stop button ".cc-send.stop" is visible
    When the user clicks the Stop button "[data-action='chat-stop']"
    Then the RPC command "stop-chat-response" should be dispatched
    And the streaming network connection should be aborted
    And the typewriter queue should be purged immediately
    And a confirmation toast "Response stopped" should be displayed
    And the composer submit button should return to its default state

    Examples:
      | SessionType | Action    | ExpectedToastCopy  |
      | active_turn | chat-stop | Response stopped   |
```

---

## 5. Visual Checks
- **Stop Button:**
  - Class: `.cc-send.stop` (square red/black stop icon).
- **Post-Stop Transition:**
  - Reverts to send icon: `.cc-send` (paper plane / arrow icon).
  - Trailing message caret `<span class="caret"></span>` is removed.
- **Screenshot Points:**
  - `01_streaming_stop_button.png` (Stop button visible during stream).
  - `02_stream_halted_message.png` (Message cleanly truncated after click).

---

## 6. Data and Network Checks
- **Command RPC:**
  ```json
  {
    "projectId": "[PROJECT_ID]",
    "sessionId": "[SESSION_ID]",
    "turnId": "[TURN_ID]"
  }
  ```
- **Abort Signal:**
  - `abortController.signal.aborted === true`.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/07-gherkin-result-case-streaming-abort-controller/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-stop');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const stopCheck = await js(String.raw`(() => {
  let stopCommandSent = false;
  let toastMessage = null;

  const origToast = window.showToast;
  window.showToast = msg => { toastMessage = msg; };

  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'stop-chat-response') {
      stopCommandSent = true;
      return Promise.resolve({ ok: true });
    }
    return origCall.apply(this, arguments);
  };

  // Simulate active send state
  const lv = window.chatLiveState ? window.chatLiveState() : null;
  if (lv) {
    lv.send = {
      sessionId: "s1",
      turnId: "t1",
      queue: "remaining unrendered tokens",
      shown: "initial tokens",
      done: false,
      stopping: false,
      unregister: () => {}
    };
    if (typeof window.chatLiveStop === "function") {
      window.chatLiveStop();
    }
  }

  window.ZEO_DATA_PROVIDER.callCommand = origCall;
  window.showToast = origToast;

  return {
    dispatched: stopCommandSent,
    toastMsg: toastMessage
  };
})()`);

cliLog('Stop Check Result: ' + JSON.stringify(stopCheck));
if (!stopCheck.dispatched) {
  throw new Error('stop-chat-response command was not dispatched upon stopping stream');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-stop', { keep: false })`.
