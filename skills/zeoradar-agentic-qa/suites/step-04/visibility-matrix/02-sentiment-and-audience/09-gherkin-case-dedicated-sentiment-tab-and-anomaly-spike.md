# Test Case: TC-SNT-09 - Dedicated Sentiment Tab & Anomaly Spike Thresholds

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-09`
- **Module:** Dedicated Sentiment Analysis Tab (`assets/radar.js`, `assets/radar.css`)
- **Parent Contract:** Spec 06 (Sentiment Analysis Architecture, BMD-BSH-03 Anomaly Spike Detection)
- **Traceability:** Maps to Source Scenarios `SNT-12`, `SNT-13`, `SNT-20`, and `SNT-21`
- **Purpose:** Verify that navigating to `/#/app/:slug/sentiment` renders the dedicated full-page sentiment analysis dashboard, displays the stacked polarity bar (`.stackbar`), evaluates the anomaly spike threshold trigger (`negPct >= 15 || negClaims >= 2`), injects the `.sent-spike-badge` alert when triggered, verifies its absence in clean baselines (`negPct < 15 && negClaims < 2`), and confirms that clicking the spike badge triggers `sent-inspect-spike`, immediately filtering the themes list to negative attributes.

---

## 2. Tester Brief
The tester or automated agent validates the dedicated Sentiment tab and anomaly detection:
1. Navigate to `/#/app/[SLUG]/sentiment`.
2. Verify the page layout:
   - Polarity split bar with positive and negative click targets (`[data-action="sent-seg"]`).
   - Stacked horizontal bar (`.stackbar`).
   - Theme quick-summary rail (`.sent-theme`).
   - Platform rank list and score chart.
3. Test Anomaly Spike Threshold Trigger:
   - On a dataset where negative claims exceed 15% OR reach at least 2 negative claims:
     - Verify `.sent-spike-badge` is injected beneath the polarity bar.
     - Confirm copy: *"⚠️ Negative spike detected: [negPct]% negative claims. Click to inspect root causes."*
4. Test Spike Click Interaction:
   - Click `.sent-spike-badge`.
   - Assert `state.expanded["sent-seg"]` updates to `"negative"`.
   - Verify the Themes & Attributes list updates to display only themes containing negative claims.
5. Test Clean Baseline:
   - On a brand dataset where `negPct < 15%` AND `negClaims < 2`:
     - Assert `.sent-spike-badge` is absent from the DOM.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/sentiment`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Dataset Variants:** High negative claims dataset vs Clean baseline dataset
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `09-gherkin-result-case-dedicated-sentiment-tab-and-anomaly-spike/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Dedicated Sentiment Tab, Anomaly Spike Detection, and Root Cause Inspection

  Background:
    Given the user navigates to "/#/app/[SLUG]/sentiment"
    Then the dedicated sentiment page should mount within 10 seconds

  Scenario: Dedicated Sentiment Page Anatomy
    Then the page container should display:
      | Element Selector            | Purpose                                            |
      | .stackbar                   | Two-color stacked polarity distribution bar        |
      | .metric-label               | "Positive Sentiment" or "Pozitif Duygu" metric card|
      | .big-num                    | Overall positive sentiment score                   |
      | .rank-list                  | Platform ranking list                              |
      | .seg-tabs                   | Theme segmentation filter buttons                  |

  Scenario Outline: Anomaly Spike Detection Threshold Logic
    Given the sentiment dataset has negative claim percentage "<NegPct>" and negative claim count "<NegCount>"
    When the dedicated sentiment tab is rendered
    Then the presence of the anomaly badge ".sent-spike-badge" should equal <ShouldRenderBadge>
    And when the badge is present, its text should state "Negative spike detected"

    Examples:
      | NegPct | NegCount | ShouldRenderBadge | Scenario Context                        |
      | 18%    | 5        | true              | Both percentage and count exceed limits |
      | 16%    | 1        | true              | Percentage exceeds 15% threshold        |
      | 10%    | 2        | true              | Negative claims reach count threshold   |
      | 8%     | 1        | false             | Clean baseline: negPct < 15 & count < 2 |

  Scenario: Clicking Anomaly Spike Badge Filters Themes to Negative Attributes
    Given the anomaly spike badge ".sent-spike-badge" is visible
    When the user clicks ".sent-spike-badge"
    Then "window.state.expanded['sent-seg']" should equal "negative"
    And the negative segment tab "button.on[data-action='sent-seg'][data-k='negative']" should be active
    And the themes list should only display themes containing negative claims
```

---

## 5. Visual Checks
1. **Anomaly Badge Styling:** Distinctive red outline and background tint (`background: color-mix(in srgb, var(--red) 12%, transparent); border: 1px solid var(--red); color: var(--red);`).
2. **Cursor Affordance:** Pointer cursor on `.sent-spike-badge` indicating interactivity.
3. **Stacked Bar Contrast:** Bold contrast between green positive section and red negative section.
4. **Theme Rail:** Horizontal scrollable rail of theme chips with green checkmarks (`✓`) for positive and red crosses (`✕`) for negative.

---

## 6. Data and Network Checks
1. **Spike Threshold Expression Verification:**
   ```js
   const isSpike = (negPct >= 15 || negClaims >= 2);
   const badgeEl = document.querySelector(".sent-spike-badge");
   assert(!!badgeEl === isSpike, "Spike badge rendering condition mismatch");
   ```
2. **Segment Tab State Sync:**
   - Confirm click triggers `sent-inspect-spike` and sets `state.expanded["sent-seg"] = "negative"`.
   - Confirm rerender filters out purely positive themes.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `09-gherkin-result-case-dedicated-sentiment-tab-and-anomaly-spike/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`dedicated_tab_layout.png`, `anomaly_spike_badge_visible.png`, `negative_themes_filtered.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-09-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/09-gherkin-result-case-dedicated-sentiment-tab-and-anomaly-spike/screenshots/
     ```
  4. Write execution report `result.md` verifying threshold triggers, badge visibility, and filter state.

### Pass/Fail Criteria
- [ ] Dedicated tab mounts with stacked bar and platform rankings.
- [ ] Spike badge renders when `negPct >= 15%` or `negClaims >= 2`.
- [ ] Spike badge is absent in clean baselines.
- [ ] Clicking the badge filters themes to negative drivers.
