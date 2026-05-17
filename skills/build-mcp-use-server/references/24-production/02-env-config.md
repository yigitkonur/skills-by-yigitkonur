# Environment config

Validate every required env var **at startup**, before `server.listen()`. A missing API key should crash the process at boot — not on the first request five minutes later when a client hits the tool that uses it.

## Fail-fast helper

```typescript
function requireEnv(key: string): string {
  const val = process.env[key];
  if (!val || val.trim() === "") {
    throw new Error(`Missing required env var: ${key}`);
  }
  return val;
}

function optionalEnv(key: string, fallback: string): string {
  return process.env[key]?.trim() || fallback;
}

function intEnv(key: string, fallback: number): number {
  const raw = process.env[key];
  if (!raw) return fallback;
  const n = parseInt(raw, 10);
  if (isNaN(n)) throw new Error(`Env var ${key} must be an integer, got: ${raw}`);
  return n;
}
```

The error message must name the env var. `Missing API_KEY` is debuggable; `Configuration invalid` is not.

## Centralize at the top

One `config` object, read once, frozen. Reading `process.env` from inside tool handlers re-reads on every call and silently drifts when the env changes (e.g. on a process restart in dev).

```typescript
const config = Object.freeze({
  // Server
  name: optionalEnv("SERVER_NAME", "my-server"),
  version: optionalEnv("SERVER_VERSION", "1.0.0"),
  port: intEnv("PORT", 3000),
  nodeEnv: optionalEnv("NODE_ENV", "development"),

  // Required secrets
  apiKey: requireEnv("API_KEY"),
  databaseUrl: requireEnv("DATABASE_URL"),

  // Optional infrastructure
  redisUrl: process.env.REDIS_URL,
  allowedOrigins: process.env.ALLOWED_ORIGINS
    ?.split(",")
    .map((s) => s.trim())
    .filter(Boolean),
});
```

Pass `config` into modules; never re-read `process.env` deeper in the call tree.

## Production-only requirements

Some env vars only matter in production. Check `nodeEnv` and tighten:

```typescript
if (config.nodeEnv === "production") {
  if (!config.allowedOrigins || config.allowedOrigins.length === 0) {
    throw new Error("ALLOWED_ORIGINS required in production (see 08-server-config/04)");
  }
  if (!config.redisUrl) {
    throw new Error("REDIS_URL required in production for distributed sessions");
  }
}
```

## Env vars mcp-use reads automatically

| Var | Effect | See |
|---|---|---|
| `PORT` | Default port for `listen()` | `08-server-config/02` |
| `HOST` | Bind address | `08-server-config/02` |
| `MCP_URL` | Public base URL (used by OAuth metadata) | `11-auth/01` |
| `NODE_ENV` | Switches some defaults to safer values in `production` | — |
| `DEBUG` | Verbosity toggle for built-in `Logger` | `15-logging/` |
| `CSP_URLS` | CSP allowlist for widget assets | `08-server-config/06` |

Don't shadow these with custom vars of the same name — set them and let mcp-use pick them up.

## Schema-validate complex config (optional)

For complex shapes (CORS objects, multi-flag JSON), validate with Zod the same way you validate tool inputs. The error messages are precise:

```typescript
import { z } from "zod";

const CorsConfig = z.object({
  origin: z.array(z.string().url()),
  allowMethods: z.array(z.string()),
});

const cors = CorsConfig.parse(JSON.parse(requireEnv("CORS_CONFIG")));
```

A typo in `CORS_CONFIG` now throws `expected array, received string at "origin"` instead of breaking at the first cross-origin request.

## Don't

- Don't read `process.env` from inside handlers — read once at startup.
- Don't default secret values (`apiKey: process.env.API_KEY ?? "test"`) — the fallback ships to production.
- Don't accept empty strings as "set" — `if (val)` passes for `""`. Use the helper above.
- Don't log `config` at startup — it includes secrets. Log key names only.
