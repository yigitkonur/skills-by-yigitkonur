# Finding file template — `nextjs-enhancement/findings/<domain>/NN-<slug>.md`

Written by an audit agent in Phase 3. One file per distinct issue. A finding is raw
evidence, not a plan — Phase 4 clusters findings into tasks.

**Zero findings is a valid result.** An agent whose domain is already compliant writes
nothing and says so in its handback.

```markdown
# Finding NN: <short descriptive title>

**Domain:** <domain slug>
**Severity:** critical | major | minor | informational
**Confidence:** probe-verified | version-inferred
**Gate row / pitfall:** <which applicability-gate row or pitfall signature this maps to>
**Recipe:** `references/fix/<domain>.md` § `<recipe H2>` — or `none — no recipe covers this`

## What was found

One or two sentences, specific and present-tense.

## Evidence

- `<path>:<line>` — `<literal matched text>`
- `<path>:<line>` — `<literal matched text>`

Detection command:
```bash
<the exact command that produced these matches>
```

## Why it matters

One or two sentences drawn from the domain reference — mechanism, not adjectives. What
degrades, breaks, or costs.

## False-positive checks cleared

- [ ] Live code, not a comment/docstring/string literal
- [ ] Not a test, story, mock, RSS/XML route, or `ImageResponse`/Satori context
- [ ] Surface is version-available on this install (probe row cited)
- [ ] Not already correct / already deliberately diverged with a rationale
- [ ] Not better filed once against a shared wrapper
- [ ] Severity reflects present-tense impact

(All six must be checked. See `references/workflow/false-positives.md`.)

## Suggested fix direction

One or two sentences. Points at the recipe; does not write the patch — that is Phase 4/5.

## Scope estimate

Files likely touched: `<paths or glob>` · Shared wrapper: `<path or none>` ·
Reversibility: `fully-reversible | component-level-revert | migration-required`
```

## Rules

1. **Evidence is copied, never paraphrased.** Exact `file:line` and the literal matched
   text, straight from the detection command's output.
2. **Include the command.** A reader must be able to reproduce the match.
3. **One issue per file.** Ten call sites of the same problem is one finding (with ten
   evidence lines), not ten files.
4. **Cite the gate row.** A finding that cannot name the gate row or pitfall it maps to is
   not grounded in the reference and should not be filed.
5. **Severity is present-tense.** Deprecated-but-working is `minor`. Reserve `critical`
   for removed surfaces, build/runtime errors, or user-visible breakage now.
6. **`informational` findings exist** for deliberate divergence worth noting — they must
   never become tasks on their own.
7. **Numbering** is per-domain discovery order (`01`, `02`, …) — no cross-domain coordination.
8. **Write scope is exactly `findings/<domain>/`.** Never another domain's folder, never
   the target repo's source.

## Worked example

```markdown
# Finding 02: Deprecated `priority` prop used in shared image wrapper

**Domain:** image-optimization
**Severity:** minor
**Confidence:** probe-verified
**Gate row / pitfall:** `<Image priority>` — deprecated 16.0.0, still functional
**Recipe:** `references/fix/image-optimization.md` § `priority → successor migration`

## What was found

The shared `ProjectImage` wrapper accepts and forwards a `priority` prop, which Next.js
deprecated in 16.0 in favour of `preload` / `fetchPriority` / `loading`. Six call sites
pass it, but all route through this one component.

## Evidence

- `src/components/project-image.tsx:128` — `priority?: boolean`
- `src/components/project-image.tsx:183` — `const imgLoading = priority ? 'eager' : loading || 'lazy'`
- `src/components/project-image.tsx:232` — `priority={priority}`

Detection command:
```bash
rg -n '\bpriority\b' --glob '*.tsx' -g '!**/*.test.*' src/components
```

## Why it matters

`priority` is deprecated as of 16.0 and slated for removal. It still works on the
installed 16.2.9, so nothing is broken today — but the successor props state intent more
precisely and avoid migration debt at the next major.

## False-positive checks cleared

- [x] Live code — JSX prop and type declaration, not comments
- [x] Not a test/story/RSS/og context
- [x] `fetchPriority` (13.3+) and `loading` are both available on 16.2.9
- [x] Not already migrated
- [x] Filed once against the wrapper, not against the six callers
- [x] `minor` — deprecated but functional on this version

## Suggested fix direction

Replace the forwarded `priority` prop with `fetchPriority="high"` + `loading="eager"`
inside the wrapper, keeping the wrapper's own boolean API so callers stay unchanged.

## Scope estimate

Files likely touched: `src/components/project-image.tsx` · Shared wrapper: same ·
Reversibility: fully-reversible
```
