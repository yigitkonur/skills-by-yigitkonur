# Test Case: Turkish Diacritic Invariance (İ/ı/ş/ğ/ü/ö/ç) and Toast Queue Sequence Settlement

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-09-TURKISH-DIACRITICS-TOAST-SETTLE`
- **Purpose:** Verify typographical integrity and Turkish diacritic preservation (`İ`, `ı`, `ş`, `ğ`, `ü`, `ö`, `ç`) across the application shell upon switching to Turkish locale, ensuring no Unicode replacement characters (``) or broken glyphs appear in navigation labels, and assert the sequential auto-settlement lifecycle of the toast notification queue (`toastSeq` sequence lock preventing premature dismissal or race conditions).

---

## 2. Tester Brief
The tester (human or AI agent) will switch the application language to Turkish (`state.lang = "tr"`), inspect the sidebar tabs for proper rendering of dotted and undotted characters (`"İş Akışları"`, `"Genel Bakış"`, `"Doğruluk K."`), trigger a toast notification via `showToast({ message: "AEO İçgörü Testi", duration: 1500 })`, assert that `#toast.show` renders with Turkish characters, wait for the settlement duration, and assert that the toast automatically closes and resets `isToastShowing`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Language set to Turkish (`state.lang = "tr"`)
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[TOAST_MESSAGE]`: Turkish notification message containing diacritics
  - `[DURATION_MS]`: Toast active duration before settlement (1500ms)

---

## 4. Gherkin Scenario

```gherkin
Feature: Localization - Turkish Diacritic Preservation and Toast Settlement Lifecycle

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    When the user switches the language to "tr"
    Then the document language attribute "lang" should equal "tr"

  @turkish @typography @diacritics @positive
  Scenario: Navigation tabs render Turkish diacritics cleanly without character corruption
    Then the sidebar items should render the following exact Turkish typography:
      | side_key      | expected_text          |
      | overview      | Genel Bakış            |
      | aei           | Görünürlük             |
      | volumes       | Promptlar              |
      | workflows     | İş Akışları            |
      | opportunities | Fırsatlar              |
      | pages         | Sayfalar               |
    And no Unicode replacement characters "" should appear in the sidebar

  @toast @settlement @queue @positive
  Scenario: Toast notification displays Turkish text and auto-settles cleanly
    When a toast is triggered with message "AEO İçgörü Testi Başarılı" and duration 1500ms
    Then the toast element "#toast" should have class "show"
    And the toast text should equal "AEO İçgörü Testi Başarılı"
    When the user waits 2000 milliseconds
    Then the toast element "#toast" should not have class "show"
    And "window.isToastShowing" should be false
```

---

## 5. Visual Checks
- **Turkish Diacritics Display:**
  - Dotted uppercase `İ` in `"İş Akışları"` and undotted lowercase `ı` in `"Fırsatlar"` render cleanly in system sans font.
- **Toast Animation:**
  - Toast slides into view smoothly, remains static for the duration, and fades out cleanly without jumping.

---

## 6. Data & Network Checks
- **DOM Assertions:**
  ```javascript
  const texts = Array.from(document.querySelectorAll('.side-item span')).map(el => el.textContent.trim());
  assert(texts.includes('İş Akışları'), "İş Akışları must be present");
  assert(texts.includes('Genel Bakış'), "Genel Bakış must be present");
  assert(!document.body.innerText.includes(''), "No Unicode replacement characters allowed");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-turkish-diacritics-and-toast-settlement/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of Turkish diacritic audit and toast settlement timer trace.
  - `evidence.json`: Captured sidebar labels and toast lifecycle timings.
  - `screenshots/09-turkish-sidebar-diacritics.png`: View of sidebar displaying Turkish labels.
  - `screenshots/09-toast-settled.png`: View after toast auto-settles.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-09-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
