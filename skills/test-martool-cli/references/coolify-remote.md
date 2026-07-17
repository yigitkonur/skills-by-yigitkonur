# Coolify remote verification

Run the authoritative audits inside an existing Coolify martool container over SSH while keeping discovery, evidence, and safety explicit.

## Value boundary

Remote mode proves the behavior of the built CLI and audit scripts inside one deployed image. It does not deploy that image, prove the checkout matches it, exercise paid providers, or authorize any production mutation.

Use `deploy-coolify-cloud` separately when the requested outcome includes deployment or updating Coolify state. After deployment, return here for runtime proof.

## Discovery contract

The default labels are:

```text
coolify.projectName=martool
com.docker.compose.service=martool
```

The runner asks the remote Docker daemon for running containers matching both labels. Discovery must yield exactly one container. It then reads only these safe inspect fields:

- container ID and name;
- configured image reference;
- immutable image ID;
- running state; and
- health status.

It never reads or prints `.Config.Env`, mounted secret contents, the remote `.env`, Docker credentials, or SSH configuration.

Override label defaults only when the deployment demonstrably uses different values:

```bash
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target coolify \
  --ssh-host hetzner \
  --coolify-project martool-staging \
  --service martool
```

Use `--container` when a specific ID or name is already the authorized target:

```bash
--container martool-project-123456
```

The override still requires a running, healthy container.

## Remote command safety

The local Node runner starts `ssh` with argument arrays. It enables bounded SSH server-alive probes because a full matrix can outlive an idle NAT or firewall timeout. It sends a fixed POSIX shell program over stdin and validates host, label, service, and container identifiers before use. User values do not become shell source.

Remote operations are read-only with respect to the deployment:

- `docker ps` for label discovery;
- `docker inspect` for safe target identity;
- `docker exec` for version, usage, and audit processes.

The audit harnesses create and remove their own temporary HOME, XDG, workspace, fixture, and output roots inside the container. They do not alter the long-running service configuration or restart its process.

## No local Docker

Coolify mode calls only the local `ssh` binary. Every Docker command executes on the SSH host. Do not start Docker Desktop, a local Compose stack, or a local martool container as a substitute.

The combined report records:

```json
{
  "safety": {
    "local_docker_used": false
  }
}
```

That field states runner behavior; the remote target block and raw reports provide the actual runtime evidence.

## Image and container pinning

Before the matrices, record the discovered container and image IDs. Run all commands against the container ID rather than its generated name. After both matrices, inspect that same ID again and require:

- identical container ID;
- identical immutable image ID;
- running state; and
- healthy status.

If Coolify redeploys during the run, discard the combined verdict and rerun against the new stable container. Do not merge cases from two images.

The CLI's own version output may report `git_commit: unknown` when build metadata is unavailable. In that case, the configured image tag and immutable image ID are the deployment proof. Do not invent a source SHA from a local checkout.

## Full remote run

```bash
report_dir=/tmp/martool-cli-coolify-$(date -u +%Y%m%dT%H%M%SZ)
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target coolify \
  --ssh-host hetzner \
  --report-dir "$report_dir"
```

Read the final compact object from stdout or:

```bash
node -e '
  const fs = require("node:fs");
  const report = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  console.log(report.verdict, report.target.container.image_id);
' "$report_dir/combined.json"
```

Then inspect each executed check's coverage, failures, provider counters, and raw report hash.

## Operational failures

Treat these as target or access failures, not CLI passes:

| Signal | Classification |
|---|---|
| SSH authentication/connectivity failure | Access or host availability |
| No matching container | Wrong labels, stopped deployment, or wrong host |
| Multiple matching containers | Ambiguous rollout or label scope |
| Container unhealthy | Deployment/runtime gate |
| Missing audit scripts | Image packaging/version mismatch |
| Container/image changed during run | Deployment drift |

Read [troubleshooting](troubleshooting.md) for bounded probes. Do not repair production unless the user separately authorized that outcome.
