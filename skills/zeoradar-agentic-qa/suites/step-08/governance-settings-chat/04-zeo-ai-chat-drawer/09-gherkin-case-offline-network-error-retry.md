# TC-CHT-09: Offline Network Disconnect Handling and Attempt Retry

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-09`
- **Purpose:** Verify that when network connectivity drops or the backend returns `dependency_unavailable`, the Copilot renders an inline attempt error banner with localized copy and a retry button (`[data-action="chat-retry-attempt"]`), preserving the user's prompt text and enabling instant re-submission upon network recovery.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/09-gherkin-result-case-offline-network-error-retry/`

---

## 2. Tester Brief
Mobile and flaky Wi-Fi networks can cause SSE or HTTP streaming requests to disconnect mid-flight.
1. When `send-chat-message` fails or times out:
   - Server returns `{ ok: false, error: { code: "dependency_unavailable" } }`.
2. The UI catches the exception and renders an inline attempt error box:
   - Copy: `"The AI service is temporarily unavailable. Please retry."` / `"Yapay Zeka servisi geçici olarak kullanılamıyor. Lütfen tekrar deneyin."`.
   - Action Button: `button[data-action="chat-retry-attempt"]`.
3. The original user query is retained in message history.
4. Clicking Retry triggers a new attempt for the same turn.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.
- **Error Condition:** `dependency_unavailable`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Offline Network Disconnect and Attempt Retry

  Scenario Outline: Rendering attempt retry controls upon network failure
    Given the Copilot assistant is awaiting an AI response in language "<Language>"
    When a network disconnect triggers error code "dependency_unavailable"
    Then an attempt error banner should be displayed in the message thread
    And the error copy should contain "<ExpectedErrorCopy>"
    And an inline retry button "[data-action='chat-retry-attempt']" should be rendered
    When the user clicks the retry button
    Then a new streaming attempt should be initiated with the preserved prompt

    Examples:
      | Language | ExpectedErrorCopy                     |
      | en       | temporarily unavailable               |
      | tr       | geçici olarak kullanılamıyor          |
```

---

## 5. Visual Checks
- **Error Banner:**
  - Container: `.chat-attempt-status` or `.chat-error-banner`.
  - Icon: Warning triangle or disconnect symbol.
  - Retry Button: `button.btn.small[data-action="chat-retry-attempt"]`.
- **Screenshot Points:**
  - `01_chat_network_error_banner.png` (Inline error banner with Retry button).

---

## 6. Data and Network Checks
- **Attempt Tracking:**
  - `turn.attempts.length` records failed attempt.
  - Retry initiates attempt increment `attemptId: "att_2"`.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/09-gherkin-result-case-offline-network-error-retry/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-offline');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const errorCheck = await js(String.raw`(() => {
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'send-chat-message') {
      return Promise.resolve({
        ok: false,
        error: { code: "dependency_unavailable", message: "Network offline" }
      });
    }
    return origCall.apply(this, arguments);
  };

  if (typeof window.chatLiveSend === "function") {
    window.chatLiveSend("Offline simulation query");
  }

  return new Promise(resolve => {
    setTimeout(() => {
      window.ZEO_DATA_PROVIDER.callCommand = origCall;
      const banner = document.querySelector('.chat-attempt-status, .chat-error-banner, .toast');
      const retryBtn = document.querySelector('[data-action="chat-retry-attempt"]');
      resolve({
        bannerFound: !!banner,
        errorText: banner ? banner.innerText.trim() : null,
        hasRetryBtn: !!retryBtn
      });
    }, 400);
  });
})()`);

cliLog('Offline Error Check: ' + JSON.stringify(errorCheck));
if (!errorCheck.errorText || !errorCheck.errorText.includes("temporarily unavailable") && !errorCheck.errorText.includes("geçici olarak kullanılamıyor")) {
  throw new Error('Chat offline retry banner failed localized copy check');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-offline', { keep: false })`.
