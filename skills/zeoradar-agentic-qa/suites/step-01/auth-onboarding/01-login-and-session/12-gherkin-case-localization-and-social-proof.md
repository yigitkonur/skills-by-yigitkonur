# Test Case: Internationalization (EN/TR), Social Proof Testimonials & Footer

## 1. Case ID & Purpose
- **Case ID:** `TC-AUTH-12-LOCALIZATION-TESTIMONIALS`
- **Purpose:** Validate complete bilingual internationalization (`t("English", "Türkçe")`) across all auth headings, labels, button texts, and error copies, verify social proof panel customer testimonials carousel rotation (`AUTH_TESTIMONIALS`), and assert persistent footer legal links.

---

## 2. Tester Brief
The tester loads the auth screen and inspects the language switcher button (`button.shell-lang-btn[data-action="lang-toggle"]`). The tester toggles between English and Turkish, asserting that all static copy, form labels, and button texts translate without placeholder leaks. Next, the tester inspects the right-hand social proof panel, verifying customer quotes (Linear, Ramp, TeachShare, Rocket55), avatar initials, and navigation dot clicking. Finally, the tester verifies the persistent footer links.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/auth`
- **Prerequisite State:** Initial view (`step === 'email'`)
- **Placeholders Used:**
  - `[APP_URL]`: Base application URL under test
  - `[LANG_EN]`: `"en"`
  - `[LANG_TR]`: `"tr"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Auth Shell - Localization, Social Testimonials and Legal Footer

  Background:
    Given the user navigates to "[APP_URL]/#/auth"
    And the auth container is displayed with both form and social panels

  @sanity @i18n @localization
  Scenario: Toggling application language translates all auth UI copy
    Given the current language is "en"
    Then the heading "h1.auth-title" should display "What's your email?"
    And the continue button should display "Continue"
    When the user clicks the language toggle button "button.shell-lang-btn"
    Then the application language should switch to "tr"
    And the heading "h1.auth-title" should translate to "E-postanız nedir?"
    And the email placeholder should be "ad@sirket.com" or "name@company.com"
    And the continue button should translate to "Devam et"
    When the user clicks the language toggle button again
    Then the language should revert to "en"

  @positive @ui @testimonials
  Scenario Outline: Testimonial navigation dots cycle through social proof quotes
    When the user clicks testimonial dot button "<dot_selector>"
    Then the active brand badge ".brand-badge-pill" should display "<expected_badge>"
    And the quote text "blockquote.testimonial-quote" should contain "<expected_quote_snippet>"
    And the author name ".author-name" should display "<expected_author>"
    And the avatar initials ".author-avatar" should display "<expected_avatar>"

    Examples:
      | dot_selector                           | expected_badge | expected_quote_snippet         | expected_author   | expected_avatar |
      | .testimonial-dots-nav button:nth-child(1) | Linear         | AI discovery channels now refer| Karri Saarinen    | KS              |
      | .testimonial-dots-nav button:nth-child(2) | Ramp           | unprecedented visibility into  | Luke Tubinis      | LT              |
      | .testimonial-dots-nav button:nth-child(3) | TeachShare     | Understanding our brand presence| Aryan Bhadouria   | AB              |
      | .testimonial-dots-nav button:nth-child(4) | Rocket55       | prompt fanout intelligence     | Sarah Jenkins     | SJ              |

  @sanity @footer
  Scenario: Persistent footer displays contact and legal links
    Then the footer "footer.auth-persistent-footer" should be visible
    And the footer should contain clickable links for "Contact Us", "Privacy Policy", and "Terms"
    When the user clicks "Contact Us"
    Then a contact or support scheduler modal/toast should be triggered
```

---

## 5. Visual Checks
- **Social Panel Typography & Layout:**
  - Quote text rendered with large readable serif/sans styling (`font-size: 1.125rem`, line-height: 1.6).
  - Navigation dots `.dot-btn` show active dot with filled circle and accent color.
- **Language Toggle Styling:**
  - Language button `.shell-lang-btn` displays current language code uppercase (`"EN"` / `"TR"`).
- **Split-Screen Ratio:**
  - Responsive flexbox: 50% left panel, 50% right panel on desktop (>= 1024px); social panel cleanly stacks or hides on mobile (< 768px).

---

## 6. Data & Network Checks
- **DOM Assertions:**
  ```javascript
  const dots = document.querySelectorAll('.testimonial-dots-nav button.dot-btn');
  assert(dots.length === 4, "Must have exactly 4 testimonial dots");
  const lang = (typeof window.lang === 'function') ? window.lang() : window.state.lang;
  assert(lang === 'en' || lang === 'tr', "Language must be en or tr");
  ```
- **State Check:**
  - `window.getAuthState().testimonialIdx` updates to 0, 1, 2, or 3 upon dot clicks.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `12-gherkin-result-case-localization-and-social-proof/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, localization string validation summary.
  - `evidence.json`: State dump of active testimonial and language setting.
  - `screenshots/01-auth-en-view.png`: English auth screen capture.
  - `screenshots/02-auth-tr-view.png`: Turkish auth screen capture.
  - `screenshots/03-testimonial-carousel.png`: Switched customer testimonial display.
- **MacBook Execution Protocol:** Ego Browser captures multi-language and testimonial renders on MacBook; images synced via SCP.
