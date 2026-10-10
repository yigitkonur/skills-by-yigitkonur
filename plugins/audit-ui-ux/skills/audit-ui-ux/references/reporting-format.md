# Unified Finding & Report Schema

This document defines the canonical markdown format for individual UI/UX findings and the consolidated final audit report written to `audit-artifacts/<YYYY-MM-DD>/AUDIT-REPORT.md`.

---

## 1. Severity Calibration Matrix

Every finding must be assigned an objective severity level:

| Severity | Definition & Usability Impact | Examples |
|---|---|---|
| **Catastrophe** | Complete task blocker; user is trapped or cannot complete the primary conversion/task. Zero escape hatch. | Modal cannot be dismissed; required payment CTA invisible below viewport; infinite spinner with no timeout. |
| **Critical** | Severe usability failure or objective accessibility violation (WCAG 2.2 AA). Significantly impairs usability or legal compliance. | Touch target < 24×24px; contrast ratio < 3.0:1 on text; primary action lacks hover/focus feedback; required memorization across steps. |
| **Major** | Noticeable friction or visual inconsistency that degrades trust, slows down completion, or violates design system tokens. | Missing error state recovery; jarring layout shift (CLS); misaligned baselines; inconsistent border radii across sibling cards; crowded padding. |
| **Minor** | Subtle visual nit or polish opportunity. Does not impede task completion or break accessibility standards. | Spacing token slightly inconsistent (14px vs 16px); secondary button elevation slightly too heavy; microcopy phrasing improvement. |

---

## 2. Individual Finding Schema

When an evaluation lens files an issue, it formats the entry as:

```markdown
### [<LENS>-<NN>] <Concise Problem Title>
- **Lens:** UI (Visual Precision) | UX (Cognitive & Usability)
- **Screen:** `<screen-slug>`
- **Observed Asset:** `audit-artifacts/<YYYY-MM-DD>/<screen-slug>/<state>.png`
- **Classification:** <WCAG 2.2 Criterion | Nielsen Heuristic | Cognitive Law | Token System>
- **Severity:** Catastrophe | Critical | Major | Minor
- **Direct Visual Observation:**
  [Describe what is visible on the screenshot as if pointing at it in person. No DOM or source code mentions.]
- **Cognitive / Visual Consequence:**
  [Explain why this impairs the human user or degrades the experience.]
- **Actionable Remediation Intent:**
  [Specify the concrete visual, ergonomic, or design system adjustment to resolve the defect.]
```

---

## 3. Consolidated Report Structure: `AUDIT-REPORT.md`

At the conclusion of Phase 4 (Synthesis), the orchestrator compiles all verified findings into `audit-artifacts/<YYYY-MM-DD>/AUDIT-REPORT.md`:

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
| **Catastrophe** | 0 | 1 | 1 |
| **Critical** | 2 | 2 | 4 |
| **Major** | 4 | 3 | 7 |
| **Minor** | 3 | 1 | 4 |
| **Total Findings** | 9 | 7 | 16 |

### Overall Readiness Verdict
- **Status:** 🛑 BLOCKED (Critical/Catastrophe issues present) | ⚠️ WARN (Major issues only) | ✅ PASS
- **Usability Index:** <Score 0–100 based on severity-weighted deductions>
- **Core Friction Summary:** <2–3 sentences summarizing the primary friction points across the application.>

---

## 2. Screen & State Inventory

| Screen Slug | Captured States | Status |
|---|---|---|
| `dashboard` | `default.png`, `hover.png`, `active.png`, `modal-open.png` | 4 states verified |
| `checkout` | `default.png`, `empty-state.png`, `error-state.png` | 3 states verified |

---

## 3. Priority Action Matrix (Ranked by Impact)

1. **[P0 - Immediate Fix]** `<Issue Title>` — <1-line summary>
2. **[P1 - Release Gate]** `<Issue Title>` — <1-line summary>
3. **[P2 - Quality Polish]** `<Issue Title>` — <1-line summary>

---

## 4. Detailed UI Lens Findings (Design Systems & Visual Precision)
[Render all UI findings in full detail]

---

## 5. Detailed UX Lens Findings (Cognitive Laws & Usability Heuristics)
[Render all UX findings in full detail]
```
