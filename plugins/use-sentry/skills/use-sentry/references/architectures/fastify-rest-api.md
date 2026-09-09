# Architecture: Fastify 4 & 5 REST API

How to integrate Sentry into Fastify applications with request context, error boundary handlers, and 4xx vs 5xx error discipline.

## The Fastify Integration Pattern

1. Fastify handles errors inside its custom `setErrorHandler` rather than crashing the Node process.
2. Fastify lifecycle hooks (`onRequest`, `onResponse`) run within an asynchronous context.
3. Client errors (4xx) should be logged as breadcrumbs or warnings, whereas server faults (5xx) must be captured as Sentry exceptions.

## 1. Request Context & Breadcrumb Hook (`request-context.ts`)

```typescript
import type { FastifyPluginAsync } from 'fastify';
import { randomUUID } from 'node:crypto';
import { withContext } from './context.js';
import { addAppBreadcrumb } from './sentry.js';

export const fastifyRequestContextPlugin: FastifyPluginAsync = async (fastify) => {
  fastify.addHook('onRequest', (request, reply, done) => {
    const requestId = (request.headers['x-request-id'] as string) || randomUUID();
    reply.header('x-request-id', requestId);

    addAppBreadcrumb({
      category: 'http.request',
      message: `${request.method} ${request.url}`,
      data: {
        method: request.method,
        url: request.url,
        ip: request.ip,
      },
    });

    withContext({ requestId }, () => {
      done();
    });
  });

  fastify.addHook('onResponse', (request, reply, done) => {
    addAppBreadcrumb({
      category: 'http.response',
      message: `${request.method} ${request.url} -> ${reply.statusCode}`,
      level: reply.statusCode >= 500 ? 'error' : reply.statusCode >= 400 ? 'warning' : 'info',
      data: {
        statusCode: reply.statusCode,
        responseTime: reply.elapsedTime,
      },
    });
    done();
  });
};
```

## 2. Fastify Custom Error Handler (`error-handler.ts`)

```typescript
import type { FastifyError, FastifyReply, FastifyRequest } from 'fastify';
import { captureAppException, addAppBreadcrumb } from './sentry.js';

export function createFastifyErrorHandler() {
  return function errorHandler(error: FastifyError, request: FastifyRequest, reply: FastifyReply) {
    const statusCode = error.statusCode || 500;

    // 4xx errors: User / client mistakes — do NOT treat as Sentry issues
    if (statusCode < 500) {
      addAppBreadcrumb({
        category: 'http.client_error',
        message: `Client error: ${error.message} (${statusCode})`,
        level: 'warning',
        data: { statusCode, code: error.code, url: request.url },
      });

      return reply.status(statusCode).send({
        error: error.name || 'ClientError',
        message: error.message,
        statusCode,
      });
    }

    // 5xx errors: Server faults or unexpected crashes — CAPTURE TO SENTRY
    const eventId = captureAppException(error, {
      url: request.url,
      method: request.method,
      statusCode,
      headers: request.headers,
    });

    reply.status(statusCode).send({
      error: 'InternalServerError',
      message: 'An internal error occurred. Please contact support with the event ID.',
      statusCode,
      eventId,
    });
  };
}
```
