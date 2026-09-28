# TC-CHT-10: Slide-In Citation Detail Drawer Non-Interference Guard

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-10`
- **Purpose:** Verify that clicking a citation chip inside an AI response opens the slide-in citation detail drawer (`#citationDrawerHolder`) without destroying, blurring, or clearing the underlying active chat conversation, session identifier, or unsubmitted composer draft text.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/10-gherkin-result-case-citation-drawer-non-interference/`

---

## 2. Tester Brief
AI answers frequently cite external domains and articles. Users click citations to verify domain authority and source topics.
1. When a user clicks a citation link in chat:
   - `window.openCitationDrawer(rawUrl)` is invoked.
   - The drawer panel `#citationDrawerHolder` slides in (`width: 480px; z-index: 9999;`).
   - Domain Authority, total citations, and referencing prompts are fetched.
2. Non-Interference Invariant:
   - The background chat session MUST remain fully active.
   - Any draft text typed by the user in `#chatInput` must NOT be wiped or reset.
   - Streaming tokens (if active) must continue rendering in the background.
3. Dismissing the drawer (via `[data-action="close-citation-drawer"]`, backdrop click, or `Escape`) leaves the chat session completely intact.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/chat.js` & `assets/brand-hub.css` (`citationDrawer`).
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.
- **Target Citation URL:** `https://searchengineland.com/what-is-geo-and-aeo`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Citation Detail Drawer Non-Interference Guard

  Scenario: Inspecting citation source metrics without disrupting active chat composer draft
    Given the test user has typed unsubmitted draft text into the chat composer
    When the user clicks a citation chip with URL "https://searchengineland.com/what-is-geo-and-aeo"
    Then the citation detail drawer "#citationDrawerHolder" should open with width 480px
    And the domain metrics (authority, citations) should be displayed
    And the composer draft text should remain intact without loss
    When the user closes the citation detail drawer
    Then the citation drawer should be dismissed
    And the composer draft text should still be preserved and editable

    Examples:
      | CitationDomain          | DraftText                                    |
      | searchengineland.com    | Preserved draft text during citation check   |
```

---

## 5. Visual Checks
- **Citation Drawer:**
  - Container: `#citationDrawerHolder .zr-drawer-panel.zr-citation-drawer`.
  - Close Button: `button[data-action="close-citation-drawer"]`.
  - Metrics Cards: Domain Authority, Total Citations.
- **Background Chat:**
  - Message thread and composer remains visible behind the semi-transparent backdrop.
- **Screenshot Points:**
  - `01_citation_drawer_opened.png` (Citation drawer overlapping active chat with preserved draft).
  - `02_citation_drawer_closed.png` (Returned to chat with draft text untouched).

---

## 6. Data and Network Checks
- **State Invariants:**
  - `window.state.citationDrawer.isOpen === true` while drawer is visible.
  - Composer value before open === Composer value after close.

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/10-gherkin-result-case-citation-drawer-non-interference/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-citation-drawer');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const nonInterferenceCheck = await js(String.raw`(() => {
  const inp = document.getElementById("chatInput");
  const testDraft = "Preserved draft text during citation inspection";
  if (inp) inp.value = testDraft;

  // Open citation drawer
  if (typeof window.openCitationDrawer === "function") {
    window.openCitationDrawer("https://searchengineland.com/what-is-geo-and-aeo");
  }

  const drawer = document.getElementById("citationDrawerHolder");
  const drawerOpen = !!(drawer && window.state && window.state.citationDrawer && window.state.citationDrawer.isOpen);
  const draftIntactWhileOpen = inp ? inp.value === testDraft : false;

  // Close citation drawer
  if (typeof window.closeCitationDrawer === "function") {
    window.closeCitationDrawer();
  }

  const drawerClosed = !(window.state && window.state.citationDrawer && window.state.citationDrawer.isOpen);
  const draftIntactAfterClose = inp ? inp.value === testDraft : false;

  return {
    drawerOpen,
    draftIntactWhileOpen,
    drawerClosed,
    draftIntactAfterClose
  };
})()`);

cliLog('Citation Non-Interference Result: ' + JSON.stringify(nonInterferenceCheck));
if (!nonInterferenceCheck.draftIntactWhileOpen || !nonInterferenceCheck.draftIntactAfterClose) {
  throw new Error('Citation drawer opening or closing disrupted active composer draft');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-citation-drawer', { keep: false })`.
