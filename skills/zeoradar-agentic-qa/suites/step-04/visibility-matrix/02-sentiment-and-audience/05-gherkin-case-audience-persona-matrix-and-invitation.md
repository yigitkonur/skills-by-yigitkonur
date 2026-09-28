# Test Case: TC-SNT-05 - Audience Persona Matrix & Demographic Invitation

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-05`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, BMD-SNT-04)
- **Traceability:** Maps to Source Scenario `SNT-06`
- **Purpose:** Verify that Section 3 of the Perception workspace (`.card.aei-persona-card`) renders the Audience Persona Simulation Matrix, displays demographic cohort cards (`.aei-p-card`) with Role, Industry Sector, Search Tone, and projected AI Recommendation, or renders an inviting zero-state invitation (`.aei-persona-invitation`) with an action button when no personas are pre-configured.

---

## 2. Tester Brief
The tester or automated agent verifies the audience persona simulation surface:
1. Locate `.card.aei-persona-card` in the Perception workspace.
2. Confirm header contains:
   - Heading: *"Audience Persona Simulation Matrix & Custom Builder"*.
   - Subtitle: *"Simulate how answer engines tailor recommendations across demographic buyer personas."*
   - Primary action button: `button[data-action="aei-open-persona-builder"]`.
3. If personas are configured for the brand:
   - Verify the grid container `.aei-persona-grid` is present.
   - For each `.aei-p-card`, assert presence of:
     - Role & Title in `.aei-p-head strong`.
     - Industry sector in `.aei-p-head .chip.mono`.
     - Communication tone in `.aei-p-meta`.
     - AI Recommendation projection in `.aei-p-reco strong`.
4. If zero personas exist:
   - Verify `.aei-persona-grid` is absent.
   - Verify `.aei-persona-invitation` renders an invitation prompt and a *"Configure Demographic Persona"* button.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Persona Data Variants:** Brand with pre-seeded personas vs Brand with empty personas
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `05-gherkin-result-case-audience-persona-matrix-and-invitation/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Audience Persona Simulation Matrix and Zero-State Invitation

  Background:
    Given the user is on the "perception" workspace of Zeo Geo-Radar
    Then the persona simulation card ".card.aei-persona-card" should be visible

  Scenario: Persona Simulation Matrix Card Layout and Primary Action
    Then the persona card header ".aei-card-head" should display:
      | Element Selector                                   | Purpose                               |
      | h3                                                 | Section title                         |
      | .sub                                               | Explanatory subtitle                  |
      | button[data-action="aei-open-persona-builder"]     | Modal launch trigger button           |

  Scenario: Rendered Demographic Persona Card Anatomy
    Given at least one audience persona is configured
    Then the persona grid ".aei-persona-grid" should be attached to the DOM
    And each persona card ".aei-p-card" should display:
      | Field Selector              | Expected Content Example                               |
      | .aei-p-head strong          | Role (e.g. "Enterprise Procurement Director")          |
      | .aei-p-head .chip.mono      | Industry Sector (e.g. "Technology & SaaS")             |
      | .aei-p-meta                 | Search Tone (e.g. "Tone: Formal & Analytical")         |
      | .aei-p-reco strong          | AI Recommendation (e.g. "Recommended")                 |

  Scenario: Zero-State Demographic Invitation Handling
    Given no audience personas are configured for the active project
    And "window.aeiState.customPersonas" is empty
    Then the persona grid ".aei-persona-grid" should not exist
    And the container ".aei-persona-invitation" should display an invitation message
    And the invitation should contain a button "[data-action='aei-open-persona-builder']"
```

---

## 5. Visual Checks
1. **Persona Card Design:** Responsive card with soft borders, padding `16px`, and clean typography.
2. **Industry Chip Badge:** Monospaced, rounded pill badge (`.chip.mono`) distinguishing industry verticals.
3. **AI Recommendation Highlight:** Bold recommendation status in `.aei-p-reco strong` with subtle accent color.
4. **Empty State Cleanliness:** Centered layout, calm typography, and a prominent primary button.

---

## 6. Data and Network Checks
1. **Persona Aggregation Hierarchy:**
   - 1st Priority: Answers containing `personaId`.
   - 2nd Priority: Project profile `p.personas`.
   - 3rd Priority: User-created custom personas `window.aeiState.customPersonas`.
2. **No Data Bleed:** Personas from one project must not leak into another project upon switching brands.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `05-gherkin-result-case-audience-persona-matrix-and-invitation/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`persona_matrix_grid.png`, `persona_card_anatomy.png`, `persona_empty_invitation.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-05-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/05-gherkin-result-case-audience-persona-matrix-and-invitation/screenshots/
     ```
  4. Write execution report `result.md` verifying persona counts, roles, industries, and DOM nodes.

### Pass/Fail Criteria
- [ ] Persona card renders header with create button.
- [ ] Persona cards display role, industry chip, tone, and recommendation.
- [ ] Empty state invitation renders when 0 personas exist.
- [ ] No layout broken elements or console errors.
