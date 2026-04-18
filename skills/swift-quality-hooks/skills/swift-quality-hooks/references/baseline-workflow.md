# Baseline workflow

For greenfield projects, the SwiftLint baseline file should be `[]` (empty — zero violations to suppress). For legacy codebases with existing violations, the baseline lets you roll out strict linting **without forcing a rewrite of every existing file**: future PRs fail only on NEW violations.

Native baselines were added in **SwiftLint 0.55.1** and are the modern way to roll out strict linting on legacy code.

## Greenfield — baseline as `[]`

```bash
echo '[]' > .swiftlint-baseline.json
git add .swiftlint-baseline.json
```

That's it. The baseline file exists, suppresses nothing, and grows zero hidden debt over time.

## Legacy codebase rollout

When the repo has many existing violations and you don't want to fix them all upfront:

```bash
# Step 1: Snapshot all current violations into the baseline
swiftlint --write-baseline .swiftlint-baseline.json

# Step 2: Verify the baseline filters them out
swiftlint --baseline .swiftlint-baseline.json --strict
# Should report 0 violations now

# Step 3: Commit the baseline
git add .swiftlint-baseline.json
git commit -m "chore(lint): seed SwiftLint baseline (legacy debt = N violations)"
```

From now on, `swiftlint lint` (which auto-applies the baseline at the default location) reports only NEW violations. The pre-commit hook will block on those, not on legacy debt.

## When to retire the baseline

The baseline is **technical debt made visible**. Retire it when:

1. Total baselined violations drop below ~20 (worth one cleanup session)
2. The baseline is older than 12 months and the codebase has shifted (regenerate to ensure it's still valid)
3. You're upgrading SwiftLint major version (rule renames invalidate baseline entries)

To retire:

```bash
# Fix the remaining violations one at a time
swiftlint lint --quiet | grep -v "$(cat .swiftlint-baseline.json | jq -r '.[].location.file' | sort -u)"

# Or sweep them all (risky on a large file count):
swiftlint --fix && # ... manual review of remaining ...

# Once clean, regenerate the baseline as empty
swiftlint --write-baseline .swiftlint-baseline.json
# Should write `[]`

git commit -am "chore(lint): retire SwiftLint baseline (zero violations)"
```

## When NOT to commit the baseline

- The repo has zero violations and zero plans for legacy debt → don't bother creating the file at all (SwiftLint just reports normally)
- Each developer is supposed to see different violations (rare; usually wrong)

The baseline is meant to be a **shared fact** — every contributor's `swiftlint lint` produces the same filtered result. Don't gitignore it.

## Known issues

- **Open issue (#6511):** fixing a baselined violation does NOT currently fail the lint — meaning a developer who fixes a baselined violation gets no feedback that they should also remove it from the baseline. Periodically regenerate (`swiftlint --write-baseline`) to drop fixed entries.
- **Issue #5597:** the baseline is generated against a specific `.swiftlint.yml` config; if you change the config (e.g., enable a new opt-in rule), the baseline can become stale. Regenerate after any config change.

## CI integration

In CI, run `swiftlint --strict --baseline .swiftlint-baseline.json` to enforce the baseline. Don't let CI write a new baseline (`--write-baseline`) — that would silently absorb new violations and defeat the purpose.

## Make targets

The skill's `Makefile.fragment` exposes:

```make
make lint-new       # swiftlint --baseline .swiftlint-baseline.json --strict
make lint-baseline  # swiftlint --write-baseline .swiftlint-baseline.json
```

Document `lint-baseline` as a "I just did a sweep, lock in the new state" command — not a daily-use command.

## Migration sequence for the very first SwiftLint adoption

```bash
# 1. Install SwiftLint, write configs
brew install swiftlint
cp <skill-assets>/.swiftlint.yml .

# 2. Capture the legacy debt
swiftlint --write-baseline .swiftlint-baseline.json
echo "Captured $(jq length .swiftlint-baseline.json) baseline violations"

# 3. Install the hook
make install-hooks

# 4. Commit everything
git add .swiftlint.yml .swiftlint-baseline.json .githooks/ Makefile
git commit -m "chore(lint): adopt SwiftLint with legacy baseline"

# 5. Periodically (monthly?) sweep the baseline down
swiftlint --fix && # review residue
swiftlint --write-baseline .swiftlint-baseline.json
# commit new baseline
```

## References

- realm/SwiftLint README §Configuration §baseline
- Baseline API docs — https://realm.github.io/SwiftLint/Structs/Baseline.html
- Issue #5597 — baseline config consistency
- Issue #6511 — baseline doesn't fail on fixed violations
