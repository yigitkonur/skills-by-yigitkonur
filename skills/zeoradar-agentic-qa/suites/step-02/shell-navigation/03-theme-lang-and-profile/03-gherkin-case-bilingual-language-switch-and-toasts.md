# Test Case: Bilingual Language Toggling (EN <-> TR), HTML Lang Attribute & Toast Lifecycle

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-03-BILINGUAL-LANGUAGE-TOAST`
- **Purpose:** Verify the bilingual internationalization engine (`assets/ui-shell.js`), ensuring that clicking the language toggle button (`.foot-btn.lang-btn[data-action="lang-toggle"]`) inverts language state between English (`en`) and Turkish (`tr`), synchronizes the `document.documentElement.lang` attribute, persists selection to `localStorage` under `zeo-radar-lang` and `zeo_lang`, triggers the feedback toast (`#toast.toast-info`), and causes UI strings across the shell to update instantly.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to `[APP_URL]/#/[SLUG]/overview` in default English mode, assert that sidebar item `overview` displays `"Overview"`, click the language button in the sidebar footer (`.foot-btn.lang-btn`), assert that the button text changes to `"TR"`, assert that a toast appears saying `"Dil: Türkçe"`, assert that `document.documentElement.lang` is `"tr"`, assert that the overview tab text flips to `"Genel Bakış"`, click the language button again, and verify complete restoration to English.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** `state.lang === "en"`, `document.documentElement.lang === "en"`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[TARGET_LANG]`: Inverted language code (`tr`, `en`)
  - `[EXPECTED_TOAST]`: Localized toast notification string (`Dil: Türkçe`, `Language: English`)
  - `[OVERVIEW_LABEL]`: Localized text for Overview tab (`Genel Bakış`, `Overview`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Preferences - Bilingual Language Toggling and Toast Notification Lifecycle

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And "window.state.lang" is "en"
    And the overview tab element ".side-item[data-key='overview'] span" displays "Overview"

  @i18n @language @toast @positive
  Scenario: Toggling language to Turkish updates HTML attribute, toast, and shell typography
    When the user clicks the footer language button ".foot-btn.lang-btn"
    Then "window.state.lang" should equal "tr"
    And the document element attribute "lang" should equal "tr"
    And localStorage item "zeo-radar-lang" should equal "tr"
    And the toast notification "#toast" should be visible with text "Dil: Türkçe"
    And the overview tab element ".side-item[data-key='overview'] span" should display "Genel Bakış"
    And the language button text should reflect "TR"

  @i18n @language @toast @positive
  Scenario: Toggling language back to English restores English strings
    Given "window.state.lang" is "tr"
    When the user clicks the footer language button ".foot-btn.lang-btn"
    Then "window.state.lang" should equal "en"
    And the document element attribute "lang" should equal "en"
    And localStorage item "zeo-radar-lang" should equal "en"
    And the toast notification "#toast" should be visible with text "Language: English"
    And the overview tab element ".side-item[data-key='overview'] span" should display "Overview"
    And the language button text should reflect "EN"
```

---

## 5. Visual Checks
- **Button Visuals:**
  - In English mode, button displays `"EN"` with tooltip `"Türkçe'ye geç"`.
  - In Turkish mode, button displays `"TR"` with tooltip `"Switch to English"`.
- **Toast Visuals:**
  - Toast slides in cleanly at top or bottom-right with high contrast and auto-dismisses after duration.

---

## 6. Data & Network Checks
- **State & Storage Invariants:**
  ```javascript
  assert(document.documentElement.lang === window.state.lang, "HTML lang attribute must match state.lang");
  assert(localStorage.getItem('zeo-radar-lang') === window.state.lang, "localStorage must persist selected lang");
  assert(typeof window.t === "function", "window.t must exist as language evaluator");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-bilingual-language-switch-and-toasts/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of language toggle transitions and toast triggers.
  - `evidence.json`: Captured state dumps and localized string mappings.
  - `screenshots/03-lang-turkish-toast.png`: Screen capture showing Turkish UI and feedback toast.
  - `screenshots/03-lang-english-restored.png`: Screen capture showing restored English UI.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-03-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
