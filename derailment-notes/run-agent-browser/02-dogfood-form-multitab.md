# Derailment Test: run-agent-browser on "Multi-Tab Form Filling"

Date: 2026-03-11
Skill under test: run-agent-browser
Test task: Open example.com in tab 0, open httpbin.org/forms/post in tab 1, fill the pizza order form with text/radio/checkbox fields, submit, verify response, switch back to tab 0, close only opened tab.
Method: Follow SKILL.md steps 1–6 exactly as written, recording every friction point.

---

## Pre-scan summary

Same as run 01. Focused on multi-tab + form interaction workflow path.
Minimal reading set used: snapshot-refs.md, commands.md (per SKILL.md "Form or login automation" set).

---

## Friction points

### Phase 1: Establish session and baseline

Clean pass (same friction as F-01/F-02 from run 01, not double-counted).

### Phase 2: Navigate — multi-tab

**F-01 — `tab new` output doesn't confirm which tab is now active** (P2, O2)
After `agent-browser tab new https://httpbin.org/forms/post`, the output was just `✓ Done` — no indication of which tab index was created or whether focus shifted to it. The skill correctly says "verify focus with `tab`, `get url`, `get title`" after `tab new`, so the verification step catches this. But the output mismatch means an executor who skips verification (against rules) wouldn't know their focus state.
Fix: This is a tool behavior, not a skill instruction issue. Tag as `external`. The skill's explicit verification-after-tab-switch instruction is the correct mitigation and already works well.

### Phase 3: Inspect before interacting

Clean pass. `snapshot -i` on the httpbin form was excellent — every form element had a clear ref, role, label, and type. This is the ideal snapshot output: structured, unambiguous, and directly actionable.

### Phase 4: Interact one state change at a time

**F-02 — `check` command returns `true` instead of `✓ Done`** (P2, O2)
`agent-browser fill @e1 "text"` returns `✓ Done` but `agent-browser check @e7` returns `true`. The inconsistent output format is confusing — `true` looks like a check-state query response, not a confirmation of action. Similarly, `click @e6` (radio button) returned `✓ Done` but `check @e7` returned `true`.
Fix: Tag as `external` (tool behavior). Add a note to SKILL.md §4: "Note: `check` and `uncheck` commands return `true`/`false` (the new checked state) rather than `✓ Done`."

**F-03 — No guidance on verifying radio button selection** (P1, M4)
SKILL.md §5 lists `is checked REF` for checkboxes but doesn't explicitly mention it works for radio buttons too. After clicking `@e6` (radio "Large"), the executor wonders: should I use `is checked @e6` or `get value @e6` or something else? The commands.md lists `is checked @e1` generically. The executor had to guess that `is checked` works for radios too.
Fix: Add to SKILL.md §5 verification list: "- `agent-browser is checked REF` — works for both checkboxes and radio buttons"

### Phase 5: Verify the result

**F-04 — Post-submission page with no interactive elements: `snapshot -i` returns "(no interactive elements)"** (P1, M4)
After form submission, the result page (httpbin.org/post) was pure JSON text with no interactive elements. `snapshot -i` returned `(no interactive elements)` which is technically correct but unhelpful for verification. The skill says to verify using at least one deterministic check, but all the listed checks (get text REF, get value REF, is visible REF) require a REF. The executor must independently know to use `get text body` or a CSS selector.
Fix: Add to SKILL.md §5 verification list: "If `snapshot -i` returns `(no interactive elements)`, verify with `get text body` (for raw page content) or `get url`/`get title` (for navigation confirmation)."

### Phase 6: Clean up deliberately

**F-05 — `tab close` syntax for closing a specific tab is underdocumented in SKILL.md** (P2, M5)
SKILL.md §6 says "close those tabs" but doesn't specify the syntax `tab close INDEX`. The executor finds `agent-browser tab close 2` in `references/commands.md` but has to leave SKILL.md to discover this. The cleanup rules say "Record which tabs you created" and "Close only the ones you created" — excellent guidance — but missing the how.
Fix: Add to SKILL.md §6: "Close auxiliary tabs with `agent-browser tab close INDEX` (index from `tab` listing)."

---

## What worked well

1. **Form element identification was flawless.** `snapshot -i` on httpbin form returned perfectly labeled refs: `textbox "Customer name:" [ref=e1]`, `radio "Large" [ref=e6]`, `checkbox "Bacon" [ref=e7]`. Zero ambiguity.

2. **Multi-tab workflow felt natural.** The skill's tab rules (prefer `tab new URL`, verify focus, track what you opened) created a clean mental model that translated directly to commands.

3. **`get value` verification pattern is excellent.** Being able to `get value @e1` to confirm fill worked before submitting is a huge win for reliable automation.

4. **Tab listing clearly shows active tab.** The `→` indicator in `tab` output made focus state immediately obvious.

5. **Form submission worked without explicit wait.** `click @e13` (submit) navigated and `get url` immediately returned the new URL. No need for `wait --load networkidle` in this case.

6. **Cleanup rules are well-designed.** "Close only what you opened" + "Record which tab you started in" prevented accidental destruction of the original tab.

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 0 | — |
| P1 | 2 | F-03, F-04 |
| P2 | 3 | F-01 (ext), F-02 (ext), F-05 |

## Metrics

| Metric | Value |
|---|---|
| Total steps attempted | 16 |
| Clean passes | 11 |
| P0 (blocks progress) | 0 |
| P1 (causes confusion) | 2 |
| P2 (minor annoyance) | 3 |
| Derailment density | 0.31 |
| Clean pass rate | 69% |

## Cross-run comparison

| Run | Date | Task | Steps | P0 | P1 | P2 | Total | Density | Clean % |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 2026-03-11 | HN data extraction + search | 19 | 1 | 6 | 1 | 8 | 0.42 | 58% |
| 02 | 2026-03-11 | Multi-tab form filling | 16 | 0 | 2 | 3 | 5 | 0.31 | 69% |

**Trajectory:** Improving. The form-filling workflow path is cleaner than the data extraction path. The skill's core observe→act→verify loop works well for interactive form elements. The primary gaps are in data extraction scenarios and edge cases (no interactive elements, multiple matches).
