# The 30 Laws of UX — Scientifically Grounded Catalog

An authoritative, empirically grounded catalog of the **30 Laws of UX**, categorizing each principle by scientific domain, debunking common design myths, and specifying exact mathematical and standard formulations.

---

## 1. Category Demarcation

To prevent category errors, the 30 principles are organized into four distinct tiers:
1. **Empirical Motor & Perceptual Laws:** Formally validated with mathematical models and physiological constants.
2. **Cognitive Psychology & Working Memory Limits:** Grounded in peer-reviewed neuroscience and short-term memory experiments.
3. **Gestalt Principles of Visual Perception:** Validated rules of how human visual cortex groups visual stimuli.
4. **HCI Design Heuristics & Philosophical Principles:** Operational heuristics and rules of thumb (clearly distinguished from physiological laws).

---

## 2. Empirical Motor & Perceptual Laws

### 1. Fitts's Law (Paul Fitts, 1954; I. Scott MacKenzie, 1992)
- **Principle:** Movement time ($MT$) to acquire a target is a logarithmic function of target distance ($D$) and width ($W$).
- **Mathematical Model (Shannon Formulation):**
  $$MT = a + b \cdot \log_2\left(\frac{D}{W} + 1\right)$$
  Where $\text{Index of Difficulty } (ID) = \log_2\left(\frac{D}{W} + 1\right)$ bits.
- **Scientific Corrections:**
  - *Debunked Rule:* There is no such thing as an arbitrary linear "200px distance rule". Difficulty scales logarithmically with the ratio $D/W$, not linearly.
  - *Desktop Edge Invariant:* Desktop screen edges and corners provide *infinite target depth* ($W \to \infty$), making $ID \to 0$ and acquisition near-instantaneous.
  - *Touch Surface Reality:* On mobile touchscreens, edges do not stop fingers. Acquisition is governed by finger contact pads (8–10mm) and thumb reach zones (Natural, Stretch, Hard).
- **Target Size & Spacing Standards (WCAG 2.2 SC 2.5.8 Level AA):**
  - **Normative Minimum:** Pointer target size must be at least **24 by 24 CSS pixels**.
  - **Spacing Circle Exception:** If a target's bounding box is smaller than 24×24 CSS px, a 24 CSS px diameter circle centered on the target must not intersect any other target or another target's spacing circle.
    - *Center-to-Center Euclidean Distance:* For targets $A$ and $B$ at $(x_A, y_A)$ and $(x_B, y_B)$:
      $$\sqrt{(x_A - x_B)^2 + (y_A - y_B)^2} \ge 24\text{ CSS px}$$
    - *Edge-to-Edge Clearance Spacing:* If target $A$ has width $W < 24\text{px}$, clearance spacing $S$ to adjacent target $B$ must satisfy:
      $$S \ge 24\text{px} - W$$
  - **Inline Exception:** Targets within a sentence or text block (e.g., inline hyperlinks, footnote superscripts) are exempt.
  - **User Agent Control Exception:** Unstyled native HTML controls determined entirely by the browser (e.g. default `<input type="checkbox">`).
  - **Essential Exception:** Presentations legally or functionally essential to the information conveyed (e.g., map pins, digital piano keys, visual graphic handles).
- **Cross-Platform Target Size Comparison Matrix:**

| Standard / Design System | Minimum Interactive Target | Minimum Separation Spacing | Modality & Context |
|---|---|---|---|
| **WCAG 2.2 SC 2.5.8 (Level AA)** | **24 × 24 CSS px** | Spacing circle $\ge 24\text{px}$ diameter ($S \ge 24\text{px} - W$) | All pointer surfaces (mouse, touch, stylus) |
| **WCAG 2.2 SC 2.5.5 (Level AAA)** | **44 × 44 CSS px** | None required if target $\ge 44\text{px}$ | Enhanced motor accessibility |
| **Apple Human Interface Guidelines (HIG)** | **44 × 44 pt** | $\ge 8\text{ pt}$ padding | iOS / iPadOS touch surfaces |
| **Google Material Design 3 (M3)** | **48 × 48 dp** | $\ge 8\text{ dp}$ spacing | Android touch / desktop surfaces |
| **Microsoft Fluent Design System** | **32 × 32 px** (desktop) / **40 × 40 px** (touch) | $\ge 4\text{ px}$ margin | Windows / Web hybrid inputs |

- **Visual Evaluation Protocol:** Inspect icon buttons, table row actions, and close buttons on mobile viewports (`390×844`, `360×800`). If interactive hit area is $< 24\text{px}$ and spacing to adjacent target is $< 12\text{px}$, flag as **Critical (WCAG 2.2 SC 2.5.8 AA)**. If target is between $24\text{px}$ and $44\text{px}$ on a touch viewport, flag as **Major (Ergonomic Touch Friction / Apple HIG / M3 Violation)**.

### 1B. Dragging Movement Alternatives (WCAG 2.2 SC 2.5.7 Level AA)
- **Principle:** All functionality that uses a dragging movement for operation must be achievable via a **single pointer without dragging**, unless dragging is essential.
- **Dragging Definition:** An interaction where a pointer engages an element with pointer-down, moves along a path while maintaining contact, and releases on pointer-up (e.g., drag-and-drop sortable lists, kanban card movement, sliders, map panning, swipe-to-dismiss).
- **Essential Exception:** Freeform drawing, digital signatures, or visual canvas manipulation where dragging is the intrinsic task.
- **Single-Pointer Non-Dragging Alternatives Catalog:**

| Interactive Dragging Pattern | Required Accessible Non-Dragging Alternative |
|---|---|
| **Sortable List / Reorderable Table** | Dedicated Up/Down arrow buttons on each item, a numeric position input field, or a "Move to position..." dropdown menu. |
| **Kanban Board Column Transfer** | "Move to [Column Name]" dropdown button or context menu on each card. |
| **Continuous Value Slider** | Tapping anywhere on the slider track jumps the thumb to that position, supplemented by stepper buttons (+ / -) or an editable numeric text input. |
| **Pan & Zoom Canvas / Maps** | Dedicated directional pan buttons (North, South, East, West) and Zoom In/Out (+ / -) controls. |
| **Swipe-to-Dismiss / Swipe-to-Action** | Persistent action buttons visible on the row (e.g., Trash / Archive button) or an overflow (More `...`) action sheet. |
| **Range Slider (Two Thumbs)** | Two independent numeric input fields for minimum and maximum bounds. |

- **Visual Evaluation Protocol:** When inspecting `default.png`, `hover.png`, and `active.png`, if an interface displays drag handles ($\equiv$, grab cursor) or slider thumbs with **no visible single-pointer tap controls**, flag as **Critical (WCAG 2.2 SC 2.5.7 Violation)**.

### 2. Hick's Law (Hick-Hyman Law, 1952–1953)
- **Principle:** Reaction time ($RT$) increases logarithmically with the number of equally probable alternatives.
- **Mathematical Model:**
  $$RT = b \cdot \log_2(n + 1)$$
- **Scientific Corrections & Scope Boundary:**
  - *Strict Applicability:* Applies **only** to simple stimulus-response reaction tasks (e.g. reacting to lights, simple emergency alerts).
  - *Complex Decision-Making Boundary:* Does **not** apply to qualitative decisions, reading comprehension, or hierarchical search.
  - *Choice Overload Meta-Analyses:* Meta-analyses (Scheibehenne et al. 2010; Chernev et al. 2015) demonstrate that choice overload is moderated by task difficulty, sorting/filtering tools, and preference clarity. Do not artificially limit necessary product options when categorization and filters can be provided.

### 3. Weber-Fechner Law of Just Noticeable Difference
- **Principle:** The perceived change in a stimulus is proportional to the initial magnitude of the stimulus ($\Delta I / I = k$).
- **UI/UX Application:** Micro-interactions, volume sliders, dark-mode brightness steps, and contrast gradients must scale geometrically, not linearly, for the human eye to perceive even steps.

### 3B. Spatial Frequency Contrast Sensitivity & The APCA Model (Somers, W3C Silver / WCAG 3)
- **Sensory Biophysics Foundation:** The human eye does not perceive contrast as a flat ratio of two color hex codes. Perceptual contrast is governed by the **Contrast Sensitivity Function (CSF)** of the visual cortex, which is highly dependent on **spatial frequency** (stroke width, font weight, and character size).
- **The Fundamental Mathematical Flaws of WCAG 2.x Relative Luminance Contrast:**
  WCAG 2.x specifies contrast using relative luminance:
  $$\text{Ratio} = \frac{L_1 + 0.05}{L_2 + 0.05} \quad \text{where } L = 0.2126R + 0.7152G + 0.0722B$$
  This mathematical formula has four severe empirical defects:
  1. **Spatial Frequency Blindness:** It evaluates color pairs in a vacuum. A 100-weight hairline font passing 4.5:1 is practically invisible to older adults or under ambient glare, whereas a 900-weight heavy headline at 3.5:1 is effortlessly legible.
  2. **Polarity Asymmetry & Dark-Mode Retinal Halation (Irradiation):**
     - *Positive Contrast (Dark text on light background):* The human pupil constricts under high light, increasing ocular depth of field and edge sharpness.
     - *Negative Contrast (Light text on dark background):* The pupil dilates, which amplifies spherical aberrations and astigmatism. Pure white text (`#FFFFFF`) on pure black (`#000000`) causes **retinal halation / irradiation**—the bright text appears to bleed, glow, and distort across the retina, causing ocular fatigue.
     - WCAG 2.x treats `#000000` on `#FFFFFF` and `#FFFFFF` on `#000000` as an identical 21:1, failing to detect dark-mode halation.
  3. **Chromatic Inaccuracies:** Saturated blue (`#0000FF`) on black produces a low mathematical ratio (~2.44:1) despite having strong perceptual boundaries, whereas medium gray (`#767676`) on white passes 4.54:1 (AA) yet washes out completely in mobile sunlight.
  4. **Perceptual Non-Uniformity:** A 1.5:1 delta in dark luminance ranges represents a massive perceptual jump, whereas the same delta in bright luminance is negligible.
- **The APCA (Accessible Perceptual Contrast Algorithm) Model:**
  APCA models human visual perception using the SAPC (S-LUV Advanced Perceptual Contrast) algorithm to calculate **Lightness Contrast ($L_c$)**:
  - Incorporates human nonlinear photoreceptor response (power-law curve).
  - Explicitly accounts for polarity ($L_c$ is positive for dark text on light, negative for light text on dark).
  - Directly couples contrast requirement to spatial frequency (minimum font size and font weight pairings).
- **Visual Evaluation Standards:** When auditing visual assets, enforce WCAG 2.2 AA (4.5:1 text, 3.0:1 UI components) as the absolute legal floor, while applying APCA Lightness Contrast ($L_c$) to detect unreadable thin weights and dark-mode retinal halation.

---

## 3. Cognitive Psychology & Memory Laws

### 4. Working Memory Capacity (Nelson Cowan 4±1 vs. Miller Myth)
- **Principle:** Working memory's focus of attention holds **4 ± 1 chunks** (Nelson Cowan, 2001, *Behavioral and Brain Sciences*).
- **Scientific Corrections:**
  - *Debunked Myth:* George Miller's 1956 "7 ± 2" applied to immediate digit span and unidimensional stimuli under active verbal rehearsal. In pure working memory without active strategies, capacity is ~4 chunks.
  - *Recognition over Recall:* Display items on screen do NOT consume internal working memory slots ("Knowledge in the World", Don Norman; Jakob Nielsen Heuristic #6). Restricting on-screen menus or lists to 7 items is a debunked myth. Working memory limits only apply when a user must memorize information across steps.

### 5. Chunking
- **Principle:** Grouping individual data points into meaningful units allows users to process complex data efficiently.
- **UI/UX Application:** Format phone numbers `(555) 123-4567`, payment cards `4000 1234 5678 9010`, and group related form inputs into `<fieldset>` elements.

### 6. Cognitive Load (Sweller, 1988)
- **Principle:** Total mental effort allocated to working memory. Distinguishes *intrinsic* (task difficulty), *germane* (schema building), and *extraneous* (mental friction from poor UI).
- **UI/UX Application:** Eliminate extraneous cognitive load: prefill known data, use smart defaults, and remove confusing jargon.

### 7. Serial Position Effect (Hermann Ebbinghaus)
- **Principle:** Humans remember the first (Primacy effect) and last (Recency effect) items in a sequence best, while middle items suffer highest recall decay.
- **UI/UX Application:** Place most critical navigational items or actions at the beginning and end of toolbars and menus.

### 8. Von Restorff Effect (Isolation Effect, 1933)
- **Principle:** When multiple homogeneous items are presented, the stimulus that differs visually from the rest is most likely to be remembered and noticed.
- **UI/UX Application:** Primary Call-to-Action (CTA) styling: ensure exactly one prominent accent-styled button stands out from muted secondary actions.

### 9. Selective Attention & Inattentional Blindness
- **Principle:** Humans attend to task-relevant visual stimuli and filter out peripheral elements (e.g. Banner Blindness).
- **UI/UX Application:** Critical notices and alerts must be placed directly within the user's primary line of sight / task flow, not in banner sidebars.

### 10. Paradox of the Active User (Carroll & Rosson, 1987)
- **Principle:** Users almost never read documentation, user manuals, or long explanatory onboarding copy before using a software tool; they learn by doing.
- **UI/UX Application:** Design interfaces to be self-explanatory with immediate visual affordances, contextual hints, and forgiving error recovery.

### 11. Mental Models & Conceptual Mappings (Don Norman)
- **Principle:** Users form an internal cognitive model of how a system works based on past interactions with the physical and digital world.
- **UI/UX Application:** Match controls to expected real-world behaviors (e.g. toggles reflect switches, sliders reflect continuous ranges).

### 12. Aesthetic-Usability Effect (Kurosu & Kashimura, 1995; Tractinsky, 2000)
- **Principle:** Users perceive visually attractive interfaces as more usable and exhibit higher tolerance for minor operational friction.
- **UI/UX Warning:** Visual beauty can mask fundamental usability defects during testing. Evaluate usability independently of visual polish.

### 13. Goal-Gradient Effect (Clark Hull, 1932)
- **Principle:** The tendency to approach a goal increases with proximity to the goal.
- **UI/UX Application:** Show progress bars and stepped wizards; an endowed initial progress state (e.g. "Step 1 completed") significantly accelerates task completion.

### 14. Zeigarnik Effect (Bluma Zeigarnik, 1927)
- **Principle:** Uncompleted or interrupted tasks create cognitive tension and are remembered better than completed tasks.
- **UI/UX Application:** Profile completion checklists, onboarding progress bars, and draft saving indicators.

### 15. Peak-End Rule (Daniel Kahneman, 1993)
- **Principle:** Psychological evaluation of an experience is determined almost entirely by its emotional peak (positive or negative) and its ending.
- **UI/UX Application:** Ensure task completion, confirmation, and error recovery screens are thoroughly polished and empowering.

### 16. Flow State (Mihaly Csikszentmihalyi)
- **Principle:** Deep, frictionless cognitive immersion achieved when task challenge matches user capability and feedback is immediate.
- **UI/UX Application:** Eliminate unnecessary modal interruptions, optimize keyboard shortcuts, and preserve state during uninterrupted typing.

---

## 4. Gestalt Principles of Visual Perception

### 17. Law of Proximity
- **Principle:** Objects placed close to each other are perceived as belonging to a common group.
- **UI/UX Application:** Form label must sit closer to its input field ($4–8\text{px}$) than to the preceding field ($16–24\text{px}$).

### 18. Law of Similarity
- **Principle:** Elements sharing visual characteristics (color, shape, size, orientation) are perceived as having a shared function.
- **UI/UX Application:** Consistent component styling: all clickable links share the same color/underline treatment; all destructive actions share consistent red styling.

### 19. Law of Common Region (Stephen Palmer, 1992)
- **Principle:** Elements bounded within a shared visual border or background color are perceived as a unified group, overriding proximity.
- **UI/UX Application:** Card containers, modal sheets, and bordered summary panels.

### 20. Law of Uniform Connectedness (Palmer & Rock, 1994)
- **Principle:** Visually connected elements (via lines, arrows, or enclosing paths) are perceived as more strongly related than elements related only by proximity or similarity.
- **UI/UX Application:** Steppers with connecting lines, node-based graph editors, breadcrumb trails.

### 21. Law of Continuity (Good Continuation)
- **Principle:** Elements arranged on a line or gentle curve are perceived as belonging together and continuing along the established path.
- **UI/UX Application:** Horizontal carousels that visually bleed off the edge of the viewport indicate that additional items can be scrolled into view.

### 22. Law of Closure
- **Principle:** The visual cortex automatically fills in missing visual information to perceive a complete, coherent shape.
- **UI/UX Application:** Minimalist iconography and progress rings.

### 23. Law of Prägnanz (Good Form / Simplicity)
- **Principle:** Visual perception resolves ambiguous or complex stimuli into the simplest, most regular shape possible.
- **UI/UX Application:** Avoid unnecessary irregular polygons or visual clutter that forces extra cognitive parsing.

### 24. Law of Focal Point
- **Principle:** Whatever stands out visually will capture and hold the viewer's attention first.
- **UI/UX Application:** Key visual anchors on hero sections and landing pages.

---

## 5. HCI Principles & Design Heuristics

### 25. Jakob's Law of Internet User Experience (Jakob Nielsen)
- **Principle:** Users spend most of their time on *other* sites. They expect your system to work the same way as products they already know.
- **UI/UX Application:** Do not reinvent standard navigational structures (logo top-left, cart top-right, search in header, standard keyboard navigation).

### 26. Postel's Law (The Robustness Principle — Jon Postel, RFC 760)
- **Principle:** "Be conservative in what you do, be liberal in what you accept from others."
- **UI/UX Application:** Forgiving input parsing: accept phone numbers with spaces, dashes, or parentheses; auto-format credit card numbers; normalize email whitespace.

### 27. Tesler's Law (The Law of Conservation of Complexity — Larry Tesler)
- **Principle:** Every system possesses an inherent amount of irreducible complexity. The only choice is whether the user or the software absorbs that complexity.
- **UI/UX Application:** Absorb complexity into smart system defaults, auto-detection (timezone, currency, card issuer), and progressive disclosure.

### 28. Doherty Threshold (Empirically Modernized)
- **Principle:** Originally 400ms for 1980s mainframe terminals (Doherty & Thadhani, 1982).
- **Modern Interactive Standard:**
  - **$\le 100\text{ ms}$:** Visual response to user action (active press, toggle switch).
  - **Core Web Vitals INP:** **$\le 200\text{ ms}$** for Interaction to Next Paint.
  - **$> 1,000\text{ ms}$:** Must display skeleton screens or progress bars.

### 29. Occam's Razor (Lex Parsimoniae — Design Heuristic)
- **Classification:** Epistemological heuristic, **not** an empirical sensory law.
- **UI/UX Application:** Strip unnecessary decorative flourishes and redundant controls that do not contribute to task completion, without stripping essential accessibility features.

### 30. Pareto Principle & Parkinson's Law (Managerial & Prioritization Rules)
- **Classification:** Sociological / bureaucratic aphorisms, **not** empirical HCI laws.
- **UI/UX Application:**
  - *Pareto (80/20):* Focus visual polish on the core 20% of user flows that generate 80% of daily active volume.
  - *Parkinson:* Streamline form flows and provide auto-complete to reduce the time spent on administrative data entry.
