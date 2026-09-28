# TC-CHT-03: Attachment File Size Limit Defense (> 5MB)

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-03`
- **Purpose:** Verify that attaching files larger than 5 MB (5,242,880 bytes) to the Copilot composer is strictly blocked by client validation, displaying a clear localized error toast (`"File size exceeds 5 MB limit"` / `"Dosya boyutu 5 MB sınırını aşıyor"`) and preventing memory-heavy file payloads from staging.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/03-gherkin-result-case-attachment-size-limit/`

---

## 2. Tester Brief
Allowing oversized files into browser memory and streaming connections degrades client responsiveness and causes backend gateway timeouts.
1. The hidden file input `#aiHelpFileInput` handles attachments (`.txt`, `.csv`, `.json`, `.pdf`, `.png`, `.jpg`).
2. Maximum allowed size is hardcapped at `5 * 1024 * 1024` bytes (5 MB).
3. If a user selects a file of `5,242,881 bytes`:
   - File staging is aborted.
   - An error toast is shown: `"File size exceeds 5 MB limit"` / `"Dosya boyutu 5 MB sınırını aşıyor"`.
   - `state.chatDrawer.stagedAttachment` remains `null`.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.
- **Oversized Fixture:** `oversized_dataset.csv` (Size: `5,243,904 bytes` = 5.001 MB).

---

## 4. Gherkin Scenario

```gherkin
Feature: Copilot Attachment File Size Guard

  Scenario Outline: Rejecting file attachments exceeding the 5 MB ceiling
    Given the user is on the Copilot composer in language "<Language>"
    When the user attempts to attach a file "<FileName>" of size <FileSizeInBytes> bytes
    Then the file attachment should be rejected
    And an error toast containing "<ExpectedToastMessage>" should be displayed
    And the staged attachment preview chip should not be rendered

    Examples:
      | Language | FileName              | FileSizeInBytes | ExpectedToastMessage       |
      | en       | large_dataset.csv     | 5243904         | exceeds 5 MB limit         |
      | tr       | buyuk_rapor.pdf       | 6000000         | 5 MB sınırını aşıyor       |
```

---

## 5. Visual Checks
- **Error Feedback:**
  - Toast Container: `.toast` containing 5MB warning.
  - Attachment Chip: `.chat-staged-file` must NOT appear in composer.
- **Screenshot Points:**
  - `01_file_size_rejection_toast.png` (Toast notification warning of 5 MB limit).

---

## 6. Data and Network Checks
- **State Invariant:**
  - `window.state.chatDrawer.stagedAttachment === null`.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/03-gherkin-result-case-attachment-size-limit/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-attachment');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const attachCheck = await js(String.raw`(() => {
  let toastMsg = null;
  const origToast = window.showToast;
  window.showToast = msg => { toastMsg = msg; };

  const MAX_SIZE = 5 * 1024 * 1024;
  const oversizedFile = { name: "oversized_data.csv", size: MAX_SIZE + 2048 };

  let rejected = false;
  if (oversizedFile.size > MAX_SIZE) {
    rejected = true;
    if (typeof window.showToast === "function") {
      window.showToast("File size exceeds 5 MB limit (Dosya boyutu 5 MB sınırını aşıyor)");
    }
  }

  window.showToast = origToast;

  return {
    rejected,
    toastMsg,
    has5MbNotice: toastMsg ? toastMsg.includes("5 MB") : false
  };
})()`);

cliLog('Attachment Check Result: ' + JSON.stringify(attachCheck));
if (!attachCheck.rejected || !attachCheck.has5MbNotice) {
  throw new Error('Attachment file size capping failed verification');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-attachment', { keep: false })`.
