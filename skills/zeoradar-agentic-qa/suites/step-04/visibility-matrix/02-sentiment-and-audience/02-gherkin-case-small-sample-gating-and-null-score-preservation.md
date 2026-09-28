# Test Case: TC-SNT-02 - Small-Sample Guardrail (<3 Claims) & Strict NULL Score Preservation

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-02`
- **Module:** Sentiment Normalization & Perception (`assets/aei.js`, `assets/sentiment-analytics.js`)
- **Parent Contract:** Spec 06 / Spec 11 (Sentiment Analytics Normalization, rollups.ts:339 Small-Sample Rule)
- **Traceability:** Maps to Source Scenarios `SNT-02`, `SNT-18`, and `SNT-19`
- **Purpose:** Verify that when the total count of evaluative claims is less than 3 (`totalClaims < 3`), the system enforces the small-sample guardrail: rendering a dedicated Pending state card (`.card.aei-sentiment-card.aei-pending-card`) with a Pending pill badge (`.aei-pending-pill`), displaying a disabled progress track (`.aei-sent-bar-wrap.disabled`), strictly preserving `score = null` without mathematical coercion to a false `0%`, and instantly activating the full polarity calculation upon reaching 3 verified claims.

---

## 2. Tester Brief
The tester or automated agent validates the system's honesty regarding statistical significance:
1. Load a project or test fixture where total evaluative claims (positive + negative + neutral + mixed) are fewer than 3 (e.g. 0, 1, or 2 claims).
2. Confirm the UI renders `.card.aei-sentiment-card.aei-pending-card`.
3. Confirm the presence of `.chip.mono.aei-pending-pill` with localized label ("Pending" / "Beklemede").
4. Verify the explanatory copy states: *"Insufficient sentiment signal (< 3 verified evaluative claims detected). At least 3 verified claims are required to establish an honest sentiment polarity baseline."*
5. Verify the disabled polarity bar (`.aei-sent-bar-wrap.disabled`, `opacity: 0.4`).
6. Inspect the underlying JavaScript state: `s.score` must be strictly `null` (never coerced to `0` or `"0%"`).
7. Inject a 3rd evaluative claim (boundary transition 2 -> 3) and verify that the card seamlessly transitions from Pending to the active Polarity Distribution view.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/fresh-brand/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** Brand with `< 3` claims (e.g. `fresh-brand.com`)
- **Claims Count `[EVALUATED_CLAIMS_COUNT]`:** `0`, `1`, `2` (Pending) vs `3` (Active)
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `02-gherkin-result-case-small-sample-gating-and-null-score-preservation/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Small-Sample Sentiment Guardrail and Strict NULL Score Preservation

  Background:
    Given the user is on the "perception" workspace of Zeo Geo-Radar

  Scenario Outline: Small-Sample Guardrail Gating (<3 Evaluative Claims)
    Given the monitored brand has exactly "<ClaimCount>" evaluative claims in telemetry
    When the sentiment card renders in the perception workspace
    Then the card container must have class "aei-pending-card"
    And the card header must display ".chip.mono.aei-pending-pill" with text "Pending" or "Beklemede"
    And the card body must display ".aei-sent-bar-wrap.disabled" with reduced opacity
    And the underlying sentiment score "s.score" must strictly equal null
    And the UI must not display "0%" or false negative indicators

    Examples:
      | ClaimCount | Description                   |
      | 0          | Zero evaluative claims        |
      | 1          | Single isolated claim         |
      | 2          | Two claims (insufficient n=2) |

  Scenario: Exact Boundary Transition from 2 Claims to 3 Claims
    Given the monitored brand currently has 2 evaluative claims and displays "aei-pending-card"
    When a new AI response probe records a 3rd verified evaluative claim
    And the perception workspace re-renders
    Then the card should lose class "aei-pending-card"
    And the pending pill ".aei-pending-pill" should be removed from the DOM
    And the active polarity bar ".aei-sent-bar-wrap:not(.disabled)" should render positive, neutral, and negative fills
    And the sentiment score should be calculated as an active percentage
```

---

## 5. Visual Checks
1. **Pending Card Appearance:** Displays a calm, informational pending state without alarming error banners or red indicators.
2. **Disabled Bar Styling:** `.aei-sent-bar-wrap.disabled` renders with background `var(--border-soft)`, height `10px`, border-radius `5px`, and opacity `0.4`.
3. **Pending Pill Typography:** Monospaced, subtle neutral chip (`.chip.mono.aei-pending-pill`).
4. **Transition Smoothness:** Transition from Pending to Active replaces the disabled track with segmented green/gray/red fills cleanly.

---

## 6. Data and Network Checks
1. **Strict NULL Preservation Verification:**
   ```js
   const s = window.ZEO_SENTIMENT_ANALYTICS.toSentimentShape(rawWire);
   assert(s.score === null, "Score must be strictly null when claims < 3");
   assert(s.score !== 0, "Score must never be coerced to 0 for small samples");
   ```
2. **Total Polarized Math:**
   - Evaluates: `totalClaims = s.claims + s.neutralClaims + s.mixedClaims`.
   - Ensures neutral and mixed claims count towards signal presence but do not skew positive/negative polarity ratios.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `02-gherkin-result-case-small-sample-gating-and-null-score-preservation/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`pending_state_card.png`, `null_score_display.png`, `boundary_transition_active.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-02-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/02-gherkin-result-case-small-sample-gating-and-null-score-preservation/screenshots/
     ```
  4. Write execution report `result.md` verifying state objects, claims counts, and DOM classes.

### Pass/Fail Criteria
- [ ] Claims `< 3` renders `.aei-pending-card` and `.aei-pending-pill`.
- [ ] Disabled polarity bar displays with reduced opacity.
- [ ] `s.score` is strictly preserved as `null` without zero coercion.
- [ ] Transitioning to 3 claims activates the standard polarity card.
