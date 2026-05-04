# Apps: deploy and invoke

A Kernel **App** is a deployed codebase exposing one or more **Actions**. Each **Invocation** runs an action with a `payload`, and the action runs on a unikernel co-located with its browser VMs — no CDP latency.

## When to deploy an app vs embed the SDK

| Deploy a Kernel App when… | Embed `@onkernel/sdk` directly when… |
|---|---|
| You run long browser work (minutes to hours) | The flow is fast (sub-100s) and lives inside an HTTP request |
| You need per-invocation isolation | One service handles many sessions concurrently |
| You want zero CDP latency to the browser | You're already paying the round-trip for other reasons |
| You want logs/replays/lifecycle tied to the invocation | You manage logs/lifecycle in your own service |

You can mix: have your service embed `@onkernel/sdk` and `invocations.create` to fire long-running work into a deployed app.

## Develop locally

```ts
// app.ts
import Kernel, { type KernelContext } from '@onkernel/sdk';

const kernel = new Kernel();
const app = kernel.app('my-agent');

app.action(
  'analyze',
  async (ctx: KernelContext, payload: { url: string }) => {
    const session = await kernel.browsers.create({
      stealth: true,
      invocation_id: ctx.invocation_id,
    });
    try {
      // …work…
      return { ok: true, title: 'example' };
    } finally {
      await kernel.browsers.deleteByID(session.session_id);
    }
  }
);
```

`package.json` for a TS app:

```json
{
  "name": "my-agent",
  "type": "module",
  "dependencies": { "@onkernel/sdk": "^…" }
}
```

`"type": "module"` is required for `kernel deploy` to recognize TS/ESM apps.

## Deploy

CLI is the canonical deploy path:

```bash
# Local source
kernel deploy app.ts \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env-file .env \
  --version 1.0.0 \
  --force

# From GitHub
kernel deploy github \
  --url https://github.com/owner/repo \
  --ref main \
  --entrypoint app.ts
```

Programmatic equivalent via the SDK:

```ts
import fs from 'node:fs';

const deployment = await kernel.deployments.create({
  file: fs.createReadStream('./build.zip'),
  entrypoint_rel_path: 'app.ts',
  env_vars: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY!,
  },
  region: 'aws.us-east-1a',         // currently the only region
  version: '1.0.0',
  force: false,                      // overwrite same version
});

// Stream the deployment build:
for await (const evt of await kernel.deployments.follow(deployment.id)) {
  // evt.event: 'log' | 'deployment_state' | 'app_version_summary' | 'error' | 'heartbeat'
}
```

## Invoke (sync vs async)

```ts
// SYNC — blocks up to ~100s (HTTP request lifetime).
// Use for fast actions only.
const inv = await kernel.invocations.create({
  app_name: 'my-agent',
  action_name: 'analyze',
  version: '1.0.0',
  payload: JSON.stringify({ url: 'https://example.com' }),
});
console.log(inv.status); // 'queued' | 'running' | 'succeeded' | 'failed'
const output = JSON.parse(inv.output ?? 'null');
```

```ts
// ASYNC — returns 202 immediately; status is 'queued'.
// Required for any action that may exceed 100s.
const async_inv = await kernel.invocations.create({
  app_name: 'my-agent',
  action_name: 'analyze',
  version: '1.0.0',
  async: true,
  async_timeout_seconds: 1800, // default 900 (15 min); max 3600 (1 hour)
  payload: JSON.stringify({ url: 'https://example.com' }),
});
```

`payload` is a string. Stringify on the way in, parse on the way out. Max **4.5 MB** encoded — bigger artifacts go through `kernel.browsers.fs.*` (write inside the action, read from outside via the same `session_id`).

## Stream status and logs

The same SSE stream emits four event kinds:

```ts
const events = await kernel.invocations.follow(async_inv.id);

for await (const evt of events) {
  switch (evt.event) {
    case 'log':
      console.log(`[${evt.timestamp}] ${evt.level} ${evt.message}`);
      break;

    case 'invocation_state': {
      const inv = evt.invocation;
      if (inv.status === 'succeeded') {
        const output = JSON.parse(inv.output ?? 'null');
        console.log('done:', output);
        return output;
      }
      if (inv.status === 'failed') {
        throw new Error(inv.status_reason ?? 'invocation failed');
      }
      break;
    }

    case 'error':
      throw new Error(evt.error.message);

    case 'heartbeat':
      // keepalive — no action needed
      break;
  }
}
```

`deployments.follow` uses the same shape but emits `deployment_state` instead of `invocation_state`, and adds an `app_version_summary` event when the build completes — handle five event kinds, not four.

## Stop

```ts
// Mark as failed and reap any browsers tagged with this invocation_id
await kernel.invocations.update(async_inv.id, { status: 'failed' });

// Or just reap browsers without changing status:
await kernel.invocations.deleteBrowsers(async_inv.id);
```

If your action's `browsers.create` calls did **not** set `invocation_id`, those browsers are not reaped on stop — they live until their own `timeout_seconds`.

## Status by polling

If SSE is inconvenient (e.g. inside a serverless function with short max duration):

```ts
const inv = await kernel.invocations.retrieve(async_inv.id);
console.log(inv.status, inv.status_reason);
```

## Apps surface

Apps are a **read view** of deployed code — the SDK exposes `apps.list` and that's it:

```ts
for await (const app of kernel.apps.list({ limit: 50 })) {
  // Field is `app_name` (not `name`); apps also expose `id`, `version`, `region`, `actions`, `env_vars`, `deployment`.
  console.log(app.app_name);
}
```

There is no `apps.create` — creation happens via `deployments.create`.

## Secrets and env

Two paths:

1. **Build-time env** — `--env`/`--env-file` at deploy or `env_vars` in `deployments.create`. Available in the action as `process.env.X`.
2. **Per-invocation payload** — pass end-user keys in `payload`. Don't bake them into the deployment.

There is no separate "secret store" SDK surface. `kernel.credentials.*` exists but it's the Managed Auth credential store (used by `auth.connections.*`), not a generic env vault.

## Logs

Each invocation emits structured log events. Stream live with `invocations.follow` or fetch them after the fact:

```ts
const inv = await kernel.invocations.retrieve(id);
// inv.logs is undefined for ongoing invocations; consume `follow` for live tails.
```

For VM-level logs (everything inside the browser VM, not just your action's `console.log`), use `kernel.browsers.logs.stream(session_id)`.

## Where to look next

- Full end-to-end deploy + invoke walk-through: `references/examples/deploy-and-invoke-app.md`
- Why your invocation hangs at exactly 100s: `references/troubleshooting/pitfalls.md`
- Pulling an invocation's output as a file (>4.5 MB): `references/troubleshooting/files-and-replays.md`
