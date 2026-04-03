# Response Compression with @fastify/compress

## Overview

`@fastify/compress` adds gzip, deflate, and brotli compression to responses. For JSON APIs
this typically reduces payload size by 70-90%, improving transfer speed significantly.

## Installation

```bash
npm install @fastify/compress
```

## Basic Setup

```typescript
import Fastify from 'fastify'
import compress from '@fastify/compress'

const app = Fastify()

await app.register(compress, {
  // Default: gzip. Brotli is better but slower to compress
  encodings: ['br', 'gzip', 'deflate'],
  // Only compress responses above this size (bytes)
  threshold: 1024,
  // Compression level (1-11 for brotli, 1-9 for gzip)
  // Higher = better ratio, slower
  zlibOptions: { level: 6 },
  brotliOptions: {
    params: {
      // Brotli quality 4 is a good balance of speed/ratio for APIs
      [require('zlib').constants.BROTLI_PARAM_QUALITY]: 4
    }
  }
})
```

## Production Configuration

```typescript
import compress from '@fastify/compress'
import { constants } from 'node:zlib'

await app.register(compress, {
  // Negotiate encoding based on Accept-Encoding header
  encodings: ['br', 'gzip', 'deflate'],

  // Don't compress tiny responses (headers overhead > savings)
  threshold: 1024,

  // Brotli: quality 4 for dynamic content, 11 for static
  brotliOptions: {
    params: {
      [constants.BROTLI_PARAM_MODE]: constants.BROTLI_MODE_TEXT,
      [constants.BROTLI_PARAM_QUALITY]: 4
    }
  },

  // Gzip: level 6 is the default sweet spot
  zlibOptions: { level: 6 },

  // Custom filter: only compress certain content types
  onUnsupportedEncoding: (encoding, request, reply) => {
    reply.code(406)
    return 'Unsupported encoding'
  }
})
```

## Selective Compression

Disable compression for specific routes:

```typescript
import { Type } from '@sinclair/typebox'

// Compress large list responses
app.get('/users', {
  schema: {
    response: { 200: Type.Array(UserSchema) }
  }
}, async () => {
  return users // Will be compressed
})

// Skip compression for small responses
app.get('/health', {
  compress: false  // Disable for this route
}, async () => {
  return { status: 'ok' } // Too small to benefit from compression
})

// Skip for file downloads (already compressed)
app.get('/files/:id', async (request, reply) => {
  reply.compress(false)
  reply.header('Content-Type', 'application/octet-stream')
  return fileStream
})
```

## Compression for Streaming Responses

```typescript
import { Readable } from 'node:stream'

app.get('/stream', async (request, reply) => {
  const stream = new Readable({
    read() {
      // Push data chunks
      this.push(JSON.stringify({ chunk: Date.now() }) + '\n')
    }
  })

  reply.type('application/x-ndjson')
  return reply.send(stream) // Compression applied to stream chunks
})
```

## Content-Type Based Compression

Only compress text-based content types:

```typescript
await app.register(compress, {
  threshold: 1024,
  // Customize which content types to compress
  customTypes: /^(application\/json|text\/.*|application\/javascript)/
})
```

## Compression Performance Impact

```
Uncompressed JSON: 50KB -> 50KB transfer, 0ms compression
Gzip level 6:     50KB ->  8KB transfer, 0.5ms compression
Brotli quality 4: 50KB ->  6KB transfer, 1.0ms compression
Brotli quality 11: 50KB ->  5KB transfer, 50ms compression (too slow for APIs)
```

For dynamic API responses, use brotli quality 4 or gzip level 6. Reserve
high compression levels for static file serving.

## Request Decompression

Handle compressed request bodies:

```typescript
await app.register(compress, {
  // Also decompress incoming requests with Content-Encoding header
  requestEncodings: ['gzip', 'br']
})

// Clients can now send compressed bodies:
// POST /data Content-Encoding: gzip
```

## Key Points

- Register compress early (before routes) for global effect
- Set `threshold` to 1024+ bytes to avoid compressing tiny responses
- Use brotli quality 4 for APIs (good speed/ratio balance)
- Disable compression for health checks, binary files, and SSE streams
- Response compression is automatic based on client `Accept-Encoding` header
- Combine with fast-json-stringify (response schemas) for maximum throughput
- Compression adds CPU overhead -- monitor in production
