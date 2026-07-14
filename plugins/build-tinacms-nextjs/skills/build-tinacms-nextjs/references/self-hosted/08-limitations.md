# Self-hosted Limitations

What you give up when self-hosting vs TinaCloud.

## Major limitations

### No Editorial Workflow

The branch-based PR workflow (Team Plus+ on TinaCloud) is **not available** in self-hosted. Editors save directly to the configured branch.

**Workaround:** Have editors work on feature branches manually, open PRs by hand. More friction, but achievable.

### No built-in fuzzy search

The TinaCloud search index doesn't exist for self-hosted.

**Workaround:** Use external search:

- **Algolia** — paid, easy setup
- **Meilisearch** — open source, self-host
- **Typesense** — open source
- **Pagefind** — static, build-time index

Index from `content/**/*.md` directly during build.

### No managed audit log

TinaCloud Business+ has an Activity tab. Self-hosted has just `git log`.

**Workaround:** Tail the git log and build an audit UI yourself, or use git host's API (GitHub commits API).

### No managed user dashboard

TinaCloud has a Users tab in the project dashboard. Self-hosted users are JSON files in `content/users/`.

**Workaround:** Edit user files directly or build a custom admin UI.

### No git co-authoring with editor identity (out-of-the-box)

TinaCloud automatically attributes commits to the editor. Self-hosted commits use the GitHub PAT's identity (usually a bot account).

**Workaround:** Customize the GitHub provider to set `author` from the editor's session info.

```typescript
new GitHubProvider({
  // ... base config
  author: (user: any) => ({
    name: user.username,
    email: user.email,
  }),
})
```

(Verify the API in `tinacms-gitprovider-github` docs.)

### No Vercel-style preview-per-branch baked in

TinaCloud + Vercel auto-creates preview deploys per editor branch. Self-hosted relies on you wiring `previewUrl` and Vercel preview settings yourself.

**Workaround:** Standard Vercel preview deployments + manual `previewUrl` config.

## Runtime limitations

### Edge runtime not supported

TinaCMS backend (`@tinacms/datalayer`, `@tinacms/graphql`) requires Node.js. **Cannot run on:**

- Cloudflare Workers
- Vercel Edge Functions
- Any V8-isolate runtime

Use a Node.js host (Vercel Functions, AWS Lambda, your own server).

### Sub-path deployment broken

Even with `basePath`, the admin SPA fails to load assets when deployed to a sub-path. Same as TinaCloud — deploy at domain root.

### Admin SPA still served from TinaCloud's CDN (in some configs)

The admin SPA is built statically from `tinacms build`, but in some configs it pulls assets from TinaCloud's CDN. For air-gapped self-hosted setups, you may need additional configuration to fully self-serve.

## Cost limitations

| Cost | Self-hosted |
|---|---|
| TinaCloud subscription | $0 (you self-host) |
| Vercel hosting | Existing |
| Vercel KV | $0–$20/month for typical use |
| MongoDB Atlas (alternative) | Free tier covers small sites |
| GitHub | Free for public repos; existing Team plan otherwise |

Self-hosted is usually cheaper than Team Plus on TinaCloud, except very small projects (free tier covers them).

## Operational complexity

| Concern | TinaCloud | Self-hosted |
|---|---|---|
| Setup time | 30 min | 4–8 hours |
| Backend code to maintain | None | ~150 LOC + auth wiring |
| Updates / patches | Auto (TinaCloud manages) | You apply package updates |
| Incident response | TinaCloud team | You |
| User support | TinaCloud Discord/email | Internal |

The operational overhead is the biggest hidden cost. Consider whether your team has bandwidth.

## Migration friction

| Direction | Friction |
|---|---|
| TinaCloud → Self-hosted | Medium (~1 day for setup + user migration) |
| Self-hosted → TinaCloud | Low (just env var swap) |

Self-hosted → TinaCloud is easy. The reverse takes more work.

## When NOT to self-host

- Small team (< 5 editors)
- No specific compliance requirement
- Editorial Workflow is critical
- Built-in search is critical
- You don't have ops bandwidth

For these cases, TinaCloud is simpler and probably cheaper at the team's scale.

## When self-hosting is right

- Strict compliance / data residency
- Need custom auth provider not in TinaCloud's options
- Existing Auth.js or Clerk infrastructure to reuse
- Large content team (cost favors self-hosted at scale)
- Comfortable maintaining backend code
