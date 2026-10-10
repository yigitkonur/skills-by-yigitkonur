# Strict Vision-First Air-Gap (Zero Code Leaking)

## 1. The Core Invariant: Pixels Only

The fundamental architectural invariant of this audit framework is the **Strict Vision-First Air-Gap**:

> **Evaluation subagents must NEVER inspect application source code, DOM trees, CSS classes, AST structures, internal selectors, or workspace text files.**

### The Law of Omniscience Bias
When an auditor or an LLM inspects source code (`<div className="flex gap-4 p-6 bg-slate-900 border border-slate-800 rounded-xl">`), it experiences **omniscience bias**:
- It infers human intent from component names, props, variable names, and code comments.
- It assumes layout rules work as intended without checking whether CSS cascade specificity, clipping bounds, z-index stacking, or font rendering broke visual output.
- It forgives illegible contrast ratios or misaligned baselines because it "knows what the developer intended."

**Human users never read source code when using software.**
They experience digital products purely through photons emitted from physical displays. They navigate via optical hierarchy, perceive contrast directly, and encounter usability obstacles strictly in the rendered visual medium.

To deliver true human-fidelity evaluation, all audit subagents are strictly **air-gapped** from the codebase.

---

## 2. The Four Prohibited Inspection Vectors

During evaluation, orchestrators and subagents must enforce strict boundaries across four distinct vectors:

| Inspection Vector | Forbidden Operations | Permitted Visual Operations |
|---|---|---|
| **Vector A: Source Code & AST** | Running `cat`, `grep`, `view_file`, or AST parsers on `.tsx`, `.jsx`, `.vue`, `.svelte`, `.html`, `.css`, `.swift`, `.kt` files. | Inspecting rendered `.png` screenshots under `audit-artifacts/<YYYY-MM-DD>/` via `view_file`. |
| **Vector B: Workspace String Grepping** | Using `grep_search`, `rg`, `ag`, or terminal commands to search the repository for button labels, headers, or text seen in screenshots. | Reading text visually from rendered screenshot pixels. |
| **Vector C: DOM & DevTools Trees** | Inspecting Chrome DevTools Elements panel, querying CDP node IDs, reading accessibility tree dumps, injecting JavaScript, or calling `window.getComputedStyle`. | Measuring visual alignment, spacing, typographic hierarchy, and contrast directly from rendered pixels. |
| **Vector D: Config & Design Tokens** | Inspecting `tailwind.config.*`, CSS custom property files, or Figma token JSONs to check color codes or spacing values. | Evaluating perceived color contrast, spacing rhythm, and border radius harmony purely from visual output. |

### Component Name Guessing Trap
Evaluators must NEVER invent or hallucinate internal component names (e.g. `<BillingModalHeader />`, `<ActionDropdownContainer />`, `<CustomSelectInput />`) or HTML/CSS selectors. Describing elements using non-existent code identifiers misleads developers and downstream fix agents. All elements must be identified solely by their visual appearance and spatial position.

---

## 3. Visual-Spatial Grounding Framework

Because evaluators do not have access to source code, DOM IDs, or CSS classes, they must locate UI elements using the **Visual-Spatial Grounding Framework**. This framework provides unambiguous dual-layer localization for both humans and downstream automated fix agents (`build-frontend`).

### Layer 1: Directional Landmark Hierarchy
Evaluators describe element locations using a standardized 4-part hierarchical path:
```
[Screen Region / Chrome] > [Container Landmark] > [Relative Flow Position] > [Visual Feature Anchor]
```

#### Taxonomy Standards:
1. **Screen Region / Chrome:**
   - `Sticky Header` / `Top App Bar`
   - `Left Navigation Sidebar`
   - `Main Content Area`
   - `Right Inspector Panel`
   - `Sticky Footer / Bottom Action Bar`
   - `Overlay Modal / Dialog Window`
   - `Slide-over Drawer / Sheet`
   - `Floating Toast / Notification Banner`
2. **Container Landmark:**
   - High-level visual container identifiable by borders, backgrounds, elevation cards, or section headers (e.g., `Billing Summary Card`, `Hero Conversion Section`, `Search & Filter Toolbar`, `User Profile Dropdown Menu`, `Line-Item Table Row 2`).
3. **Relative Flow Position:**
   - Position within container (e.g., `Top-Right Utility Cluster`, `Bottom-Center Action Bar`, `Directly Below Password Input`, `Leading Item in Segmented Control`).
4. **Visual Feature Anchor:**
   - Concrete visual styling and label (e.g., `'Upgrade Plan' Purple Pill Button`, `Destructive Red 'Delete' Button with Trash Icon`, `Muted Gray Caption Text`).

### Layer 2: Normalized Bounding Coordinates
Every finding must include normalized visual bounding coordinates:
- **`quadrant`**: Standard 3×3 grid anchor (`Top-Left`, `Top-Center`, `Top-Right`, `Mid-Left`, `Mid-Center`, `Mid-Right`, `Bottom-Left`, `Bottom-Center`, `Bottom-Right`) or overlay anchor (`Sticky-Header`, `Sticky-Footer`, `Modal-Center`, `Drawer-Right`, `Bottom-Sheet`).
- **`bounding_box`**: Normalized percentage coordinates (`top`, `left`, `width`, `height`) representing values between `0.0%` and `100.0%` relative to the captured viewport:
  ```yaml
  location:
    landmark: "Sticky Header > Right Utility Actions > Notification Bell Button"
    quadrant: "Top-Right"
    bounding_box:
      top: 2.4
      left: 92.1
      width: 2.2
      height: 3.5
      unit: "percent"
  ```

---

## 4. Subagent Prompt Envelope & System Boundary

When the orchestrator invokes evaluation subagents, it must wrap the agent instructions with this mandatory system boundary:

```markdown
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
```

---

## 5. Comparative Examples: Air-Gapped vs Code-Leaked Descriptions

### Example 1: Navigation Spacing Defect
- ❌ **Code-Leaked (Banned):**
  `"In src/components/Sidebar.tsx line 48, the NavItem component for Analytics has className='pr-0' which removes right padding."`
- ❌ **Grep-Assisted (Banned):**
  `"Grepped workspace for 'Analytics' and found Sidebar.module.css; the .nav-link-active selector lacks padding-right."`
- ✅ **Air-Gapped & Spatially Grounded (Mandatory):**
  `"In Left Navigation Sidebar > Workspace Section > Navigation List, the active 'Analytics' item (Location: [Mid-Left], top: 24.2%, left: 1.5%, w: 14.8%, h: 3.8%) has its text label running flush against the right container border with 0px visual clearance, violating internal component padding consistency."`

### Example 2: Inaccessible Contrast on Destructive Button
- ❌ **Code-Leaked (Banned):**
  `"The DeleteButton component in DangerZone.tsx sets color to #f87171 on #ef4444 background, failing contrast."`
- ✅ **Air-Gapped & Spatially Grounded (Mandatory):**
  `"In Main Content Area > Danger Zone Card > Action Footer, the destructive 'Delete Project' button (Location: [Bottom-Right], top: 82.5%, left: 74.0%, w: 12.5%, h: 4.2%) uses light pink text (#f87171) on a solid red background (#ef4444), producing an illegible visual contrast ratio of ~1.9:1, violating WCAG 2.2 SC 1.4.3."`

---

## 6. Remediation Recommendations Under the Air-Gap

Because the evaluating agent does not read the code, its remediation advice is expressed in **architectural, dimensional, and visual intent**, not verbatim line patches or guessed variable names:

- **Specify concrete visual target states:** *"Increase horizontal padding to 16px, align the icon baseline with the label, and ensure the active state container carries at least 4.5:1 text contrast."*
- **Specify measurable target parameters:** Provide exact pixel dimensions, token scales (e.g. `min_width: 24px`, `min_height: 24px`, `padding: 8px`), and contrast targets without referencing internal CSS classes.
- **Specify explicit anti-patterns:** Guide downstream fix agents on what to avoid (e.g., *"Do not shrink the icon glyph to achieve clearance; expand the parent container hit area."*).
