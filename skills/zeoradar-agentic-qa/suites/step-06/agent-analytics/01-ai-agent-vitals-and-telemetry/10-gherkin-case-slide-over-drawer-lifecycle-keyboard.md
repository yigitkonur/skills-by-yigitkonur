# Case 10: Slide-Over Drawer Lifecycle, Keyboard Dismissal & Focus Management

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-10`
- **Purpose**: Verify the lifecycle, accessibility, and dismissal mechanics of both slide-over drawers in Agent Analytics: the Visit Details Slide-Over Drawer (`.zr-drawer-panel.aa-drawer`) and the All Data / Answers Drawer (`.aa-answer-drawer`), testing backdrop clicking, close 'X' buttons, foot close actions, `Escape` key handling, focus restoration, and drawer deep actions (e.g. "Analyze Page Web Vitals" prefilling the Pages tab).

## 2. Tester Brief
The tester opens the Visit Details drawer by clicking a log row in the Server Logs tab, verifies that metadata (Client IP, User Agent, Method, Path, Status) renders correctly, and tests dismissing the drawer via the backdrop `.zr-drawer-backdrop`, the header 'X' button, and keyboard `Escape`. The tester opens the drawer again, clicks "Analyze Page Web Vitals", and confirms that the drawer dismisses, the app switches to the Pages tab, and the URL input is prefilled. Next, the tester opens the All Answers drawer from the toolbar, traverses its Citations, Summarized, and Raw JSON tabs, and tests dismissal without leftover backdrop overlays.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Selected Log Entry: `id: "log_1"`, path: `"/pricing"`, status: `200`
- **Prerequisites**:
  - Server Logs tab active.

## 4. Gherkin Scenario

```gherkin
Feature: Slide-Over Drawers Lifecycle, Interactions and Focus Management
  As a User Experience and Accessibility Engineer
  I want slide-over inspection drawers to open smoothly, present rich metadata, and dismiss reliably
  So that users can inspect log details and citations without keyboard focus traps or orphaned backdrops

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And the user switches to the Server Logs tab "button.aa-tab-item[data-tab='logs']"

  Scenario Outline: Open and dismiss Visit Details drawer via multiple dismissal mechanisms
    Given a log entry with ID "log_1" exists in the table
    When the user clicks the log row "tr.clickable[data-action='aa-open-drawer'][data-id='log_1']"
    Then the drawer panel ".zr-drawer-panel.aa-drawer" should slide into view
    And the semi-transparent backdrop ".zr-drawer-backdrop" should be mounted in the DOM
    And the drawer should display the full request path, client IP, and User-Agent string
    When the user triggers dismissal via "<dismissal_action>"
    Then the drawer panel should be unmounted from the DOM
    And the backdrop should be removed
    And "window.AgentAnalyticsState.selectedLog" should be null

    Examples:
      | dismissal_action                                                    |
      | clicking backdrop ".zr-drawer-backdrop[data-action='aa-close-drawer']" |
      | clicking close button ".aa-drawer-x[data-action='aa-close-drawer']" |
      | clicking footer close button "button[data-action='aa-close-drawer']"|
      | pressing keyboard key "Escape"                                      |

  Scenario: Deep action from Visit Details drawer to Web Vitals audit runner
    Given the Visit Details drawer is open for a log on path "/pricing"
    When the user clicks the action button "button[data-action='aa-analyze-log-page']"
    Then the Visit Details drawer should be closed
    And the application active tab should switch to "pages"
    And the Web Vitals target URL input should contain "https://[DOMAIN]/pricing"

  Scenario: Inspect All Answers drawer sub-tabs and raw JSON viewer
    When the user clicks the toolbar button "button[data-action='aa-open-answer-drawer']"
    Then the slide-over drawer ".aa-answer-drawer" should appear
    And the default active sub-tab should be "citations"
    When the user clicks sub-tab "button[data-action='aa-answer-tab'][data-tab='summarized']"
    Then the summarized AI insights view should be displayed
    When the user clicks sub-tab "button[data-action='aa-answer-tab'][data-tab='raw']"
    Then the raw JSON payload box ".aa-code-box.mono" should render valid JSON text
    When the user clicks close button ".aa-drawer-x[data-action='aa-close-answer-drawer']"
    Then the All Answers drawer should dismiss cleanly
```

## 5. Visual Checks
- **Drawer Animation**: Smooth slide-in from the right edge with cubic-bezier transition.
- **Backdrop Styling**: Deep darkened translucent veil (`rgba(0,0,0,0.4)`).
- **Code Box**: Monospaced font with subtle syntax highlighting or dark card background.

## 6. Data and Network Checks
- **State Property Synchronizations**:
  ```javascript
  // Open Visit Details
  assert.notStrictEqual(window.AgentAnalyticsState.selectedLog, null);
  // Close Visit Details
  assert.strictEqual(window.AgentAnalyticsState.selectedLog, null);
  // Open Answer Drawer
  assert.strictEqual(window.AgentAnalyticsState.showAnswerDrawer, true);
  // Close Answer Drawer
  assert.strictEqual(window.AgentAnalyticsState.showAnswerDrawer, false);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-slide-over-drawer-lifecycle-keyboard/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-10-drawer-open.png`
     - `/tmp/ego-shots/tc-aa-10-raw-json-tab.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-10-*.png ./01-gherkin-result-case-slide-over-drawer-lifecycle-keyboard/
     ```
