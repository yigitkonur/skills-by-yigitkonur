# Auditing an Existing macOS App

Use this when the user asks for "review", "audit", "assess", or "make this look like Apple". Produce a single report with severity-tagged findings; never auto-fix in audit mode unless the user explicitly opts in.

## Output format (mandatory)

Every finding follows:

```
[SEVERITY] [CATEGORY] file:line — short description
  → Fix: one-sentence remediation
  → Reference: references/path/to/deep-dive.md
```

**Severities:**
- **CRITICAL** — guardrail violation, runtime crash risk, App Review reject risk, or HIG Three-Laws violation.
- **HIGH** — visible regression on Tahoe, missing keyboard shortcuts, hardcoded colors, deprecated API.
- **MEDIUM** — design quality (tinting hierarchy, spacing, typography drift).
- **LOW** — polish (animation timing, badge style, optional refinements).

**Categories:** `HIG`, `LiquidGlass`, `A11y`, `Quality`, `Tests`, `CloudSync`.

## Audit phases

Walk these in order. Don't skip phases — coverage matters more than depth on a first pass.

### Phase 1 — Sweep for guardrail violations (10 min)

Use grep/glob to find the unambiguous violations first:

```bash
# CRITICAL — deprecated navigation
grep -rn "NavigationView " --include="*.swift" .

# CRITICAL — superseded state APIs
grep -rn "@StateObject\|@ObservedObject\|@EnvironmentObject" --include="*.swift" .

# HIGH — hardcoded colors
grep -rn "Color(red:\|Color(\"#\|UIColor\\.\\|NSColor\\." --include="*.swift" .

# HIGH — fixed font sizes
grep -rn "\\.system(size:" --include="*.swift" .

# HIGH — iOS-only API on macOS path
grep -rn "\\.interactive()" --include="*.swift" .

# HIGH — visible toolbar background on Tahoe
grep -rn "\\.toolbarBackground(.visible" --include="*.swift" .

# MEDIUM — glass on content (heuristic; review hits)
grep -rn "\\.glassEffect" --include="*.swift" . | grep -i "list\|row\|cell\|card"

# MEDIUM — missing keyboard shortcuts on top-level commands
grep -rn "Button(" --include="*.swift" . | grep -v "keyboardShortcut"
```

→ `references/liquid-glass/design-diagnosis.md` has the full 41-row deprecated-API replacement table and 30-smell catalog.

### Phase 2 — HIG sweep (15 min)

Open the project in Xcode, run it, and walk through:

- **Menu bar.** Every toolbar action also in a menu? Standard items present (App / File / Edit / View / Window / Help)? "Settings…" not "Preferences"? → `references/hig/components/menus.md`
- **Keyboard shortcuts.** `Cmd-N/O/S/Shift-S/Z/Shift-Z/Q/W/Comma/F` — wired? → `references/hig/platform/keyboard-shortcuts.md`
- **Settings scene.** Cmd-Comma opens? Changes apply immediately (no Save/Cancel/Apply)? → `references/hig/components/menus.md`
- **Window chrome.** Default traffic lights? No custom drag regions? Resizable as expected? → `references/hig/platform/windows.md`
- **Dialogs.** `[Destructive][Cancel][Default]` order? Specific verbs not "OK"/"Yes"? → `references/hig/components/alerts-and-sheets.md`
- **Sidebars.** `NavigationSplitView`? Sized in the 160-400pt range? Material `.sidebar`? → `references/hig/platform/sidebars-and-split-views.md`

### Phase 3 — Liquid Glass sweep (15 min)

For each view that renders chrome:

- Glass on navigation only, never content?
- ONE `.glassProminent` per screen?
- `.tint(.accentColor)` on the primary, no tint on secondaries, `.tint(.red)` on destructive?
- `#available(macOS 26, *)` gating around Tahoe-only APIs?
- Concentric corner radii (`.containerConcentric` or `ConcentricRectangle()`) instead of hardcoded radii?
- `.scrollEdgeEffectStyle(.hard)` left as the macOS default?
- `NSVisualEffectView` migrated to `NSGlassEffectView` where applicable, or kept intentionally with rationale?

→ `references/liquid-glass/design-principles.md` for the full diagnosis grid.
→ `references/liquid-glass/pitfalls-and-solutions.md` for known bugs to flag (e.g. `.glassEffect()` + `.background(.ultraThinMaterial)` runtime crash, inactive-window opacity).

### Phase 4 — Accessibility sweep (10 min)

- Every interactive element has `accessibilityLabel` (icon-only buttons especially)?
- Decorative images marked `.accessibilityHidden(true)`?
- Custom `NSView` controls adopt `NSAccessibilityButton` / role-specific protocols?
- `accessibilityReduceMotion` honored on transitions?
- Test pass with VoiceOver (`Cmd-F5`) on at least one main flow?
- Test pass with Full Keyboard Access?

→ `references/hig/technologies/accessibility.md` for the 33-item audit checklist.

### Phase 5 — Quality hooks (5 min)

- Pre-commit hook installed (`git config --get core.hooksPath` returns `.githooks`)?
- `.swiftlint.yml` and `.swiftformat` present and not stale?
- `make lint` runs cleanly (or has a baseline)?
- CI workflow runs the same tools the hook runs?

→ `references/quality-hooks/hook-architecture.md`. If absent, propose `install-hooks` operation.

### Phase 6 — Tests (5 min)

- Snapshot test target present?
- At least one happy-path UI snapshot per top-level view?
- `Matches` / `Drift` / `Better-than-expected` discipline followed in PR descriptions?
- Snapshots pinned to a stable simulator / runner OS?

→ `references/visual-validation/expectation-loop.md`.
→ `references/visual-validation/snapshot-testing-spm.md` if no harness exists.

### Phase 7 — Cloud sync (only if applicable)

If `Package.swift` contains `ConvexMobile`, `Clerk`, or similar — run the cloud-sync sweep.
→ `references/cloud-sync/swiftui-client.md`, `auth-presentation.md`.

## Reporting back

Group findings by severity, not by phase. The user wants to know "what must I fix to ship?" first.

```
## Audit summary

### CRITICAL (3)
[CRITICAL] [HIG] AppDelegate.swift:42 — Settings window uses Save/Cancel buttons.
  → Fix: remove buttons, use @AppStorage with immediate persistence.
  → Reference: references/hig/components/menus.md

[CRITICAL] [LiquidGlass] ContentView.swift:88 — `.glassEffect()` on List rows.
  → Fix: glass goes on navigation only; remove from rows, add to surrounding toolbar.
  → Reference: references/liquid-glass/design-principles.md

…

### HIGH (12)
…

### MEDIUM (8)
…

### LOW (3)
…

Verification rung reached: Rung 2 (read code, ran the app, did not run tests).
Next action: triage CRITICAL items with the user before any code changes.
```

Never silently fix anything in audit mode. The findings document IS the deliverable.
