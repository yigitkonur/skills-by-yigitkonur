# `build` and `server` Config

The two sections that control where TinaCMS writes its admin assets and how the dev server runs.

## `build` section

```typescript
build: {
  outputFolder: 'admin',     // required
  publicFolder: 'public',    // required
  basePath: undefined,       // optional — DO NOT SET (broken upstream)
}
```

| Property | Default | Purpose |
|---|---|---|
| `outputFolder` | — | Relative to `publicFolder`. The admin SPA writes here. With `outputFolder: 'admin'` and `publicFolder: 'public'`, the admin lives at `public/admin/`. |
| `publicFolder` | — | Your framework's static assets directory. For Next.js this is `public`. |
| `basePath` | undefined | For sub-path deployments. **Known broken** — see warning below. |

## Why these matter

After `tinacms build`:

```
your-project/
├── public/
│   └── admin/                    ← created by tinacms build
│       ├── index.html
│       ├── assets/
│       │   ├── index-XXXX.js
│       │   └── index-XXXX.css
│       └── ...
```

Visiting `http://localhost:3000/admin/index.html` loads this static SPA. The Next.js app serves `public/` natively, so no extra routing needed.

If `outputFolder` and `publicFolder` are wrong:

- Admin returns 404
- Admin loads but can't find its assets (404s on `index-XXXX.js`)
- `tinacms build` succeeds but production can't find the admin

## DON'T set `basePath`

If you deploy to a sub-path like `example.com/blog/`, the natural instinct is:

```typescript
build: {
  outputFolder: 'admin',
  publicFolder: 'public',
  basePath: 'blog',  // ❌ DO NOT
}
```

This is **broken upstream**. The admin SPA still tries to load assets from `example.com/admin/...` (root), not `example.com/blog/admin/...`. Even with `basePath` set, asset paths in `index.html` use absolute roots.

**Workaround: don't sub-path-deploy TinaCMS.** Put it at the domain root.

## `server` section

```typescript
server: {
  // optional dev-server overrides
}
```

The `server` section is mostly handled by CLI flags (`--port`, `--datalayer-port`). For most projects you don't need to set anything here.

## Custom output paths

If you want the admin at a different path:

```typescript
build: {
  outputFolder: 'cms',
  publicFolder: 'public',
}
```

Visit `http://localhost:3000/cms/index.html` to access the admin.

You'd also need to update `app/admin/[[...index]]/page.tsx` if you want the Next.js admin route to match the new folder name. See `references/config/03-admin-and-ui.md`.

## Multiple-project setups

If you have multiple TinaCMS projects in the same repo (rare), each needs a unique `outputFolder` to avoid collisions:

```typescript
// site-a/tina/config.ts
build: { outputFolder: 'admin-a', publicFolder: 'public' }

// site-b/tina/config.ts
build: { outputFolder: 'admin-b', publicFolder: 'public' }
```

But this is a code smell — usually it's better to have one TinaCMS instance per repo.

## Verification

```bash
pnpm tinacms build
ls public/admin/

# Should show:
# index.html  assets/  ...
```

Visit `http://localhost:3000/admin/index.html` — admin should load.

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| `outputFolder: '/admin'` (leading slash) | Admin written outside `public/` | Use `'admin'` (no leading slash) |
| `outputFolder: 'public/admin'` (duplicated `public`) | Admin written to `public/public/admin/` | Use `'admin'` only — `outputFolder` is relative to `publicFolder` |
| `publicFolder: 'static'` (wrong dir) | Admin writes to `static/admin/` but Next.js doesn't serve it | Set `publicFolder` to your actual static dir (`public` for Next.js) |
| Setting `basePath` | Admin assets 404 in production | Remove `basePath`; deploy at domain root |
