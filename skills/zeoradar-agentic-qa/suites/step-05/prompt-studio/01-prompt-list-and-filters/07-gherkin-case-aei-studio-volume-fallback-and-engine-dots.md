# Test Case 07: AEI Volume Fallback Hierarchy & 5-Engine Win/Loss Outcome Dots

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-07-VOLUME-ENGINEDOTS`
- **Purpose**: Verify that the Prompts & Citations Studio renders the 3-tier search volume fallback hierarchy (`aiv` → `gv` → unmeasured dash `–`) and displays the 5-engine micro-indicator cluster (ChatGPT, Perplexity, Gemini, Claude, Google AI Mode) with accurate win/loss status classes (`won`, `partial`, `lost`, `unmeasured`) and informative tooltips.

---

## 2. Tester Brief
The tester will navigate to `[APP_URL]/#/[SLUG]/visibility?workspace=studio` and:
1. Inspect `.aei-master-item` elements in the master prompt list.
2. Verify the search volume readout logic in the second row of each item:
   - When AI Volume (`aiv`) is present, it displays the localized integer without prefix.
   - When only Google Volume (`gv`) is present, it renders with `"GV: "` prefix.
   - When neither is present, it renders an unmeasured dash `–` with `title="Volume unmeasured"`.
3. Locate the 5-engine mini-dots cluster (`.aei-m-dots`) on prompt rows and assert:
   - Exactly 5 micro-dots are rendered per prompt row.
   - Each dot possesses one of the 4 valid outcome classes (`won`, `partial`, `lost`, `unmeasured`).
   - Hovering each dot reveals a title attribute describing the platform and ranking outcome.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/visibility?workspace=studio`
- **Pre-existing Data**: Tracked prompts with known measurement outcomes across the 5 models.
- **Micro-Dot Selectors**: `.aei-m-dots`, `.aei-mini-dot`
- **Outcome Status Classes**: `.won`, `.partial`, `.lost`, `.unmeasured`

---

## 4. Gherkin Scenario

```gherkin
Feature: AEI Studio Search Volume Fallback & 5-Engine Micro-Dots

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompts & Citations Studio at "[APP_URL]/#/[SLUG]/visibility?workspace=studio"
    And the workspace container ".aei-studio-workspace" has rendered

  @smoke @aei @volume
  Scenario Outline: Verify volume resolution follows the strict three-tier fallback hierarchy
    Given a prompt query exists with aiv value "<AIV>" and gv value "<GV>"
    When the tester inspects the volume label for this prompt in ".aei-master-item"
    Then the displayed volume text should match "<ExpectedDisplay>"
    And any unmeasured dash should contain the tooltip "Volume unmeasured"

    Examples:
      | AIV  | GV   | ExpectedDisplay |
      | 1450 | 800  | 1,450           |
      | null | 620  | GV: 620         |
      | null | null | –               |

  @aei @engine-dots
  Scenario: Each prompt item renders 5 engine mini-dots with valid status and platform tooltip
    When the tester inspects the engine dots container ".aei-m-dots" on the first prompt item
    Then the container must contain exactly 5 child elements with class ".aei-mini-dot"
    And every dot must carry one of the outcome classes "won", "partial", "lost", or "unmeasured"
    When the tester inspects the "title" attribute of each dot
    Then the tooltip must specify one of "ChatGPT", "Perplexity", "Gemini", "Claude", or "AI Mode"
```

---

## 5. Visual Checks
1. **Engine Dots Alignment**: The 5 mini-dots render horizontally in `.aei-m-dots` with 4px circular dimensions and 3px margins.
2. **Outcome Color Coding**:
   - `won`: Green accent fill.
   - `partial`: Amber / yellow fill.
   - `lost`: Muted red / grey fill.
   - `unmeasured`: Subtle dashed or neutral border.
3. **Volume Readout Typography**: Volume strings render in small muted mono font (`.small.dim`).

---

## 6. Data and Network Checks
1. **Volume Hierarchy Logic Check**:
   ```javascript
   const items = document.querySelectorAll('.aei-master-item');
   items.forEach(item => {
     const volText = item.querySelector('.aei-m-row2 span:last-child').textContent.trim();
     assert.ok(
       /^[0-9,]+$/.test(volText) || volText.startsWith('GV: ') || volText === '–',
       `Volume text "${volText}" must conform to fallback specification`
     );
   });
   ```
2. **Engine Dots Count Assertion**:
   ```javascript
   const dotContainers = document.querySelectorAll('.aei-master-item .aei-m-dots');
   dotContainers.forEach(container => {
     assert.strictEqual(container.children.length, 5, 'Every prompt item must render exactly 5 engine dots');
   });
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-aei-studio-volume-fallback-and-engine-dots/`
- **Execution Model Notice**: Remote test execution runs via Ego Browser on macOS. Micro-dot hover screenshots and volume elements are captured to `/tmp/shots/aei-dots-[PROMPT_ID].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Execution log and assertion status.
  - `screenshot-volume-hierarchy.png`: Visual verification of `aiv`, `gv`, and `–` readouts.
  - `screenshot-engine-dots-hover.png`: Tooltip display on engine micro-dot hover.
