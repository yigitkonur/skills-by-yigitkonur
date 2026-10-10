# Strict Vision-First Air-Gap (Zero Code Leaking)

## 1. The Core Invariant: Pixels Only

The fundamental rule of this audit architecture is the **Strict Vision-First Air-Gap**:

> **Evaluation subagents must NEVER inspect application source code, DOM trees, CSS classes, AST structures, or internal selectors.**

### The Law of Omniscience Bias
When an auditor or an LLM looks at source code (`<div className="flex gap-4 p-6 bg-slate-900 border border-slate-800 rounded-xl">`), it experiences **omniscience bias**:
- It infers intent from variable names, component props, and comments.
- It assumes CSS rules apply without checking whether cascade specificity, overflow clipping, or z-index stacking context breaks rendering.
- It forgives poor visual contrast or misalignment because it "knows what the code intended to do."

**Human users never read source code when interacting with a digital product.**
They see visual light emitted by display pixels. They experience layout shifts, unreadable contrast ratios, crowded touch targets, and ambiguous visual hierarchies strictly through optical perception.

To deliver true human-fidelity review, the audit subagents are deliberately **air-gapped** from the codebase.

---

## 2. Air-Gap Enforcement Protocol

During Phase 3 (Evaluation), the orchestrator enforces the following boundaries on all evaluating agents:

| Allowed Operations | Strictly Banned Operations |
|---|---|
| Inspecting rendered `.png` screenshots via `view_file` | Running `cat`, `grep`, or `view_file` on `.tsx`, `.jsx`, `.vue`, `.svelte`, `.html`, `.css` |
| Measuring relative visual spacing, padding, alignment, typography | Inspecting DevTools Elements panel or reading DOM trees |
| Analyzing color contrast from rendered pixels | Inspecting Tailwind config, CSS variables, or design token files |
| Evaluating visual hierarchy, state clarity, and cognitive flow | Reading component test files, unit tests, or Storybook source files |
| Citing observed UI components by visual appearance ("Primary Blue Submit Button in Modal Footer") | Citing file paths or line numbers (e.g. `src/components/Modal.tsx:42`) |

---

## 3. How to Describe Components Without Source Code

When reporting issues, agents must describe what is visible to the human eye, exactly as a senior designer or product architect would during an in-person design critique:

- **Banned:** `"In src/components/Sidebar.tsx line 48, the NavItem component lacks padding-right."`
- **Mandatory:** `"In the left navigation sidebar under the 'Workspace' section, the active 'Analytics' item's text label runs flush against the right container edge with 0px visual clearance, violating visual padding consistency."`

- **Banned:** `"The div with class 'bg-red-500 text-gray-400' has bad contrast."`
- **Mandatory:** `"The destructive 'Delete Project' button in the danger zone card uses light gray text on a bright red background, producing an unreadable visual contrast ratio of ~2.1:1 (violating WCAG 2.2 AA)."`

---

## 4. Remediation Recommendations Under the Air-Gap

Because the evaluating agent does not read the code, its remediation advice is expressed in **architectural and visual intent**, not verbatim line patches:

- Specify the target visual state: *"Increase horizontal padding from 0px to 16px (`px-4`), align the icon baseline with the label, and ensure the active state container carries at least 4.5:1 text contrast."*
- Specify the design system token intent: *"Normalize card border-radius to the system standard (12px / `rounded-xl`) to eliminate jarring visual discordance with adjacent 8px rounded cards."*
- Specify component grouping: *"Group the 3 separate billing toggles into a single segmented control with clear selected pill styling."*
