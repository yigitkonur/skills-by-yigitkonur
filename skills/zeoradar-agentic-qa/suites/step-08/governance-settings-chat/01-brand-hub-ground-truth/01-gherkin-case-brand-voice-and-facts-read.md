# TC-BH-01: Brand Voice Guidelines and Facts Read View

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-01`
- **Purpose:** Verify that an authenticated user navigating to Brand Hub can inspect the authoritative Brand Voice guidelines, version indicator, tone pills, style tags, and the list of verified facts without visual degradation or layout overflow.
- **Target Result Directory:** `01-brand-hub-ground-truth/01-gherkin-result-case-brand-voice-and-facts-read/`

---

## 2. Tester Brief
This test inspects the baseline read-only presentation of Brand Hub in both English and Turkish locales. Testers must verify that:
1. Brand Hub header renders the title and current version badge (`v{version}`).
2. Brand Voice guidelines card displays Tone of Voice (`.bh-tone-pill`), About the Brand, Value Propositions, Core Guidelines, and newline-separated Style Rules (`.bh-rule-tag`).
3. Switching between subtabs (`voice`, `facts`, `hallucinations`) updates active state classes and tab counter pills.
4. **Execution Model:** Ego Browser operates on the remote MacBook. The tester or AI agent drives the session via `ego-browser nodejs`, captures full-viewport and component screenshots to remote storage, and downloads them via SCP before referencing them in local reports.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner or Workspace Member).
- **Target URL:** `[APP_URL]/#/[SLUG]/kb` (or `.side-item[data-key="kb"]`).
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[COUNTRY]`: `TR`
  - `[LANGUAGE]`: `en` or `tr`
  - `[PROJECT_ID]`: `proj_default_01`

---

## 4. Gherkin Scenario

```gherkin
Feature: Brand Hub Ground Truth Read View

  Scenario Outline: Inspecting Brand Voice guidelines and active facts catalog
    Given the test user is signed in with email "e2e-agent@zeogen.com"
    And the application language is set to "<Language>"
    When the user navigates to the Brand Hub route "#/[SLUG]/kb"
    Then the Brand Hub page container ".page.brand-hub-page" should be visible
    And the header should display the version badge containing "v"
    And the Brand Voice card ".bh-voice-card" should render the tone pill ".bh-tone-pill"
    And the style rules wrap ".bh-rules-wrap" should render at least 1 rule tag ".bh-rule-tag"
    When the user clicks the navigation tab "<TabName>" with selector "<TabSelector>"
    Then the target tab content should be displayed with active status

    Examples:
      | Language | TabName       | TabSelector                                                 |
      | en       | Facts Tab     | .brand-hub-tab-btn[data-action="bh-switch-live-tab"][data-tab="facts"]          |
      | en       | Truth Vault   | .brand-hub-tab-btn[data-action="bh-switch-live-tab"][data-tab="hallucinations"] |
      | tr       | Facts Tab     | .brand-hub-tab-btn[data-action="bh-switch-live-tab"][data-tab="facts"]          |
```

---

## 5. Visual Checks
- **Header Elements:**
  - Title: `h2` containing `"Brand Hub"` (or `"Marka Kiti"`).
  - Version Badge: `<span class="badge">v{version}</span>`.
- **Voice Guidelines View:**
  - Card: `.card.bh-voice-card`.
  - Tone Pill: `.bh-tone-pill` (e.g., `"Authoritative, Technical, Transparent"`).
  - Style Tags: `.bh-rules-wrap > .bh-rule-tag`.
- **Screenshot Points:**
  - `01_bh_voice_desktop.png` (Full page view of Voice tab).
  - `02_bh_facts_tab_overview.png` (Facts tab with filter pills and fact cards).

---

## 6. Data and Network Checks
- **Resource Loading:**
  - Call: `window.ZEO_DATA_PROVIDER.loadResource("brandHub", { projectId: "[PROJECT_ID]" })`.
  - Asserts response schema contains `voice.tone`, `voice.styleRules` (array), and `facts` (array).
- **Client State Assertion:**
  - `window.state.brandHub.data.version >= 1`.
  - `window.state.brandHub.activeLiveTab === "voice"` (initially).

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/01-gherkin-result-case-brand-voice-and-facts-read/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
// Phase 1: Task Space Initialization
const task = await useOrCreateTaskSpace('e2e-bh-voice-facts-read');
cliLog('TaskSpace ID: ' + task.id);

// Phase 2: Open Application Tab
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

// Phase 3: Assert Visual State
const check = await js(String.raw`(() => {
  const page = document.querySelector('.page.brand-hub-page');
  const tone = document.querySelector('.bh-tone-pill');
  const rules = document.querySelectorAll('.bh-rule-tag');
  const verBadge = document.querySelector('.brand-hub-header .badge');
  return {
    pageFound: !!page,
    toneText: tone ? tone.innerText.trim() : null,
    rulesCount: rules.length,
    versionText: verBadge ? verBadge.innerText.trim() : null
  };
})()`);
cliLog('Read Assertions: ' + JSON.stringify(check));
if (!check.pageFound || !check.toneText) {
  throw new Error('Brand Hub voice read view failed to render essential components');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-voice-facts-read', { keep: false })` in dedicated cleanup step.
