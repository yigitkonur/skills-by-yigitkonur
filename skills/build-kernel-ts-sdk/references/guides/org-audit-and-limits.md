# Org, audit logs, spending caps, projects, API keys and limits

Organization-level surfaces: what the API exposes, what gates it, and how to call it from `@onkernel/sdk@0.123.0`.

Source note: Verified against Kernel docs (`info/audit-logs`, `info/spending-caps`, `info/projects`, `info/api-keys`, `info/network-access`) and `@onkernel/sdk@0.123.0` types in October 2026.

## Check access before calling

Resolved feature flags and limits are the authority; do not compare plan names.

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();
const ent = await kernel.organization.entitlements.retrieve();
// ent.features.{browser_pools,vaults,managed_auth,profiles,custom_proxies,managed_proxies,
//   proxy_bypass_hosts,credentials,credential_providers,browser_extensions,browser_replays,
//   file_io,gpu,search}.enabled; ent.features.managed_auth.max_connections (null = unlimited)
// ent.limits.{max_concurrent_browsers,max_concurrent_invocations,default_max_concurrent_invocations_per_app,max_vaults}
// ent.plan.{id,effective_id,is_trialing,status}  (active trials resolve to START_UP)
if (!ent.features.browser_pools.enabled) throw new Error('browser pools not enabled for this org');

const lim = await kernel.organization.limits.retrieve();
// lim.max_concurrent_sessions, concurrent_sessions_used / _available (null when unreadable),
// lim.max_auth_connections / auth_connections_used (null max = unlimited),
// lim.max_vaults / vaults_used, lim.min_health_check_interval_seconds,
// lim.default_project_max_concurrent_sessions (null = no org default)
await kernel.organization.limits.update({ default_project_max_concurrent_sessions: 5 });   // 0 removes; cannot exceed the org limit
```

Audit-log search/download and S3 export are not in `entitlements.features`; they are plan-gated (below). The org concurrency limit covers on-demand browsers and pool reservations together, and a per-project default never exceeds it. Most project administration needs an org-wide credential (a project-scoped key may only rename its own project and cannot create, archive or delete projects or change project limits); export destinations and `vaultProviderConfigs` also need an organization-scoped credential.

## Audit logs

Plans: search and download on **Start-Up** and **Enterprise**; continuous S3 export on **Enterprise**. Retention is 1 year. Search returns up to 100 events per page and covers at most 30 days per query; a download window is at most 30 days. Bulk export belongs to download or S3 export, not `list`.

Filters (search and download): `auth_strategy` (e.g. `api_key`, `dashboard`, `oauth`), `service`, `method`, `exclude_method[]`, `search` (path, user id, email, client IP, status), `search_user_id[]` (ORed into free-text). Entry fields: `auth_strategy, client_ip, domain, duration_ms, email, method, path, route, status, timestamp, user_agent, user_id`; downloaded lines add `event_id`.

```ts
for await (const e of kernel.auditLogs.list({
  start: '2026-10-01T00:00:00Z',     // inclusive
  end: '2026-10-02T00:00:00Z',       // exclusive
  exclude_method: ['GET'],
})) {
  console.log(e.timestamp, e.method, e.path, e.status);
}
```

`download(query, destination, options?)` takes any object with `write(chunk: Uint8Array)`, not a path. The SDK verifies each chunk and retries transient transfer failures (`maxTransferRetries`, default 6), does not close the destination, and a failed download leaves a partial file: write to a temp file and rename.

```ts
import { open, rename } from 'node:fs/promises';

const tmp = 'audit-logs.jsonl.gz.part';
const file = await open(tmp, 'w');
try {
  const res = await kernel.auditLogs.download(
    { start: '2026-10-01T00:00:00Z', end: '2026-10-08T00:00:00Z', exclude_method: ['GET'] },
    file,
    { onProgress: (p) => console.log(p.chunks, p.rows) },
  );
  console.log(res.bytesWritten, res.rows);
} finally {
  await file.close();
}
await rename(tmp, 'audit-logs.jsonl.gz');   // only reached after a complete download
```

Docs list the download destination as a file object; the shipped helper requires `write()`.

### Continuous S3 export (Enterprise)

`kernel.auditLogs.exportDestinations` has `create, retrieve, update, list, delete, test` only. There is no `pause` / `resume`: use `update(id, { status })`. (The CLI has `export pause` / `resume` subcommands.) All destination calls need an organization-level credential.

```ts
const dest = await kernel.auditLogs.exportDestinations.create({
  type: 's3',
  format: 'jsonl.gz',
  region: 'us-east-1',
  bucket: 'customer-audit-logs',
  prefix: 'audit-logs',
  role_arn: 'arn:aws:iam::123456789012:role/customer-audit-log-export',
  // kms_key_id: 'arn:aws:kms:...',   // '' on update removes it
});
// dest.status === 'paused'. In AWS: trust policy on role_arn must allow Principal.AWS = dest.kernel_role_arn
// with Condition sts:ExternalId = dest.external_id; identity policy needs s3:PutObject (+ s3:DeleteObject for the
// test probe) on the prefix, and kms:GenerateDataKey when a KMS key is set.

const test = await kernel.auditLogs.exportDestinations.test(dest.id);
if (!test.success) throw new Error(`export test failed at ${test.stage}`);   // assume_role | put_object | complete
await kernel.auditLogs.exportDestinations.update(dest.id, { status: 'active' });
// later: update(dest.id, { status: 'paused' }); delete(dest.id)
```

- Created `paused`; recreating a destination issues a new `external_id` (update the trust policy).
- Delivery starts at activation (no backfill). Events recorded while paused are never exported; pausing does not defer delivery. An upload in progress can finish after a pause or delete.
- Delivery is at-least-once: deduplicate on `event_id`. Each event-time window is held about 10 minutes before commit; a row visible after its window commits may not be delivered.
- Object key: `<prefix>/destination_id=<id>/org_id=<org>/date=<YYYY-MM-DD>/hour=<HH>/<window>-<chunk>.jsonl.gz` (UTC; Hive-partition safe; empty prefix drops the leading segment).
- Monitor with `retrieve` / `list`: `status`, `last_success_at`, `last_error`, `last_error_at`, `consecutive_failures`, `next_attempt_at`. `update` returns 409 if the destination changed concurrently; retry on fresh state.
- CLI: `kernel audit-logs export create --region us-east-1 --bucket B --prefix P --role-arn ARN [--kms-key-id K]` (all four required; no `--name`), then `export test <id>` and `export resume <id>`.

## Spending caps

Dashboard-only (billing page, org admin sets them); there is no SDK or CLI surface for caps. Monthly, evaluated from the first of the month 00:00 UTC; subscription fees are excluded.

| | Organization cap | Project cap |
|---|---|---|
| Counts | Gross usage minus monthly credits | That project's gross usage |
| At 80% | Warning email; work continues | same |
| At 100% | New usage pauses across every project | New usage pauses for that project only |
| Availability | Eligible self-serve orgs (Enterprise limited preview) | Limited preview for all orgs |

At 100% new browser sessions, pool acquires and app invocations return **403** for the capped scope; running sessions and invocations continue to their end; read, delete and non-billable admin calls (projects, limits, API keys) still work. A pool can hold idle capacity but cannot hand out a new browser. Treat a 403 on `browsers.create`, `browserPools.acquire` or `invocations.create` as a possible cap before debugging the code. The cap is an admission guardrail, not a hard ceiling: running work can add usage after the threshold; leave headroom. It resets next month or when an admin raises or removes it. Spending caps bound cost; concurrency limits bound simultaneous browsers.

## Projects

A project is a container for browsers, profiles, credentials, proxies, extensions, deployments and pools. Every org has at least one (`Default`); requests without a project act on the default project.

```ts
const scoped = new Kernel({ projectID: 'proj_abc123' });          // adds X-Kernel-Project-Id to every request
const project = await kernel.projects.create({ name: 'staging' }); // 1-255 chars, no '/' or '%'; unique per org
await kernel.projects.retrieve('staging');                         // id or name (docs call it `get`; the SDK method is `retrieve`)
await kernel.projects.update(project.id, { name: 'production', status: 'archived' });   // 'active' | 'archived'
for await (const p of kernel.projects.list({ name: 'staging' })) console.log(p.id, p.status);
await kernel.projects.limits.update(project.id, { max_concurrent_sessions: 5, max_concurrent_invocations: 10 });   // 0 clears
const pl = await kernel.projects.limits.retrieve(project.id);     // null = no project cap (org limit applies)
await kernel.projects.delete(project.id);
```

- Effective per-project browser cap: explicit override, else the org default, else none; never above the org limit. `max_pooled_sessions` is deprecated (pool browsers count toward `max_concurrent_sessions`; setting it is a 400).
- Delete is a soft delete: 409 `project_not_empty` while resources remain, 409 `last_active_project` for the final project. Orgs without projects get 404 `projects_disabled`; an unknown or archived project is 404 `project_not_found`.
- A project-scoped key with a conflicting `X-Kernel-Project-Id` gets 403. OAuth (CLI login, MCP server) is always org-wide: scope with `--project` / `KERNEL_PROJECT`. The docs accept only a project ID in the header; the client also has a `project` option (name) that sends `X-Kernel-Project`.
- Scope every pool, profile, vault and credential call to the same project as the browser that uses them.

## API keys

```ts
const key = await kernel.apiKeys.create({ name: 'staging-ci', days_to_expire: 30, project_id: 'proj_abc123' });
// key.key is the plaintext, shown once; omit project_id for an org-scoped key; days_to_expire 1-3650 or null = never
for await (const k of kernel.apiKeys.list({ status: 'active', query: 'staging' })) console.log(k.id, k.masked_key, k.project_id);
await kernel.apiKeys.update(key.id, { name: 'staging-ci-2' });
const next = await kernel.apiKeys.rotate(key.id, { days_to_expire: 30, expire_in_days: 7 });   // new plaintext once
await kernel.apiKeys.delete(key.id);   // must be authenticated with a different key (cannot delete itself)
```

- Rotate copies name and project; the old key works for `expire_in_days` (default 7, `0` revokes now; 0-3650). `days_to_expire` must not be shorter than `expire_in_days` (400). Omit `days_to_expire` to reuse the old lifetime.
- A project-scoped key can create or rotate keys only for its own project (404 otherwise). List `status`: `active` (default, includes expired-not-deleted) | `deleted` | `all`; `sort_by`: `created_at | name | expires_at`.
- Each deploy injects a deployment-scoped `KERNEL_API_KEY` (reserved name; a value you set is overridden). Pass a long-lived key under another name for anything that must outlive the deployment.

## Network and account notes

- Allow outbound `api.onkernel.com:443`; `auth.onkernel.com` and `dashboard.onkernel.com:443` for `kernel login`; `*.onkernel.com` and `*.kernel.sh` on **8443** (CDP, BiDi, live view, replays, app connections); `stun.relay.metered.ca:80`, `global.relay.metered.ca:443` (live view media); `kernel-api-prod.s3.us-east-1.amazonaws.com:443` (replay files). Never allow a single hostname copied from `cdp_ws_url`; it changes per session.
- Zero data retention is Enterprise-only, configured per org through Kernel support; it suppresses recordings, live view streams and telemetry.
- Stripe Projects: `stripe projects add kernel/browser:api-access --config '{"name":"production"}'` provisions a project-scoped API key; one plan can be active per Kernel org; copy slugs from `stripe projects services list`.
