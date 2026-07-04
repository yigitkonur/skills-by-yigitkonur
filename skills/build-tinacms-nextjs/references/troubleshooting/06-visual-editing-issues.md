# Visual Editing Issues

The 9-step debugging checklist when click-to-edit doesn't work. Run through in order.

## The checklist

| # | Check | Quick fix |
|---|---|---|
| 1 | Draft Mode enabled? | Visit `/api/preview` |
| 2 | Renderer is `"use client"`? | Add directive |
| 3 | All three of `query`, `variables`, `data` passed? | Check Server → Client prop spread |
| 4 | Reading from `data` (hook return) not `props.data`? | Use `const { data } = useTina(props)` |
| 5 | `data-tina-field` on a DOM element? | Move from React component to DOM |
| 6 | `tinacms dev` running locally? | Use `pnpm dev`, not `next dev` |
| 7 | Generated types fresh? | Run `pnpm tinacms build` |
| 8 | `ui.router` set on collection? | Add to schema |
| 9 | Browser console errors? | CORS, websocket, mixed-content |

## Step 1: Draft Mode

Browser dev tools → Application → Cookies → look for `__prerender_bypass`.

Missing? Visit `http://localhost:3000/api/preview` (or your deployed URL).

If `/api/preview` returns 404, you're missing the route handler:

```typescript
// app/api/preview/route.ts
import { draftMode } from 'next/headers'
import { redirect } from 'next/navigation'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const slug = searchParams.get('slug') || '/'
  ;(await draftMode()).enable()
  redirect(slug)
}
```

## Step 2: `"use client"` directive

```bash
head -1 app/<route>/client-page.tsx
# Should output: 'use client'
```

If missing, add at the top.

## Step 3: All three props

Server Component:

```tsx
return (
  <PageClient
    query={result.query}
    variables={result.variables}
    data={result.data}
  />
)
```

Client Component:

```tsx
const { data } = useTina({
  query: props.query,
  variables: props.variables,
  data: props.data,
})
```

Missing one → useTina silently doesn't subscribe.

## Step 4: Read from `data`, not `props.data`

```tsx
// ❌ Wrong
return <h1>{props.data.page.title}</h1>

// ✅ Right
const { data } = useTina(props)
return <h1>{data.page.title}</h1>
```

`props.data` is a snapshot at fetch time. The hook's returned `data` updates live.

## Step 5: `data-tina-field` on DOM

```tsx
// ❌ Wrong — React component
<MyHeading data-tina-field={tinaField(data.page, 'title')} />

// ✅ Right — DOM element
<h1 data-tina-field={tinaField(data.page, 'title')}>{data.page.title}</h1>
```

For React components that wrap children, pass tinaField as a prop and forward to DOM:

```tsx
function Section({ children, tinaFieldRef }: any) {
  return <section data-tina-field={tinaFieldRef}>{children}</section>
}

<Section tinaFieldRef={tinaField(data.page, 'body')}>
  <TinaMarkdown content={data.page.body} />
</Section>
```

## Step 6: `tinacms dev` running

In your terminal:

```
[tinacms] GraphQL server listening on http://localhost:4001
[next] ready - started server on http://localhost:3000
```

If only `next` is running, you ran `next dev` instead of `pnpm dev` (which wraps with `tinacms dev`).

## Step 7: Generated types fresh

```bash
ls -la tina/__generated__/
# Recent timestamps?

pnpm tinacms build
# Force-regenerate
```

If you changed the schema but didn't rebuild, types and runtime client are out of sync.

## Step 8: `ui.router` set

```typescript
// In tina/config.ts schema:
{
  name: 'page',
  ui: {
    router: ({ document }) => `/${document._sys.filename}`,
  },
}
```

Without it, clicking a doc in the admin opens the form-only view, not the live page iframe.

## Step 9: Browser console

| Error | Cause | Fix |
|---|---|---|
| `Mixed content` | HTTP page loading HTTPS admin | Serve site over HTTPS |
| `CORS error` | Origin not allowed | Check TinaCloud project config |
| `Websocket connection failed` | Local server not running, or TinaCloud unreachable | Restart dev / check network |
| `Schema unknown` | Tina lock or schema out of sync | Run `pnpm tinacms build` |
| `401 Unauthorized` | Token wrong or session expired | Log out and back in |

## Production-specific issues

For deployed environments where local dev works:

| Symptom | Fix |
|---|---|
| Static page (no live updates) | Visit `/api/preview` on the deployed domain to enable Draft Mode |
| Stale content | Add `next: { revalidate: 60 }` to client queries |
| Admin loads localhost:4001 | `tinacms dev` ran in CI; use `tinacms build` |
| Empty admin | Wrong `NEXT_PUBLIC_TINA_CLIENT_ID` |

## Editorial Workflow specific

If using Team Plus+ Editorial Workflow:

| Symptom | Fix |
|---|---|
| Branch switcher missing | Editorial Workflow not enabled in Configuration tab |
| Save modal asks for new branch every time | Working as intended on protected branch |
| Preview link wrong | Fix `previewUrl` in `tina/config.ts` |
| Editor's saves fail | Editor lacks GitHub write access |

## When all else fails

1. Compare against the official Next.js TinaCMS starter
2. Ask in the [TinaCMS Discord](https://discord.gg/zumN63Ybpf) `#help`
3. File a minimal repro on GitHub

Pin your TinaCMS version when filing — UI assets are CDN-served and version drift causes confusion.
