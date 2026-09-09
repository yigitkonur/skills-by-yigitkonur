# AsyncLocalStorage Context Propagation

How to bind request IDs, tenant IDs, and operational metadata to asynchronous call trees without parameter threading.

## The Problem with Parameter Passing

In asynchronous architectures (Fastify, Express, Next.js, worker pipelines), passing `requestId`, `user`, and `tenant` through every service, repository, and utility function creates brittle code and function signature bloat.

`AsyncLocalStorage` creates an ambient, asynchronous context that automatically travels across `await` boundaries, callbacks, and microtasks.

## 1. Defining the Context Store (`src/core/context.ts`)

```typescript
import { AsyncLocalStorage } from 'node:async_hooks';

export interface RequestContext {
  requestId?: string;
  runId?: string;
  tenantId?: string;
  userId?: string;
  site?: string;
  driver?: string;
  module?: string;
}

const storage = new AsyncLocalStorage<RequestContext>();

export function withContext<R>(ctx: RequestContext, fn: () => R): R {
  const parent = storage.getStore() || {};
  return storage.run({ ...parent, ...ctx }, fn);
}

export function currentContext(): RequestContext {
  return storage.getStore() || {};
}
```

## 2. Binding Sentry Scopes Automatically

Create an adapter that automatically pulls from `currentContext()` whenever an error is captured or span is created:

```typescript
import * as Sentry from '@sentry/node';
import { currentContext } from './context.js';

export function captureExceptionWithContext(error: unknown, extra?: Record<string, any>): string {
  const ctx = currentContext();

  return Sentry.withScope((scope) => {
    if (ctx.requestId) scope.setTag('requestId', ctx.requestId);
    if (ctx.runId) scope.setTag('runId', ctx.runId);
    if (ctx.tenantId) scope.setTag('tenantId', ctx.tenantId);
    if (ctx.site) scope.setTag('site', ctx.site);
    if (ctx.driver) scope.setTag('driver', ctx.driver);
    if (ctx.module) scope.setTag('module', ctx.module);

    if (ctx.userId) {
      scope.setUser({ id: ctx.userId });
    }

    if (extra) {
      scope.setExtras(extra);
    }

    return Sentry.captureException(error);
  });
}
```

## 3. Fastify & HTTP Server Middleware Integration

```typescript
fastify.addHook('onRequest', (request, reply, done) => {
  const requestId = (request.headers['x-request-id'] as string) || crypto.randomUUID();
  reply.header('x-request-id', requestId);

  withContext({ requestId }, () => {
    done();
  });
});
```

Every database query, outgoing HTTP call, or caught exception within this request lifecycle will inherit `requestId` automatically without passing it as an argument.
