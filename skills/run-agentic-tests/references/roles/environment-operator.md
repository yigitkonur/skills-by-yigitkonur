# Environment operator

Prepare and own the assigned dev runtime and tool access. Wave 0 establishes
readiness; it does not award acceptance-case PASS or perform the executor's run.

## Read / write

Read the assigned task/target, project startup instructions, relevant case setup,
resource claims, and [Runtimes and isolation](../runtimes-and-isolation.md).
Read [Cloudflare tunnels](../cloudflare-tunnels.md) only for remote HTTP access.

Write the assigned environment draft, setup/readiness artifacts, owned logs and
runtime configuration. Use [environment.yaml](../../assets/templates/environment.yaml).
The helper publishes the canonical environment record. Preserve source/config
belonging to an active test generation and unrelated processes/credentials.
Use the task's `companion_paths.setup` for setup notes and its ignored
`companion_paths.configuration` for any required local `.env` values. Read the
CLI-owned log paths shown in the handoff; do not precreate a target generation
directory or replace its logs with a success summary.

## Procedure

1. Identify exact source revision/provider/worktree, argv/cwd, variable names,
   and tool/client locations. Declare source/config paths for CLI attestation;
   resolve prerequisites without printing secrets.
2. Allocate independent data namespaces/accounts/sessions/device and port leases,
   or declare shared read/write claims. Prove fixture/reset access.
3. Select the actual adapter: HTTP dev server, CLI executable, MCP stdio/HTTP,
   or native mobile. Establish the available client/driver and its relevant
   protocol capabilities. A responsive browser is not a native device.
4. Complete the assigned draft with its `record_id`, `task_id`, `actor_id`, and
   `target_id`. Set the declared readiness marker and bounded timeout. Launch:

   ```bash
   node "$AT_CLI" runtime start --campaign "$CAMPAIGN" --file "$DRAFT"
   ```

5. Inspect the actual receipt and canonical environment. Prove application
   access from the actual executor client, including needed auth/dependencies.
   For MCP stdio, use a client-owned tool session with real initialization/tool
   access and the concrete MCPC example in Runtimes and isolation. A raw
   startup marker cannot prove attachment. For remote HTTP, finish all tunnel
   readiness layers.
6. Hand off exact target identity, endpoint/tool attachment, fixture/reset steps,
   resource leases, owned lifecycle handles, and remaining capability limitations.

## Done / blocked / submit

The environment role uses `runtime start`, not a second `submit` of the same
canonical record. Its assigned output identity must match the task. Read the
receipt and report canonical path/status; the orchestrator closes the task only
after actual worker termination. `FAILED` can be an honest completed operator
result; it cannot make dependent execution ready.

On failure, preserve logs and report the failed phase plus reason: unavailable
tool/credential, runtime start, source selection, transport, or unsupported tunnel
protocol. Do not use a generic always-success marker. If no process can be
started, report the blocker and leave only truthful artifacts for controller
recovery. Restart/fix means a new target generation, never overwrite the old one.

Read retry context before attempting recovery. State what changed, the new
readiness hypothesis, what not to repeat, and whether leases must be reacquired.
Stop only verified owned unused resources; retain final inspection runtimes.
