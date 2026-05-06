# Prerequisites

## Required

| Tool | Minimum | Why |
|---|---|---|
| Node.js | `>= 20.9.0` | Next.js 16 floor; some Tina utilities need Node 20+ |
| pnpm | `>= 9` | TinaCMS ≥ 2.7.3 expects pnpm; npm/yarn cause module-resolution failures |
| Git | any recent | TinaCMS commits content via git |
| GitHub account | — | TinaCloud and the default Git Provider both go through GitHub |

## Recommended

| Tool | Why |
|---|---|
| TinaCloud account at `https://app.tina.io` | The default backend (free tier: 2 users) |
| Vercel account | The default deploy target |
| VS Code or Cursor | TypeScript types from `tina/__generated__/types.ts` work great in either |

## Why pnpm specifically

TinaCMS' release process from 2.7.3 onward assumes pnpm-style hoisting. With npm or yarn you may hit:

- `Could not resolve "tinacms"` even though it's installed
- Generated types missing peer types
- Inconsistent admin asset versions

If you must use npm: avoid `--no-optional` and `--omit=optional`, and ensure `react` + `react-dom` are explicitly in `dependencies` (not just peerDependencies).

## Verify versions before starting

```bash
node -v          # v20.9.0+
pnpm -v          # 9.x+
npm view tinacms version
npm view @tinacms/cli version
npm view next version
```

May 2026 floors:

| Package | Floor |
|---|---|
| `next` | `>=16.0` |
| `react`, `react-dom` | `>=19.0` |
| `tinacms` | `>=3.7` |
| `@tinacms/cli` | `>=2.2` |
| `@tinacms/datalayer` (self-hosted) | `>=1.x` matching `tinacms` major |
| `tinacms-authjs` (self-hosted) | matching `tinacms` major |
| `tinacms-clerk` (self-hosted) | matching `tinacms` major |

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
