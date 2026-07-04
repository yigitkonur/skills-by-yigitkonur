# Visual Editing Overview

What "visual editing" means in TinaCMS, the moving pieces, and when to invest in it.

## What it is

Click-to-edit on the live page: editors visit the deployed site (or a local preview), see their content rendered, click any element, and the form opens directly to the field that produced it. Edits stream live to the preview as they type — no save-and-refresh.

## What you need

| Piece | Where | Required? |
|---|---|---|
| `ui.router` per collection | `tina/config.ts` | Yes — maps documents to live URLs |
| Two-component split (Server + Client) | `app/<route>/{page,client-page}.tsx` | Yes — `useTina` requires `"use client"` |
| `useTina(props)` hook | Client Component | Yes — subscribes to live edits |
| `data-tina-field={tinaField(...)}` | DOM elements | Yes — targets specific fields |
| Draft Mode route | `app/api/preview/route.ts` | Yes — required for editing in deployed env |
| Editorial Workflow `previewUrl` | `tina/config.ts` `ui` | Optional — for branch-based preview links |

## End-to-end flow

```
1. Editor opens admin (/admin)
2. Editor clicks document → ui.router returns live URL
3. Live page loads in iframe with Draft Mode enabled
4. Client Component on that page calls useTina(props)
5. useTina opens GraphQL websocket
6. Editor types in the form → websocket pushes update → page re-renders
7. Editor clicks page element with data-tina-field → form opens to that field
8. Editor saves → mutation commits to git
```

## When to invest in visual editing

**Invest if:**

- Editors are non-technical and need to "see what they're editing"
- Site has many editable elements per page (block-based marketing pages)
- Editor satisfaction is a stakeholder

**Skip if:**

- Single technical editor who's fine with form-only
- Site is small (5 pages, mostly static content)
- Editing happens infrequently

Visual editing adds:

- ~20% more setup work (server/client split, `tinaField` placement everywhere)
- Same content, same data — purely an editor-experience layer

The form-only path still works without any of the visual-editing wiring. You can add visual editing incrementally per page.

## Reading order

| File | When |
|---|---|
| `references/visual-editing/02-router-config.md` | Setting up `ui.router` per collection |
| `references/visual-editing/03-tinafield-helper.md` | Using `tinaField` on DOM elements |
| `references/visual-editing/04-tinamarkdown-tinafield.md` | `tinaField` inside MDX content |
| `references/visual-editing/05-draft-mode.md` | The `/api/preview` route |
| `references/visual-editing/06-edit-state-hook.md` | `useEditState` for manual toggle |
| `references/visual-editing/07-debugging-checklist.md` | What to check when click-to-edit fails |
| `references/visual-editing/08-proxy-ts.md` | Next.js 16 middleware-to-proxy migration |

## What "live edit" means in production

In production (without Draft Mode), `useTina()` is a no-op — it returns `props.data` unchanged. Zero overhead.

In Draft Mode, `useTina()` opens a websocket to TinaCloud (or your self-hosted backend) and re-renders on every keystroke. Only editors with auth see this — public visitors get the static page.

This means: **visual editing is "free" in production, expensive only when actually editing.**

## Common mistakes (high level)

| Mistake | Symptom | Fix |
|---|---|---|
| No Draft Mode route | Editor sees static page in deployed env | Add `app/api/preview/route.ts` |
| `useTina` in Server Component | Build error | Wrap in Client Component |
| Forgot `ui.router` | Click in admin doesn't open live page | Add `router` per collection |
| `data-tina-field` on React component (not DOM) | Click-to-edit ignored | Place on DOM element |
| Using `props.data` instead of `data` from hook | Edits don't show in preview | Read from hook return |
