# Pre-Release Ship Checklist

Run before every TestFlight / Mac App Store / direct-distribution release. This is the final gate. Do not claim "ready to ship" until every item is checked or explicitly waived in writing.

## 1. Code health

- [ ] `make lint` passes (zero warnings unless baselined; baseline diff reviewed in PR).
- [ ] `make format-check` passes.
- [ ] `SWIFT_HOOK_TYPECHECK=1 make lint-all` passes on macOS, plus every additional platform target.
- [ ] No `// TODO`, `// FIXME`, or `// HACK` introduced in this release without an issue link.
- [ ] No `print(...)` left in non-test code (custom SwiftLint rule `no_print_statements` should catch this).
- [ ] No `try!` or `as!` introduced without a justifying comment.

→ `references/quality-hooks/hook-architecture.md`

## 2. HIG compliance

- [ ] **Three Laws of macOS UI**:
  1. Every action in a menu equivalent.
  2. Standard keyboard shortcuts wired (`Cmd-N/O/S/Shift-S/Z/Shift-Z/Q/W/Comma/F`).
  3. Settings take effect immediately — no Save/Cancel/Apply.
- [ ] App, File, Edit, View, Window, Help menus present and ordered correctly.
- [ ] "Settings…" (not "Preferences…") on macOS 13+.
- [ ] Ellipsis only on items that need more input (`Open…`, `Save As…`) — not on About / Quit.
- [ ] Help menu has a search field.
- [ ] Modifier glyph order is canonical: Fn → Ctrl → Opt → Shift → Cmd.
- [ ] Toolbar items: leading sidebar toggle, app items, center nav, trailing search/share/inspector.

→ `references/hig/components/menus.md`, `references/hig/platform/toolbars.md`, `references/hig/platform/keyboard-shortcuts.md`.

## 3. Liquid Glass discipline

- [ ] Glass on navigation only — never on list rows, table cells, content text.
- [ ] Exactly ONE `.glassProminent` per screen.
- [ ] No hardcoded colors (`Color(red:)`, hex literals, `Color("#…")`) on glass surfaces.
- [ ] No fixed font sizes (`.font(.system(size:))`).
- [ ] `NavigationSplitView` (not `NavigationView`); `NavigationStack` for stack flows.
- [ ] No `@StateObject`/`@ObservedObject`/`@EnvironmentObject` on new code (use `@Observable`).
- [ ] No `.toolbarBackground(.visible)` on macOS 26 paths.
- [ ] No `.interactive()` on macOS code paths.
- [ ] Default window chrome and traffic lights — no custom drag regions.
- [ ] Tahoe-only APIs gated with `#available(macOS 26, *)`.
- [ ] Concentric corner radii (`.containerConcentric` / `ConcentricRectangle()`) where glass meets bordered content.

→ `references/liquid-glass/design-principles.md`, `references/liquid-glass/design-diagnosis.md`.

## 4. Accessibility

- [ ] Every interactive element has an `accessibilityLabel`.
- [ ] Icon-only buttons have a label (image-only is not enough).
- [ ] Decorative images marked `.accessibilityHidden(true)`.
- [ ] VoiceOver pass on the primary user flow (`Cmd-F5`, navigate, key actions reachable).
- [ ] Full Keyboard Access pass — every action reachable without mouse.
- [ ] Reduce Motion honored — transitions substitute `.opacity` or instant cuts.
- [ ] Increase Contrast honored — colors derived from semantic styles, not hex.
- [ ] Reduce Transparency honored — glass surfaces fall back to opaque material; NO crash, NO black void (known bug, see pitfalls).

→ `references/hig/technologies/accessibility.md`, `references/liquid-glass/pitfalls-and-solutions.md`.

## 5. Visual validation

- [ ] Snapshot tests pass on the pinned simulator OS / runner image.
- [ ] At least one snapshot per top-level view, both light and dark mode.
- [ ] `Matches` / `Drift` / `Better-than-expected` triage written in the release PR description.
- [ ] No "force-record" of snapshots in this release (record-mode commits should never land on `main`).

→ `references/visual-validation/expectation-loop.md`, `references/visual-validation/snapshot-testing-spm.md`.

## 6. Distribution prep

- [ ] App icon: 10 required sizes present, squircle geometry, no transparency on the largest. → `references/hig/foundations/icons-and-sf-symbols.md`
- [ ] App Sandbox entitlements reviewed — only the entitlements you actually use.
- [ ] Hardened runtime enabled.
- [ ] Notarization on direct-distribution builds; staple the ticket.
- [ ] Code signing identity matches the destination (Developer ID for direct, Mac App Distribution for MAS).
- [ ] `Info.plist` `LSMinimumSystemVersion` matches the deployment target.
- [ ] Crash reporter or telemetry signing/permissions verified.

## 7. Cloud sync (only if app talks to a backend)

- [ ] Auth token rotation works after expiry — tested with a forced-expire flow.
- [ ] Offline state shows a deterministic, user-visible indicator.
- [ ] Subscription cancellation on view dismiss verified — no leaked observers.
- [ ] Optimistic-update rollback paths tested.
- [ ] Production environment URL pinned and matches signing config.

→ `references/cloud-sync/swiftui-client.md`, `references/cloud-sync/auth-presentation.md`.

## 8. CI / Release artifacts

- [ ] CI on `main` is green for the release commit.
- [ ] Tag created and pushed (`git tag vX.Y.Z && git push --tags`) only after explicit user authorization.
- [ ] Release notes drafted.
- [ ] Sparkle/AppCenter/MAS upload artifact archived.

## 9. Sign-off

State to the user, in this exact form:

```
Ship checklist: PASSED / PARTIAL / BLOCKED

Verification rung reached: Rung 5 (app launches, primary flow exercised end-to-end).

PASSED items: …
PARTIAL items (waived with reason): …
BLOCKED items: … — these block the release.
```

If any CRITICAL or HIGH item is BLOCKED, the release does not ship. Do not unilaterally promote. Surface to the user.
