# Capability probe — the gate primitive

**The rule: gate on what the installed package supports, never on a version number you
assumed.** A repo's `package.json` can say one thing, its lockfile another, and its
`node_modules` a third. Only the installed package decides whether a config key is real.

This file defines the probe. Everything in `references/detect/*.md` depends on it.

## Why version arithmetic is not enough

This skill's knowledge was verified against Next.js 16.3.0. Most repos are not on 16.3.0.
Three failure modes come from reasoning off the version string alone:

1. **Recommending a feature that does not exist yet.** `partialPrefetching` shipped in
   16.3.0. On 16.2.9 the key is absent from the config schema; setting it can throw at
   config validation. A version-only gate that mis-parses `16.2.9` as "16.2 ≥ 16" ships a
   broken config.
2. **Deleting a key that still works.** The corpus records `experimental.viewTransition`
   as removed in the 16 line. But a specific 16.2.x install may still carry the key in its
   schema. Blind removal based on the graveyard alone is a breaking change.
3. **Trusting `package.json` over reality.** `"next": "^16.2.0"` with a stale lockfile,
   a patched fork, or a monorepo hoist can resolve to something else entirely.

The probe replaces all three guesses with one observation.

## What the probe reads

`scripts/probe-capabilities.py <repo-root>` resolves, in order:

| Signal | Path | What it establishes |
|---|---|---|
| Installed version | `node_modules/next/package.json` → `.version` | The only authoritative version |
| Config-key support | `node_modules/next/dist/server/config-schema.js` | Whether a `next.config` key is accepted |
| React version | `node_modules/react/package.json` → `.version` | Gates React 19.2 APIs (`<Activity>`, `useEffectEvent`) |
| Declared version | `package.json` → `dependencies.next` | Compared against installed; a mismatch is itself a finding |

The config schema is a single bundled file listing every accepted key. Grepping it for an
exact key name answers "does this install accept this option?" without running a build.

## Probe verdicts

Each probed key resolves to one of:

- **`present`** — key found in the installed schema. The feature can be configured.
- **`absent`** — key not found. **Never recommend it.** Emit no task proposing it.
- **`unresolved`** — `node_modules` missing or schema file not where expected (pnpm strict
  layouts, Yarn PnP, unusual hoisting). Fall back to version comparison and **mark every
  downstream finding `confidence: version-inferred`** so a human can see the weaker basis.

`present` does not mean "should adopt" — that is what `references/gating/priority-matrix.md`
and `references/gating/lockin-reversibility.md` decide. The probe answers *availability
only*.

## Keys worth probing

Probe these before any recommendation touching them. (Grouped by the domain that owns them.)

| Key | Domain | Introduced | Note |
|---|---|---|---|
| `cacheComponents` | rendering-strategy-caching | 16.0.0 | Gates Partial Prefetching + automatic `<Activity>` |
| `partialPrefetching` | navigation-prefetching | 16.3.0 | Also requires `cacheComponents` |
| `experimental.staleTimes` | navigation-prefetching | 14.2.0 | Present ≠ advisable — experimental, production-discouraged |
| `experimental.viewTransition` | page-transitions-view-transitions | 15.x | Corpus records removal in 16; probe before removing |
| `experimental.cachedNavigations` | navigation-prefetching | 16.2.0 | Experimental |
| `experimental.prefetchInlining` | navigation-prefetching | 16.2.0 | Experimental |
| `experimental.useOffline` | navigation-prefetching | 16.3.0 | Experimental |
| `experimental.inlineCss` | bundle-code-splitting | 16.2.0 | CSS delivery |
| `reactCompiler` | bundle-code-splitting | 16.0.0 stable opt-in | Not a bundle-size reducer |
| `experimental.turbopackRustReactCompiler` | build-performance-turbopack | 16.3.0 | Experimental |
| `experimental.optimizePackageImports` | bundle-code-splitting | pre-14.2 | Formally experimental despite wide use |
| `experimental.turbopackFileSystemCacheForBuild` | build-performance-turbopack | 16.0/16.3 default | Default-on state varies by minor |
| `htmlLimitedBots` | seo-metadata | 15.2.0 | Overrides, does not extend, the default bot list |
| `serverExternalPackages` | bundle-code-splitting | 15.0.0 | Renamed from `serverComponentsExternalPackages` |

Absence of a key in this table is not permission to skip probing — probe any key a task
would add or remove.

## Worked example (real, `../zeo-website`, captured during design)

```
installed next: 16.2.9        declared: 16.2.9        react: 19.2.7
partialPrefetching            → absent      (0 matches in config-schema.js)
useOffline                    → absent
turbopackRustReactCompiler    → absent
prefetchInlining              → present
cachedNavigations             → present
inlineCss                     → present
cacheComponents               → present     (and set true in next.config.ts)
staleTimes                    → present     (and set — see the advisability note below)
viewTransition                → present     (and set true — do NOT blind-delete)
```

Three conclusions the skill must draw from exactly this output:

1. **`partialPrefetching` is `absent` → withhold it entirely.** Even though its documented
   prerequisite (`cacheComponents`) is satisfied, the feature does not exist in this
   install. No task. Not "consider upgrading" inside a prefetching task either — an upgrade
   recommendation is its own separate, explicit task.
2. **`viewTransition` is `present` and set.** The graveyard says removed-in-16; the install
   disagrees. Probe wins: do **not** emit a removal task. Emit at most a `minor`
   informational task noting the key is slated for removal and should be re-checked when
   upgrading to ≥16.3. This is the case where naive gating produces a breaking change.
3. **`staleTimes` is `present` and set.** Availability is not endorsement — it is
   experimental and production-discouraged, and under `cacheComponents` the supported knob
   is per-scope `cacheLife({ stale })`. Emit a task to migrate off it, severity `minor`,
   reversibility `fully-reversible` — but the task's justification is the stability tier,
   not absence.

## Recording the probe

Write the full probe table verbatim into `nextjs-enhancement/00-recon.md`. Every later
finding that depends on a probed key cites the probe row. A finding that recommends
adding a key with no `present` probe row backing it is invalid and must be dropped during
Phase 4 synthesis.

When the probe returns `unresolved` for the whole repo (no `node_modules`), say so in the
recon report, run the audit anyway using version comparison, and stamp
`confidence: version-inferred` on every affected finding. Never silently degrade.
