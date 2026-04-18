# Hook architecture

The skill installs a single `.githooks/pre-commit` script that runs 4 stages against staged `.swift` files only. Architecture decisions and their rationale.

## Why `.githooks/` + `core.hooksPath`, not `.git/hooks/`

| | `.git/hooks/` (legacy) | `.githooks/` + `core.hooksPath` |
|---|---|---|
| Versioned in git | No (local only) | **Yes** — committed to repo |
| Shared across team | No | **Yes** |
| Survives `git clone` | No | **Yes** (after one-time `make install-hooks`) |
| Conflict with global hooks | Often unclear | Clean — repo override visible |
| Modern best practice | No | **Yes** (since git 2.9, May 2016) |

The skill always uses `core.hooksPath`. Never copy hooks to `.git/hooks/` directly.

## The 4 stages

```
pre-commit
├── Stage 0: Skip if $CI is set                      (CI runs full matrix separately)
├── Stage 1: SwiftLint --strict                       (block on any warning)
├── Stage 2: SwiftFormat --lint  OR  swift-format    (block on any format diff)
├── Stage 3: scripts/check-quality.sh                 (optional repo-side guardrail)
└── Stage 4: scripts/swift-typecheck.sh               (opt-in via SWIFT_HOOK_TYPECHECK=1)
```

Each stage either passes silently or aborts the commit with a one-line remediation hint.

## Why staged files only, not the whole repo

Linting the whole repo on every commit:
- Wastes time on files the user didn't touch
- Surfaces pre-existing violations the user didn't introduce
- Conflicts with the baseline workflow (which suppresses pre-existing debt)

Linting **only staged files** (`git diff --cached --name-only --diff-filter=ACMR | grep '\.swift$'`):
- Sub-second on typical commits
- Only flags what the user is actually about to commit
- Gives the boy-scout-rule: leave-cleaner-than-you-found-it incentive

The downside: SwiftLint when invoked with explicit file args **bypasses the baseline** (the baseline is consulted only when running against the whole project). For per-file invocations, every violation in the touched files is reported. This is a feature: a developer touching a file with pre-existing violations sees them and can choose to fix or `// swiftlint:disable:this <rule>` them.

## Why `--strict`

`swiftlint lint` (no `--strict`) downgrades violations to warnings — the hook would never block a commit. `--strict` upgrades all violations to errors, so the hook blocks on anything the config flags. This is the only way to enforce style at commit time.

If the team isn't ready for full strictness, **lower the rules in `.swiftlint.yml`**, don't drop `--strict`. A weakened ruleset is intentional; a non-strict hook is just absent.

## Why `--lint` for the formatter (not auto-rewrite)

Auto-formatting at commit time silently rewrites files the developer didn't review. Two failure modes:

1. The developer staged file A; the formatter rewrote files B and C as a side effect. The commit now contains files the developer didn't intend.
2. The formatter has a bug or rule disagreement; auto-rewrite introduces an unintended change.

`--lint` mode verifies and fails — explicit. `make format` is the explicit-rewrite escape hatch when the developer wants to apply formatting.

## Why CI auto-skip

CI runs the **full** check matrix (all platforms, all rules, full project) via `make lint-all`. Re-running the pre-commit hook in CI duplicates work and clutters logs. The `$CI` env var is set by GitHub Actions, GitLab CI, CircleCI, and most CI providers — the skip is universal.

## Why the typecheck stage is opt-in

Apple-platform builds break transiently:
- Package graph drift (e.g., a local SPM dep was deleted but project.yml still references it)
- Missing simulator runtimes (visionOS especially)
- Swift compiler version mismatches in transitive SPM deps
- Expired developer certs
- Macros and SPM plugins requiring trust prompts

A hook that fails on every commit during these states becomes useless — developers add `--no-verify` and never remove it. The opt-in `SWIFT_HOOK_TYPECHECK=1` env var means typecheck only runs when the developer explicitly trusts the build state. CI runs typecheck unconditionally (separate from the hook).

## `make install-hooks` semantics

```make
install-hooks: ## Install repo-managed git hooks
	@git config core.hooksPath .githooks
	@echo "✓ git hooks installed (core.hooksPath = .githooks)"
```

One-time per clone. Doesn't write to `~/.gitconfig` (only to the repo's local `.git/config`). Safe to re-run; idempotent.

## `make uninstall-hooks` semantics

```make
uninstall-hooks: ## Restore default git hooks path
	@git config --unset core.hooksPath || true
	@echo "✓ git hooks uninstalled (core.hooksPath unset)"
```

Removes the local override. If the user has a **global** `core.hooksPath` configured (`git config --global core.hooksPath`), git falls back to that. If no global value, git uses `.git/hooks/` (which contains only the stock samples).

## Bypass for emergency commits

`git commit --no-verify` skips the pre-commit hook for one commit. Document in the team's CLAUDE.md / README that this is for emergencies only — fix the underlying issue and re-enable.

## References

- git-config(1) man page — `core.hooksPath` (since git 2.9, 2016-06-13)
- realm/SwiftLint README §Git pre-commit Hook — https://github.com/realm/SwiftLint
- nicklockwood/SwiftFormat issue #966 — `--lint` exit codes
- gist.github.com/candostdagdeviren/9716e514355ab0fee4858c3d467269aa — staged-files lint pattern
