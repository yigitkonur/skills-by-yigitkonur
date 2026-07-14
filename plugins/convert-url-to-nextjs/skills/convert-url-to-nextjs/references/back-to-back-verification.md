# Back-to-Back Verification — Per-Type Original vs Candidate Loop

This is the named phase that proves the Next.js rebuild is faithful to the deployed source. It runs **once per page type** produced by the type-extraction phase, not once per URL. The output is a structured pass/iterate/escalate decision plus screenshot evidence the user can inspect later.

Read this when a type template renders locally and you need to decide whether to ship it or keep iterating.

---

## Loop overview

```
for each type in route-map.json:
  for each viewport in [1440, 768, 375]:
    load ORIGINAL (exemplar URL on the live deployed site)
    capture original-{viewport}.png
    load CANDIDATE (the Next.js dev/preview URL for the same type)
    capture candidate-{viewport}.png
    compare → write iteration entry → decide pass / iterate / escalate
  if any viewport failed → iterate (max 5 rounds), then escalate
  else → mark type passed
```

Original and candidate must be loaded at the **same viewport**, in the **same browser**, with the **same settle time**. Same browser instance prevents font-rendering noise that comes from switching between headless backends.

---

## `run-agent-browser` is the verification tool

This phase explicitly drives `run-agent-browser`. The skill assumes the agent has already read `run-agent-browser`'s SKILL (or is willing to read it now if it has not).

### Commands the loop uses

| Step | `run-agent-browser` verb | Purpose |
|---|---|---|
| Open the original URL | `agent-browser open <ORIGINAL_URL>` | Load the live deployed page |
| Wait for layout to settle | `agent-browser snapshot -i` | Confirm the DOM is interactive (acts as a settle signal) |
| Switch viewport | `agent-browser viewport 1440x900` (and `768x1024`, `375x812`) | Run the loop at the three target widths |
| Capture original screenshot | `agent-browser screenshot .design-soul/verify/{type}/original-{viewport}.png` | Pixel record of the source |
| Open the candidate URL | `agent-browser open http://localhost:3000/{path}` | Load the Next.js dev/preview build at the same viewport |
| Capture candidate screenshot | `agent-browser screenshot .design-soul/verify/{type}/candidate-{viewport}.png` | Pixel record of the rebuild |
| Inspect divergent text | `agent-browser get text <selector>` | Confirm visible copy matches when the user expects identical text |
| Extract heading outline | `agent-browser eval --stdin` heredoc → `Array.from(document.querySelectorAll('h1,h2,h3')).map(h => [h.tagName, h.textContent.trim()])` | Layout-structure comparison without pixel noise |

When the verb names above do not exactly match the installed `run-agent-browser` version, use the closest equivalent named in `run-agent-browser`'s own SKILL. The verification loop's contract — *same viewport, same settle, original first then candidate, structured iteration entry* — is what matters; the exact CLI surface follows whatever `run-agent-browser` exposes today.

### Browser hygiene

- Open the original first, capture, then navigate the same tab/session to the candidate. Re-snapshot before screenshotting the candidate.
- Use a single named session for the whole type (`--session-name verify-{type}`) so cookies/cache do not contaminate later types.
- For sites with heavy anti-bot defense, switch to `--headed` mode for the original capture; the candidate is local so it is unaffected.
- Close auxiliary tabs at the end of each type — leave the browser in a sane state for the next type.

---

## What "acceptable parity" means

This skill defines parity as **substantial visual match at three viewports against the original deployed build**. It is not full pixel-perfect identity; that is a strictly stronger claim only made when the user explicitly sets a measured threshold.

A type passes when **all** of the following hold at desktop (1440), tablet (768), and mobile (375):

| Dimension | Acceptable means |
|---|---|
| **Layout structure** | Same direct-child section order under `<main>`. No sections missing or added. |
| **Section dimensions** | Each major section's visible height and width are within ~10% of the original. |
| **Heading outline** | H1/H2/H3 text content matches the original verbatim (modulo intentional copy edits the user named). |
| **Visible image positions** | Hero/feature/illustration positions are within ~5% of the original on the X axis and visually anchored to the same section. |
| **Typography** | Font family, weight, and approximate size match. Letter shapes look the same; small kerning drift is acceptable. |
| **Colors** | Background, primary text, accent, and CTA colors are within ~5 luminance units in CSS. No swapped semantic roles. |
| **Header/footer** | Both shells render identically across all three viewports. |
| **Responsive behavior** | The candidate's breakpoints fire at the same widths as the original — no obviously wrong mobile/tablet layout. |

If any of these fail at any of the three viewports, the type fails the round and iterates.

---

## Iteration entry — structured output per round

Every comparison round writes one entry into `.design-soul/verify/{type}/iterations.json`. The file is an append-only array.

```json
{
  "iteration": 1,
  "type": "pricing",
  "exemplarUrl": "https://example.com/pricing",
  "candidateUrl": "http://localhost:3000/pricing",
  "viewport": 1440,
  "originalScreenshot": ".design-soul/verify/pricing/original-1440.png",
  "candidateScreenshot": ".design-soul/verify/pricing/candidate-1440.png",
  "checks": {
    "sectionSequenceMatches": true,
    "headingOutlineMatches": true,
    "sectionHeightDriftMax": 0.07,
    "typographyMaterialMatch": true,
    "colorMaterialMatch": true,
    "headerFooterMatch": true
  },
  "decision": "pass",
  "notes": []
}
```

The same JSON shape is used for `tablet` and `mobile` viewports. `decision` is one of `pass`, `iterate`, `escalate`.

Write a summary doc at `.design-soul/verify/{type}/summary.md` at the end of the type's loop. It links every iteration entry, names the round that passed, and surfaces residual drift the user should know about.

---

## Pass / iterate / escalate rule

Apply this rule at the end of every round.

| Outcome | Trigger | Next action |
|---|---|---|
| **pass** | All three viewports satisfy the parity dimensions above | Write `summary.md`, move to the next type |
| **iterate** | Any viewport fails on a recoverable dimension (sectionSequence wrong, heading text drift, typography wrong, colors wrong, responsive breakpoint wrong) | Fix the candidate template, increment iteration, re-run the loop for that type |
| **escalate** | 5 rounds elapsed without a pass, or the same dimension fails three rounds in a row, or capture artifacts are missing/corrupted | Pause, summarize the residual diff for the user (the screenshot pair and the failing dimension), ask whether to accept the current candidate, change strategy, or skip the type |

Five rounds is the default ceiling. Lower it to three for small marketing sites; raise it to seven only if the user explicitly asks for more iterations.

Do not silently mark a type passed when a single dimension is still failing. Acceptance of residual drift requires the user's explicit nod, captured in `summary.md`.

---

## Failure-mode shortlist (what usually breaks each dimension)

| Failing dimension | Probable cause | First fix to try |
|---|---|---|
| `sectionSequenceMatches: false` | Wave 0 section inventory missed a below-the-fold block, or Wave 2 brief omitted it | Re-read the L1 capture's full-page screenshot; add the missing section to the brief and the template |
| `headingOutlineMatches: false` | Copy was paraphrased instead of copied; or hydration replaced placeholder copy | Pull headings from `.design-soul/capture/{route}/headings.json` literally |
| `sectionHeightDriftMax > 0.10` | Spacing tokens swapped to defaults; padding or `gap` not extracted | Re-extract from the source CSS corpus; do not normalize values |
| `typographyMaterialMatch: false` | Font fell back because `@font-face` was missing or the local file did not load | Self-host the original font; verify `font-display`; confirm the path in `globals.css` |
| `colorMaterialMatch: false` | Token table swapped a brand color for a Tailwind default | Re-read `wave1/{group}/token-values.json` against `tailwind.config.ts` |
| `headerFooterMatch: false` | Shared shell built per-route instead of imported from `components/shared/` | Move the shell into `components/shared/` and import |
| Responsive breakpoints wrong | Tailwind defaults used instead of extracted breakpoints | Set breakpoints from `wave1/{group}/responsive-map.md` |

---

## Where verification artifacts live

```
.design-soul/verify/
├── {type}/
│   ├── original-1440.png
│   ├── original-768.png
│   ├── original-375.png
│   ├── candidate-1440.png
│   ├── candidate-768.png
│   ├── candidate-375.png
│   ├── iterations.json
│   └── summary.md
└── verification-report.md   # aggregate across all types — fed to Phase 5
```

Keep the screenshots after the loop ends. They are the user's audit trail.

---

## Coordination with `scripts/diff-screenshots.sh`

The helper at `scripts/diff-screenshots.sh` (read `scripts/diff-screenshots.md`) can take the captured pair and produce an RMSE metric plus a diff image when ImageMagick is installed. Use it for the desktop pair as the first numeric signal; it does not replace the structural checks above, but a low RMSE on desktop is a useful pre-filter before running the structural checks on tablet/mobile.

If ImageMagick is missing, the script writes `comparatorAvailable: false` and does not invent a metric — fall back to the structural checks only and note the gap in `summary.md`.

---

## When to skip a viewport

Default: always run all three viewports. Skip a viewport only when:

- the user explicitly named a target device (e.g. "desktop-only redesign")
- the original site has no mobile breakpoint and renders the desktop layout below 768px (rare; document the evidence)

A skipped viewport is logged in `summary.md` with the reason, not silently omitted.

---

## What this phase does NOT do

- it does not run unit/integration tests of the Next.js build (`tsc --noEmit`, `npm run build` are separate; see SKILL.md "CLI-verifiable acceptance criteria")
- it does not author or modify route data — only the template is fixed when a round iterates
- it does not crawl new URLs — only the exemplars chosen during type-extraction are verified
