# Step 08.4 — Zeo AI Copilot, Chat Drawer & Citation Engine QA Suite

## 1. Overview & Architecture

The Zeo AI Copilot subsystem provides conversational intelligence across two primary surfaces: a floating slide-out Copilot drawer (`.ai-help-trigger` / `#aiHelpInput`) and a dedicated full-page assistant workspace (`tab=assistant` / `#chatInput`). It features markdown formatting toolbars, 5MB file attachment validation, a 5-event streaming RPC protocol (`send-chat-message`), an adaptive 60 FPS typewriter rendering engine, AbortController cancellation (`stop-chat-response`), keyboard navigation ergonomics, offline retry resilience, and non-interfering slide-in citation detail inspection.

This test suite provides granular, adversarial, code-grounded Gherkin test cases verifying:
- Dual-surface initiation: floating contextual drawer vs full-page assistant thread view, including preset card catalogs (`.preset-card`).
- Composer markdown formatting toolbar (`[data-action="chat-format"]`) wrapping selected text in bold, italic, code, and links with correct caret placement.
- File attachment size capping strictly rejecting files exceeding 5MB (5,242,880 bytes) with localized warning toasts.
- Live mode RPC payload isolation ensuring binary files and mock skill definitions never contaminate production `send-chat-message` commands.
- 5-event streaming RPC protocol (`onAccepted`, `onSnapshot`, `onReset`, `onEvent`, promise completion).
- Adaptive typewriter loop (`typeTick`) rendering at 16ms intervals (1 to 9 chars/tick based on queue depth) with smooth auto-scroll.
- Stream cancellation via `AbortController` and `stop-chat-response` RPC, instantly flushing the typewriter queue and preventing ghost responses.
- Keyboard shortcuts: `Enter` submitting messages while `Shift+Enter` inserts newlines and expands the composer up to 190px.
- Offline network disconnects and `dependency_unavailable` exceptions rendering inline attempt retry controls.
- Slide-in citation detail drawer (`openCitationDrawer`) opening and closing cleanly without blurring, resetting, or destroying active chat sessions or unsubmitted drafts.

---

## 2. Vocabulary & Placeholders

All test cases in this directory adhere to the standardized parameter vocabulary:

| Placeholder | Semantic Type | Description / Example Values |
| :--- | :--- | :--- |
| `[DOMAIN]` | Domain Name | Workspace primary brand domain (e.g., `zeo.org`, `acme.com`). |
| `[COUNTRY]` | Market Country Code | Monitoring region ISO code (e.g., `US`, `TR`, `UK`). |
| `[LANGUAGE]` | Language Code | Application UI language (e.g., `en`, `tr`). |
| `[PROJECT_ID]` | UUID / String | Unique identifier of active project (e.g., `proj_01j7xyz...`). |
| `[SESSION_ID]` | UUID / String | Unique chat conversation session identifier (e.g., `sess_01j7chat...`). |
| `[TURN_ID]` | UUID / String | Unique conversational turn identifier (e.g., `turn_01j7turn...`). |
| `[PROMPT_QUERY]` | Text String | User prompt question (e.g., `"Why did visibility drop this week?"`). |
| `[ATTACHMENT_FILE]` | File Path / Name | Staged file name (e.g., `q3_audit.pdf`, `oversized_dataset.csv`). |
| `[CITATION_URL]` | URL String | Authoritative citation link (e.g., `https://searchengineland.com/guide`). |

---

## 3. Ego Browser / MacBook Execution Model

Test execution runs within an isolated **Ego Browser** instance operating on a remote host (MacBook environment):
1. **Remote Execution:** Automated driver scripts are executed on the MacBook via SSH using the `ego-browser nodejs` CLI harness.
2. **Artifact Generation:** Visual snapshots, streaming token states, and DOM recordings are captured on the MacBook.
3. **Evidence Ingestion (SCP):** The executor retrieves captured screenshots from the MacBook via SCP (`scp macbook:/tmp/ego-artifacts/*.png <case-result-dir>/`) before compiling the final execution report.
4. **Result Directories:** Each test case references its designated result directory following the convention:
   `04-zeo-ai-chat-drawer/01-gherkin-result-case-<short-slug>/`. Result directories are created exclusively upon test execution, never pre-populated with empty folders.

---

## 4. Test Case Inventory

| Case File | Title & Core Verification | Scenarios Covered |
| :--- | :--- | :--- |
| [`01-gherkin-case-copilot-dual-surface-initiation.md`](./01-gherkin-case-copilot-dual-surface-initiation.md) | Dual Surface Initiation & Presets | Floating drawer toggle, full-page assistant tab, preset card click. |
| [`02-gherkin-case-markdown-formatting-toolbar.md`](./02-gherkin-case-markdown-formatting-toolbar.md) | Markdown Formatting Toolbar | Bold (`**`), italic (`_`), code (```), link syntax wrapping and selection. |
| [`03-gherkin-case-attachment-size-limit.md`](./03-gherkin-case-attachment-size-limit.md) | Attachment 5MB Size Cap Defense | Rejection of files >5,242,880 bytes with localized warning toast. |
| [`04-gherkin-case-live-payload-isolation.md`](./04-gherkin-case-live-payload-isolation.md) | Live Cloud RPC Payload Isolation | Enforcing content-only transmission without file bloat or mock skills. |
| [`05-gherkin-case-streaming-rpc-lifecycle.md`](./05-gherkin-case-streaming-rpc-lifecycle.md) | 5-Event Streaming RPC Protocol | Handling `onAccepted`, `onSnapshot`, `onReset`, `onEvent` tokens. |
| [`06-gherkin-case-adaptive-typewriter-rendering.md`](./06-gherkin-case-adaptive-typewriter-rendering.md) | Adaptive Typewriter Loop (`typeTick`) | 16ms 60 FPS pacing (1-9 chars/tick), markdown caret, auto-scroll. |
| [`07-gherkin-case-streaming-abort-controller.md`](./07-gherkin-case-streaming-abort-controller.md) | Stream Cancellation & Queue Flush | `stop-chat-response` RPC, `AbortController.abort()`, stopping ghost bubbles. |
| [`08-gherkin-case-keyboard-shortcuts-navigation.md`](./08-gherkin-case-keyboard-shortcuts-navigation.md) | Keyboard Navigation (`Shift+Enter` vs `Enter`) | `Enter` submits message; `Shift+Enter` inserts newline and expands box. |
| [`09-gherkin-case-offline-network-error-retry.md`](./09-gherkin-case-offline-network-error-retry.md) | Offline Error Handling & Attempt Retry | `dependency_unavailable` handling, retry button, preserved user prompt. |
| [`10-gherkin-case-citation-drawer-non-interference.md`](./10-gherkin-case-citation-drawer-non-interference.md) | Citation Drawer Non-Interference Guard | `openCitationDrawer` over active chat preserving composer draft and thread. |

---

## 5. Traceability & Coverage Matrix

| Original Monolithic Section (`04-zeo-ai-chat-drawer.md`) | New Modular Case File | Coverage Status | Notes & Invariants Added |
| :--- | :--- | :---: | :--- |
| **Section 1 & 6.1**: Dual Surfaces & Presets | `01-gherkin-case-copilot-dual-surface-initiation.md` | Full | Drawer `.ai-help-trigger` and full-page assistant preset cards. |
| **Section 2.2 & 6.1**: Markdown Formatting Toolbar | `02-gherkin-case-markdown-formatting-toolbar.md` | Full | Tests bold, italic, code, and link markdown token wrapping. |
| **Section 2.3 & 6.2**: 5MB Attachment Limit | `03-gherkin-case-attachment-size-limit.md` | Full | Asserts files >5,242,880 bytes trigger localized 5MB error toast. |
| **Section 2.3**: Live Cloud Payload Isolation | `04-gherkin-case-live-payload-isolation.md` | Full | Asserts `send-chat-message` payload excludes binary attachments. |
| **Section 3**: 5-Event Streaming Protocol | `05-gherkin-case-streaming-rpc-lifecycle.md` | Full | Tests onAccepted, onSnapshot, onReset, assistant_delta, complete. |
| **Section 3.1**: Adaptive Typewriter Engine | `06-gherkin-case-adaptive-typewriter-rendering.md` | Full | Verifies 16ms pacing, adaptive slice rates, and caret blinking. |
| **Section 3.2 & 6.4**: Stream Abort Controller | `07-gherkin-case-streaming-abort-controller.md` | Full | Tests `stop-chat-response` + `AbortController.abort()` + queue purge. |
| **Section 2.1 & 6.5**: Keyboard Shortcuts | `08-gherkin-case-keyboard-shortcuts-navigation.md` | Full | Proves `Enter` submits; `Shift+Enter` inserts clean newline. |
| **Section 6.3**: Offline Disconnect & Retry | `09-gherkin-case-offline-network-error-retry.md` | Full | Validates `dependency_unavailable` copy and attempt retry action. |
| **Section 5 & 6.6**: Citation Detail Drawer | `10-gherkin-case-citation-drawer-non-interference.md` | Full | Verifies citation drawer opening preserves active composer draft. |
