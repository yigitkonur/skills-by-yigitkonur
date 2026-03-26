# Fastify Content Type Parsing

## Default Parsers

Fastify includes parsers for:
- `application/json` (parsed to object)
- `text/plain` (parsed to string)

```typescript
import Fastify from 'fastify'
import { Type } from '@sinclair/typebox'

const app = Fastify()

app.post('/json', {
  schema: {
    body: Type.Object({ name: Type.String() }),
    response: { 200: Type.Object({ received: Type.Unknown() }) },
  },
}, async (request) => ({ received: request.body }))

app.post('/text', async (request) => ({ text: request.body }))
```

## @fastify/formbody for URL-Encoded Forms

```typescript
import formbody from '@fastify/formbody'

app.register(formbody)

app.post('/form', {
  schema: {
    body: Type.Object({
      name: Type.String(),
      email: Type.String({ format: 'email' }),
    }),
    response: { 200: Type.Object({ name: Type.String(), email: Type.String() }) },
  },
}, async (request) => {
  const { name, email } = request.body
  return { name, email }
})
```

## Custom Content Type Parser

```typescript
// URL-encoded manually
app.addContentTypeParser(
  'application/x-www-form-urlencoded',
  { parseAs: 'string' },
  async (request, body) => {
    const parsed = new URLSearchParams(body)
    return Object.fromEntries(parsed)
  },
)
```

## XML Parsing

```typescript
import { XMLParser } from 'fast-xml-parser'

const xmlParser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
})

app.addContentTypeParser(
  'application/xml',
  { parseAs: 'string' },
  async (request, body) => xmlParser.parse(body),
)

app.addContentTypeParser(
  'text/xml',
  { parseAs: 'string' },
  async (request, body) => xmlParser.parse(body),
)

app.post('/xml', {
  schema: { response: { 200: Type.Object({ data: Type.Unknown() }) } },
}, async (request) => ({ data: request.body }))
```

## Protocol Buffers

```typescript
import protobuf from 'protobufjs'

const root = await protobuf.load('./schema.proto')
const MessageType = root.lookupType('package.MessageType')

app.addContentTypeParser(
  'application/x-protobuf',
  { parseAs: 'buffer' },
  async (request, body) => {
    const message = MessageType.decode(body)
    return MessageType.toObject(message)
  },
)
```

## Regex Content Type Matching

```typescript
// Match any JSON variant (application/vnd.api+json, etc.)
app.addContentTypeParser(
  /^application\/.*\+json$/,
  { parseAs: 'string' },
  async (request, body) => JSON.parse(body),
)
```

## Custom JSON Parser with Better Error Handling

```typescript
app.removeContentTypeParser('application/json')

app.addContentTypeParser(
  'application/json',
  { parseAs: 'string' },
  async (request, body) => {
    try {
      return JSON.parse(body)
    } catch {
      throw { statusCode: 400, code: 'INVALID_JSON', message: 'Invalid JSON payload' }
    }
  },
)
```

## Stream Processing for Large Payloads

```typescript
import { pipeline } from 'node:stream/promises'
import { createWriteStream } from 'node:fs'

app.addContentTypeParser(
  'application/octet-stream',
  async (request, payload) => payload, // Return stream directly
)

app.post('/upload-stream', async (request, reply) => {
  const destination = createWriteStream('./upload.bin')
  await pipeline(request.body, destination)
  return { success: true }
})
```

## Catch-All Parser

```typescript
app.addContentTypeParser('*', async (request, payload) => {
  const chunks: Buffer[] = []
  for await (const chunk of payload) chunks.push(chunk)
  const buffer = Buffer.concat(chunks)

  const contentType = request.headers['content-type']
  if (contentType?.includes('json')) return JSON.parse(buffer.toString('utf-8'))
  if (contentType?.includes('text')) return buffer.toString('utf-8')
  return buffer
})
```

## Body Size Limits

```typescript
// Global limit
const app = Fastify({ bodyLimit: 1048576 }) // 1MB

// Per-route limit
app.post('/large-upload', {
  bodyLimit: 52428800, // 50MB
  schema: { response: { 200: Type.Object({ size: Type.Integer() }) } },
}, async (request) => ({ size: JSON.stringify(request.body).length }))

// Per content-type limit
app.addContentTypeParser('application/json', {
  parseAs: 'string',
  bodyLimit: 2097152, // 2MB for JSON
}, async (request, body) => JSON.parse(body))
```

## Content Negotiation

```typescript
app.post('/data', async (request, reply) => {
  const data = request.body

  // Respond based on Accept header
  const accept = request.headers.accept
  if (accept?.includes('application/xml')) {
    reply.type('application/xml')
    return `<data>${JSON.stringify(data)}</data>`
  }

  reply.type('application/json')
  return data
})
```

## Validation After Parsing

Schemas validate after content type parsing:

```typescript
app.post('/users', {
  schema: {
    body: Type.Object({
      name: Type.String({ minLength: 1 }),
      email: Type.String({ format: 'email' }),
    }),
  },
}, async (request) => {
  // Body is parsed AND validated
  return request.body
})
```

## Content Type with Parameters

```typescript
app.addContentTypeParser(
  'application/json; charset=utf-8',
  { parseAs: 'string' },
  async (request, body) => JSON.parse(body),
)
```

## Key Rules

- Fastify only parses `application/json` and `text/plain` by default
- Use `@fastify/formbody` for URL-encoded form data
- Use `@fastify/multipart` for file uploads (see file-uploads.md)
- Custom parsers can be async or callback-based
- Always set `bodyLimit` appropriately
- Schema validation runs AFTER content type parsing
