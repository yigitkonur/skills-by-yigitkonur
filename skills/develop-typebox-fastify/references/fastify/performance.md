# Fastify Performance

## Fastify Is Fast by Default

Built-in optimizations:
- `fast-json-stringify` for response serialization (2-3x faster than JSON.stringify)
- `find-my-way` for efficient routing
- `ajv` compiled validators for schema validation
- Low overhead request/response handling

## Always Define Response Schemas

Response schemas activate fast-json-stringify:

```typescript
import { Type } from '@sinclair/typebox'

// FAST: uses fast-json-stringify
app.get('/users', {
  schema: {
    response: {
      200: Type.Array(Type.Object({
        id: Type.String(),
        name: Type.String(),
        email: Type.String(),
      })),
    },
  },
}, async () => db.users.findAll())

// SLOW: uses JSON.stringify
app.get('/users-slow', async () => db.users.findAll())
```

## @fastify/under-pressure for Load Shedding

Protect against overload:

```typescript
import underPressure from '@fastify/under-pressure'
import { Type } from '@sinclair/typebox'

app.register(underPressure, {
  maxEventLoopDelay: 1000,
  maxHeapUsedBytes: 1_000_000_000,   // ~1GB
  maxRssBytes: 1_500_000_000,        // ~1.5GB
  maxEventLoopUtilization: 0.98,
  pressureHandler: (request, reply, type, value) => {
    reply.code(503).send({
      error: 'Service Unavailable',
      message: `Server under pressure: ${type}`,
    })
  },
})
```

## Connection Pooling

```typescript
import postgres from 'postgres'

const sql = postgres(process.env.DATABASE_URL, {
  max: 20,
  idle_timeout: 20,
  connect_timeout: 10,
})

app.decorate('db', sql)

app.get('/users', {
  schema: { response: { 200: Type.Array(UserSchema) } },
}, async () => app.db`SELECT * FROM users LIMIT 100`)
```

## Avoid Blocking the Event Loop with Piscina

```typescript
import Piscina from 'piscina'
import { join } from 'node:path'
import { Type } from '@sinclair/typebox'

const piscina = new Piscina({
  filename: join(import.meta.dirname, 'workers', 'compute.js'),
})

app.post('/compute', {
  schema: {
    body: Type.Object({ data: Type.Unknown() }),
    response: { 200: Type.Object({ result: Type.Unknown() }) },
  },
}, async (request) => {
  const result = await piscina.run(request.body.data)
  return { result }
})
```

## Stream Large Responses

```typescript
import { createReadStream } from 'node:fs'

// GOOD: stream file
app.get('/large-file', async (request, reply) => {
  const stream = createReadStream('./large-file.json')
  reply.type('application/json')
  return reply.send(stream)
})

// BAD: load entire file into memory
app.get('/large-file-bad', async () => {
  const content = await fs.readFile('./large-file.json', 'utf-8')
  return JSON.parse(content)
})

// Stream database results
app.get('/export', async (request, reply) => {
  reply.type('application/json')
  const cursor = db.users.findCursor()
  reply.raw.write('[')
  let first = true
  for await (const user of cursor) {
    if (!first) reply.raw.write(',')
    reply.raw.write(JSON.stringify(user))
    first = false
  }
  reply.raw.write(']')
  reply.raw.end()
})
```

## Caching with LRU

```typescript
import { LRUCache } from 'lru-cache'
import { Type } from '@sinclair/typebox'

const cache = new LRUCache<string, unknown>({ max: 1000, ttl: 60000 })

app.get('/expensive/:id', {
  schema: {
    params: Type.Object({ id: Type.String() }),
    response: { 200: Type.Unknown() },
  },
}, async (request) => {
  const cacheKey = `expensive:${request.params.id}`
  const cached = cache.get(cacheKey)
  if (cached) return cached

  const result = await expensiveOperation(request.params.id)
  cache.set(cacheKey, result)
  return result
})
```

## Request Coalescing with async-cache-dedupe

Deduplicate concurrent identical requests:

```typescript
import { createCache } from 'async-cache-dedupe'

const cache = createCache({
  ttl: 60,
  stale: 5,
  storage: { type: 'memory' },
})

cache.define('fetchData', async (id: string) => db.findById(id))

app.get('/data/:id', {
  schema: {
    params: Type.Object({ id: Type.String() }),
    response: { 200: Type.Unknown() },
  },
}, async (request) => cache.fetchData(request.params.id))

// Distributed caching with Redis
import Redis from 'ioredis'
const redis = new Redis(process.env.REDIS_URL)

const distributedCache = createCache({
  ttl: 60,
  storage: { type: 'redis', options: { client: redis } },
})
```

## Compression

```typescript
import fastifyCompress from '@fastify/compress'

app.register(fastifyCompress, {
  global: true,
  threshold: 1024,
  encodings: ['gzip', 'deflate'],
})

// Disable for specific route
app.get('/already-compressed', { compress: false }, handler)
```

## Payload Limits

```typescript
const app = Fastify({ bodyLimit: 1048576 }) // 1MB default

// Per-route override
app.post('/upload', {
  bodyLimit: 10485760, // 10MB
  schema: {
    response: { 200: Type.Object({ size: Type.Integer() }) },
  },
}, async (request) => ({ size: Buffer.byteLength(JSON.stringify(request.body)) }))
```

## Connection Timeouts

```typescript
const app = Fastify({
  connectionTimeout: 30000,
  keepAliveTimeout: 72000,
})
```

## Disable Unnecessary Features

```typescript
const app = Fastify({
  disableRequestLogging: true,  // if you handle logging yourself
  caseSensitive: true,          // slight performance gain
})
```

## Logger Performance

```typescript
// Avoid logging large objects
app.get('/data', async (request) => {
  // BAD
  request.log.info({ data: largeObject }, 'Processing')

  // GOOD
  request.log.info({ id: largeObject.id }, 'Processing')

  return largeObject
})

// Check log level before expensive computation
if (app.log.isLevelEnabled('debug')) {
  request.log.debug({ details: expensiveToCompute() }, 'Debug info')
}
```

## Benchmarking with autocannon

```bash
autocannon http://localhost:3000/api/users
autocannon -c 100 -d 30 -p 10 http://localhost:3000/api/users
```

## Profiling

```bash
npx @platformatic/flame app.js
```

## Memory Monitoring

```typescript
app.get('/health', {
  schema: {
    response: {
      200: Type.Object({
        status: Type.String(),
        memory: Type.Object({
          heapUsed: Type.String(),
          heapTotal: Type.String(),
          rss: Type.String(),
        }),
      }),
    },
  },
}, async () => {
  const mem = process.memoryUsage()
  return {
    status: 'ok',
    memory: {
      heapUsed: Math.round(mem.heapUsed / 1024 / 1024) + 'MB',
      heapTotal: Math.round(mem.heapTotal / 1024 / 1024) + 'MB',
      rss: Math.round(mem.rss / 1024 / 1024) + 'MB',
    },
  }
})
```

## Key Performance Rules

- Always define response schemas (enables fast-json-stringify)
- Compile schemas at startup, never at request time
- Use connection pooling for databases
- Stream large payloads instead of buffering
- Use piscina for CPU-intensive work
- Set appropriate body limits
- Use async-cache-dedupe for request coalescing
