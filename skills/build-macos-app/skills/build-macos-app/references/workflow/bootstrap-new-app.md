# Bootstrapping a New macOS App

Use this when the user is starting a fresh macOS app and wants HIG/Liquid Glass/quality discipline from day one. Walk through these phases in order. Stop and confirm with the user only at the explicit checkpoints.

## Phase 0 — Prerequisites

Verify before any code:

- Xcode 26 installed (`xcodebuild -version` returns `Xcode 26.x`).
- macOS Tahoe (26) on the build machine if Liquid Glass APIs will be used at compile time without `#available` gating.
- A clean target directory. If a project already exists, reroute to `audit-existing.md`.

## Phase 1 — Project skeleton (5 min)

**Decision:** Xcode project (`.xcodeproj`) or Swift Package (`Package.swift`)?

| Choice | When |
|---|---|
| Xcode project | App with bundle, code signing, App Sandbox entitlements, MAS distribution |
| Swift Package + executable target | Tooling, CLI, headless agent, dev-only utility |

Default to Xcode project for a real macOS app — Settings scene, App Sandbox, distribution flow all need it.

Use the **macOS App** template, SwiftUI Lifecycle, language Swift, deployment target macOS 26 (or 14+ with `#available(macOS 26, *)` gates if backward compatibility is needed). Confirm with user.

## Phase 2 — App scaffold (15 min)

Write the following at minimum:

```swift
@main
struct AppNameApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            CommandGroup(replacing: .appInfo) { Button("About AppName") { /* … */ } }
            CommandMenu("View") { /* app-specific items */ }
        }

        Settings {
            SettingsView()
        }
    }
}
```

Required first-day pieces:

- `WindowGroup` (or `Window` for single-window apps).
- `Settings { … }` scene — even if empty. Wires up `Cmd-Comma`. → `references/hig/components/menus.md`.
- `.commands { … }` — at minimum a placeholder so menu items can grow without restructuring. → `references/hig/platform/keyboard-shortcuts.md`.

## Phase 3 — Initial view (30 min)

Apply the **Three Questions** before writing any view:

1. **Is this navigation or content?**
2. **What is the ONE primary action?**
3. **Would Apple ship this?**

For a typical app start with `NavigationSplitView` + sidebar + detail:

```swift
struct ContentView: View {
    @State private var selection: Item.ID?

    var body: some View {
        NavigationSplitView {
            List(items, selection: $selection) { item in
                Label(item.name, systemImage: item.icon)
            }
            .backgroundExtensionEffect()
            .navigationSplitViewColumnWidth(min: 180, ideal: 200)
        } detail: {
            if let id = selection, let item = items.first(where: { $0.id == id }) {
                DetailView(item: item)
            } else {
                ContentUnavailableView("Select an item", systemImage: "sidebar.left")
            }
        }
        .toolbar { /* see references/hig/platform/toolbars.md */ }
    }
}
```

→ `references/liquid-glass/macos-patterns.md` for the canonical sidebar/toolbar/inspector recipes.

## Phase 4 — Quality hooks (10 min)

Install the pre-commit hook before any code is committed. Skipping this and adding it later means retrofitting baselines on a dirty tree.

Run from the repo root:

```bash
mkdir -p .githooks scripts
cp <skill-dir>/assets/swiftlint.yml      .swiftlint.yml
cp <skill-dir>/assets/swiftformat        .swiftformat
cp <skill-dir>/assets/githooks/pre-commit .githooks/pre-commit
cp <skill-dir>/assets/scripts/swift-typecheck.sh scripts/swift-typecheck.sh
chmod +x .githooks/pre-commit scripts/swift-typecheck.sh

# Append the Make targets, or copy if no Makefile exists yet
cat <skill-dir>/assets/Makefile.fragment >> Makefile

git config core.hooksPath .githooks
```

→ `references/quality-hooks/hook-architecture.md` for what each stage does and why.

For multi-platform CI, also drop `<skill-dir>/assets/github-workflows/swift-quality.yml` into `.github/workflows/`.

## Phase 5 — Snapshot scaffold (15 min)

Add a snapshot test target so visual drift is caught before a release.

→ `references/visual-validation/snapshot-testing-spm.md` for the full SPM + test-target wiring.

Smoke test:

```bash
xcodebuild test -scheme AppName -destination 'platform=macOS' -only-testing AppNameSnapshotTests
```

This will fail with "no recorded snapshot" the first time — that's expected. Record once, commit, then it becomes the regression check.

## Phase 6 — First commit

Stage and commit:

```bash
git add .swiftlint.yml .swiftformat .githooks/ scripts/ Makefile .github/workflows/
git commit -m "chore(scaffold): bootstrap macOS app with HIG, Liquid Glass, hooks, snapshots"
git add -A    # source files
git commit -m "feat(app): initial scaffold"
```

The pre-commit hook will run on the second commit and catch any SwiftFormat-pending changes — fix and re-stage if so.

## Phase 7 — Verification rung

State to the user which rung you actually reached:

- **Rung 1** — files created, no compile.
- **Rung 2** — `xcodebuild build` succeeds (run it).
- **Rung 3** — `make lint` clean, `make format-check` clean.
- **Rung 4** — `xcodebuild test` succeeds.
- **Rung 5** — App actually launches (`open *.app` or run from Xcode), main window renders, Cmd-Comma opens Settings.

Never claim done past Rung 2 without running the build. Never claim Rung 5 without observing the running app.

## Common bootstrap mistakes

- Skipping the `Settings { }` scene — Cmd-Comma silently no-ops, and there's no good time to retrofit it later.
- Using `NavigationView` instead of `NavigationSplitView` — deprecated and visually wrong on Tahoe.
- Hardcoding `.font(.system(size: 14))` anywhere — breaks Dynamic Type. Use `.body`, `.headline`, etc.
- Installing hooks after the first 50 commits — retrofitting baselines hides legacy issues silently. Install on commit zero.
- Recording snapshots on a non-pinned macOS version — pin the simulator or runner OS so renders are stable.
