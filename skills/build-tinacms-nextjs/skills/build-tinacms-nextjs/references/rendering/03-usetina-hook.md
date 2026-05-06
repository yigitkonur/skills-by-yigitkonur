# `useTina` Hook

The hook that turns a static page into a live-editable preview.

## The contract

```tsx
import { useTina } from 'tinacms/dist/react'

const { data } = useTina({
  query: props.query,
  variables: props.variables,
  data: props.data,
})
```

**All three** properties are required:

- `query` — the GraphQL query string used to fetch
- `variables` — the variables object
- `data` — the result data

These come from the GraphQL client response: `client.queries.page(...)` returns `{ query, variables, data }` — pass them through.

## Behavior

| Mode | Behavior |
|---|---|
| **Production** | Returns `props.data` unchanged. Zero overhead. |
| **Edit mode** (Draft Mode enabled) | Subscribes to GraphQL websocket. Returns live-updated data. |

The mode is detected via Next.js' `draftMode()`. When draft mode is active, the hook becomes "live."

## Where it goes

Always in a **Client Component** (`"use client"` directive). Server Components can't use hooks.

```tsx
'use client'

import { useTina, tinaField } from 'tinacms/dist/react'

export default function PostClient(props: any) {
  const { data } = useTina({
    query: props.query,
    variables: props.variables,
    data: props.data,
  })

  return (
    <article>
      <h1 data-tina-field={tinaField(data.post, 'title')}>{data.post.title}</h1>
    </article>
  )
}
```

## What changes between props.data and useTina's data

```tsx
// Before useTina
console.log(props.data.post.title)  // 'Original Title' (snapshot at fetch time)

// In edit mode, the editor types — props.data doesn't change
// but useTina's returned data does:
const { data } = useTina(props)
console.log(data.post.title)  // 'Updated Title' (live as editor types)
```

**Always read from `data` (the hook return), not `props.data`** in your render.

## Type safety

The auto-generated client gives you typed responses:

```tsx
import type { PostQuery } from '@/tina/__generated__/types'

type Props = {
  query: string
  variables: Record<string, unknown>
  data: PostQuery
}

export default function PostClient(props: Props) {
  const { data } = useTina(props)
  // data.post is fully typed
}
```

Generated types live at `tina/__generated__/types.ts`. Import per-collection types as needed.

## Multiple `useTina` per page

```tsx
'use client'

export default function PageClient(props: { page: any; global: any; nav: any }) {
  const { data: pageData } = useTina(props.page)
  const { data: globalData } = useTina(props.global)
  const { data: navData } = useTina(props.nav)

  // Render with all three
}
```

Each `useTina` call subscribes to its own document. Useful for pages that aggregate global settings + navigation + page content.

## When `useTina` returns stale data

Symptoms:

- Editor types in admin, but the preview iframe doesn't update
- Production rebuild shows old content

Possible causes:

| Cause | Fix |
|---|---|
| Draft mode not enabled | Visit `/api/preview` to enable |
| Missing one of `query`/`variables`/`data` | Pass all three |
| Reading from `props.data` instead of `data` | Read from hook return |
| Component not `"use client"` | Add directive |
| TinaCMS dev server not running | Use `tinacms dev -c "next dev"` |

## Performance

`useTina` is lightweight in production (passes data through). In edit mode it opens a websocket — only one connection per page regardless of how many `useTina` calls.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Reading from `props.data` (not the hook return) | Editor edits don't show in preview | Read from `data` (hook return) |
| Forgetting one of `query`/`variables`/`data` | Subscription fails silently | Pass all three |
| Spread props directly: `useTina(props)` without explicit object | Works but type-unsafe | Either explicit object or typed Props |
| Using in Server Component | "Hook outside component" | Wrap in `"use client"` component |
| Two pages share a `useTina` mutation | Confusing — each page should have its own | Each route's Client Component should call its own `useTina` |
