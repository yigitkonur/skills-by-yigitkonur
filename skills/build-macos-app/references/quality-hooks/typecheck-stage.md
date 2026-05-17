# Typecheck stage (opt-in)

Stage 4 of the hook. Disabled by default; enable per-shell with `export SWIFT_HOOK_TYPECHECK=1`. Catches real Swift type errors that SwiftLint can't see (missing types, signature mismatches, generic constraints).

## Why opt-in (not default)

Apple-platform builds drift. Package graph state is fragile. Simulator runtimes go missing. The hook must stay deterministic; an unreliable typecheck stage trains developers to `--no-verify` reflexively.

Opt-in semantics: developer explicitly says "I trust the build state right now, run the typecheck". CI runs typecheck unconditionally (separate from the hook).

## Per-platform destination matrix

The script translates `SWIFT_HOOK_PLATFORM` to the right xcodebuild destination:

| `SWIFT_HOOK_PLATFORM` value | xcodebuild destination | Simulator runtime needed? | Typical incremental speed |
|---|---|---|---|
| `macOS` (default) | `generic/platform=macOS` | No | 3-8s |
| `iOS` | `generic/platform=iOS Simulator` | Yes (preinstalled) | 5-15s |
| `tvOS` | `generic/platform=tvOS Simulator` | Yes (usually present) | 5-15s |
| `watchOS` | `generic/platform=watchOS Simulator` | Yes (usually present) | 5-15s |
| `visionOS` | `generic/platform=visionOS Simulator` | **Often missing** — install with `sudo xcodebuild -downloadPlatform visionOS` | 10-25s |

Per-platform deep dives: `references/platforms/<name>.md`.

## Why `xcodebuild build`, not `swiftc -typecheck` per file

`swiftc -typecheck path/to/file.swift` would be the fastest per-file mode. But:

- `swiftc` needs all framework search paths, defines, module maps, and conditional-compilation flags from the project's build settings
- Recovering them via `xcodebuild -showBuildSettings` per file is slow and brittle
- An Xcode project's modules can't be typechecked file-by-file without the project context

So the script runs `xcodebuild build` against the project graph. Slower per-invocation but accurate. Incremental builds (with derived-data warm) are still <10s for typical projects.

## Why `xcodebuild build`, not `xcodebuild analyze` or `-dry-run`

Per the Apple `xcodebuild(1)` man page, the available actions are: `build, build-for-testing, analyze, archive, test, test-without-building, docbuild, installsrc, install, clean`.

- `analyze` runs the static analyzer **on top of** a build — slower than `build`
- `-dry-run` only prints what *would* be executed without doing anything — does NOT typecheck
- There is **no first-class "typecheck-only" action**

So `build` is the right verb. The flags below make it as fast as possible.

## Speed-up flags

```bash
-quiet                              # suppress all output except warnings/errors
-parallelizeTargets                 # build independent targets concurrently
-skipMacroValidation                # bypass "Trust & Enable" prompt for swift-syntax macros
-skipPackagePluginValidation        # bypass equivalent for SPM plugins (acccept security tradeoff)
-derivedDataPath /tmp/swift-hook-build      # shared with Makefile to avoid duplicating builds
-clonedSourcePackagesDirPath .spm-cache     # reuse SPM checkout cache
ONLY_ACTIVE_ARCH=YES                # build only the active arch — single biggest local-build speedup
CODE_SIGNING_ALLOWED=NO             # skip codesign step (no value for typecheck)
CODE_SIGNING_REQUIRED=NO            # ditto, belt-and-suspenders
```

Note: `-skipMacroValidation` and `-skipPackagePluginValidation` "bypass Xcode's validation dialogs and implicitly trust all plugins and macros, which has security implications" (per SwiftPackageIndex SwiftLint page). Fine for a developer-machine pre-commit hook on a trusted repo; consider whether to enable in CI.

## Project-type detection

The script auto-detects:

```sh
HAS_PACKAGE_SWIFT && ! HAS_XCWORKSPACE && ! HAS_XCODEPROJ  →  spm
HAS_XCWORKSPACE                                            →  workspace
HAS_XCODEPROJ                                              →  xcodeproj
```

Then chooses:

| Type | Command |
|---|---|
| `spm` + macOS | `swift build --build-tests=false` (fastest; host-platform only) |
| `spm` + non-macOS | `xcodebuild -scheme <pkg-name> -destination "generic/platform=..."` |
| `workspace` | `xcodebuild -workspace <name>.xcworkspace ...` |
| `xcodeproj` | `xcodebuild -project <name>.xcodeproj ...` |

`swift build --triple arm64-apple-ios` is **NOT supported** for cross-compiling to Apple non-host platforms (apple/swift-package-manager#6571). Even pure-SPM repos must use `xcodebuild` for non-host targets.

## Package-graph sanity check

Before running xcodebuild on `xcodeproj` projects with a `project.yml` (xcodegen), the script checks that each `Packages/<name>/` path referenced by `project.yml` actually exists. If any is missing, the script **gracefully skips** with a warning — graph drift is not a hook failure (the developer may be in the middle of an SPM migration). The hook still passes.

This pattern came from the FastTalk reference implementation where deleted local packages would otherwise have blocked every commit.

## Failure output

On typecheck failure, the script prints:
- The platform that failed
- The first 30 error/warning lines from the xcodebuild log
- The path to the preserved log file for full inspection

```
  ✗ xcodebuild typecheck failed (platform=iOS, scheme=YourApp):
    /Users/.../File.swift:42:10: error: cannot find 'foo' in scope
    /Users/.../Other.swift:15:5: warning: 'bar' is deprecated
    ...
    Full log: /tmp/swift-typecheck.XXXXXX.log (preserved on failure)
```

## Disabling for one commit

When a developer needs to commit despite a transient build break:

```bash
SWIFT_HOOK_TYPECHECK=0 git commit -m "wip: refactor in progress"
```

This is a per-command env override; the developer's shell-level `export SWIFT_HOOK_TYPECHECK=1` stays active for subsequent commits.

## References

- `xcodebuild(1)` man page — actions, destinations
- Apple build settings reference — `ONLY_ACTIVE_ARCH`, `CODE_SIGNING_ALLOWED`
- apple/swift-package-manager#6571 — `swift build --triple` unsupported
- forums.swift.org/t/77609 — swift build vs xcodebuild relationship
- SwiftPackageIndex SwiftLint page — security implications of `-skipPackagePluginValidation`
