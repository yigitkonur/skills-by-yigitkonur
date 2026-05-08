# build-macos-app

Building, auditing, or shipping a production-grade macOS SwiftUI or AppKit app needing HIG compliance, Liquid Glass design, snapshot validation, SwiftLint/SwiftFormat hooks, or Convex+Clerk cloud sync.

**Category:** development

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-macos-app
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## What you get

The skill bundles 69 deep-dive references organized by domain:

- **`references/hig/`** — Apple Human Interface Guidelines for macOS: foundations (color, typography, spacing, icons, materials, motion), components (buttons, text inputs, menus, popovers, tables, alerts, selection controls), platform patterns (windows, sidebars, toolbars, keyboard shortcuts, drag-drop), accessibility, widgets/notifications, plus practitioner-level overrides.
- **`references/liquid-glass/`** — macOS 26 (Tahoe+) Liquid Glass: API reference (SwiftUI + AppKit), 12 design principles with concentricity rules, full deprecation/smell catalog for modernizing existing code, toolbar/sidebar/window recipes, 5-phase migration guide, 34 known bugs with workarounds, AppKit↔SwiftUI bridging.
- **`references/visual-validation/`** — Expectation-first screenshot discipline: 5-step loop, capture-mode preference order, drift taxonomy, `swift-snapshot-testing` SPM wiring + CI, troubleshooting.
- **`references/quality-hooks/`** — Pre-commit hook architecture, baseline workflow for legacy code, typecheck stage opt-in, SwiftLint + SwiftFormat config rationale, per-platform xcodebuild destination matrix.
- **`references/cloud-sync/`** — Convex + Clerk SwiftUI client patterns: macOS app entry, per-window view-model gotchas, four-state offline UX, connection banner, tri-state loading, pipeline recovery, Clerk auth gate, SIWA, reactive `switchToLatest` queries, SDK cheat sheet, limitations.
- **`references/workflow/`** — Operations: bootstrap a new app, audit an existing app, pre-release ship checklist.

Plus calibrated configs at `assets/`:

- `assets/swiftlint.yml` — 28 opt-in rules + 5 custom rules tuned for SwiftUI / Concurrency / Performance.
- `assets/swiftformat` — 17-rule allowlist, Swift 6, 4-space indent.
- `assets/githooks/pre-commit` — 4-stage hook (detect → SwiftLint → SwiftFormat → optional typecheck) with CI auto-skip.
- `assets/scripts/swift-typecheck.sh` — Per-platform xcodebuild matrix (macOS / iOS / tvOS / watchOS / visionOS) with speed-up flags.
- `assets/Makefile.fragment` — `lint` / `lint-fix` / `lint-new` / `format` / `install-hooks` / `lint-all` targets.
- `assets/github-workflows/swift-quality.yml` — CI workflow with snapshot-failure artifact upload.

## Operations the skill handles

- **bootstrap** — fresh project from zero with all four pillars wired in
- **build** — apply Three Questions before any new view
- **redesign** — modernize existing code (Liquid Glass diagnosis catalog)
- **audit** — severity-tagged review report (CRITICAL / HIGH / MEDIUM / LOW)
- **migrate** — 5-phase pre-Tahoe → Tahoe migration
- **install hooks** — drop calibrated configs into a repo
- **add tests** — `swift-snapshot-testing` SPM scaffold
- **wire cloud sync** — Convex + Clerk client setup
- **ship** — pre-release checklist
