# Dev-bypass recipes for auth-gated apps

When the project has Clerk/NextAuth/Auth.js + a soft-gate password, the dev server will 500 on every page until the bypass is configured. This is the "all-Next-pages-blank" diagnostic.

## Clerk + soft-gate (zeo-radar pattern)

Two env vars required, BOTH must be present:

```sh
# .env.local
AUTH_ENABLED=false
SOFT_GATE_PASSWORD=<any-non-empty-string>
```

`AUTH_ENABLED=false` ALONE is insufficient — the dev-bypass predicate requires the password too:

```ts
export function isDevBypassActive(env: NodeJS.ProcessEnv = process.env): boolean {
  if (env.AUTH_ENABLED !== "false") return false;
  if (!env.SOFT_GATE_PASSWORD?.trim()) return false;
  return true;
}
```

Without the password, Clerk's middleware takes over with possibly-mismatched keys → infinite redirect loop → every page returns 500.

## Diagnostic: "every page is 500/blank"

Symptoms in dev log:

```
Clerk: Refreshing the session token resulted in an infinite redirect loop.
This usually means that your Clerk instance keys do not match — make sure
to copy the correct publishable and secret keys from the Clerk dashboard.
```

OR:

```
PrismaClientKnownRequestError P1001 DatabaseNotReachable
  at readStoredTheme (src/lib/theme/server.ts:61)
  at RootLayout (src/app/layout.tsx:50)
```

OR:

```
PrismaClientKnownRequestError P2021
The table `public.user_preferences` does not exist in the current database.
```

The first is auth misconfig. The second is DB unreachable. The third is migrations not applied. All three present as "blank page / Internal Server Error" in the browser.

## Fix order

1. **Auth bypass** — set `AUTH_ENABLED=false` + `SOFT_GATE_PASSWORD=...` in `.env.local`. Pull the password from a sibling deploy if available:

   ```bash
   # Pull SOFT_GATE_PASSWORD from a Railway noauth deploy so local matches prod
   railway variables --service noauth --kv | grep "^SOFT_GATE_PASSWORD=" | cut -d= -f2-
   ```

2. **DB reachability** — ensure `docker compose up -d` has been run (or OrbStack daemon is running). Local Postgres on `:5434`, Redis on `:6379`. Check `nc -z 127.0.0.1 5434`.

3. **Schema** — apply migrations against the correct DB:

   ```bash
   DATABASE_URL=$(grep ^DATABASE_URL= .env.local | cut -d= -f2-) npx prisma migrate deploy
   ```

   Critical: use `.env.local`'s `DATABASE_URL`, NOT `.env`'s. Prisma's default config-file resolution may pick the wrong one.

4. **Theme reader resilience** — the root layout's theme resolver should NOT crash the app on DB outage. Wrap the prisma call in try/catch:

   ```ts
   async function readStoredTheme(): Promise<ThemeId | null> {
     const userId = await readAuthenticatedUserId();
     if (!userId) return null;
     try {
       const pref = await prisma.userPreference.findUnique({ where: { userId }, select: { theme: true } });
       return isThemeId(pref?.theme) ? pref.theme : null;
     } catch {
       return null;  // UI hint, not load-bearing
     }
   }
   ```

   Without this, a transient DB blip 500s every page.

## Walking the gate in tests

To verify the dev-bypass works end-to-end via real browser:

```bash
# Open the gate page
agent-browser --session test open "http://<host>/gate"
# Submit the password
agent-browser --session test type 'input[type="password"]' "$SOFT_GATE_PASSWORD"
agent-browser --session test click 'button[type="submit"]'
sleep 6  # wait for redirect + cookie set + first compile
# Verify landed on the real app
agent-browser --session test get url
agent-browser --session test screenshot /tmp/post-gate.png
```

Expected: URL becomes `/projects` (or the project's home), page renders the actual app.

## Pointing local at remote DB (for read-only debugging)

Sometimes the cleanest way to verify the local dev server works is to skip docker entirely and point at the production DB:

```sh
# .env.local
# REMOTE-DB MODE — local dev hits Railway production data
DATABASE_URL=postgresql://...@shortline.proxy.rlwy.net:NNNNN/railway
REDIS_URL=redis://...@interchange.proxy.rlwy.net:NNNNN
```

⚠️ **All mutations land on production.** Reads safe; writes dangerous. Document this in `.env.local` with a banner comment.

Pull the URLs from Railway:

```bash
railway variables --service postgres-service-name --kv | grep "DATABASE_PUBLIC_URL"
railway variables --service redis-service-name --kv | grep "REDIS_PUBLIC_URL"
```

## Other auth systems

| Library | Bypass pattern |
|---|---|
| **NextAuth / Auth.js** | Set `NEXTAUTH_SECRET` + `NEXTAUTH_URL` to dummy values; auth-protected routes still redirect to /signin but render. No silent infinite-loop. |
| **Lucia** | Mock the session cookie in middleware for `NODE_ENV === 'development'`. |
| **Custom JWT middleware** | Add a `DEV_BYPASS=1` env check at the top of middleware that short-circuits with a fake user. |
| **No auth** | Skip this section entirely. |

## Verification before declaring done

```bash
# Walking the gate via real Chrome ─ the only definitive test
make tunnel  # or make local
# In another terminal:
PASS=$(grep ^SOFT_GATE_PASSWORD= .env.local | cut -d= -f2-)
agent-browser --session t open "http://<tunnel-host>/gate"
agent-browser --session t type 'input[type="password"]' "$PASS"
agent-browser --session t click 'button[type="submit"]'
sleep 6
agent-browser --session t get url    # MUST be the post-gate route, not /gate
agent-browser --session t screenshot /tmp/verify.png   # MUST show the app, not "Internal Server Error"
```

curl is insufficient — server actions and the gate cookie flow don't work via plain HTTP POST.
