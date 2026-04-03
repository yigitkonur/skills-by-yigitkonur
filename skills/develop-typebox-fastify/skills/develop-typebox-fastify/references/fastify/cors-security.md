# Fastify CORS and Security

## CORS with @fastify/cors

```typescript
import Fastify from 'fastify'
import cors from '@fastify/cors'
import { Type } from '@sinclair/typebox'

const app = Fastify()

// Simple CORS - allow all origins
app.register(cors)

// Configured CORS
app.register(cors, {
  origin: ['https://example.com', 'https://app.example.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  exposedHeaders: ['X-Total-Count'],
  credentials: true,
  maxAge: 86400,
})
```

## Dynamic CORS Origin

```typescript
app.register(cors, {
  origin: (origin, callback) => {
    if (!origin) return callback(null, true) // mobile apps, curl

    const allowedOrigins = [
      'https://example.com',
      /\.example\.com$/,
    ]

    const isAllowed = allowedOrigins.some((allowed) =>
      allowed instanceof RegExp ? allowed.test(origin) : allowed === origin
    )

    if (isAllowed) callback(null, true)
    else callback(new Error('Not allowed by CORS'), false)
  },
  credentials: true,
})
```

## Security Headers with @fastify/helmet

```typescript
import helmet from '@fastify/helmet'

app.register(helmet, {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'", 'https://api.example.com'],
    },
  },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  frameguard: { action: 'deny' },
  noSniff: true,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  crossOriginEmbedderPolicy: false,
})
```

## Rate Limiting

```typescript
import rateLimit from '@fastify/rate-limit'

app.register(rateLimit, {
  max: 100,
  timeWindow: '1 minute',
  errorResponseBuilder: (request, context) => ({
    statusCode: 429,
    error: 'Too Many Requests',
    message: `Rate limit exceeded. Retry in ${context.after}`,
    retryAfter: context.after,
  }),
})

// Per-route rate limit
app.get('/expensive', {
  config: { rateLimit: { max: 10, timeWindow: '1 minute' } },
  schema: { response: { 200: Type.Object({ data: Type.String() }) } },
}, handler)

// Skip rate limit
app.get('/health', {
  config: { rateLimit: false },
}, () => ({ status: 'ok' }))
```

## Redis-Based Rate Limiting (Required for Production)

```typescript
import rateLimit from '@fastify/rate-limit'
import Redis from 'ioredis'

const redis = new Redis(process.env.REDIS_URL)

app.register(rateLimit, {
  max: 100,
  timeWindow: '1 minute',
  redis,
  nameSpace: 'rate-limit:',
  keyGenerator: (request) => request.user?.id || request.ip,
})
```

## CSRF Protection

```typescript
import fastifyCsrf from '@fastify/csrf-protection'
import fastifyCookie from '@fastify/cookie'

app.register(fastifyCookie)
app.register(fastifyCsrf, {
  cookieOpts: { signed: true, httpOnly: true, sameSite: 'strict' },
})

app.get('/csrf-token', async (request, reply) => {
  const token = reply.generateCsrf()
  return { token }
})

app.post('/transfer', {
  preHandler: app.csrfProtection,
  schema: {
    body: Type.Object({ amount: Type.Number(), to: Type.String() }),
    response: { 200: Type.Object({ success: Type.Boolean() }) },
  },
}, async () => ({ success: true }))
```

## Secure Cookies

```typescript
import cookie from '@fastify/cookie'

app.register(cookie, {
  secret: process.env.COOKIE_SECRET,
  parseOptions: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: '/',
    maxAge: 3600,
  },
})

app.post('/login', async (request, reply) => {
  const token = await createSession(request.body)
  reply.setCookie('session', token, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    signed: true,
    maxAge: 86400,
  })
  return { success: true }
})
```

## Input Validation Security

Schema-based validation protects against injection:

```typescript
app.post('/users', {
  schema: {
    body: Type.Object({
      email: Type.String({ format: 'email', maxLength: 254 }),
      name: Type.String({ minLength: 1, maxLength: 100, pattern: '^[a-zA-Z\\s]+$' }),
    }),
  },
}, handler)
```

## Trust Proxy

```typescript
const app = Fastify({
  trustProxy: true,                      // trust all
  // trustProxy: ['127.0.0.1', '10.0.0.0/8'], // trust specific
  // trustProxy: 1,                          // trust N proxies
})

app.get('/ip', async (request) => ({
  ip: request.ip,       // real client IP
  ips: request.ips,     // all IPs in chain
}))
```

## HTTPS Redirect

```typescript
app.addHook('onRequest', async (request, reply) => {
  if (
    process.env.NODE_ENV === 'production' &&
    request.headers['x-forwarded-proto'] !== 'https'
  ) {
    reply.redirect(301, `https://${request.hostname}${request.url}`)
  }
})
```

## IP Filtering

```typescript
app.addHook('onRequest', async (request, reply) => {
  if (request.url.startsWith('/admin')) {
    const allowedIps = new Set(['192.168.1.0/24', '10.0.0.0/8'])
    if (!isIpAllowed(request.ip, allowedIps)) {
      reply.code(403).send({ error: 'Forbidden' })
    }
  }
})
```

## Complete Security Setup

```typescript
import Fastify from 'fastify'
import cors from '@fastify/cors'
import helmet from '@fastify/helmet'
import rateLimit from '@fastify/rate-limit'

const app = Fastify({
  trustProxy: true,
  bodyLimit: 1048576,
})

app.register(helmet)
app.register(cors, {
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true,
})
app.register(rateLimit, { max: 100, timeWindow: '1 minute' })

// Validate all input with schemas
// Never expose internal errors in production
// Use parameterized queries for database
// Keep dependencies updated
```

## Custom Security Headers

```typescript
app.addHook('onSend', async (request, reply) => {
  reply.header('X-Request-ID', request.id)
  reply.header('X-Content-Type-Options', 'nosniff')
  reply.header('X-Frame-Options', 'DENY')
  reply.header('Permissions-Policy', 'geolocation=(), camera=()')
})
```
