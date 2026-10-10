# Execution Modes & Multi-Agent Orchestration

This reference defines the execution modes supported by `audit-ui-ux`, detailing subagent dispatch recipes, persona configurations, and synthesis behavior across execution targets.

---

## 1. Supported Modes Overview

The skill supports three operational execution modes:

| Mode | Active Lenses | Subagent Concurrency | Target Use Case | Default? |
|---|---|---|---|---|
| **`both`** | UI Lens + UX Lens | 2 parallel subagents | Full comprehensive audit covering visual craft and cognitive ergonomics. | **Yes (Default)** |
| **`ui`** | UI Lens only | 1 subagent | Frontend design system audit, visual regression review, spacing/contrast token verification. | No |
| **`ux`** | UX Lens only | 1 subagent | Usability flow review, cognitive ergonomics, Nielsen heuristic evaluation, onboarding critique. | No |

---

## 2. Mode Dispatch Recipes via Antigravity Orchestration

All evaluation subagents are dispatched using Antigravity multi-agent orchestration (`invoke_subagent`):
- `Model: 'inherit'` (Non-negotiable top-tier reasoning intelligence).
- `Workspace: 'branch'` (Isolated workspace to prevent artifact collision).
- Mandatory `AIR_GAP_SYSTEM_BOUNDARY` prompt envelope embedded in subagent instructions (`references/vision-air-gap.md`).

### 2.1 Mode: `both` (Default Dual-Lens Audit)
The orchestrator launches both lenses concurrently:

```python
# Pseudo-orchestration recipe for mode: both
subagent_ui = invoke_subagent(
    Role="UI Design Systems & Precision Specialist",
    Model="inherit",
    Workspace="branch",
    Instruction="""
    <AIR_GAP_SYSTEM_BOUNDARY>
    CRITICAL OPERATING CONSTRAINT: STRICT VISION-FIRST AIR-GAP ACTIVE.
    1. You are an external human observer evaluating the interface purely through optical perception.
    2. You have access ONLY to PNG screenshot files under `audit-artifacts/<YYYY-MM-DD>/`.
    3. You are STRICTLY FORBIDDEN from reading source code, markup, stylesheets, or configuration files.
    4. You are STRICTLY FORBIDDEN from running search/grep commands across the workspace to locate source files matching text seen on screen.
    5. You must NEVER guess or mention component names (e.g. `<Button />`), HTML tags (`<div>`), or CSS classes (`.flex`).
    6. You must describe all element locations using the Visual-Spatial Grounding Framework:
       [Screen Region] > [Container Landmark] > [Relative Flow Position] > [Visual Feature Anchor]
       accompanied by normalized visual coordinates: [top%, left%, width%, height%].
    7. Any finding citing source files, DOM nodes, or code classes will be automatically rejected.
    </AIR_GAP_SYSTEM_BOUNDARY>

    Execute UI Lens evaluation over audit-artifacts/<YYYY-MM-DD>/ following references/ui-lens-persona.md.
    Record all findings using references/reporting-format.md schema.
    """
)

subagent_ux = invoke_subagent(
    Role="Principal Usability & Cognitive HCI Specialist",
    Model="inherit",
    Workspace="branch",
    Instruction="""
    <AIR_GAP_SYSTEM_BOUNDARY>
    CRITICAL OPERATING CONSTRAINT: STRICT VISION-FIRST AIR-GAP ACTIVE.
    1. You are an external human observer evaluating the interface purely through optical perception.
    2. You have access ONLY to PNG screenshot files under `audit-artifacts/<YYYY-MM-DD>/`.
    3. You are STRICTLY FORBIDDEN from reading source code, markup, stylesheets, or configuration files.
    4. You are STRICTLY FORBIDDEN from running search/grep commands across the workspace to locate source files matching text seen on screen.
    5. You must NEVER guess or mention component names (e.g. `<Button />`), HTML tags (`<div>`), or CSS classes (`.flex`).
    6. You must describe all element locations using the Visual-Spatial Grounding Framework:
       [Screen Region] > [Container Landmark] > [Relative Flow Position] > [Visual Feature Anchor]
       accompanied by normalized visual coordinates: [top%, left%, width%, height%].
    7. Any finding citing source files, DOM nodes, or code classes will be automatically rejected.
    </AIR_GAP_SYSTEM_BOUNDARY>

    Execute UX Lens evaluation over audit-artifacts/<YYYY-MM-DD>/ following references/ux-lens-persona.md.
    Record all findings using references/reporting-format.md schema.
    """
)
```

### 2.2 Mode: `ui` (Visual Precision Only)
Only the UI Lens subagent is invoked. The orchestrator produces `AUDIT-REPORT.md` containing only UI Lens findings, marking UX Lens metrics in the Executive Dashboard as `N/A (Mode: UI Only)`.

### 2.3 Mode: `ux` (Usability & Cognitive Laws Only)
Only the UX Lens subagent is invoked. The orchestrator produces `AUDIT-REPORT.md` containing only UX Lens findings, marking UI Lens metrics in the Executive Dashboard as `N/A (Mode: UX Only)`.

---

## 3. Lens Responsibilities & Persona Integration

### UI Lens Responsibilities:
- **Design System Tokens:** Spacing grid consistency (4px/8px rhythm), elevation hierarchy, corner radii harmony.
- **Visual Contrast & Color:** Perceptual lightness contrast (APCA / WCAG 2.2 SC 1.4.3 / SC 1.4.11), color independence.
- **Typography:** Modular type scales, line heights, character measure (45–75 CPL), alignment baselines.
- **Focus & States:** Focus visibility (WCAG 2.2 SC 2.4.11), active depression depth, hover affordances.

### UX Lens Responsibilities:
- **Heuristic Evaluation:** Nielsen's 10 heuristics (visibility of status, system-world match, user freedom, etc.).
- **Cognitive Ergonomics:** Nelson Cowan's 4±1 working memory chunks, cognitive load reduction, recognition vs recall.
- **Motor Control:** Fitts's Law touch target acquisition, single-pointer alternatives (WCAG 2.2 SC 2.5.7 / SC 2.5.8).
- **Task Flows & Error Recovery:** Onboarding friction, error diagnostics, dismissible overlays, escape hatches.

---

## 4. Token Budget & Mode Selection Heuristics

Multi-agent vision analysis requires substantial token allocation for processing high-resolution screenshots. Selecting the appropriate mode optimizes execution speed and token consumption:

- Run **`both`** when preparing for major production releases, client handoffs, end-to-end design QA, or initial full-stack baseline audits.
- Run **`ui`** when verifying frontend PRs, CSS refactors, design token updates, Tailwind migrations, dark mode additions, or responsive layout fixes.
- Run **`ux`** when reviewing new multi-step wizards, checkout conversion funnels, onboarding flows, navigation restructuring, or information architecture changes.
