# TinaCloud vs Self-Hosted Decision

TinaCMS has two backend modes. **TinaCloud is the default** and the right answer for ~90% of projects. Self-hosted is for teams who need full backend control or want to avoid the SaaS dependency.

## Quick decision

**Pick TinaCloud if:** you want the editor working in production with zero backend code, you need editorial workflow (branch-based PR review), you need built-in fuzzy content search, you're under the free-tier limits, or you want any of: managed user auth, GitHub integration auto-wired, audit logs, branch switcher.

**Pick self-hosted if:** you must keep all infrastructure on your own VPC, your auth needs Clerk/custom OIDC/specific compliance, you've outgrown the TinaCloud paid tiers, you need MongoDB/Postgres-backed indexing, or your editorial process doesn't need PR-based review.

## Decision matrix

| Concern | TinaCloud | Self-hosted |
|---|---|---|
| Setup time | 30 min | 4–8 hours |
| Backend code | None | ~150 LOC + auth wiring |
| Editorial Workflow | Team Plus+ ($49/mo) | Not available |
| Content search | Built-in fuzzy | Not available |
| Auth options | TinaCloud SSO, GHE | Auth.js, Clerk, custom |
| Database | Managed | Vercel KV, MongoDB |
| Git provider | GitHub auto-wired | GitHub PAT or custom |
| Audit log | Yes | DIY |
| Free tier | 2 users | n/a (you pay infra) |
| Vendor risk | TinaCloud SaaS | Your infra |
| Migration | Migrate to self-hosted later | Migrate to TinaCloud later |
| Edge runtime | n/a — you connect to TinaCloud | **Not supported** — Node.js only |
| Custom branding | Limited | Full |

## TinaCloud tiers

| Tier | Price | Users | Notable features |
|---|---|---|---|
| Free | $0 | 2 | Community support |
| Team | $29/mo | 3 (up to 10) | Team support |
| Team Plus | $49/mo | 5 (up to 20) | **Editorial Workflow**, AI features |
| Business | $299/mo | 20+ | 3 roles, API access |
| Enterprise | Custom | Custom | SSO, GHE |

Check `https://tina.io/pricing` for current numbers.

## Default-stance rules of thumb

- **Marketing site, single editor, < 5 pages of content:** TinaCloud Free.
- **Blog or docs site, 2-3 editors, want PR-review:** TinaCloud Team Plus.
- **Enterprise content team, must run on-prem:** Self-hosted.
- **Content team using Clerk for everything else:** Self-hosted with `tinacms-clerk`.
- **Heavy content load (10k+ docs), need MongoDB:** Self-hosted with MongoDB adapter.

## "I need to migrate later" — both directions work

You can move from TinaCloud to self-hosted (`references/self-hosted/05-migrating-from-tinacloud.md`) or vice versa. Content is plain files in git, so migration is mostly backend wiring. The schema doesn't change.

## Hard exclusions

- **TinaCMS backend never runs in edge runtimes.** No Cloudflare Workers, no Vercel Edge Functions. The backend depends on Node.js APIs (filesystem operations, esbuild, GraphQL server). This is upstream wontfix. See `references/deployment/05-edge-runtime-not-supported.md`.

- **Sub-path deployment is broken.** Deploying TinaCMS to `example.com/blog/` (with `basePath` set) breaks admin asset loading. Deploy at the domain root.

- **You cannot run both backends at once.** Pick one in `tina/config.ts`: omit `contentApiUrlOverride` for TinaCloud, or set it to `/api/tina/gql` for self-hosted.

## Cost ballpark

For a typical small/medium site:

| Stack | Monthly cost |
|---|---|
| TinaCloud Free + Vercel Hobby | $0 |
| TinaCloud Team Plus + Vercel Pro | ~$70 |
| Self-hosted: Vercel Pro + Vercel KV + GitHub | ~$25 (Vercel only — KV is included) |
| Self-hosted: Vercel Pro + MongoDB Atlas (M0 free tier) | ~$25 |
| Self-hosted: Vercel Pro + Vercel KV + Clerk | ~$45 (Clerk has free tier up to 10k MAU) |

Self-hosted hosting is usually cheaper than Team Plus, but you give up Editorial Workflow and search.

## Default for this skill

Throughout the rest of this skill, the **default-path examples assume TinaCloud + Vercel**. Self-hosted alternatives are documented in `references/self-hosted/` but are not the primary path.
