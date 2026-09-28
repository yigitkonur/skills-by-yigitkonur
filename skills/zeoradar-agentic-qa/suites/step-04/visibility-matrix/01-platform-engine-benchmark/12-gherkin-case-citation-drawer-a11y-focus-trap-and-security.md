# Test Case: TC-VIS-12 - Citation Drawer Accessibility, Focus Trapping & Triple Dismissal

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-12`
- **Module:** Citation Drawer Subsystem (`assets/radar.js`, `assets/radar.css`)
- **Parent Contract:** Spec 09 / Spec 11 (Citation Intelligence & Authoritative Telemetry Pipeline, Accessibility Standard)
- **Traceability:** Maps to Source Scenarios `VIS-16`, `VIS-17`, `VIS-28`, `VIS-29`, and `VIS-30`
- **Purpose:** Verify that the Citation Drawer strictly satisfies the WAI-ARIA modal dialog contract (`role="dialog"`, `aria-modal="true"`, `aria-labelledby="citationDrawerTitle"`), captures caller focus before open, auto-focuses the close button upon mount, confines keyboard Tab navigation within the drawer panel, cleanly executes all three dismissal paths (Escape key, close button click, and backdrop click), restores focus to `previousActiveCitationEl` upon dismissal, and protects against XSS attacks via `normalizeCitationUrl` and `esc()` sanitization.

---

## 2. Tester Brief
The tester or automated agent verifies the accessibility and security contracts:
1. Open the citation drawer from a specific element (e.g. table row or citation leaf).
2. Inspect modal ARIA attributes on `.zr-citation-drawer`:
   - `role="dialog"`
   - `aria-modal="true"`
   - `aria-labelledby="citationDrawerTitle"`
3. Verify initial focus: `document.activeElement` must equal the close button (`button[data-action="close-citation-drawer"]`).
4. Test keyboard Tab cycling: Pressing `Tab` repeatedly cycles only through focusable elements within the drawer (close button, retry button, links) without escaping to background page elements.
5. Verify the Triple Dismissal mechanisms:
   - Dismissal Path 1: Pressing keyboard `Escape` closes the drawer and restores focus to the originating trigger element.
   - Dismissal Path 2: Clicking `button[data-action="close-citation-drawer"]` closes the drawer and restores focus.
   - Dismissal Path 3: Clicking `.zr-drawer-backdrop` closes the drawer and restores focus.
6. Verify URL normalization and XSS defense:
   - Trigger drawer with dirty URL (e.g. `https://www.example.com/path?utm_source=test#frag<script>alert(1)</script>`).
   - Confirm protocol, `www.`, tracking parameters, and hash are stripped, and HTML is safely escaped in the header title.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=studio`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Dirty Test URL:** `https://www.forbes.com/best-luxury-gifts/?utm_medium=paid&test=1#frag<script>alert('xss')</script>`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `12-gherkin-result-case-citation-drawer-a11y-focus-trap-and-security/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Citation Drawer Accessibility, Focus Trapping, Triple Dismissal, and URL Sanitization

  Background:
    Given the user is in the "studio" workspace of Zeo Geo-Radar
    And a citation trigger element "[data-action='open-citation-drawer']" is focused

  Scenario: ARIA Attributes and Initial Auto-Focus
    When the user triggers "openCitationDrawer"
    Then the drawer container ".zr-citation-drawer" must have attribute "role='dialog'"
    And the drawer container must have attribute "aria-modal='true'"
    And the drawer container must have attribute "aria-labelledby='citationDrawerTitle'"
    And the close button "button[data-action='close-citation-drawer']" must receive focus within 100ms

  Scenario Outline: Triple Dismissal Mechanisms and Focus Restoration
    Given the citation drawer is open
    When the user performs dismissal action "<DismissalAction>"
    Then the drawer holder "#citationDrawerHolder" should be unmounted from "document.body"
    And "window.state.citationDrawer.isOpen" should equal false
    And the browser focus should return to the original trigger element

    Examples:
      | DismissalAction         | Trigger Mechanism                                         |
      | Escape Key              | Pressing the physical "Escape" key on the keyboard        |
      | Close Button Click      | Clicking "button[data-action='close-citation-drawer']"     |
      | Backdrop Overlay Click  | Clicking the background overlay ".zr-drawer-backdrop"     |

  Scenario: Keyboard Tab Navigation Focus Trapping
    Given the citation drawer is open
    When the user presses the "Tab" key repeatedly
    Then the focus must remain strictly confined within ".zr-citation-drawer"
    And no background page buttons, inputs, or links should receive focus

  Scenario: URL Normalization and XSS Prevention
    When "openCitationDrawer" is invoked with a dirty URL containing query parameters, hashes, and script tags
    Then "normalizeCitationUrl" should strip protocols, "www.", query parameters, and hashes
    And the drawer title "#citationDrawerTitle" should render the sanitized normalized URL
    And no JavaScript execution, alerts, or DOM script injections should occur
```

---

## 5. Visual Checks
1. **Backdrop Isolation:** `.zr-drawer-backdrop` renders full-bleed over viewport with `z-index: 1000`.
2. **Panel Elevation:** `.zr-citation-drawer` has `z-index: 1001`, box-shadow `0 0 24px rgba(0,0,0,0.15)`.
3. **Focus Ring:** When focused, the close button displays a high-visibility accessibility outline (`outline: 2px solid var(--accent)`).
4. **Header Ellipsis:** Long citation URLs truncate gracefully with `overflow: hidden; text-overflow: ellipsis; white-space: nowrap;` without overflowing panel boundaries.

---

## 6. Data and Network Checks
1. **Focus Restoration Logic:**
   ```js
   const trigger = document.querySelector("[data-action='open-citation-drawer']");
   trigger.focus();
   openCitationDrawer(trigger.getAttribute("data-url"));
   closeCitationDrawer();
   assert(document.activeElement === trigger, "Focus must be restored to caller element");
   ```
2. **URL Sanitization Function:**
   ```js
   const dirty = "https://www.example.com/test?utm_campaign=xyz#token";
   const clean = window.normalizeCitationUrl(dirty);
   assert(clean === "example.com/test", "URL normalization must strip protocol, www, query, and hash");
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `12-gherkin-result-case-citation-drawer-a11y-focus-trap-and-security/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`drawer_auto_focus.png`, `dismissal_focus_restored.png`, `xss_sanitized_title.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-12-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/12-gherkin-result-case-citation-drawer-a11y-focus-trap-and-security/screenshots/
     ```
  4. Write execution report `result.md` verifying ARIA tags, focus activeElements, and URL sanitization.

### Pass/Fail Criteria
- [ ] Panel enforces `role="dialog"`, `aria-modal="true"`, `aria-labelledby`.
- [ ] Close button receives auto-focus upon opening.
- [ ] Triple dismissal paths (Escape, close button, backdrop) cleanly unmount drawer.
- [ ] Focus returns to caller element upon dismissal.
- [ ] URL normalization strips dirty query parameters and escapes HTML entities.
