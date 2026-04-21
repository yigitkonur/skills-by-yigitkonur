# UI Engineering Review

Author-side checklist for PRs focused on *visual* changes — CSS, design tokens, layout, typography, spacing, accessibility, component visuals. Distinct from `frontend-ts-js.md` which covers logic + data flow. Use when classifying the diff's domain as **ui-engineering** in SKILL.md Step 4.

## What UI reviewers care about

| Concern | Why it matters | Evidence they want |
|---|---|---|
| **Design-token fidelity** | Hardcoded colors/spacings drift from the system | Classes/tokens from the system, not raw values |
| **Responsive behavior** | Breaks at the breakpoint reviewers don't test on | Viewport screenshots at mobile / tablet / desktop |
| **Accessibility** | Keyboard, screen reader, color contrast, focus | Contrast ratio ≥ AA; focus visible; labels/roles correct |
| **Interactive states** | Hover, focus, active, disabled, loading, error | All states designed, not just default |
| **Motion + transitions** | Animations skip for `prefers-reduced-motion` users | Respects user preference |
| **Dark mode / theme** | New component respects theme automatically | No hardcoded `text-gray-900` outside theme tokens |
| **Layout stability** | CLS (Cumulative Layout Shift) from images/fonts | Image dimensions set; font-display/preload |
| **Copy** | UI text ships to every user; typos and tone issues are public | Reviewed copy; sentence case (or the repo's convention) consistent |

## Weaknesses the author should pre-empt

- **Breakpoint coverage.** Did you test the changed screen at mobile (360-420px), tablet (768px), and desktop (1280+)? Any known breakage?
- **Contrast.** New text on new background? Check the ratio. 4.5:1 for normal text, 3:1 for large. One failing token breaks the whole system's claim.
- **Keyboard traversal.** Can every interactive element be reached via Tab? Does the order match visual order? Is focus visible?
- **Screen reader output.** Does the component announce itself correctly? Try VoiceOver / NVDA / TalkBack on one critical path.
- **Hover-only interactions.** Anything that only appears on hover is invisible to touch and keyboard users. Have a non-hover path.
- **`line-clamp` + long content.** Does overflow cut mid-word? Does it respect RTL?
- **Animation on scroll or mount.** Respect `prefers-reduced-motion: reduce`. One vestibular user's nausea is a shipping bug.
- **Dark mode token coverage.** If you introduced a new color, is its dark-mode variant also added?
- **Image dimensions.** Width + height attributes set to prevent layout shift during load?
- **Focus trap on modals.** Can keyboard users escape? Is focus returned to the trigger on close?

## Questions to ask the reviewer explicitly

- "Spacing between the header and the card grid is `gap-6` (24px). The system uses `gap-8` for similar pairings elsewhere — which is right here?"
- "Contrast on the secondary button (`bg-slate-200` on `bg-white`) is 3.2:1. Is that acceptable for the size (14px) or should we bump?"
- "I added `animate-fade-in` on mount. Should every new component get `motion-safe:animate-fade-in` instead, to respect user prefs?"
- "The modal's close button is top-right. The design system's pattern is top-left for RTL locales — do we need to flip?"
- "Is the new `<Toast>` variant expected to match `<Alert>` styling exactly, or is divergence okay because of functional difference?"

## What to verify before opening the PR

- [ ] Visual check at mobile / tablet / desktop viewports
- [ ] Keyboard-only traversal of the changed screen
- [ ] Light mode + dark mode both rendered
- [ ] Contrast ratios on new color combinations
- [ ] `prefers-reduced-motion: reduce` in DevTools — animations respect it
- [ ] Screenshots attached to the PR body (before/after or `after` only if new)
- [ ] Lint / stylelint passes if the project uses it
- [ ] Screenshot diff tool (Chromatic, Percy, `test-macos-snapshots`) if available

If screenshots would materially help the reviewer, include them. GitHub supports image paste in PR bodies.

## Signals the review is off-track

- "The design looks close enough." → "Close enough" drifts. Match the system or justify the divergence.
- "Dark mode works because I used theme classes." → Verify by actually switching modes.
- "Contrast is probably fine." → Check. It takes 10 seconds with browser devtools.
- "I'll add the reduced-motion guard later." → Vestibular users don't have "later."
- "A11y is the design system's job." → Anything you add inherits the a11y obligation. If it's not accessible, it's not done.

## When to split the PR

- Pure visual change + unrelated logic change → split
- New design token + code that uses it → usually one PR (they're coupled); exception is when the token needs team review first
- Theming refactor + new component → split; theming lands first, new component builds on it

## UI-engineering follow-up skills

For PRs that touch specific UI ecosystems, route additionally:

| Ecosystem | Skill |
|---|---|
| daisyUI components | `build-daisyui-mcp` |
| macOS HIG SwiftUI | `develop-macos-hig` |
| macOS Liquid Glass | `develop-macos-liquid-glass` |
| SaaS design extraction | `extract-saas-design` |
| HTML → Next.js | `convert-snapshot-nextjs` |
| React compositional patterns | `composition-patterns` (external pack) |
| Web Interface Guidelines | `web-design-guidelines` (external pack) |

Name the specific ecosystem in the PR body so the reviewer pulls the right lens.
