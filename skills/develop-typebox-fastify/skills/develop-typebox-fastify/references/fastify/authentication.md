# Fastify Authentication

## JWT with @fastify/jwt and TypeBox

```typescript
import Fastify from 'fastify'
import fastifyJwt from '@fastify/jwt'
import { Type } from '@sinclair/typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

app.register(fastifyJwt, {
  secret: process.env.JWT_SECRET,
  sign: { expiresIn: '1h' },
})

// Authentication decorator
app.decorate('authenticate', async function (request, reply) {
  try {
    await request.jwtVerify()
  } catch (err) {
    reply.code(401).send({ error: 'Unauthorized' })
  }
})

// Login route
app.post('/login', {
  schema: {
    body: Type.Object({
      email: Type.String({ format: 'email' }),
      password: Type.String(),
    }),
    response: {
      200: Type.Object({ token: Type.String() }),
    },
  },
}, async (request, reply) => {
  const { email, password } = request.body
  const user = await validateCredentials(email, password)
  if (!user) return reply.code(401).send({ error: 'Invalid credentials' })

  const token = app.jwt.sign({ id: user.id, email: user.email, role: user.role })
  return { token }
})

// Protected route
app.get('/profile', {
  onRequest: [app.authenticate],
  schema: {
    response: {
      200: Type.Object({
        id: Type.String(),
        email: Type.String(),
        role: Type.String(),
      }),
    },
  },
}, async (request) => request.user)
```

## Refresh Token Rotation

```typescript
import { randomBytes } from 'node:crypto'

app.register(fastifyJwt, {
  secret: process.env.JWT_SECRET,
  sign: { expiresIn: '15m' }, // Short-lived access tokens
})

const refreshTokens = new Map<string, { userId: string; expires: number }>()

app.post('/auth/login', {
  schema: {
    body: Type.Object({
      email: Type.String({ format: 'email' }),
      password: Type.String(),
    }),
    response: {
      200: Type.Object({
        accessToken: Type.String(),
        refreshToken: Type.String(),
      }),
    },
  },
}, async (request, reply) => {
  const user = await validateCredentials(request.body.email, request.body.password)
  if (!user) return reply.code(401).send({ error: 'Invalid credentials' })

  const accessToken = app.jwt.sign({ id: user.id, role: user.role })
  const refreshToken = randomBytes(32).toString('hex')

  refreshTokens.set(refreshToken, {
    userId: user.id,
    expires: Date.now() + 7 * 24 * 60 * 60 * 1000, // 7 days
  })

  return { accessToken, refreshToken }
})

app.post('/auth/refresh', {
  schema: {
    body: Type.Object({ refreshToken: Type.String() }),
    response: {
      200: Type.Object({ accessToken: Type.String(), refreshToken: Type.String() }),
    },
  },
}, async (request, reply) => {
  const stored = refreshTokens.get(request.body.refreshToken)
  if (!stored || stored.expires < Date.now()) {
    refreshTokens.delete(request.body.refreshToken)
    return reply.code(401).send({ error: 'Invalid refresh token' })
  }

  refreshTokens.delete(request.body.refreshToken) // rotation
  const user = await db.users.findById(stored.userId)
  const accessToken = app.jwt.sign({ id: user.id, role: user.role })
  const newRefreshToken = randomBytes(32).toString('hex')

  refreshTokens.set(newRefreshToken, { userId: user.id, expires: Date.now() + 7 * 24 * 60 * 60 * 1000 })
  return { accessToken, refreshToken: newRefreshToken }
})
```

## Role-Based Access Control (RBAC)

```typescript
type Role = 'admin' | 'user' | 'moderator'

app.decorate('authorize', function (...allowedRoles: Role[]) {
  return async (request, reply) => {
    await request.jwtVerify()
    if (!allowedRoles.includes(request.user.role)) {
      return reply.code(403).send({
        error: 'Forbidden',
        message: `Role '${request.user.role}' is not authorized`,
      })
    }
  }
})

// Admin only
app.get('/admin/users', {
  onRequest: [app.authorize('admin')],
  schema: { response: { 200: Type.Array(UserSchema) } },
}, async () => db.users.findAll())

// Admin or moderator
app.delete('/posts/:id', {
  onRequest: [app.authorize('admin', 'moderator')],
  schema: {
    params: Type.Object({ id: Type.String() }),
    response: { 200: Type.Object({ deleted: Type.Boolean() }) },
  },
}, async (request) => {
  await db.posts.delete(request.params.id)
  return { deleted: true }
})
```

## Bearer Token / API Key Auth

```typescript
import bearerAuth from '@fastify/bearer-auth'

// Simple API key set
app.register(bearerAuth, {
  keys: new Set([process.env.API_KEY]),
  errorResponse: () => ({ error: 'Unauthorized', message: 'Invalid API key' }),
})

// Database-backed API keys
app.register(bearerAuth, {
  auth: async (key, request) => {
    const apiKey = await db.apiKeys.findByKey(key)
    if (!apiKey || !apiKey.active) return false
    request.apiKey = apiKey
    return true
  },
  errorResponse: () => ({ error: 'Unauthorized', message: 'Invalid API key' }),
})
```

## OAuth 2.0

```typescript
import fastifyOauth2 from '@fastify/oauth2'

app.register(fastifyOauth2, {
  name: 'googleOAuth2',
  scope: ['profile', 'email'],
  credentials: {
    client: {
      id: process.env.GOOGLE_CLIENT_ID,
      secret: process.env.GOOGLE_CLIENT_SECRET,
    },
  },
  startRedirectPath: '/auth/google',
  callbackUri: 'http://localhost:3000/auth/google/callback',
  discovery: { issuer: 'https://accounts.google.com' },
})

app.get('/auth/google/callback', async (request, reply) => {
  const { token } = await app.googleOAuth2.getAccessTokenFromAuthorizationCodeFlow(request)
  const userInfo = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: { Authorization: `Bearer ${token.access_token}` },
  }).then((r) => r.json())

  let user = await db.users.findByEmail(userInfo.email)
  if (!user) user = await db.users.create({ email: userInfo.email, name: userInfo.name, provider: 'google' })

  const jwt = app.jwt.sign({ id: user.id, role: user.role })
  return reply.redirect(`/auth/success?token=${jwt}`)
})
```

## Session-Based Auth

```typescript
import fastifyCookie from '@fastify/cookie'
import fastifySession from '@fastify/session'

app.register(fastifyCookie)
app.register(fastifySession, {
  secret: process.env.SESSION_SECRET,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000,
  },
})

app.post('/login', {
  schema: {
    body: Type.Object({ email: Type.String(), password: Type.String() }),
  },
}, async (request, reply) => {
  const user = await validateCredentials(request.body.email, request.body.password)
  if (!user) return reply.code(401).send({ error: 'Invalid credentials' })
  request.session.userId = user.id
  return { success: true }
})
```

## Rate Limiting Auth Endpoints (MUST Use Redis in Production)

```typescript
import fastifyRateLimit from '@fastify/rate-limit'
import Redis from 'ioredis'

const redis = new Redis(process.env.REDIS_URL)

app.register(async function authRoutes(fastify) {
  await fastify.register(fastifyRateLimit, {
    max: 5,
    timeWindow: '1 minute',
    redis,
    keyGenerator: (request) => `${request.ip}:${request.body?.email || ''}`,
  })

  fastify.post('/login', loginHandler)
  fastify.post('/register', registerHandler)
}, { prefix: '/auth' })
```

## Password Hashing

```typescript
import { hash, verify } from '@node-rs/argon2'

async function hashPassword(password: string): Promise<string> {
  return hash(password, { memoryCost: 65536, timeCost: 3, parallelism: 4 })
}

async function verifyPassword(hash: string, password: string): Promise<boolean> {
  return verify(hash, password)
}
```
