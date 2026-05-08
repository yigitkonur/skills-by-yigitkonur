# SwiftFormat Configuration

This skill defaults to **Nick Lockwood's `SwiftFormat`** (`brew install swiftformat`, latest stable `0.61.0` as of 2026-04). It is the dominant 2025-2026 production iOS/macOS choice (~4:1 install share over Apple's `swift-format` per Homebrew analytics) and ships a battle-tested `.pre-commit-hooks.yaml` at its repo root. SwiftFormat is also the formatter wired into the reference implementation in `~/dev/fast-talk` that this skill generalizes.

For the alternative path (Apple's `swift-format`), see the bottom of this file.

## Recommended `.swiftformat` for new Apple-platform projects

Drop this at the repo root. Tuned to match SwiftLint's expectations and Swift 6 idioms.

```
--swiftversion 6.0
--indent 4
--indentcase true
--trimwhitespace always
--voidtype void
--wraparguments before-first
--wrapparameters before-first
--wrapcollections before-first
--maxwidth 160
--rules sortImports,blankLinesBetweenScopes,consecutiveBlankLines,consecutiveSpaces,duplicateImports,redundantBreak,redundantLet,redundantNilInit,redundantParens,redundantReturn,redundantSelf,redundantVoidReturnType,strongifiedSelf,trailingCommas,trailingSpace,unusedArguments,wrapMultilineStatementBraces
--disable acronyms,wrapConditionalBodies
--exclude .build,Packages,.spm-cache,DerivedData,*.xcodeproj
```

### Why these flags

| Flag | What it does | Why this value |
|---|---|---|
| `--swiftversion 6.0` | Tunes rules to Swift 6 idioms (e.g. `consume`, `sending`, `~Copyable`) | Modern Apple-platform default; bump alongside the project's `swift-tools-version`. |
| `--indent 4` | 4-space indent | Apple's house style; matches Xcode default. |
| `--indentcase true` | Indent `case` inside `switch` | Reduces visual noise in long switches. |
| `--trimwhitespace always` | Trim trailing whitespace on all lines | Eliminates whitespace diffs on save. |
| `--voidtype void` | Use `Void` (lowercase `void` is `()` parens) | Idiomatic Swift; avoids confusion with empty tuple. |
| `--wraparguments before-first` | Multi-line call args wrap with paren on its own line | Cleaner diffs when args are added/removed. |
| `--wrapparameters before-first` | Same for declarations | Consistent with calls. |
| `--wrapcollections before-first` | Same for arrays/dicts/sets | Ditto. |
| `--maxwidth 160` | Soft wrap target | Generous enough for descriptive Swift symbol names without forcing ugly breaks; pair with SwiftLint `line_length: warning: 140` for stricter enforcement. |
| `--rules ...` | Explicit allow-list | Prevents accidental rule additions when SwiftFormat updates. Pinned set covers the common-sense formatting cleanups without aggressive rewrites. |
| `--disable acronyms,wrapConditionalBodies` | Turn off two opt-out rules | `acronyms` rewrites your identifiers (`URL` → `Url`) — annoying. `wrapConditionalBodies` collapses guards in surprising ways. |
| `--exclude` | Skip generated/vendored dirs | `.build`, `.spm-cache`, `Packages` (vendored SPM packages), Xcode project bundles. |

## Pre-commit invocation

The hook runs SwiftFormat in **`--lint` mode** — it verifies formatting matches the config and exits non-zero if any staged file would change. It does NOT modify files at commit time.

```bash
swiftformat --lint --quiet "$@"        # $@ = the staged .swift files
```

When this fails, the hook tells the developer to run `make format` (or `swiftformat .`) and re-stage. The `--lint` mode returns exit code `1` on any diff (per SwiftFormat issue #966).

### Why not auto-format on commit?

Auto-formatting at commit time silently rewrites files the developer didn't review. That's surprising behavior and can introduce unintended changes if the formatter's rules drift. The hook stays advisory; the `make format` target stays explicit.

## Disable list inside `.swiftlint.yml`

SwiftFormat overlaps with several SwiftLint rules. Disable these in `.swiftlint.yml` to prevent fighting between the tools:

```yaml
disabled_rules:
  - opening_brace                            # SwiftFormat owns brace placement
  - trailing_comma                           # SwiftFormat adds trailing commas; SwiftLint defaults to forbidding them
  - vertical_parameter_alignment_on_call     # SwiftFormat owns wrap style
  - statement_position                       # SwiftFormat owns `else` placement
```

Source: this is the same disabled-rules block used in apple/pir-service-example/.swiftlint.yml (an Apple-published repo using SwiftFormat).

## Configuration tuning by project age

| Project state | Recommendation |
|---|---|
| Greenfield Swift 6 project | Use the config above as-is. Run `swiftformat .` once to baseline, then enforce via hook. |
| Mature project (>50k LOC) | Run `swiftformat --lint .` first to see the diff size. If huge, do the format pass on a dedicated PR (no other changes), then enable the hook. Never mix a format-everything commit with feature work. |
| Library targeting older Swift | Drop `--swiftversion 6.0` to whatever your `Package.swift` declares (`5.9` is a common floor). |

## Apple platform notes

SwiftFormat is **platform-agnostic** — it parses `.swift` source on the host machine and produces identical output regardless of whether the target is macOS, iOS, tvOS, watchOS, or visionOS. There are no per-platform `.swiftformat` settings to worry about.

`#if os(...)` conditional-compilation blocks are correctly handled (since SwiftFormat 0.55.x) including parameter packs and Swift 6 strict-concurrency annotations.

## Alternative: Apple's `swift-format`

If the team already uses Apple's `swift-format` (Xcode 16+ ships it built-in via Editor → Structure → Format File, and the Swift toolchain provides it as `swift format`), use it instead of SwiftFormat. The two tools are NOT compatible — pick one and never run both.

### When to choose `swift-format`

- Repo is destined for `swiftlang/` open-source publication
- Team wants a single Swift-toolchain dependency (no Homebrew formula)
- Project already has a `.swift-format` JSON file
- Team uses Xcode 16's built-in formatter via `⌃⇧I` and wants CI/hook to match exactly

### `swift-format` config (`.swift-format`)

```json
{
    "version": 1,
    "indentation": { "spaces": 4 },
    "lineLength": 140,
    "respectsExistingLineBreaks": true,
    "lineBreakBeforeControlFlowKeywords": false,
    "lineBreakBeforeEachArgument": true,
    "lineBreakBeforeEachGenericRequirement": true,
    "rules": {
        "AllPublicDeclarationsHaveDocumentation": false,
        "NoBlockComments": false
    }
}
```

### `swift-format` pre-commit invocation

```bash
swift-format lint --strict --configuration .swift-format "$@"
```

`--strict` makes lint warnings exit non-zero (per swiftlang/swift-format LintFormatOptions.swift). The default behavior since `602.0.0` is warnings, not errors — `--strict` restores commit-blocking semantics.

### `swift-format` SwiftLint disable list

Same as SwiftFormat:

```yaml
disabled_rules:
  - opening_brace
  - trailing_comma
  - vertical_parameter_alignment_on_call
  - statement_position
```

## References

- nicklockwood/SwiftFormat — https://github.com/nicklockwood/SwiftFormat
- SwiftFormat Rules.md — https://github.com/nicklockwood/SwiftFormat/blob/main/Rules.md
- SwiftFormat .pre-commit-hooks.yaml — https://github.com/nicklockwood/SwiftFormat/blob/main/.pre-commit-hooks.yaml
- swiftlang/swift-format — https://github.com/swiftlang/swift-format
- swift-format Configuration.md — https://github.com/swiftlang/swift-format/blob/main/Documentation/Configuration.md
- apple/pir-service-example/.swiftlint.yml — disabled_rules pattern (Apple-published repo using SwiftFormat)
