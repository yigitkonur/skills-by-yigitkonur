# TC-CHT-02: Composer Markdown Formatting Toolbar and Syntax Wrapping

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-02`
- **Purpose:** Verify that clicking markdown formatting toolbar buttons (`[data-action="chat-format"]`) wraps highlighted text with the correct markdown syntax tokens (`**bold**`, `_italic_`, `` `code` ``, `[link](https://)`) and positions the text selection caret accurately without corrupting unselected composer text.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/02-gherkin-result-case-markdown-formatting-toolbar/`

---

## 2. Tester Brief
The Copilot composer includes a quick-formatting toolbar above or below the textarea.
1. The user types a query: `"Examine visibility trends"`.
2. Selecting the word `"visibility"` and clicking:
   - Bold (`data-f="bold"`): wraps to `"**visibility**"`.
   - Italic (`data-f="italic"`): wraps to `"_visibility_"`.
   - Inline Code (`data-f="code"`): wraps to `` "`visibility`" ``.
   - Link (`data-f="link"`): wraps to `"[visibility](https://)"` with caret positioned inside URL parentheses.
3. If no text is selected, clicking a button inserts empty tokens (e.g. `****`) with the caret placed between them.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.
- **Sample Text:** `"Audit visibility rankings"`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Composer Markdown Formatting Toolbar

  Scenario Outline: Applying markdown syntax formatting to selected prompt text
    Given the user has entered "Audit visibility rankings" into the composer
    When the user highlights the word "visibility" (characters 6 to 16)
    And the user clicks the formatting button with action "<FormatAction>"
    Then the composer value should update to "<ExpectedFormattedText>"
    And the selection caret should be positioned properly

    Examples:
      | FormatAction | ExpectedFormattedText                  |
      | bold         | Audit **visibility** rankings          |
      | italic       | Audit _visibility_ rankings            |
      | code         | Audit `visibility` rankings            |
      | link         | Audit [visibility](https://) rankings  |
```

---

## 5. Visual Checks
- **Toolbar Buttons:**
  - Bold: `button[data-action="chat-format"][data-f="bold"]`.
  - Italic: `button[data-action="chat-format"][data-f="italic"]`.
  - Code: `button[data-action="chat-format"][data-f="code"]`.
  - Link: `button[data-action="chat-format"][data-f="link"]`.
- **Screenshot Points:**
  - `01_composer_formatted_text.png` (Composer displaying formatted markdown text).

---

## 6. Data and Network Checks
- **DOM Value Assertion:**
  - `document.getElementById("chatInput").value` contains exact markdown tokens.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/02-gherkin-result-case-markdown-formatting-toolbar/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-format');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const formatCheck = await js(String.raw`(() => {
  const inp = document.getElementById("chatInput") || document.getElementById("aiHelpInput");
  if (!inp) return { found: false };

  inp.value = "Audit visibility rankings";
  inp.setSelectionRange(6, 16); // selects 'visibility'

  const boldBtn = document.querySelector('[data-action="chat-format"][data-f="bold"]');
  if (boldBtn) boldBtn.click();

  return {
    found: true,
    finalValue: inp.value,
    isBoldWrapped: inp.value.includes("**visibility**")
  };
})()`);

cliLog('Format Check Result: ' + JSON.stringify(formatCheck));
if (!formatCheck.isBoldWrapped) {
  throw new Error('Markdown bold formatting failed to wrap highlighted text');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-format', { keep: false })`.
