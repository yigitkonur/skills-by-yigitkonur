# Network and Artifacts

Use this file when checkout, package fetch, cache transfer, Docker layers, LFS, or artifact upload/download dominate the critical path.

## Checkout

Choose by history need:

| Need | Pattern |
|---|---|
| Build/test only, no history | shallow checkout (`fetch-depth: 1`) |
| Affected detection or changelog | full history or enough depth to include merge base |
| Huge monorepo, subset needed | sparse checkout plus required root manifests |
| Partial clone | only when tools will not walk missing blobs/trees repeatedly |

Do not combine shallow checkout with merge-base-dependent affected detection. Use event SHAs or full history.

## Git LFS

If the build does not need binary assets, skip LFS smudge and hydrate only selected assets:

```bash
git lfs pull --include="test/fixtures/*.bin"
```

Do not download gigabytes of design/media assets for a TypeScript typecheck.

## Package and registry locality

- Cache the package-manager store near the runner.
- Use an internal/proxy registry when many self-hosted runners fetch the same packages.
- Keep self-hosted runners in the same region/network zone as registry, cache, artifact store, and source mirror where possible.
- Treat egress and rate limits as measured bottlenecks, not assumptions.

## Artifact transfer

- Upload only targeted outputs (`dist/`, reports, release candidates), not whole workspaces.
- Use immutable artifact versions and unique names.
- Set short retention for intermediate artifacts and longer retention only for release evidence.
- Match compression to entropy:
  - source/text/logs: normal compression,
  - videos, traces, precompressed archives, binaries: compression level 0.
- Bound matrix fan-out so artifact/cache APIs and registries are not saturated.

## Cache transfer economics

A cache is not free. Measure:

```text
saved time = clean operation time - (download + restore + post-hit work)
```

If the result is near zero or negative, remove or narrow the cache. Large package stores, Docker caches, and DerivedData can all lose to a fast nearby network.

## Common pitfalls

- Cache key based on `package.json` instead of lockfile.
- `node_modules` cache larger and slower than package store.
- Full checkout for affected detection on a shallow clone.
- LFS assets downloaded but never used.
- `compression-level: 9` on already-compressed media.
- Deployment concurrency cancelling an in-flight production deploy.
- Twelve shards all uploading artifacts at once without a cap.

## Sources

- actions/checkout: https://github.com/actions/checkout (accessed 2026-07-28)
- actions/cache: https://github.com/actions/cache (accessed 2026-07-28)
- actions/upload-artifact: https://github.com/actions/upload-artifact (accessed 2026-07-28)
- Git partial clone: https://git-scm.com/docs/partial-clone (accessed 2026-07-28)
- GitHub partial/shallow clone guide: https://github.blog/open-source/git/get-up-to-speed-with-partial-clone-and-shallow-clone/ (accessed 2026-07-28)
- pnpm CI: https://pnpm.io/continuous-integration (accessed 2026-07-28)
