# Test Case: Brand Switcher Popover Lifecycle, Filtering & Workspace Transition

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-03-BRAND-SWITCHER-POPOVER`
- **Purpose:** Verify the complete interactive lifecycle of the Brand Switcher dropdown (`.side-asset[data-action="asset-pop"]`), including popover instantiation (`#assetPop`), real-time search filtering, brand row selection, workspace state re-scoping (`state.slug`), tab reset to `"overview"`, filter clearing, and navigation to the all-workspaces home catalog.

---

## 2. Tester Brief
The tester (human or AI agent) will click the active brand element in the sidebar header to open `#assetPop`, type filter strings into the search input (`.asset-pop .search input`), assert that non-matching brand rows are hidden via `display: none`, click a brand row with a different slug (`data-slug="ulker"`), verify that `window.state.slug` updates and tab resets to `"overview"`, and test clicking the footer link (`.all[data-action="goto-home"]`) to reach the root home catalog.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand `"[SLUG]"` loaded on `"overview"`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[SEARCH_QUERY]`: Filter text typed into the popover search input
  - `[TARGET_SLUG]`: Selected brand workspace slug (`ulker`, `superfresh`)
  - `[TARGET_LABEL]`: Expected brand title displayed after switch

---

## 4. Gherkin Scenario

```gherkin
Feature: Sidebar Shell - Brand Switcher Popover and Workspace Selection

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the initial brand workspace is "[SLUG]"

  @sanity @brand-switcher @positive
  Scenario: Opening brand switcher and selecting another brand updates workspace
    When the user clicks the brand switcher trigger ".side-asset[data-action='asset-pop']"
    Then the popover container "#assetPop" should become visible without class "hidden"
    And the popover search input ".asset-pop .search input" should be rendered
    When the user types "ulker" into the search input ".asset-pop .search input"
    Then the asset row with data-slug "ulker" should remain visible
    And the asset row with data-slug "superfresh" should have style display "none"
    When the user clicks the asset row ".asset-pop .row[data-slug='ulker']"
    Then the popover "#assetPop" should receive class "hidden"
    And "window.state.slug" should equal "ulker"
    And "window.state.tab" should equal "overview"
    And the URL path should update to "/ulker"
    And the brand trigger label ".side-asset span" should contain "Ülker"

  @home-catalog @navigation @positive
  Scenario: Clicking All Assets footer link navigates to Home catalog
    When the user clicks the brand switcher trigger ".side-asset[data-action='asset-pop']"
    Then the popover container "#assetPop" should not have class "hidden"
    When the user clicks the all assets button ".asset-pop .all[data-action='goto-home']"
    Then "window.state.slug" should be null
    And the URL path should equal "/"
    And the home catalog container ".home-grid" should be displayed
```

---

## 5. Visual Checks
- **Popover Placement:**
  - `#assetPop` renders directly below `.side-asset` with elevated shadow and border radius.
  - Active checkmark icon is displayed strictly alongside the currently active brand.
- **Search Filtering Animation:**
  - Rows show/hide instantly without layout thrashing.
  - Group title `"Your Assets"` (or `"Varlıklarınız"`) remains anchored at top.
- **All Assets Link:**
  - Bottom button `.all` renders with `"All Assets"` (or `"Tüm Varlıklar"`) and grid icon.

---

## 6. Data & Network Checks
- **State & DOM Assertions:**
  ```javascript
  const pop = document.getElementById('assetPop');
  assert(pop && !pop.classList.contains('hidden'), "Popover must be open");
  // After selecting Ulker
  assert(window.state.slug === 'ulker', "state.slug must equal 'ulker'");
  assert(window.state.tab === 'overview', "state.tab must reset to 'overview'");
  assert(window.state.topics === null, "topics filter must be cleared");
  assert(window.state.platforms === null, "platforms filter must be cleared");
  ```
- **URL Synchronization:**
  ```javascript
  assert(window.location.pathname === '/ulker' || window.location.hash === '#/ulker');
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-brand-switcher-popover-and-selection/`
- **Required Artifacts:**
  - `result.md`: Step-by-step validation trace of popover opening, search, brand switch, and home link.
  - `evidence.json`: State dumps before and after brand switch.
  - `screenshots/03-asset-popover-open.png`: Popover view with active brand checkmark.
  - `screenshots/03-asset-filtered.png`: Popover view filtered with "ulker".
  - `screenshots/03-asset-switched-view.png`: Overview dashboard for Ülker.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/nav/case-03-*.png` on the MacBook, retrieved via SCP before compiling `result.md`.
