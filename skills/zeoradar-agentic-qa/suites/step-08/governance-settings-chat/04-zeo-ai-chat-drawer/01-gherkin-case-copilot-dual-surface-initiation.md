# TC-CHT-01: Zeo AI Copilot Dual Surface Initiation and Preset Selection

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-01`
- **Purpose:** Verify that users can invoke the Zeo AI Copilot via the floating slide-out drawer trigger (`.ai-help-trigger`) or the dedicated full-page assistant tab (`#/[SLUG]/assistant`), inspecting preset question cards (`.preset-card`) on empty threads and dispatching them with a single click.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/01-gherkin-result-case-copilot-dual-surface-initiation/`

---

## 2. Tester Brief
The Copilot offers two interaction modes:
1. Floating Drawer: Triggered from any page via `.ai-help-trigger` or `[data-action="toggle-ai-help"]`, allowing fast query assistance without losing page context.
2. Full-Page Assistant: Located at `#/[SLUG]/assistant`, providing a full-width chat interface with multi-turn conversation switching.
3. On an empty conversation, the interface renders a catalog of preset prompt cards:
   - *"Why did our Visibility Score drop this week?"*
   - *"Which domains cite our competitors most frequently?"*
   - *"Identify high-intent prompts where we hold rank #1."*
4. Clicking any preset card populates the composer and automatically triggers message dispatch.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.
- **Target Trigger:** `.ai-help-trigger` or `[data-action="toggle-ai-help"]`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Zeo AI Copilot Dual Surface Initiation

  Scenario Outline: Initiating AI Copilot and triggering preset prompts
    Given the test user is on route "<StartingRoute>"
    When the user invokes the Copilot via "<InvokeAction>"
    Then the Copilot composer "<ComposerSelector>" should be visible and focused
    And the empty conversation view should render at least 3 preset cards ".preset-card"
    When the user clicks the preset card with query "<PresetQuery>"
    Then the message should be dispatched to the streaming assistant

    Examples:
      | StartingRoute            | InvokeAction                  | ComposerSelector | PresetQuery                                      |
      | #/[SLUG]/overview| click .ai-help-trigger        | #aiHelpInput     | Why did our Visibility Score drop this week?     |
      | #/[SLUG]/kb      | navigate /assistant           | #chatInput       | Which domains cite our competitors most frequently?|
```

---

## 5. Visual Checks
- **Surface Elements:**
  - Floating Trigger: `.ai-help-trigger` floating button in bottom-right corner.
  - Floating Drawer: `#aiHelpDrawerHolder` sliding in from right.
  - Full-Page Container: `.page.chat-page` with sidebar session list.
  - Preset Cards: `.preset-card[data-action="chat-preset"]`.
- **Screenshot Points:**
  - `01_copilot_drawer_opened.png` (Floating Copilot drawer open with preset cards).
  - `02_fullpage_assistant.png` (Dedicated full-page assistant view).

---

## 6. Data and Network Checks
- **Session State:**
  - `window.state.chatDrawer.isOpen === true` (when drawer is active).
  - `window.state.tab === "assistant"` (when full page is active).

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/01-gherkin-result-case-copilot-dual-surface-initiation/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-copilot-init');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/overview', { wait: true, timeout: 30 });
await wait(2);

// Click floating trigger
await click('.ai-help-trigger, [data-action="toggle-ai-help"]');
await wait(2);

const drawerCheck = await js(String.raw`(() => {
  const inp = document.getElementById("aiHelpInput") || document.getElementById("chatInput");
  const presets = document.querySelectorAll('.preset-card');
  return {
    composerFound: !!inp,
    presetsCount: presets.length,
    firstPresetText: presets[0] ? presets[0].innerText.trim() : null
  };
})()`);

cliLog('Drawer Init Check: ' + JSON.stringify(drawerCheck));
if (!drawerCheck.composerFound || drawerCheck.presetsCount < 3) {
  throw new Error('Copilot drawer or preset cards failed to initialize');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-copilot-init', { keep: false })`.
