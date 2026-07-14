# Deployment Decision Matrix

Pick a target by what your server actually needs — sessions, OAuth, widgets, runtime, control over the box.

---

## 1. Quick choose

- **Just ship it** → Manufact Cloud (`platforms/01-mcp-use-cloud.md`).
- **Already on GCP** → Cloud Run (`platforms/03-google-cloud-run.md`).
- **Already on Supabase** → Supabase Edge Functions (`platforms/02-supabase.md`).
- **Want a long-running container with disks** → Fly.io (`platforms/05-fly.md`).
- **Stateless, low traffic, free tier** → Vercel or Cloudflare Workers (`platforms/04-vercel.md`, `platforms/06-cloudflare-workers.md`).
- **Deno first** → Deno Deploy (`platforms/07-deno-deploy.md`).
- **Self-hosted box** → Docker (`03-docker.md`).

---

## 2. Capability matrix

| Need                         | Manufact Cloud | Cloud Run     | Supabase Edge | Fly.io       | Vercel/Netlify | Cloudflare Workers | Deno Deploy   | Docker (self) |
|------------------------------|----------------|---------------|---------------|--------------|----------------|--------------------|---------------|---------------|
| Setup effort                 | Minimal        | Moderate      | Moderate      | Low          | Low            | Low                | Minimal       | High          |
| Sessions (in-process)        | Yes            | Yes + Redis   | Stateless     | Yes          | No             | No (KV needed)     | No (KV needed)| Yes           |
| Built-in OAuth               | Yes            | IAM only      | Anon key      | Manual       | Manual         | Manual             | Manual        | Manual        |
| Widget assets served         | Native         | Manual        | Storage CDN   | Manual       | No             | Manual             | Manual        | Manual        |
| Stateful tools (notifications, sampling, elicit) | Yes | Yes + Redis | No (Deno stateless) | Yes | No  | No                 | No            | Yes           |
| WebSocket / SSE long-poll    | Yes            | Yes           | Limited       | Yes          | No             | Limited            | Yes           | Yes           |
| Cold starts                  | Managed        | Configurable  | ~50 ms        | Configurable | Yes            | None               | None          | None          |
| Runtime                      | Node           | Node (any)    | Deno          | Node (any)   | Node           | Workers (V8)       | Deno          | Node (any)    |
| Custom domains               | CNAME          | Yes           | Yes           | Yes          | Yes            | Yes                | Yes           | Yes           |

---

## 3. Pick by feature requirement

| Requirement                           | Pick                                             |
|---------------------------------------|--------------------------------------------------|
| Need `RedisSessionStore`              | Manufact Cloud, Cloud Run, Fly.io, Docker        |
| Multi-replica with sticky sessions    | Cloud Run + Redis, Fly.io                        |
| Built-in OAuth provider routing       | Manufact Cloud                                    |
| Hosted widgets out of the box         | Manufact Cloud                                    |
| Lowest latency global edge            | Cloudflare Workers                                |
| Strict regional pinning               | Cloud Run, Fly.io                                 |
| Free tier viable for stateless tools  | Vercel, Cloudflare Workers                        |
| Existing Supabase backend             | Supabase Edge                                     |
| Need full Node APIs (`fs`, `child_process`) | Manufact Cloud, Cloud Run, Fly.io, Docker  |

---

## 4. Disqualifiers

- **Stateless platform + stateful MCP feature:** notifications, sampling, elicitation, and progress all require a session store. Vercel/Netlify, Cloudflare Workers, Deno Deploy without external KV cannot host these reliably. Pick a stateful target or accept stateless mode.
- **Edge runtime + Node-only deps:** Workers/Deno cannot run packages depending on Node `fs`, `net`, native modules. Audit before committing.
- **Single-instance state in a multi-replica deploy:** the in-memory session store is per-process. Multi-replica without `RedisSessionStore` will lose sessions on the wrong shard.

---

**Canonical doc:** https://manufact.com/docs/typescript/server/deployment/mcp-use
