# Apps: deploy and invoke

A Kernel **App** is a deployed codebase exposing one or more **Actions**. Each **Invocation** runs an action with a `payload`, load-balanced across cluster hosts while staying co-located with its browser VMs (no CDP round-trip).

Source note: checked against `@onkernel/sdk@0.123.0` (`deployments.ts`, `invocations.ts`, `apps.ts`, `core/app-framework.ts`), `@onkernel/cli@0.47.0` (`cmd/deploy.go`, `cmd/invoke.go`) and the docs pages `apps/*`. Payload-size docs conflict; see "Payload size".

## When to deploy an app vs embed the SDK

| Deploy a Kernel App when… | Embed `@onkernel/sdk` directly when… |
|---|---|
| You run long browser work (minutes to hours) | The flow is fast (well under 60 s) and lives inside an HTTP request |
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
  async (ctx: KernelContext, payload?: { url: string }) => {
    if (!payload?.url) throw new Error('payload.url is required');
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

Handlers must accept at least the context parameter (`(ctx) => …` is fine; a zero-argument handler throws "Action handlers must accept at least the context parameter"). `KernelContext` is `{ invocation_id: string }`. Whatever the handler returns is JSON-serialised into the invocation `output`.

## Deploy prerequisites

`kernel deploy <entrypoint>` zips **the entrypoint's directory** (honouring `.gitignore`, but including hidden files such as `.env` unless ignored) and sends the file name as `entrypoint_rel_path`. That directory must therefore be the project root:

```
project-root/
├─ .gitignore          # exclude node_modules (and .env)
├─ app.ts              # entrypoint, next to package.json
├─ package.json        # "type": "module" for TS/ESM apps
├─ tsconfig.json       # if TypeScript
└─ package-lock.json   # one of: bun.lock | package-lock.json | pnpm-lock.yaml
```

- Python apps need `pyproject.toml` next to the entrypoint.
- A 500 on deploy usually means a wrong entrypoint file name or extension.
- The docs tree shows an entrypoint "in a subdirectory, e.g. src/my_app.ts"; the CLI does not do that (`kernel deploy src/app.ts` uploads only `src/`). To deploy a nested entrypoint, call `deployments.create({ file: <zip of the project root>, entrypoint_rel_path: 'src/app.ts' })`.

## Deploy

```bash
# Local source
kernel deploy app.ts \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env-file .env \
  --version 1.0.0 \
  --force

# From GitHub (private repos: --github-token; the docs also mention GITHUB_TOKEN, but CLI 0.47.0 only reads the flag)
kernel deploy github \
  --url https://github.com/owner/repo \
  --ref main \
  --entrypoint app.ts \
  [--path services/agent]
```

`--version` defaults to `latest`. `--force` overwrites an existing version with the same label; without it a duplicate version fails. Programmatic equivalent (every `DeploymentCreateParams` field is optional; `file` and `source` are alternatives):

```ts
import fs from 'node:fs';
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

async function deployZip() {
  return kernel.deployments.create(
    {
      file: fs.createReadStream('./build.zip'),
      entrypoint_rel_path: 'app.ts',
      env_vars: { OPENAI_API_KEY: process.env.OPENAI_API_KEY! },
      region: 'aws.us-east-1a', // currently the only region
      version: '1.0.0',
      force: true, // overwrite an existing version
    },
    { maxRetries: 0, timeout: 120_000 }, // multipart upload: do not auto-retry
  );
}

async function deployGithub() {
  // `source.type`, `url`, `ref` (branch/tag/SHA) and `entrypoint` are required inside `source`.
  return kernel.deployments.create({
    source: {
      type: 'github',
      url: 'https://github.com/owner/repo',
      ref: 'main',
      entrypoint: 'app.ts',
      // path: 'services/agent',                      // monorepo subdir; omit for repo root
      // auth: { method: 'github_token', token: '…' }, // private repos
    },
    env_vars: { OPENAI_API_KEY: process.env.OPENAI_API_KEY! },
    version: '1.0.0',
    force: true,
  });
}
```

### Deployment status

```ts
const dep = await kernel.deployments.retrieve(deploymentId);
// dep.status: 'queued' | 'in_progress' | 'running' | 'failed' | 'stopped'; dep.status_reason?

for await (const d of kernel.deployments.list({ app_name: 'my-agent', app_version: '1.0.0' })) {
  // app_version requires app_name
}

await kernel.deployments.delete(deploymentId); // stops a running deployment and marks it for deletion
```

Stream a build:

```ts
for await (const evt of await kernel.deployments.follow(deploymentId)) {
  // evt.event: 'log' | 'deployment_state' | 'app_version_summary' | 'error' | 'sse_heartbeat'
}
```

`env_vars` values are returned as empty strings to API-key callers; only dashboard sessions see them.

## Identifiers to keep straight

| Identifier | Comes from | Use |
|---|---|---|
| `deployment.id` | `kernel deploy` / `deployments.create` | Build/deploy event; deployment logs and state |
| `app_name` + `version` | `kernel.app('name')` and deploy version (`latest` if omitted) | Stable target for invocations |
| `action_name` | `app.action('name', fn)` | Function entry point within the app |
| `invocation.id` | `invocations.create` / `kernel invoke` | One execution; status, logs/events, browser cleanup by `invocation_id` |

## Invoke (sync vs async)

Sync vs async is chosen **per request** (`async` flag); the same deployed app serves both, no redeploy.

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

// SYNC: one HTTP request, docs say it times out after 100 s. The SDK's default 60 s
// request timeout and 2 retries would abort and re-send it, so override both.
async function syncInvoke() {
  const inv = await kernel.invocations.create(
    {
      app_name: 'my-agent',
      action_name: 'analyze',
      version: '1.0.0', // required by the SDK type; 'latest' is also accepted (CLI/MCP default)
      payload: JSON.stringify({ url: 'https://example.com' }),
    },
    { timeout: 110_000, maxRetries: 0 },
  );
  console.log(inv.status); // 'queued' | 'running' | 'succeeded' | 'failed'
  return JSON.parse(inv.output ?? 'null');
}

// ASYNC: returns 202 immediately with status 'queued'. Use for anything that may exceed ~50 s.
async function asyncInvoke() {
  return kernel.invocations.create(
    {
      app_name: 'my-agent',
      action_name: 'analyze',
      version: '1.0.0',
      async: true,
      async_timeout_seconds: 1800, // 10-3600, default 900 (15 min)
      payload: JSON.stringify({ url: 'https://example.com' }),
    },
    { maxRetries: 0 }, // a retried create starts a second (billed) invocation
  );
}
```

`payload` is a string: stringify on the way in, parse on the way out. `invocations.create` returns `{ id, action_name, status, output?, status_reason? }`. Exceeding the project's invocation concurrency returns 429 immediately (`Kernel.RateLimitError`). Invocation compute is billed per second of execution, separately from the browsers it creates; failed and cancelled runs still bill.

### Payload size

Docs disagree and nothing in the SDK or CLI enforces a limit: `apps/develop` and the CLI `--payload` row say **64 KB**, `apps/invoke` says stringified JSON up to **4.5 MB**. Treat 64 KB as the safe limit. Send multi-MB screenshots, HTML dumps, archives and traces through `kernel.browsers.fs.*` or your own object storage and pass a small JSON pointer.

## List and inspect invocations

```ts
for await (const inv of kernel.invocations.list({ app_name: 'my-agent', status: 'running' })) {
  // also: action_name, deployment_id, version, query, since ('5m' or RFC timestamp)
}
const inv = await kernel.invocations.retrieve(invocationId);
// { id, action_name, app_name, version, started_at, finished_at?, status, status_reason?, output?, payload? }
```

## Stream status and logs

```ts
async function follow(invocationId: string) {
  const events = await kernel.invocations.follow(invocationId, { since: '5m' });

  for await (const evt of events) {
    switch (evt.event) {
      case 'log':
        console.log(`[${evt.timestamp}] ${evt.message}`); // lines over 64 KiB are truncated
        break;

      case 'invocation_state': {
        const inv = evt.invocation;
        if (inv.status === 'succeeded') return JSON.parse(inv.output ?? 'null');
        if (inv.status === 'failed') throw new Error(inv.status_reason ?? 'invocation failed');
        break;
      }

      case 'error':
        throw new Error(evt.error.message);

      case 'sse_heartbeat':
        break; // keepalive
    }
  }
  throw new Error('stream ended without a terminal state');
}
```

`deployments.follow` has the same shape but emits `deployment_state` instead of `invocation_state` and adds `app_version_summary` (five kinds, not four). The stream ends when the invocation reaches a terminal state.

## Stop

```ts
// Mark as failed (optionally with output) and destroy browsers created with this invocation_id
await kernel.invocations.update(invocationId, {
  status: 'failed',
  output: JSON.stringify({ error: 'cancelled by caller' }),
});

// Or only reap browsers (no status change); list them first with listBrowsers
const { browsers } = await kernel.invocations.listBrowsers(invocationId);
await kernel.invocations.deleteBrowsers(invocationId);
```

`update` accepts `status: 'succeeded' | 'failed'`. Browsers created without `invocation_id` are not reaped; they live until their own `timeout_seconds`.

## Status by polling

```ts
const inv = await kernel.invocations.retrieve(invocationId);
console.log(inv.status, inv.status_reason);
```

## CLI vs SDK invocation behavior

- SDK `kernel.invocations.create({...})` is **synchronous** unless `async: true`.
- CLI `kernel invoke <app> <action>` submits an **async** invocation, then follows the SSE stream, printing logs and the final result, and blocks until the run ends. Ctrl+C marks the invocation failed and deletes its browsers.
- CLI `kernel invoke --sync` (`-s`) is one HTTP POST that times out after **60 s**; no log stream. Use it only for short actions.
- CLI flags: `--version/-v` (default `latest`), `--payload/-p`, `--payload-file/-f` (`-` = stdin), `--async-timeout` (10-3600), `--since`, `--output json` (JSONL events). Docs page `reference/cli/apps` says the CLI "returns immediately after the invocation is queued"; the CLI source and the other docs pages (logs "stream automatically") say it follows.
- The CLI sets `maxRetries: 0` on invoke and deploy; copy that in SDK code.

## Apps surface

Apps are a **read view** of deployed code; the SDK exposes `apps.list` only (`app_name`, `version`, `query` filters):

```ts
for await (const app of kernel.apps.list({ app_name: 'my-agent', limit: 50 })) {
  // Fields: id, app_name, version, region, deployment (id), env_vars (values redacted),
  // actions: [{ name, input_schema?, output_schema? }]  (JSON Schema draft-07, null if not derivable)
  console.log(app.app_name, app.version, app.actions.map((a) => a.name));
}
```

There is no `apps.create`; creation happens through `deployments.create`.

## Secrets and env

1. **Deploy-time env**: `--env`/`--env-file` or `env_vars` in `deployments.create`; read with `process.env.X` in the action.
2. **Per-invocation payload**: pass end-user keys in `payload` (encrypt them in your app); do not bake them into the deployment.

`KERNEL_API_KEY` and `ENTRYPOINT_RELPATH` are **reserved**: Kernel overrides any value you pass (the CLI prints a warning). `KERNEL_API_KEY` inside an action is a per-deployment key minted on each deploy, so a bare `new Kernel()` works. To call Kernel with a longer-lived org/project key, use another name: `new Kernel({ apiKey: process.env.MY_KERNEL_API_KEY })`. A superseded deployment's key stays valid until its in-flight invocations finish.

There is no generic secret-store SDK surface. `kernel.credentials.*` is the Managed Auth credential store.

## Logs

Invocation logs are delivered as a stream. `invocations.retrieve(id)` has no `logs` field, and there is no "fetch logs after the fact" call; do not build a collector on polling `retrieve`.

```ts
// `since` takes an RFC timestamp or a duration like '5m'
for await (const evt of await kernel.invocations.follow(invocationId, { since: '5m' })) {
  if (evt.event === 'log') console.log(`[${evt.timestamp}] ${evt.message}`);
}
```

CLI: `kernel logs <app> [--invocation/-i <id>] [--follow] [--since 5m]` (without `--follow` it stops after ~3 s idle), `kernel deploy logs <deployment_id> --follow`.

For VM-level logs (everything inside the browser VM), use `kernel.browsers.logs.stream(session_id, { source: 'supervisor', follow: true })` or `{ source: 'path', path: '/var/log/…', follow: true }`. `source` is required.

## Where to look next

- Full end-to-end deploy + invoke walk-through: `references/examples/deploy-and-invoke-app.md`
- Multi-provider web search and content extraction: `references/guides/search.md`
- Why your invocation hangs at exactly 100s: `references/troubleshooting/pitfalls.md`
- Pulling large invocation artifacts as files: `references/troubleshooting/files-and-replays.md`
