# Fastify Logging (Pino)

## Basic Configuration

```typescript
import Fastify from 'fastify'

// Simple enable
const app = Fastify({ logger: true })

// With configuration
const app = Fastify({
  logger: {
    level: 'info',
    transport: {
      target: 'pino-pretty',
      options: { colorize: true },
    },
  },
})
```

## Log Levels

```typescript
app.log.trace('Detailed debugging')
app.log.debug('Debugging information')
app.log.info('General information')
app.log.warn('Warning messages')
app.log.error('Error messages')
app.log.fatal('Fatal errors')
```

## Environment-Based Config

```typescript
function getLoggerConfig() {
  if (process.env.NODE_ENV === 'test') return false

  if (process.env.NODE_ENV === 'development') {
    return {
      level: 'debug',
      transport: {
        target: 'pino-pretty',
        options: {
          colorize: true,
          translateTime: 'HH:MM:ss Z',
          ignore: 'pid,hostname',
        },
      },
    }
  }

  // Production: JSON output for log aggregation
  return {
    level: process.env.LOG_LEVEL || 'info',
    formatters: {
      level: (label) => ({ level: label }),
      bindings: (bindings) => ({
        pid: bindings.pid,
        service: 'my-api',
        version: process.env.APP_VERSION,
      }),
    },
  }
}

const app = Fastify({ logger: getLoggerConfig() })
```

## Request-Scoped Logging

Each request has its own logger with request context (includes request ID):

```typescript
app.get('/users/:id', async (request) => {
  request.log.info('Fetching user')                          // includes reqId
  request.log.warn({ userId: request.params.id }, 'User not found')
  request.log.info({ userId: user.id }, 'User fetched')
  return user
})
```

## Structured Logging (Always Use Objects)

```typescript
// GOOD: structured, searchable
request.log.info({
  action: 'user_created',
  userId: user.id,
  email: user.email,
}, 'User created successfully')

request.log.error({
  err: error,
  userId: request.params.id,
  operation: 'fetch_user',
}, 'Failed to fetch user')

// BAD: unstructured, hard to parse
request.log.info(`User ${user.id} created with email ${user.email}`)
```

## Child Loggers

```typescript
// Add context to all logs for a request
app.addHook('onRequest', async (request) => {
  if (request.user) {
    request.log = request.log.child({
      userId: request.user.id,
      userRole: request.user.role,
    })
  }
})

// Service-level child logger
const userService = {
  log: app.log.child({ service: 'UserService' }),

  async create(data) {
    this.log.info({ email: data.email }, 'Creating user')
  },
}
```

## Redacting Sensitive Data

```typescript
const app = Fastify({
  logger: {
    level: 'info',
    redact: {
      paths: [
        'req.headers.authorization',
        'req.headers.cookie',
        'body.password',
        'body.creditCard',
        '*.password',
        '*.secret',
        '*.token',
      ],
      censor: '[REDACTED]',
    },
  },
})
```

## Custom Serializers

```typescript
const app = Fastify({
  logger: {
    level: 'info',
    serializers: {
      req: (request) => ({
        method: request.method,
        url: request.url,
        headers: { host: request.headers.host, 'user-agent': request.headers['user-agent'] },
        remoteAddress: request.ip,
      }),
      res: (response) => ({
        statusCode: response.statusCode,
      }),
      user: (user) => ({
        id: user.id,
        email: user.email,
        // Exclude sensitive fields like password
      }),
    },
  },
})
```

## Custom Request Logging

```typescript
const app = Fastify({
  logger: true,
  disableRequestLogging: true, // disable default
})

app.addHook('onRequest', async (request) => {
  request.log.info({ method: request.method, url: request.url, query: request.query }, 'Request received')
})

app.addHook('onResponse', async (request, reply) => {
  request.log.info({
    statusCode: reply.statusCode,
    responseTime: reply.elapsedTime,
  }, 'Request completed')
})
```

## Error Logging

```typescript
app.setErrorHandler((error, request, reply) => {
  request.log.error({
    err: error,       // Pino serializes error objects properly
    url: request.url,
    method: request.method,
    body: request.body,
    query: request.query,
  }, 'Request error')

  reply.code(error.statusCode || 500).send({ error: error.message })
})
```

## Request ID Tracking

```typescript
import { randomUUID } from 'node:crypto'

const app = Fastify({
  logger: true,
  requestIdHeader: 'x-request-id',
  genReqId: (request) => request.headers['x-request-id']?.toString() || randomUUID(),
})

// Forward to downstream services
app.addHook('preHandler', async (request) => {
  request.requestId = request.id
})

const response = await fetch('http://other-service/api', {
  headers: { 'x-request-id': request.id },
})
```

## Multiple Log Destinations

```typescript
import pino from 'pino'
import { createWriteStream } from 'node:fs'

const streams = [
  { stream: process.stdout },
  { stream: createWriteStream('./app.log') },
  { level: 'error', stream: createWriteStream('./error.log') },
]

const app = Fastify({
  logger: pino({ level: 'info' }, pino.multistream(streams)),
})
```

## Log Aggregation (Production)

```typescript
const app = Fastify({
  logger: {
    level: 'info',
    base: {
      service: 'user-api',
      version: process.env.APP_VERSION,
      environment: process.env.NODE_ENV,
    },
  },
})
```

## Performance Considerations

```typescript
// Avoid string concatenation
request.log.info({ userId: user.id, action }, 'User action')   // GOOD
request.log.info('User ' + user.id + ' did ' + action)          // BAD

// Check level before expensive computation
if (app.log.isLevelEnabled('debug')) {
  request.log.debug({ details: expensiveToCompute() }, 'Debug info')
}

// Use appropriate log levels - don't info-log in hot paths
```

## Log Rotation

```bash
# Using pino-roll
node app.js | pino-roll --frequency daily --extension .log
```
