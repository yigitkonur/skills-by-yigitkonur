# Prerequisites

## Required

| Tool | Minimum | Why |
|---|---|---|
| Node.js | `>= 20.9.0` | Next.js 16 floor; some Tina utilities need Node 20+ |
| Package manager | project-specific | TinaCMS supports npm, pnpm, and yarn; prefer pnpm for greenfield App Router projects |
| Git | any recent | TinaCMS commits content via git |
| GitHub account | — | TinaCloud and the default Git Provider both go through GitHub |

## Recommended

| Tool | Why |
|---|---|
| TinaCloud account at `https://app.tina.io` | The default backend (free tier: 2 users) |
| Vercel account | The default deploy target |
| VS Code or Cursor | TypeScript types from `tina/__generated__/types.ts` work great in either |

## Package manager guidance

The official TinaCMS App Router guide recommends pnpm, and this skill defaults to pnpm for greenfield projects. Current TinaCMS docs also state that TinaCMS works with npm, pnpm, and yarn, so do not treat npm/yarn as unsupported.

With any package manager you may hit module-resolution issues if the install is inconsistent:

- `Could not resolve "tinacms"` even though it's installed
- Generated types missing peer types
- Inconsistent admin asset versions

If using npm or yarn: avoid `--no-optional` and `--omit=optional`, ensure `react` + `react-dom` are explicitly in `dependencies`, and keep one lockfile. If a project already has a clean npm/yarn lockfile, respect it rather than rewriting package manager state.

## Verify versions before starting

```bash
node -v          # v20.9.0+
pnpm -v          # 9.x+
npm view tinacms version
npm view @tinacms/cli version
npm view next version
npm view react version
```

Registry snapshot checked on 2026-05-09; re-run these commands before encoding version-specific guidance:

| Package | Latest checked |
|---|---|
| `next` | `16.2.6` |
| `react`, `react-dom` | `19.2.6` |
| `tinacms` | `3.7.6` |
| `@tinacms/cli` | `2.2.6` |
| `@tinacms/datalayer` (self-hosted) | `>=1.x` matching `tinacms` major |
| `tinacms-authjs` (self-hosted) | matching `tinacms` major |
| `tinacms-clerk` (self-hosted) | matching `tinacms` major |

Compatibility anchors:

- Next.js 16 requires Node.js `>=20.9.0`.
- Next.js current peer range accepts React 18.2+ or React 19.
- TinaCMS current peer range accepts React `>=16.14.0`, but App Router projects should follow Next.js's peer range.

## Pin exact TinaCMS versions

The TinaCMS admin SPA assets are served from a CDN that may update before your CLI catches up. **Pin exact versions** (no `^` or `~`) and group all `tinacms*` packages in RenovateBot/Dependabot so they upgrade together:

```json
{
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "matchPackagePatterns": ["tinacms", "@tinacms/*"],
      "groupName": "TinaCMS"
    }
  ]
}
```

Drift between `tinacms` and `@tinacms/cli` causes the most confusing bug reports.

## What you do NOT need

- A CMS you're migrating from (Forestry, Contentful, etc.) — TinaCMS is greenfield-friendly
- Docker — local dev runs on the host
- Any specific Vercel plan to start (Hobby is fine)
- A separate database — TinaCloud manages it, self-hosted comes later in the workflow
