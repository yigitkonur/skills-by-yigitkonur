# Unified Finding & Report Schema

This document defines the canonical specification for individual UI/UX findings and the consolidated final audit report written to `audit-artifacts/<YYYY-MM-DD>/AUDIT-REPORT.md`.

Findings must be deterministically parseable and directly actionable by both human engineers and downstream autonomous coding agents (such as `build-frontend`).

---

## 1. Severity Calibration & Priority Matrix

Every finding must be assigned an objective severity level and corresponding release priority:

| Severity | Priority | Definition & Usability Impact | Release Gate Action | Examples |
|---|---|---|---|---|
| **Catastrophe** | **P0** | Complete task blocker; user is trapped or cannot complete primary task. Zero escape hatch. | **Release Blocker.** Immediate fix required before proceeding. | Modal close 'X' missing and backdrop non-dismissible; payment submit button clipped below viewport with no scroll; infinite loading spinner without timeout. |
| **Critical** | **P1** | Objective accessibility failure (WCAG 2.2 AA) or severe usability barrier. Significantly impairs usability or legal compliance. | **Quality Gate Blocker.** Must be resolved before production release. | Touch target < 24×24px (WCAG 2.5.8); text contrast < 3.0:1 (WCAG 1.4.3); destructive action without confirmation; unannounced state change. |
| **Major** | **P2** | Noticeable friction or visual inconsistency that degrades trust, slows down completion, or breaks design system tokens. | **Sprint Priority.** Scheduled for remediation in active iteration. | Missing loading skeleton causing layout shift (CLS); misaligned baselines; inconsistent border radii across sibling cards; crowded form field padding. |
| **Minor** | **P3** | Subtle visual nit or polish opportunity. Does not impede task completion or violate accessibility standards. | **Polish Backlog.** Non-blocking refinement. | Spacing token slightly off (14px vs 16px); elevation shadow slightly too prominent; minor microcopy wording improvement. |

---

## 2. Standardized Taxonomy Enumeration

To allow automated categorization and lookup by downstream fix agents, all findings must reference canonical rule IDs:

### WCAG 2.2 Accessibility Criteria:
- `WCAG_2.2_SC_1.4.3`: Contrast (Minimum) (4.5:1 text, Level AA)
- `WCAG_2.2_SC_1.4.11`: Non-text Contrast (3.0:1 UI components/borders, Level AA)
- `WCAG_2.2_SC_2.4.7`: Focus Visible (Level AA)
- `WCAG_2.2_SC_2.4.11`: Focus Appearance (Level AAA)
- `WCAG_2.2_SC_2.4.12`: Focus Not Obscured (Minimum) (Level AA)
- `WCAG_2.2_SC_2.5.7`: Dragging Movements (Level AA)
- `WCAG_2.2_SC_2.5.8`: Target Size (Minimum) (24×24px, Level AA)

### Nielsen's 10 Usability Heuristics:
- `NIELSEN_01_VISIBILITY_SYSTEM_STATUS`
- `NIELSEN_02_MATCH_SYSTEM_REAL_WORLD`
- `NIELSEN_03_USER_CONTROL_FREEDOM`
- `NIELSEN_04_CONSISTENCY_STANDARDS`
- `NIELSEN_05_ERROR_PREVENTION`
- `NIELSEN_06_RECOGNITION_OVER_RECALL`
- `NIELSEN_07_FLEXIBILITY_EFFICIENCY`
- `NIELSEN_08_AESTHETIC_MINIMALIST_DESIGN`
- `NIELSEN_09_ERROR_RECOVERY`
- `NIELSEN_10_HELP_DOCUMENTATION`

### Empirical Cognitive & Motor Laws:
- `COGNITIVE_FITTS_LAW`: Index of Difficulty, Target Acquisition
- `COGNITIVE_HICK_LAW`: Simple Decision Reaction Time
- `COGNITIVE_COWAN_WORKING_MEMORY`: Nelson Cowan 4±1 Working Memory Capacity
- `COGNITIVE_DOHERTY_THRESHOLD`: Feedback $\le 100\text{ms}$, INP $\le 200\text{ms}$
- `GESTALT_PROXIMITY`: Relative whitespace and visual clustering
- `GESTALT_COMMON_REGION`: Card containers and visual boundaries
- `DESIGN_TOKEN_SPACING`: 4px/8px Spatial rhythm adherence
- `DESIGN_TOKEN_TYPOGRAPHY`: Modular typographic scale adherence

---

## 3. Individual Finding Schema (Dual YAML + Markdown)

To ensure findings are deterministically parseable by downstream agents while remaining readable for human developers, every finding must be recorded using this hybrid block format:

````markdown
### [<LENS>-<NN>] <Concise Problem Title>

```yaml finding-spec
id: "<LENS>-<NN>"
lens: "UI" # UI | UX
screen: "<screen-slug>"
observed_asset: "audit-artifacts/<YYYY-MM-DD>/<screen-slug>/<state>.png"
severity: "Critical" # Catastrophe | Critical | Major | Minor
priority: "P1" # P0 | P1 | P2 | P3
rule:
  type: "WCAG_2.2" # WCAG_2.2 | NIELSEN_HEURISTIC | COGNITIVE_LAW | DESIGN_TOKEN
  id: "WCAG_2.2_SC_2.5.8"
  name: "Target Size (Minimum)"
  level: "AA"
location:
  landmark: "[Screen Region] > [Container Landmark] > [Relative Flow Position] > [Visual Feature Anchor]"
  quadrant: "Top-Right"
  bounding_box:
    top: 2.4
    left: 92.1
    width: 2.2
    height: 3.5
    unit: "percent"
visual_fix:
  target_visual_state: "Expand interactive hit bounding box to minimum 24×24px with ≥8px spacing to adjacent avatar."
  target_parameters:
    min_width: "24px"
    min_height: "24px"
    padding: "8px"
    touch_spacing: "8px"
  anti_patterns:
    - "Do not scale down the icon; expand container padding."
    - "Do not overlap hit targets of adjacent buttons."
```

- **Screen:** `<screen-slug>`
- **Observed Asset:** `audit-artifacts/<YYYY-MM-DD>/<screen-slug>/<state>.png`
- **Location:** `<landmark>` (`[<quadrant>]`, `[top: <top>%, left: <left>%, w: <width>%, h: <height>%]`)
- **Severity / Priority:** `<severity>` (`<priority>`)
- **Violated Rule:** `<rule.name>` (`<rule.id>`)
- **Direct Visual Observation:**
  [Detailed description of what is seen on the screenshot as an external human observer. Zero code, DOM, or CSS mentions.]
- **Cognitive / Visual Consequence:**
  [Explain why this impairs the user, causes cognitive friction, or violates accessibility.]
- **Deterministic Visual Fix Recommendation:**
  [Concrete visual end-state specification: target dimensions, padding, contrast, and alignment.]
````

---

## 4. Consolidated Report Structure: `AUDIT-REPORT.md`

At the conclusion of the audit, the orchestrator compiles all findings into `audit-artifacts/<YYYY-MM-DD>/AUDIT-REPORT.md`:

```markdown
# Vision-First UI & UX Audit Report
**Audit Date:** <YYYY-MM-DD>  
**Target:** <Application Name / URL / Mobile Package>  
**Execution Mode:** `both` | `ui` | `ux`  
**Capture Engine:** `ego-browser` (Web) | `test-by-maestro` (Mobile)

---

## 1. Executive Dashboard

| Metric | UI Lens | UX Lens | Total Combined |
|---|---|---|---|
| **Catastrophe (P0)** | 0 | 1 | 1 |
| **Critical (P1)** | 2 | 2 | 4 |
| **Major (P2)** | 4 | 3 | 7 |
| **Minor (P3)** | 3 | 1 | 4 |
| **Total Findings** | 9 | 7 | 16 |

### Overall Readiness Verdict
- **Status:** 🛑 BLOCKED (Critical/Catastrophe issues present) | ⚠️ WARN (Major issues only) | ✅ PASS
- **Usability Index:** <Score 0–100 based on severity-weighted deductions>
- **Core Friction Summary:** <2–3 sentences summarizing primary friction points across the application.>

---

## 2. Screen & State Inventory

| Screen Slug | Captured States | Status |
|---|---|---|
| `dashboard` | `default.png`, `hover.png`, `active.png`, `modal-open.png` | 4 states verified |
| `checkout` | `default.png`, `empty-state.png`, `error-state.png` | 3 states verified |

---

## 3. Priority Action Matrix (Ranked by Impact)

1. **[P0 - Immediate Blocker]** `[UX-01]` Modal Trap in Checkout Flow — Add dismiss button and escape hatch.
2. **[P1 - Release Gate]** `[UI-01]` Top-Right Header Notification Bell Target Size — Expand hit target to >= 24×24px.
3. **[P1 - Release Gate]** `[UI-02]` Danger Zone Delete Button Contrast — Raise contrast to >= 4.5:1.
4. **[P2 - Quality Polish]** `[UI-03]` Billing Card Padding Inconsistency — Normalize internal padding to 16px.

---

## 4. Detailed UI Lens Findings (Design Systems & Visual Precision)
[Render all UI findings using the Dual YAML + Markdown format]

---

## 5. Detailed UX Lens Findings (Cognitive Laws & Usability Heuristics)
[Render all UX findings using the Dual YAML + Markdown format]
```

---

## 5. Downstream Fix Agent Ingestion Protocol

Autonomous downstream coding agents (such as `build-frontend`) consume `AUDIT-REPORT.md` using the following deterministic 4-step pipeline:

```
┌────────────────────────────────────────────────────────────────────────┐
│             DOWNSTREAM FIX AGENT INGESTION PROTOCOL                    │
├────────────────────────────────────────────────────────────────────────┤
│ STEP 1: PARSE & TRIAGE                                                 │
│ Extract all ```yaml finding-spec blocks from AUDIT-REPORT.md.          │
│ Filter and sort by Priority: P0 (Catastrophe) → P1 (Critical) → P2/P3. │
├────────────────────────────────────────────────────────────────────────┤
│ STEP 2: VISUAL-SPATIAL ELEMENT GROUNDING                               │
│ 1. Match `screen` to application route/page in codebase.               │
│ 2. Trace `location.landmark` down component tree (Header → Actions).   │
│ 3. Match `location.bounding_box` against rendered element bounds.     │
│ 4. NEVER guess components from nonexistent names; ground on structure. │
├────────────────────────────────────────────────────────────────────────┤
│ STEP 3: APPLY DETERMINISTIC VISUAL FIX                                 │
│ 1. Apply `visual_fix.target_parameters` (padding, dimensions, tokens). │
│ 2. Strictly adhere to `visual_fix.anti_patterns`.                      │
│ 3. Adjust styles in target component stylesheet / Tailwind classes.    │
├────────────────────────────────────────────────────────────────────────┤
│ STEP 4: CLOSED-LOOP VISUAL RE-VERIFICATION                             │
│ 1. Trigger `ego-browser` or `test-by-maestro` to capture new screen.   │
│ 2. Run `validate-capture-gate.sh` to ensure intact artifacts.          │
│ 3. Verify optical resolution of finding without regression.            │
└────────────────────────────────────────────────────────────────────────┘
```

### Ingestion Details by Step:

### Step 1: Parse & Triage
1. Read `audit-artifacts/<YYYY-MM-DD>/AUDIT-REPORT.md`.
2. Extract all ```yaml finding-spec``` blocks using standard YAML parsing.
3. Group findings by priority: resolve all `P0` (Catastrophe) first, followed by `P1` (Critical), then `P2` and `P3`.

### Step 2: Visual-Spatial Element Grounding
1. Map `finding.screen` to the relevant route or view template in the codebase (e.g. `screen: "dashboard"` -> `src/pages/dashboard/` or `app/dashboard/`).
2. Follow `finding.location.landmark` down the component tree (e.g., `Sticky Header > Right Utility Actions > Notification Bell Button` -> `<Header>` -> `<div className="actions">` -> `<button aria-label="Notifications">`).
3. Correlate with `finding.location.bounding_box` and `finding.observed_asset` to confirm exact target element identity.
4. **Invariant:** Fix agents must never guess component names from missing code mentions; locate elements purely by structural position in layout.

### Step 3: Implement Deterministic Visual Fix
1. Apply the target visual parameters specified in `finding.visual_fix.target_parameters` (e.g. set `min-w-[24px] min-h-[24px] p-2`).
2. Respect all declared `finding.visual_fix.anti_patterns`.
3. Preserve surrounding layout stability and design tokens.

### Step 4: Closed-Loop Verification Gate
1. Trigger the capture engine (`ego-browser` or `test-by-maestro`) to generate new screenshots for the modified screen states.
2. Run `validate-capture-gate.sh` to confirm artifact integrity.
3. Visually confirm that the target defect is resolved without introducing secondary visual regressions.
