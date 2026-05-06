# New Project Scaffold

The scaffolding flow for a brand-new Next.js + TinaCMS project. For brownfield projects see `references/setup/03-existing-project-add.md`.

## Scaffold

```bash
pnpm dlx create-next-app@latest my-site \
  --typescript \
  --app \
  --src-dir \
  --tailwind \
  --eslint
cd my-site
```

Flags explained:

| Flag | Why |
|---|---|
| `--typescript` | TinaCMS works best with the generated TS types |
| `--app` | App Router is the canonical TinaCMS Next.js path |
| `--src-dir` | `src/` keeps `tina/` cleanly at the root |
| `--tailwind` | Optional but recommended for the block components |

## Initialize TinaCMS

```bash
pnpm dlx @tinacms/cli@latest init
```

The CLI prompts:

1. **Public assets directory** — answer `public`
2. **Whether to add a sample blog collection** — your call; you can delete it later

What it does:

- Installs `tinacms` and `@tinacms/cli`
- Creates `tina/config.ts` with a starter schema
- Adds `app/admin/[[...index]]/page.tsx` (the admin route)
- Updates `package.json` scripts (dev/build/start)
- Adds an example `content/` folder with a sample post

## Verify it runs

```bash
pnpm dev
```

Open `http://localhost:3000/admin/index.html`. The admin should load.

If it doesn't:

- Check the terminal — `tinacms dev -c "next dev"` should be running, not just `next dev`
- Check `package.json` scripts (see `references/setup/04-package-scripts.md`)
- If admin shows localhost:4001 errors, the local GraphQL server isn't running

## Next steps

After scaffold:

1. Read `references/setup/05-env-vars.md` to set up `.env`
2. Read `references/setup/06-gitignore-and-lockfile.md` to gitignore `__generated__/`
3. Read `references/schema/01-collections.md` to design your collections
4. Read `references/rendering/01-app-router-pattern.md` to wire dynamic pages

## What `tinacms init` does NOT do

- It doesn't sign you up for TinaCloud — register at `app.tina.io` separately
- It doesn't deploy anything — you handle Vercel/host setup
- It doesn't create blocks — only a generic blog post collection

## Alternative: official starter

If you want a more opinionated start with blocks, MDX components, and SEO already wired:

```bash
pnpm dlx create-tina-app@latest my-site --template tina-cloud-starter
```

This gives you the **Tina NextJS Starter** — full-featured: Tailwind, blocks pattern, visual editing already configured. Trade-off: more code to read and remove if you don't need it. For a clean baseline use `create-next-app` + `tinacms init`.

## Sanity check

```bash
ls tina/
# Should show: config.ts (or config.tsx), tina-lock.json after first build
ls content/
# Should show: posts/ (or whatever sample collection init created)
ls app/admin/
# Should show: [[...index]]/page.tsx
```

If any of these is missing, the init didn't complete — re-run it.
