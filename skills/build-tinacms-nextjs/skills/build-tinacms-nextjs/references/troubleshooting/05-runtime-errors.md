# Runtime Errors

Errors at runtime in production or during dev.

## Vercel cache returning stale TinaCloud content

**Cause:** Vercel data cache stores `fetch()` responses for up to a year by default.

**Fix:** Pass `revalidate` to client queries:

```tsx
const result = await client.queries.page(
  { relativePath: `${slug}.md` },
  { fetchOptions: { next: { revalidate: 60 } } },
)
```

For aggressive freshness use `revalidate: 0`. For low-changing content, `3600` (1 hour). See `references/rendering/11-vercel-cache-caveat.md`.

## Sub-path deployment broken

**Cause:** TinaCMS admin SPA tries to load assets from the domain root, ignoring `basePath`.

**Fix:** **Don't sub-path-deploy TinaCMS.** Deploy at the domain root.

If you must use a sub-path for the rest of the site, host the admin at a different subdomain (e.g. `admin.example.com`).

## Edge runtime fails

**Cause:** Used `export const runtime = 'edge'` on a route that uses TinaCMS.

**Fix:** Remove the line — TinaCMS requires Node.js. See `references/deployment/05-edge-runtime-not-supported.md`.

## Localhost:4001 errors in production

**Cause:** Dev `admin/index.html` was committed/built and shipped to production. The dev admin loads assets from `localhost:4001`.

**Fix:**

```json
{
  "scripts": {
    "build": "tinacms build && next build"
  }
}
```

Always run `tinacms build` (NOT `tinacms dev`) in CI. Verify the production `public/admin/index.html` doesn't reference localhost:

```bash
grep -i localhost public/admin/index.html
# Should output nothing in production
```

## Reference field 503

Already covered in `references/troubleshooting/04-content-errors.md`.

## Click-to-edit not working in production

Already covered in `references/troubleshooting/06-visual-editing-issues.md`.

## "Schema not found" at runtime

**Cause:** `tina-lock.json` missing from deployed environment.

**Fix:**

- Verify it's committed: `git ls-files tina-lock.json` should show the file
- If missing, don't gitignore it
- Re-deploy after committing

## TinaCloud GraphQL queries return 401

**Cause:**

- Wrong `NEXT_PUBLIC_TINA_CLIENT_ID` or `TINA_TOKEN`
- Token expired or revoked
- TinaCloud project deleted

**Fix:**

- Re-check env vars from app.tina.io
- Regenerate `TINA_TOKEN`
- Verify the project still exists

## Self-hosted backend returns 500

**Cause:** Various — auth provider error, DB connection failure, GitHub API error.

**Diagnostic:**

```bash
# Vercel function logs
vercel logs --follow
```

Look for the actual error. Common causes:

| Error | Fix |
|---|---|
| `NEXTAUTH_SECRET undefined` | Add env var |
| `Cannot connect to redis` | Vercel KV not enabled or wrong creds |
| `GitHub API 401` | PAT expired or scope wrong |
| `MongoDB connection refused` | IP not whitelisted |

## Self-hosted backend hangs

**Cause:** DB indexing operation taking too long; Vercel Function 10s timeout (Hobby tier).

**Fix:**

- Upgrade to Pro tier for 60s timeout
- For initial indexing of large repos, run reindex from a long-running process (e.g. local CLI), not Vercel Function

## Vercel function memory exceeded

**Cause:** Schema or content too large for default memory.

**Fix:**

```typescript
// app/api/tina/[...routes]/route.ts
export const memory = 1024  // MB
```

Pro tier allows up to 3008 MB.

## Network timeout on TinaCloud

**Cause:** Editor's network or corporate firewall blocking TinaCloud domains.

**Fix:** See `references/troubleshooting/07-network-and-firewall.md`.

## Common mistakes

| Mistake | Fix |
|---|---|
| Forgot `revalidate` | Stale content | Add `next: { revalidate: 60 }` |
| Edge runtime | Build/runtime fails | Remove |
| Sub-path deploy | Admin assets 404 | Deploy at root |
| `tinacms dev` in CI | Localhost in production HTML | Use `tinacms build` |
| Missing `tina-lock.json` | "Schema not found" | Commit it |
| Vercel timeout on indexing | Function fails | Upgrade tier or background job |
