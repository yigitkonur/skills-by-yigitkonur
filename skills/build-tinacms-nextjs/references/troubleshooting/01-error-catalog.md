# Error Catalog (refined)

The most common TinaCMS errors and their fixes. Use this as a top-level index — for deeper dives, see the specific troubleshooting files.

## Build errors

| Error | Cause | See |
|---|---|---|
| `Schema Not Successfully Built` | Frontend imports in `tina/config.ts` | `references/troubleshooting/03-schema-errors.md` |
| `Cannot find module '../tina/__generated__/client'` | Wrong build order | `references/troubleshooting/02-build-and-types.md` |
| `require is not defined` / `ERR_REQUIRE_ESM` | TinaCMS 3.x is ESM-only | `references/troubleshooting/02-build-and-types.md` |
| `Could not resolve "tinacms"` | Module resolution / missing peers | `references/troubleshooting/02-build-and-types.md` |

## Schema errors

| Error | Cause | See |
|---|---|---|
| Field name invalid | Hyphens / reserved names | `references/troubleshooting/03-schema-errors.md` |
| `template name was not provided` | Missing `_template` in multi-shape doc | `references/troubleshooting/04-content-errors.md` |
| Schema fails on import of React component | Frontend code imported into config | `references/troubleshooting/03-schema-errors.md` |

## Content errors

| Error | Cause | See |
|---|---|---|
| Documents not appearing in admin | Path mismatch | `references/troubleshooting/04-content-errors.md` |
| Ghost upload (success toast on failed upload) | TinaCloud media bug | `references/troubleshooting/04-content-errors.md` |
| Reference field 503 / dropdown timeout | > 500 docs in referenced collection | `references/troubleshooting/05-runtime-errors.md` |
| Field with hyphens in frontmatter | Schema rejects | `references/troubleshooting/04-content-errors.md` |

## Runtime errors

| Error | Cause | See |
|---|---|---|
| Vercel cache returning stale content | Default 1-year cache | `references/troubleshooting/05-runtime-errors.md` |
| Sub-path deployment broken | Known upstream | `references/troubleshooting/05-runtime-errors.md` |
| Edge runtime fails | Node-only modules | `references/deployment/05-edge-runtime-not-supported.md` |
| Localhost:4001 errors in production | Dev admin shipped | `references/troubleshooting/05-runtime-errors.md` |

## Visual editing

| Symptom | Cause | See |
|---|---|---|
| Click-to-edit doesn't work | One of 9 things | `references/troubleshooting/06-visual-editing-issues.md` |
| Edits don't show in preview | Reading from `props.data` not hook | `references/troubleshooting/06-visual-editing-issues.md` |
| `useTina` "Hooks can only be used..." | In Server Component | `references/troubleshooting/06-visual-editing-issues.md` |

## Network / firewall

| Symptom | Cause | See |
|---|---|---|
| Admin doesn't load (corporate firewall) | Domains blocked | `references/troubleshooting/07-network-and-firewall.md` |
| Mixed content errors | HTTP page → HTTPS admin | `references/troubleshooting/07-network-and-firewall.md` |

## TinaCloud-specific

| Symptom | Cause | See |
|---|---|---|
| Indexing not happening | GitHub webhook missing | `references/troubleshooting/08-tinacloud-issues.md` |
| Auth errors | Wrong client ID | `references/troubleshooting/08-tinacloud-issues.md` |
| Hit rate limit | Free tier exceeded | `references/troubleshooting/08-tinacloud-issues.md` |
| Editorial Workflow modal missing | Tier or branch protection | `references/troubleshooting/08-tinacloud-issues.md` |

## Quick diagnostic checklist

When something breaks:

1. `pnpm dlx @tinacms/cli@latest audit` — schema vs content drift
2. `pnpm tinacms build --verbose` — surface schema errors
3. Browser console — runtime errors
4. Vercel function logs — backend errors
5. TinaCloud webhooks log — webhook delivery
6. `git log` content/ — when did content last change?

## Quick fixes for the top 5 issues

| Issue | Quick fix |
|---|---|
| Stale content in production | Add `next: { revalidate: 60 }` to client queries |
| Click-to-edit dead | Visit `/api/preview` to enable Draft Mode |
| Build fails with "Cannot find module" | Run `tinacms build` before `next build` |
| Field name error | Replace hyphens with underscores |
| Edge runtime fails | Remove `runtime: 'edge'` from the route |

For deeper diagnosis, navigate to the specific file via the "See" column above.
