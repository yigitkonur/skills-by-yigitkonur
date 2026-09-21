# Iterative Visual Refinement Methodology

This reference documents the iterative refinement process that transforms a first-draft theme from "technically correct tokens" into a production-quality branded experience. This process — not the tokens themselves — is what separates mediocre customization from excellent results.

---

## 1. Why First Drafts Always Fail

A mathematically correct token sheet (proper WCAG contrast, correct hex values from the design spec, valid @font-face declarations) will still produce a visually disappointing result on the first deploy. This is not a failure of the tokens — it's a fundamental property of design systems:

- **Token interactions are non-linear**: A focus ring color that looks perfect in isolation (`#526585`) may feel too aggressive when rendered next to a muted border (`#232e40`) in a specific card composition.
- **Dark mode reveals problems light mode hides**: Cards that look clean on white backgrounds can disappear into dark canvases.
- **Typography needs visual tuning**: Line heights and letter spacing that work in a design spec font preview feel different when wrapped around actual chat messages and code blocks.
- **Component context matters**: The same `--accent` color behaves differently in a dropdown menu (where it's a hover state) versus a sidebar (where it's a selection indicator).

**Expect 3–5 iterations minimum** before a theme reaches production quality.

---

## 2. The Refinement Loop

```
  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │   ┌──────────┐    ┌──────────┐    ┌──────────┐  │
  │   │  Change  │───►│ Restart  │───►│Screenshot│  │
  │   │  Tokens  │    │ Server   │    │ Both     │  │
  │   │          │    │          │    │ Modes    │  │
  │   └──────────┘    └──────────┘    └──────────┘  │
  │        ▲                              │         │
  │        │         ┌──────────┐         │         │
  │        │         │ Evaluate │         │         │
  │        └─────────│ Against  │◄────────┘         │
  │                  │ Sources  │                   │
  │                  └──────────┘                   │
  │                       │                         │
  │                  Pass? ──► Ship                  │
  └─────────────────────────────────────────────────┘
```

### Step 1: Change Tokens
Modify the CSS variable values in the patch script. Make **one category of change per iteration**:
- Iteration 1: Surface colors only (`--background`, `--card`, `--sidebar`)
- Iteration 2: Ink and text colors only (`--foreground`, `--muted-foreground`)
- Iteration 3: Interactive states only (`--primary`, `--ring`, `--accent`)
- Iteration 4: Typography only (`--font-sans`, `--font-head`, letter-spacing)
- Iteration 5: Polish (shadows, chart colors, dark mode logo)

**Never change everything at once.** When you change 10 tokens simultaneously and the result looks wrong, you can't isolate which change caused the problem.

### Step 2: Restart Server
After modifying the patch script, re-run it inside the container and restart the server:

```bash
docker exec <container> python3 /app/data/patches/05_custom_theme.py
```

The patch script should handle the `pkill -9 -f next-server` restart internally.

### Step 3: Screenshot Both Modes
Capture full-viewport screenshots of **both Light and Dark modes**:

```bash
# Light mode
agent-browser open "https://app.example.com/chat" --wait 3000
agent-browser screenshot /tmp/iter3_light.png

# Dark mode
agent-browser eval 'document.documentElement.classList.add("dark")'
agent-browser screenshot /tmp/iter3_dark.png
```

**Critical**: Always capture both modes. Fixing light mode often breaks dark mode (e.g., a sidebar color that provides separation on white disappears against dark navy).

### Step 4: Evaluate Against Sources
Compare the screenshots against:
1. **Design specification** (`DESIGN.md`, Figma, or design token files) — Does the implementation match the spec?
2. **Production website** (`website-brand/`) — Does the app feel like the same product?
3. **Previous iteration** — Did the changes improve or regress?

Focus on these evaluation dimensions:
- **Surface layering**: Can you visually distinguish canvas → card → sidebar → popover?
- **Ink readability**: Is all text comfortable to read? Is muted text visible but subdued?
- **Accent restraint**: Is the brand color only on primary buttons? No border bleed?
- **Focus ring**: Click into the chat input — is the ring visible but calm?
- **Typography**: Do headings feel different from body text? Do buttons look intentional?

---

## 3. The Two-Agent Review Pattern

For maximum fidelity, deploy two parallel review agents:

### Agent A: Design Spec Auditor
- Input: Current CSS tokens + `DESIGN.md` + `tokens/colors.json`
- Question: "Do the implemented tokens mathematically match the canonical design specification?"
- Output: Token audit table with exact value comparisons and WCAG contrast verification

### Agent B: Website Harmonizer
- Input: Current CSS tokens + production website CSS (`_variables.css`, `globals.css`)
- Question: "When a user navigates from the website to this app, does it feel like the same product?"
- Output: Visual parity assessment with specific component-level comparisons

Both agents produce independent recommendations. Merge them:
- If both agree on a change → apply it.
- If they conflict → favor the design spec (it's the authoritative source).
- If neither flags an issue → the token is correct.

---

## 4. Focus State Testing

Ambient screenshots only show resting states. Interactive states require explicit testing:

```bash
# Click into the chat composer input
agent-browser eval 'document.querySelector("textarea").focus()'
agent-browser screenshot /tmp/iter3_focused.png
```

Evaluate:
- Is the focus ring visible against the card background?
- Is the ring a calm neutral, not a screaming neon?
- Does the ring create clear spatial hierarchy (focused element stands out)?

---

## 5. Common Iteration Traps

### Trap 1: Fixing Light Breaks Dark
Changing `--secondary` to improve light mode card fills may make dark mode cards disappear. **Always check both modes after every change.**

### Trap 2: Fixing Focus Breaks Resting
Adjusting `--ring` for better focus visibility may also affect `--border` if both use the same token. Verify that resting borders are still neutral hairlines.

### Trap 3: Typography Changes Cascade
Changing `--font-sans` affects everything: navigation labels, chat messages, code descriptions, error messages, timestamps. A font that looks great in headings may be too heavy or too light for small metadata text.

### Trap 4: First Screenshot Bias
The first screenshot you see after deploying becomes your "mental baseline." Even if it's bad, your brain adapts. **Always compare against the design spec and website, never against your memory of the previous iteration.**

---

## 6. Convergence Criteria

The theme is ready to ship when ALL of the following are true:

- [ ] Light mode screenshot matches design spec surface ramp within 1 step
- [ ] Dark mode screenshot shows clear card/canvas/sidebar separation
- [ ] Focus ring is visible but not distracting in both modes
- [ ] Brand accent appears ONLY on primary action buttons
- [ ] Typography hierarchy is visible (headings ≠ body ≠ captions)
- [ ] User (or design reviewer) explicitly approves the visual output
- [ ] No regressions introduced compared to previous approved iteration
