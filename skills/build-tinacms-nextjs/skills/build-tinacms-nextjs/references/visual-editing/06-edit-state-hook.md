# `useEditState` Hook

Manually toggle edit-mode from your own UI without going to `/admin#/logout`. Useful for "Edit this page" buttons or admin-only UI.

## Basic

```tsx
'use client'

import { useEditState } from 'tinacms/dist/edit-state'

export function EditButton() {
  const { edit, setEdit } = useEditState()

  return (
    <button onClick={() => setEdit((current) => !current)}>
      {edit ? 'Exit edit mode' : 'Enter edit mode'}
    </button>
  )
}
```

## Hook return

```typescript
{
  edit: boolean,                   // current edit state
  setEdit: (value: boolean | ((prev: boolean) => boolean)) => void,
}
```

`setEdit(true)` enables edit mode (triggers TinaCloud login if applicable).
`setEdit(false)` disables.
`setEdit((prev) => !prev)` toggles.

## Example: floating edit button

```tsx
'use client'

import { useEditState } from 'tinacms/dist/edit-state'

export function FloatingEditButton() {
  const { edit, setEdit } = useEditState()

  return (
    <button
      onClick={() => setEdit((p) => !p)}
      className="fixed bottom-4 right-4 px-4 py-2 bg-blue-600 text-white rounded shadow-lg"
    >
      {edit ? '✕ Exit Edit' : '✎ Edit Page'}
    </button>
  )
}
```

Place in your root layout — appears on every page, only matters for editors.

## Conditional UI for editors

```tsx
'use client'

import { useEditState } from 'tinacms/dist/edit-state'

export function EditorOnlyBanner() {
  const { edit } = useEditState()

  if (!edit) return null

  return (
    <div className="bg-yellow-200 p-2 text-center">
      ⚠️ You are in edit mode. Save changes via the form panel.
    </div>
  )
}
```

## Relationship to Draft Mode

`useEditState` is **higher level** than `draftMode`:

- `useEditState` — TinaCMS's edit-state context (drives `useTina` subscriptions)
- `draftMode()` — Next.js's cache-bypass cookie

Both align in practice. When you `setEdit(true)`, TinaCMS:

1. Triggers TinaCloud login (if not authenticated)
2. Sets the local edit-mode flag
3. (Indirectly) Draft Mode is enabled via the admin login flow

For the simplest setup, **always have a `/api/preview` route** AND optionally use `useEditState` for custom UI. Don't replace one with the other.

## Programmatic enable from a server action

```tsx
// app/actions/enable-edit.ts
'use server'

import { draftMode } from 'next/headers'

export async function enableEdit() {
  ;(await draftMode()).enable()
}
```

Called from a Client Component:

```tsx
import { enableEdit } from '@/app/actions/enable-edit'

<button onClick={async () => await enableEdit()}>Edit</button>
```

Server Actions can call `draftMode()` directly. This is an alternative to the `/api/preview` GET route.

## When to use `useEditState`

Use it when:

- You want a custom "Edit" button in your site's UI
- You want editor-only UI that appears in edit mode
- You want to expose a logout button outside `/admin`

Skip it when:

- Default editor flow (visit `/admin`, click document) is sufficient
- You don't want any "Edit" entry-point on the public site

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Imported from `tinacms/dist/react` (wrong) | Module not found | Import from `tinacms/dist/edit-state` |
| Used `useEditState` in Server Component | Hook violation | Wrap in Client Component |
| `setEdit(true)` then expected immediate render | Asynchronous — Tina needs to load | Use the `edit` state to drive UI |
| Used as alternative to `/api/preview` route | Missing route still breaks deployed visual editing | Always have the `/api/preview` route |
