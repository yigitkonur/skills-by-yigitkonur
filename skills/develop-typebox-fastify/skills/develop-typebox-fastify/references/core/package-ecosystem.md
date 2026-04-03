# TypeBox + Fastify Package Ecosystem

## Core packages

| Package | Purpose | Install |
|---|---|---|
| `fastify` | HTTP framework | `npm i fastify` |
| `@fastify/type-provider-typebox` | TypeBox type provider | `npm i @fastify/type-provider-typebox` |
| `@sinclair/typebox` | Schema library (legacy name) | `npm i @sinclair/typebox` |
| `typebox` | Schema library (new name) | `npm i typebox` |

> **Note**: `typebox` is the new package name. `@sinclair/typebox` still works but is deprecated for new projects. Both re-export `Type`, `Static`, `Value`, etc. `@fastify/type-provider-typebox` re-exports `Type` and `Static` from `@sinclair/typebox`.

## Official Fastify plugins

### Validation & Serialization
| Package | Purpose |
|---|---|
| `ajv-formats` | Standard format validators (email, uri, etc.) |
| `fast-json-stringify` | Built-in — fast serialization from response schemas |

### Security
| Package | Purpose |
|---|---|
| `@fastify/cors` | Cross-Origin Resource Sharing |
| `@fastify/helmet` | Security headers (CSP, HSTS, etc.) |
| `@fastify/csrf-protection` | CSRF token protection |
| `@fastify/rate-limit` | Rate limiting (use with Redis for production) |

### Authentication
| Package | Purpose |
|---|---|
| `@fastify/jwt` | JWT token signing and verification |
| `@fastify/bearer-auth` | Bearer token / API key auth |
| `@fastify/oauth2` | OAuth 2.0 provider integration |
| `@fastify/cookie` | Cookie parsing and serialization |
| `@fastify/session` | Session management |

### Database
| Package | Purpose |
|---|---|
| `@fastify/postgres` | PostgreSQL connection pooling |
| `@fastify/mysql` | MySQL connection pooling |
| `@fastify/mongodb` | MongoDB client |
| `@fastify/redis` | Redis client |

### Content & Files
| Package | Purpose |
|---|---|
| `@fastify/multipart` | File uploads (multipart/form-data) |
| `@fastify/formbody` | URL-encoded form parsing |
| `@fastify/compress` | Response compression (gzip, brotli) |
| `@fastify/static` | Static file serving |

### API Documentation
| Package | Purpose |
|---|---|
| `@fastify/swagger` | OpenAPI spec generation |
| `@fastify/swagger-ui` | Swagger UI serving |

### Utilities
| Package | Purpose |
|---|---|
| `@fastify/autoload` | Auto-discover and load plugins/routes |
| `@fastify/env` | Environment variable validation |
| `@fastify/sensible` | HTTP error reply helpers |
| `@fastify/error` | Custom typed error factory |
| `@fastify/under-pressure` | Load shedding / circuit breaker |
| `@fastify/http-proxy` | HTTP proxying |
| `@fastify/websocket` | WebSocket support |
| `fastify-plugin` | Break plugin encapsulation (`fp()`) |
| `close-with-grace` | Graceful shutdown |

### Testing
| Package | Purpose |
|---|---|
| (built-in) `inject()` | HTTP testing without network |
| `autocannon` | Load testing / benchmarking |

### Logging
| Package | Purpose |
|---|---|
| `pino` | Built-in logger |
| `pino-pretty` | Dev-mode log formatting |

### Database ORMs (community)
| Package | Purpose |
|---|---|
| `drizzle-orm` | Type-safe SQL ORM |
| `drizzle-kit` | Migration CLI for Drizzle |
| `@prisma/client` | Prisma ORM client |
| `prisma` | Prisma CLI |

### Performance
| Package | Purpose |
|---|---|
| `async-cache-dedupe` | Request deduplication + caching |
| `piscina` | Worker thread pool for CPU work |

## Typical `package.json` scripts

```json
{
  "scripts": {
    "start": "node app.ts",
    "dev": "node --watch app.ts",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "biome check .",
    "build": "tsc",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "docs": "node -e 'import(\"./src/app.js\").then(m => m.default.swagger())'"
  }
}
```

## TypeScript configuration

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noEmit": true,
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist"
  },
  "include": ["src"]
}
```

## Version compatibility

- **Fastify v5** — requires Node.js 20+
- **TypeBox** — works with TypeScript 4.7+, recommended 5.0+
- **@fastify/type-provider-typebox** — matches Fastify major version
- **Node.js type stripping** — requires Node.js 22.6+ (`--experimental-strip-types`) or 23+ (stable)
