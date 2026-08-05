# False positives — what looks like a finding but is not

Every rule below was derived from a real probe against a production Next.js repo during
this skill's design. A naive `grep` produced each of these; each would have wasted a task
or shipped a breaking change.

**The test before filing any finding:** does this cause a measurable problem, or violate a
documented constraint? "It differs from the reference config" is not a finding.

## 1. A match inside a comment is not usage

Observed: a route handler containing the literal text `export const dynamic` inside a NOTE
comment explaining *why not to add it*. A grep for legacy segment exports flagged the one
file that was already correct.

**Rule:** before filing, confirm the match is live code — not a comment, docstring, JSDoc,
string literal, or disabled block. Check the line's leading characters (`//`, `*`, `#`) and
read surrounding context. When in doubt, read the file.

## 2. Non-page render contexts are exempt from page rules

Observed: raw `<img>` tags in `app/api/rss/**/route.ts` (XML feed strings) and in an
`api/og` route using `ImageResponse`.

**Rule:** `next/image` rules apply to JSX rendered into HTML pages. They do **not** apply to:
- RSS/XML/feed route handlers producing markup strings
- `ImageResponse` / Satori contexts, where `next/image` does not work and raw `<img>` is required
- email templates
- `.md`/`.mdx` content files
- test fixtures and stories

## 3. Test files are excluded

Observed: 29 files matched raw `<img>`, but most were `*.test.tsx` mocks; only two were
production components.

**Rule:** exclude `*.test.*`, `*.spec.*`, `__tests__/`, `__mocks__/`, `e2e/`, `.storybook/`,
`*.stories.*` from every detection sweep unless the finding is specifically about test
infrastructure.

## 4. Wrapper components collapse N call sites into one finding

Observed: `priority` appeared across 6+ components — all of which passed it through a
single shared `project-image.tsx` wrapper that owned the `<Image>` usage.

**Rule:** when many call sites route through one shared component, file **one** finding
against the wrapper. Fixing the wrapper fixes every caller. Filing six findings creates six
tasks that would conflict in the same file.

## 5. Deliberate divergence with a rationale is informational

Observed: `images: { qualities: [75, 85], minimumCacheTTL: 31536000, formats: ['image/avif','image/webp'] }`
— every value differs from the documented default, each with an adjacent comment explaining
the tradeoff.

**Rule:** config that differs from a default **and** carries an explanatory comment, or is
clearly tuned as a set, is `informational` at most. Only file a finding when the corpus
says the specific value is unsafe or breaks something — never to "restore defaults".

## 6. Deprecated-but-functional is `minor`, never `critical`

Observed: `priority` is deprecated as of 16.0, but the installed 16.2.9 still implements
it. Nothing is broken today.

**Rule:** severity reflects present-tense impact. A deprecated API that still works on the
installed version is `minor` with an upgrade note. Reserve `critical` for surfaces that are
genuinely removed, error at build/runtime, or cause user-visible breakage now.

## 7. Never recommend a config key the install does not have

Observed: `partialPrefetching` returns zero matches in 16.2.9's config schema, even though
its documented prerequisite (`cacheComponents`) was satisfied.

**Rule:** probe first (`references/gating/capability-probe.md`). A key absent from the
installed schema is `NOT-APPLICABLE` — emit no task. An upgrade recommendation is its own
separate, explicit task, never smuggled inside a feature task.

## 8. Never blind-delete a flag the install still accepts

Observed: `experimental.viewTransition` is recorded as removed in the 16 line, yet the
installed 16.2.9 schema still contains the key and the project sets it deliberately.

**Rule:** the graveyard says what the docs record; the probe says what the repo has. Probe
wins. If the key is `present`, do not emit a removal task — at most a `minor` note to
re-check on upgrade. Removal is correct only when the probe says `absent` while the config
still sets it.

## 9. A genuine dependency is not a fixable waterfall

Two sequential awaits where the second needs the first's result is structural. `Promise.all`
cannot fix it.

**Rule:** classify before filing. Same-component *independent* sequential awaits are a real
waterfall. A parent→child data dependency is not — the fix is a Suspense boundary so the
page paints, not parallelization.

## 10. Legitimate client-side fetching exists

Observed: two `useEffect` + `fetch` sites — a site-search box and a client error beacon.

**Rule:** client fetching is correct for interaction-driven data (search-as-you-type,
telemetry, polling, browser-only APIs). Only file a finding when server-fetchable initial
page content is being fetched on the client.

## 11. A repo that already did the work needs no task

Observed: `cacheComponents: true` already set; `next/font/local` already self-hosting;
zero `runtime = 'edge'` exports.

**Rule:** recon and applicability run before the audit precisely so the skill never
proposes work already done. Note it as satisfied in `01-applicability.md` and move on.

## 12. `prefetch={false}` on a long list is correct

**Rule:** disabling prefetch on large or low-click link lists is the documented
optimization. Never flag it as "prefetching disabled".

## 13. Custom implementations are not defects

Observed: custom `data-theme` theming with a pre-paint script (no `next-themes`), and
custom i18n with locale JSON dictionaries (no `next-intl`).

**Rule:** verdict `APPLICABLE-CUSTOM`. Compare the *mechanism* against the corpus pattern
and flag only genuine gaps (e.g. a missing `color-scheme`, a hydration-unsafe read).
Proposing a library migration for a working custom implementation is itself the false
positive.

## Filing discipline

Before writing a finding file, the audit agent confirms, in order:

1. The match is live code, not a comment or string.
2. The file is not excluded (test, story, mock, non-page render context).
3. The surface is version-available per the capability probe.
4. It is not already correct, already done, or deliberately diverged with a rationale.
5. It is not better filed once against a shared wrapper.
6. Severity reflects present-tense impact on the installed version.

A finding that cannot clear all six is not filed. Under-reporting a marginal issue costs
far less than a task that breaks a working repo.
