# Security Headers with @fastify/helmet

## Overview

`@fastify/helmet` sets HTTP security headers to protect against common web vulnerabilities
like XSS, clickjacking, and MIME-type sniffing. It wraps the `helmet` library for Fastify.

## Installation

```bash
npm install @fastify/helmet
```

## Basic Setup

```typescript
import Fastify from 'fastify'
import helmet from '@fastify/helmet'

const app = Fastify()

// Apply default security headers to all responses
await app.register(helmet)
```

Default headers set:

```
Content-Security-Policy: default-src 'self';...
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
X-Content-Type-Options: nosniff
X-DNS-Prefetch-Control: off
X-Download-Options: noopen
X-Frame-Options: SAMEORIGIN
X-Permitted-Cross-Domain-Policies: none
X-XSS-Protection: 0
Strict-Transport-Security: max-age=15552000; includeSubDomains
```

## Production Configuration

```typescript
await app.register(helmet, {
  // Content Security Policy
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'", 'https://api.example.com'],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      frameSrc: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"]
    }
  },

  // Force HTTPS
  strictTransportSecurity: {
    maxAge: 31536000,        // 1 year
    includeSubDomains: true,
    preload: true
  },

  // Prevent iframe embedding
  frameguard: { action: 'deny' },

  // Prevent MIME-type sniffing
  noSniff: true,

  // Hide X-Powered-By header
  hidePoweredBy: true,

  // Referrer policy
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' }
})
```

## API-Only Configuration

For pure JSON APIs (no HTML serving), relax CSP but keep other protections:

```typescript
await app.register(helmet, {
  // Disable CSP for APIs that don't serve HTML
  contentSecurityPolicy: false,

  // Keep cross-origin policies
  crossOriginEmbedderPolicy: false, // Needed if API serves to browsers
  crossOriginResourcePolicy: { policy: 'cross-origin' }, // Allow cross-origin fetches

  // Essential security headers
  strictTransportSecurity: {
    maxAge: 31536000,
    includeSubDomains: true
  },
  noSniff: true,
  hidePoweredBy: true,
  frameguard: { action: 'deny' },
  referrerPolicy: { policy: 'no-referrer' }
})
```

## Helmet with Swagger UI

Swagger UI needs inline scripts and styles. Adjust CSP when serving docs:

```typescript
// Register helmet globally with strict CSP
await app.register(helmet, {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'"]
    }
  }
})

// For swagger-ui routes, use a relaxed CSP
await app.register(async (instance) => {
  // Override helmet for this encapsulated context
  instance.addHook('onRequest', async (request, reply) => {
    reply.header(
      'Content-Security-Policy',
      "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    )
  })

  await instance.register(swaggerUi, { routePrefix: '/docs' })
})
```

## Per-Route Header Override

```typescript
app.get('/embed', {
  config: {
    // Allow this specific route to be embedded in iframes
    helmet: {
      frameguard: false
    }
  }
}, async () => {
  return { embeddable: true }
})
```

## Combining Helmet with Other Security Measures

```typescript
import helmet from '@fastify/helmet'
import cors from '@fastify/cors'
import rateLimit from '@fastify/rate-limit'

// Register in this order:
// 1. Helmet (security headers)
await app.register(helmet, { /* ... */ })

// 2. CORS (origin control)
await app.register(cors, { /* ... */ })

// 3. Rate limiting (abuse prevention)
await app.register(rateLimit, { /* ... */ })

// 4. Then register routes
await app.register(routes)
```

## Removing the X-Powered-By Header

Fastify does not send X-Powered-By by default (unlike Express). But helmet's
`hidePoweredBy` ensures it is removed if any other middleware adds it:

```typescript
await app.register(helmet, {
  hidePoweredBy: true
})
```

## Key Points

- Register helmet BEFORE other plugins for consistent header application
- For JSON APIs, disable `contentSecurityPolicy` (not applicable)
- Relax CSP for swagger-ui routes (needs inline scripts/styles)
- Always enable `strictTransportSecurity` in production
- Set `frameguard: { action: 'deny' }` unless you need iframe embedding
- Combine with CORS and rate limiting for comprehensive protection
- Test security headers with securityheaders.com or Mozilla Observatory
