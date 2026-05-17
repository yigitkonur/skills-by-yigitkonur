# Debugging Click-to-Edit

When click-to-edit doesn't work, run through these in order. Stop at the first one that's wrong — fix and retry.

## The 9-step checklist

| # | Check | Fix |
|---|---|---|
| 1 | **Is Draft Mode enabled?** | Visit `/api/preview` once. Check browser cookies for `__prerender_bypass`. |
| 2 | **Is the page rendered by a Client Component?** | The renderer must have `"use client"` at the top. Server Components can't use `useTina`. |
| 3 | **Are all three of `query`, `variables`, `data` passed?** | Server Component fetches them; Client Component receives them as props; passes all three to `useTina`. |
| 4 | **Are you reading from `data` (hook return) not `props.data`?** | `const { data } = useTina(props); ...{data.page.title}...` — NOT `props.data.page.title`. |
| 5 | **Is `data-tina-field` on a DOM element?** | Move it off React component wrappers. Place on `<h1>`, `<p>`, `<a>`, etc. |
| 6 | **Is `tinacms dev` running locally?** | Use `pnpm dev` (which runs `tinacms dev -c "next dev"`). Plain `next dev` skips the GraphQL server. |
| 7 | **Are generated types up to date?** | Run `pnpm tinacms build`. The schema and `__generated__/` may be out of sync. |
| 8 | **Is `ui.router` set on the collection?** | Without it, the admin can't open the live page (no URL to navigate to). |
| 9 | **Browser console errors?** | CORS, websocket, mixed-content, auth errors — investigate. |

## Step-by-step debugging

### Step 1: Draft Mode enabled?

```bash
# In browser dev tools → Application → Cookies → http://localhost:3000
# Look for: __prerender_bypass
```

If missing: visit `http://localhost:3000/api/preview`. Then reload the page you're trying to edit.

### Step 2: `"use client"` at top of file?

```bash
head -1 app/your-route/client-page.tsx
# Should output: 'use client'
```

If missing: add `'use client'` at the very top of the renderer file.

### Step 3: All three props?

```tsx
// Server Component
return (
  <PageClient
    query={result.query}
    variables={result.variables}
    data={result.data}
  />
)

// Client Component
const { data } = useTina({
  query: props.query,
  variables: props.variables,
  data: props.data,
})
```

Missing one → useTina silently doesn't subscribe.

### Step 4: Reading from `data` not `props.data`?

```tsx
// ❌ Wrong — props.data is a snapshot, doesn't update on edits
return <h1>{props.data.page.title}</h1>

// ✅ Right — data from hook updates live
const { data } = useTina(props)
return <h1>{data.page.title}</h1>
```

### Step 5: `data-tina-field` on DOM?

```tsx
// ❌ Wrong — React component
<MyHeading data-tina-field={tinaField(data.page, 'title')} />

// ✅ Right — DOM element
<h1 data-tina-field={tinaField(data.page, 'title')}>{data.page.title}</h1>
```

### Step 6: TinaCMS dev server running?

In your terminal you should see something like:

```
[tinacms] GraphQL server listening on http://localhost:4001
[next] ready - started server on http://localhost:3000
```

If only `next` is running, you ran `next dev` directly. Stop and run `pnpm dev` instead.

### Step 7: Generated types up to date?

```bash
ls -la tina/__generated__/
# Should show recent timestamps

# Force-regenerate:
pnpm tinacms build
```

If types are stale (you changed schema but didn't rebuild), run the build.

### Step 8: `ui.router` set?

In `tina/config.ts`:

```typescript
{
  name: 'page',
  ui: {
    router: ({ document }) => `/${document._sys.filename}`,
  },
  // ...
}
```

Without it: clicking a document in the admin opens the form-only view, not the live page iframe.

### Step 9: Console errors?

Open browser dev tools → Console:

| Error | Meaning |
|---|---|
| `Mixed content` | Trying to load HTTP from HTTPS page — config issue |
| `CORS error` | TinaCloud or self-hosted GraphQL not allowing your origin |
| `Websocket failed to connect` | TinaCloud unreachable, or local server not running |
| `Auth error` | TINA_TOKEN missing or invalid |
| `Schema unknown` | `tinacms build` didn't run, types out of sync |

## Production-specific issues

For deployed environments where local dev works but production fails:

- Check Vercel env vars (`NEXT_PUBLIC_TINA_CLIENT_ID`, `TINA_TOKEN`)
- Check Draft Mode by hitting `/api/preview` on the deployed URL
- Check Vercel cache caveat (see `references/rendering/11-vercel-cache-caveat.md`)
- Check that `tinacms build` ran in CI (look for `__generated__/` in build logs)

## When all else fails

1. Compare against the [official Next.js TinaCMS starter](https://github.com/tinacms/tina-starter-alpaca) — diff configs
2. Ask in the [TinaCMS Discord](https://discord.gg/zumN63Ybpf)
3. File a minimal repro on GitHub

Pin your TinaCMS version in the bug report — UI assets are CDN-served and version drift causes confusion.
