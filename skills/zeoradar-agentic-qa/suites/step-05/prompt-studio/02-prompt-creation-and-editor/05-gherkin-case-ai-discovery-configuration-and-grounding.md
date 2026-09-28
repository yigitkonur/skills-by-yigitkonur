# Test Case 05: AI Discovery Configuration, 1-50 Count Slider & Truth Vault Grounding

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-05-DISCOVERY-CONFIG`
- **Purpose**: Verify that Step 1 (Configuration) of the AI Prompt Discovery Wizard displays brand context, provides interactive topic selection pills and custom topic addition, bounds the prompts-per-topic counter within [1, 50], enforces the 500-character editorial instructions limit, and toggles Brand Hub Truth Vault grounding to include verified brand facts in the synthesis payload.

---

## 2. Tester Brief
The tester will:
1. Open the Prompt Designer Workbench for `[DOMAIN]`.
2. Click `button[data-action="dg-open-ai-discover"]` to open the AI Discovery Wizard.
3. Verify that Step 1 renders with:
   - Monitored Brand Name and primary domain.
   - Pre-populated topic selection pills.
   - Grounding checkbox `[data-action="dg-discover-toggle-grounding"]`.
   - Prompts-per-topic number input (default: 8).
   - Editorial instructions textarea with character counter `0/500`.
4. Toggle topic pills and verify `state.selectedTopics` updates.
5. Add a custom topic `[TOPIC_NAME]` (e.g. "VRV Sistemleri") and confirm it becomes selected.
6. Test boundary limits on prompts-per-topic: assert minimum 1 and maximum 50.
7. Type 520 characters in the instructions field and verify it truncates or blocks at 500 characters.
8. Check the Truth Vault Grounding toggle and confirm `state.useBrandGrounding === true`.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Component Selectors**:
  - Open Discovery Trigger: `button[data-action="dg-open-ai-discover"]`
  - Grounding Toggle: `input[type="checkbox"][data-action="dg-discover-toggle-grounding"]`
  - Prompts Count: `input[type="number"][data-action-input="dg-discover-prompts-count"]`
  - Custom Topic: `input.wizard-input[data-action-input="dg-discover-custom-topic"]`
  - Add Custom Topic: `button[data-action="dg-discover-add-custom-topic"]`
  - Instructions: `textarea[data-action-input="dg-discover-instructions"]`
  - Character Counter: `span#dgDiscoverInstrCount`
  - Generate Button: `button[data-action="dg-discover-generate"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: AI Discovery Wizard Step 1 Configuration & Truth Vault Grounding

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And clicks the AI Discovery button "button[data-action='dg-open-ai-discover']"

  @smoke @ai-wizard @config
  Scenario: Step 1 displays brand context, topic pills, and valid default values
    Then the wizard modal ".zr-wizard.wizard-frame" should open in step "configure"
    And the brand context panel should display the active brand name and domain
    And the prompts per topic input should default to "8"
    And the character counter "span#dgDiscoverInstrCount" should read "0/500"
    And the generate button "button[data-action='dg-discover-generate']" should be enabled

  @boundary @inputs
  Scenario Outline: Prompts-per-topic input enforces strict bounds between 1 and 50
    When the tester enters "<TestCount>" into prompts count "input[data-action-input='dg-discover-prompts-count']"
    Then the clamped input value should equal "<ExpectedCount>"

    Examples:
      | TestCount | ExpectedCount |
      | 0         | 1             |
      | 12        | 12            |
      | 50        | 50            |
      | 75        | 50            |

  @grounding @truth-vault
  Scenario: Toggle Brand Hub Truth Vault grounding and append custom topic
    When the tester enters "VRV Sistemleri" into custom topic input
    And clicks "button[data-action='dg-discover-add-custom-topic']"
    Then a new selected topic pill "VRV Sistemleri" should appear
    When the tester checks the grounding toggle "input[data-action='dg-discover-toggle-grounding']"
    Then the application state "state.useBrandGrounding" should equal true
    And the verified facts badge should indicate grounding is active
```

---

## 5. Visual Checks
1. **Split-Screen Wizard Layout**: `.wizard-split` features a dark summary side pane (`.wizard-side`) on the left and active form fields (`.gen-pane`) on the right.
2. **Topic Pills**: Selected pills have active accent background; unselected pills have subtle border.
3. **Character Counter**: `span#dgDiscoverInstrCount` increments dynamically in real-time as text is typed.

---

## 6. Data and Network Checks
1. **Wizard State Check**:
   ```javascript
   const designerState = window.ZEO_PROMPT_DESIGNER._getState();
   assert.strictEqual(designerState.step, 'configure', 'Wizard must be in configure step');
   assert.ok(designerState.selectedTopics.length > 0, 'At least one topic must be selected');
   assert.ok(designerState.promptsPerTopic >= 1 && designerState.promptsPerTopic <= 50, 'Prompts count bounded [1, 50]');
   ```
2. **Grounding Payload Check**:
   - Verify that when grounding is checked, `dispatchDiscovery` includes `# VERIFIED BRAND GROUND TRUTH` block in the Trigger.dev task payload.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-ai-discovery-configuration-and-grounding/`
- **Execution Model Notice**: Automated through Ego Browser on macOS. Modal screenshots captured to `/tmp/shots/discovery-config-[STEP].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Test execution log and assertion state.
  - `screenshot-configure-step.png`: Full Step 1 configuration view.
  - `screenshot-custom-topic-grounding.png`: View with custom topic and Truth Vault toggle active.
