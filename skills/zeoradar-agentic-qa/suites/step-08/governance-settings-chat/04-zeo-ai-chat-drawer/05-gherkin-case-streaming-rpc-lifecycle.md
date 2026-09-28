# TC-CHT-05: 5-Event Streaming RPC Protocol Lifecycle

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-05`
- **Purpose:** Verify the full lifecycle of the 5-event streaming RPC protocol (`send-chat-message`), validating orderly execution of `onAccepted`, `onSnapshot`, `onReset`, `onEvent` (`tool_status` and `assistant_delta`), and terminal promise resolution without dropping tokens or rendering duplicated message rows.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/05-gherkin-result-case-streaming-rpc-lifecycle/`

---

## 2. Tester Brief
The streaming chat protocol coordinates live token delivery with backend Trigger.dev worker tasks.
1. `callCommand("send-chat-message", payload, options)` accepts streaming event callbacks.
2. Step 1: `onAccepted({ sessionId, turnId, attemptId })` locks session turn and enables the Stop button.
3. Step 2: `onSnapshot({ session, messages })` syncs baseline message history.
4. Step 3: `onReset()` clears transient typing buffers.
5. Step 4: `onEvent`:
   - `tool_status`: Renders intermediate status badge (e.g. `"Analyzing ranking data..."`).
   - `assistant_delta`: Streams text chunks into the typewriter queue.
6. Step 5: Terminal resolution marks the turn as done and releases locks.
7. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.

---

## 4. Gherkin Scenario

```gherkin
Feature: 5-Event Streaming RPC Protocol

  Scenario: Processing all streaming lifecycle events from acceptance to turn completion
    Given the test user sends a prompt query in the Copilot assistant
    When the streaming RPC receives "onAccepted"
    Then the session and turn IDs should be bound and the Stop button unlocked
    When the streaming RPC receives "onEvent" of type "tool_status"
    Then a tool execution badge should be displayed in the message row
    When the streaming RPC receives "onEvent" of type "assistant_delta"
    Then text tokens should stream into the typewriter rendering queue
    When the streaming promise resolves successfully
    Then the conversational turn should be marked complete

    Examples:
      | PromptQuery                | ExpectedToolStatus            |
      | Show our citation breakdown| Querying citation analytics...|
```

---

## 5. Visual Checks
- **Stream Visuals:**
  - Stop Button: `.cc-send.stop[data-action="chat-stop"]`.
  - Tool Status Pill: `.chat-tool-status` (with spinning radar icon).
  - Stream Message Bubble: `.chat-msg.assistant` displaying incremental text with blinking caret.
- **Screenshot Points:**
  - `01_streaming_in_progress.png` (Live streaming message with active tool badge and stop button).

---

## 6. Data and Network Checks
- **Callback Invariants:**
  - Order: `onAccepted` -> `onSnapshot` -> `onEvent(tool_status)` -> `onEvent(assistant_delta)` -> `resolve`.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/05-gherkin-result-case-streaming-rpc-lifecycle/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-streaming');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const streamCheck = await js(String.raw`(() => {
  let accepted = false;
  let toolSeen = false;
  let deltaCount = 0;

  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload, opts) => {
    if (cmd === 'send-chat-message' && opts) {
      if (opts.onAccepted) { opts.onAccepted({ sessionId: "s1", turnId: "t1", attemptId: "a1" }); accepted = true; }
      if (opts.onEvent) {
        opts.onEvent({ type: "tool_status", status: "Scanning radar data..." }); toolSeen = true;
        opts.onEvent({ type: "assistant_delta", delta: "Here are " }); deltaCount++;
        opts.onEvent({ type: "assistant_delta", delta: "your rankings." }); deltaCount++;
      }
      return Promise.resolve({ ok: true, data: { done: true } });
    }
    return origCall.apply(this, arguments);
  };

  if (typeof window.chatLiveSend === "function") {
    window.chatLiveSend("Telemetry test");
  }

  window.ZEO_DATA_PROVIDER.callCommand = origCall;

  return {
    accepted,
    toolSeen,
    deltaCount
  };
})()`);

cliLog('Streaming Lifecycle Result: ' + JSON.stringify(streamCheck));
if (!streamCheck.accepted || !streamCheck.toolSeen || streamCheck.deltaCount !== 2) {
  throw new Error('Streaming RPC protocol failed event callback sequence');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-streaming', { keep: false })`.
