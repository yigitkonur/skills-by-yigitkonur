# Generic Dev Task Review

Catch-all for PRs that don't cleanly fit the six specific domains (backend, frontend, MCP, UI, CLI, content). Use this when the diff is:

- Configuration changes (CI/CD, lint config, package.json, Dockerfiles)
- Pure refactoring (no behavior change)
- Library or tooling upgrades
- Dev tooling scripts (pre-commit hooks, local scripts)
- Cross-domain glue that doesn't clearly sit in one area
- A small mix that's not worth fanning out to specialists

Prefer the specific domain references when they apply. Route here only when none fit.

## What a generic reviewer cares about

| Concern | Why it matters | Evidence they want |
|---|---|---|
| **Scope match** | Does the PR do what the title/description claims, and nothing more? | Files touched match stated intent |
| **No hidden behavior change** | Refactors that secretly change behavior are the worst bugs | Tests unchanged, or new tests added for new behavior |
| **Backward compatibility** | Existing callers / consumers keep working | No silent contract break |
| **Dependencies + supply chain** | Every new dep is code you now ship | Justified additions; lockfile updated |
| **CI / tooling alignment** | Config changes affect every future PR | Rationale for the config shift |
| **Evidence of intent** | "Looks clean" is not a review | Author's rationale surfaced in body |

## Weaknesses the author should pre-empt

Pick the ones that apply to your diff:

- **Behavior change hidden in a "refactor".** Did the refactor actually preserve behavior? Run the test suite before + after and compare output, not just pass/fail.
- **Dependency bump side effects.** Upgrading `somepkg ^1.4.0` → `^2.0.0` — read the changelog, list breaking changes even if they seem minor.
- **Lockfile diff size.** Big lockfile diffs from small package.json changes indicate transitive dep churn. Is it expected?
- **CI config changes.** A small tweak to `.github/workflows/ci.yml` can skip tests for everyone. Does the change preserve prior coverage?
- **Build-system changes.** Webpack → Vite, tsup → esbuild, etc. — bundle output differs even if it "works". Do size / treeshaking match?
- **Script changes.** A modified pre-commit hook affects every contributor. Is the new behavior documented?
- **Env var changes.** New required env var: documented in `.env.example` and README? Removed env var: migration note?
- **Formatter / linter config changes.** The diff now has thousands of auto-fix lines. Is the config change intended?

## Questions to ask the reviewer explicitly

Customize to your diff. Examples:

- "This PR is marked 'refactor' — please confirm the test suite output is byte-identical before and after on the `packages/core` module."
- "`eslint` config got a new rule turned on, which created 14 lint fixes in the same PR. Prefer separate PRs (rule first, then fixes), or is this fine bundled?"
- "The dependency `foo` went from `^1.4.0` to `^1.5.1`. Their changelog notes a change in `bar.baz()` return shape under specific inputs — I believe we don't hit that path (see `test/foo.test.ts`). Please verify."
- "CI config now runs tests on Node 20 instead of Node 18. Is the Node-18 coverage still required for our support matrix?"
- "Added a new env var `FEATURE_FOO_ENABLED` with default `false`. Should this be surfaced in the onboarding docs, or is env-var discoverability handled elsewhere?"

## What to verify before opening the PR

General checks:

- [ ] Test suite passes locally
- [ ] Type-check / lint passes locally
- [ ] If the PR claims "refactor": run tests before and after, confirm same pass/fail outputs (and ideally same stdout where relevant)
- [ ] If dependency changed: lockfile is in sync, `npm audit` / `pnpm audit` checked
- [ ] If CI changed: locally reproduced the CI command chain where possible
- [ ] If env var added: `.env.example` / README updated
- [ ] If script/hook added: ran it on a real change to confirm the happy path

## Signals the review is off-track

- "Refactor, no behavior change — no tests needed." → Prove it. Run tests. Paste output.
- "It's just a config tweak." → Config tweaks have blast radius. Justify the change.
- "I'll update the docs after." → Update them now or file as a follow-up explicitly.
- "The dep bump is minor, changelog says so." → Trust, verify. Paste the relevant changelog excerpt in the body.

## When to split the PR

Generic PRs are often the ones that *should* be split:

- Refactor + unrelated fixes → split
- Dep bump + code changes that use new dep features → split (dep bump first, proof it holds, then use the features)
- CI config + code that happens to pass on new CI → split
- Formatter config + the auto-fix diff → split; fix diff lands after config

When you can't describe the PR in one line without "and", you probably want two PRs.

## Default review body shape for generic PRs

Without a specific domain lens, structure the body as:

```
# <title>

## Summary
<What this does, in one paragraph. No "and"s if possible.>

## Why
<Why now. What problem this addresses. Link the issue if any.>

## Changes
<Per-file or per-logical-chunk. Rationale for each.>

## Verification
<Exactly what you ran. Do not over-claim.>

## Weaknesses and open questions
<At least two. Generic doesn't mean trivial.>

## Not in scope
<Explicit follow-ups.>
```

Keep it under 3000 characters if at all possible. Most generic PRs do not warrant long bodies.
