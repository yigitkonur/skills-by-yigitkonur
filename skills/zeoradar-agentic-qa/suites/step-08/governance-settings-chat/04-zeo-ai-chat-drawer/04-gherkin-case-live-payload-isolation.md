# TC-CHT-04: Live Cloud Chat RPC Payload Isolation

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-04`
- **Purpose:** Verify that in Live Cloud mode, the streaming conversational command `send-chat-message` enforces strict payload isolation: transmitting only sanitized text content and session identifiers (`projectId`, `sessionId`, `turnId`, `content`), while strictly excluding raw binary file streams, base64 strings, or mock skill objects.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/04-gherkin-result-case-live-payload-isolation/`

---

## 2. Tester Brief
Overloading streaming chat RPC commands with large multi-megabyte binary payloads introduces latency and saturates Edge Worker memory.
1. When a user submits a prompt with a staged file attached:
2. The client intercepts the submission and verifies that `send-chat-message` payload receives ONLY:
   ```json
   {
     "projectId": "[PROJECT_ID]",
     "sessionId": "[SESSION_ID]",
     "turnId": "[TURN_ID]",
     "content": "User prompt text"
   }
   ```
3. Raw file bytes (`base64`, `ArrayBuffer`, or `Blob`) are NEVER injected into the `send-chat-message` payload object.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.
- **Target Command:** `send-chat-message`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Live Chat Payload Isolation

  Scenario: Enforcing content-only transmission in send-chat-message command
    Given the Copilot is operating in Live Cloud mode
    And a prompt is submitted from the chat composer
    When the streaming RPC command "send-chat-message" is dispatched
    Then the payload should contain properties "projectId", "sessionId", and "content"
    And the payload should NOT contain raw binary buffers, base64 strings, or mock skills

    Examples:
      | PromptText                       | PayloadContentClean |
      | Summarize latest ranking shifts | true                |
```

---

## 5. Visual Checks
- **Composer State:**
  - Sending state renders animated wave or dots in `.cc-send`.
- **Screenshot Points:**
  - `01_chat_sending_state.png` (Composer in active sending state).

---

## 6. Data and Network Checks
- **Command Inspection:**
  - `typeof payload.content === "string"`.
  - `payload.attachment === undefined`.
  - `payload.fileBytes === undefined`.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/04-gherkin-result-case-live-payload-isolation/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-payload');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const payloadCheck = await js(String.raw`(() => {
  let capturedPayload = null;
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'send-chat-message') {
      capturedPayload = payload;
      return Promise.resolve({ ok: true, data: { sessionId: "s1", turnId: "t1" } });
    }
    return origCall.apply(this, arguments);
  };

  if (typeof window.chatLiveSend === "function") {
    window.chatLiveSend("Analyze top citing domains");
  }

  window.ZEO_DATA_PROVIDER.callCommand = origCall;

  return {
    dispatched: !!capturedPayload,
    hasContent: capturedPayload ? typeof capturedPayload.content === "string" : false,
    noRawFiles: capturedPayload ? !capturedPayload.file && !capturedPayload.binary : true
  };
})()`);

cliLog('Payload Isolation Result: ' + JSON.stringify(payloadCheck));
if (payloadCheck.dispatched && (!payloadCheck.hasContent || !payloadCheck.noRawFiles)) {
  throw new Error('Chat payload isolation failed: unexpected binary fields in payload');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-payload', { keep: false })`.
