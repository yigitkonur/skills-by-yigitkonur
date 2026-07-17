# Troubleshooting

Classify combined-run failures from evidence before changing martool, the skill, SSH access, or a deployment.

## Start with the combined report

Inspect the fatal error or failed check:

```bash
node -e '
  const fs = require("node:fs");
  const report = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  console.log(JSON.stringify({
    verdict: report.verdict,
    fatal_error: report.fatal_error,
    selection: report.selection,
    checks: report.checks
  }, null, 2));
' /path/to/combined.json
```

If a check names a raw report, inspect its failed cases rather than relying only on stderr:

```bash
node -e '
  const fs = require("node:fs");
  const report = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  console.log(JSON.stringify((report.cases || []).filter(x => x.status === "fail"), null, 2));
' /path/to/generated-flags.json
```

## Preflight failures

| Failure | Probe | Correct response |
|---|---|---|
| `package.json` is not martool | Inspect the supplied `--repo` path | Point to the checkout root |
| `pnpm build` cannot start | Check `node --version`, `pnpm --version`, and package manager declaration | Install/use the supported toolchain; do not use local Docker as a shortcut |
| Required audit file missing | Compare image/checkout revision with current martool packaging | Use a revision containing the authoritative harnesses |
| SSH cannot start or authenticate | `ssh -o BatchMode=yes HOST true` | Correct host/access outside the runner |
| Long remote run loses SSH transport | Inspect the SSH error and server TCP state; confirm this skill's runner includes server-alive options | Update/reinstall the skill, then rerun the complete matrix; never accept a truncated report |
| No matching container | Query only project/service labels on the authorized host | Correct labels or verify deployment state |
| Multiple matching containers | List matching IDs, names, image IDs, and health | Wait for rollout stability or pass an authorized `--container` |
| Container unhealthy | Read health and bounded service logs | Classify as deployment/runtime failure |

Never print `docker inspect` wholesale while debugging; it can expose environment secrets. Request explicit safe fields with `--format`.

## Invalid or missing JSON

The runner saves non-JSON stdout as `<matrix>-stdout.txt` and records the audit process exit. Common causes include:

- wrong CLI or audit script revision;
- stdout contamination from application logging;
- process termination from memory/time/resource pressure; or
- an audit setup exception before report construction.

Read the saved stdout and `stderr_tail`, then reproduce the exact harness directly on the same target. Do not strip unexpected output merely to make JSON parsing succeed; stdout purity is part of the CLI contract.

## Coverage failures

Full coverage requires manifest-derived plan IDs to reconcile exactly with completed IDs.

| Evidence | Likely layer |
|---|---|
| Missing cases after an early failed baseline | Command setup or baseline contract |
| Unexpected case IDs | Audit planner/report mismatch |
| Duplicate plan/completed IDs | Harness defect or duplicate manifest surface |
| Uncovered platform flags/positionals | Platform planner or filter mismatch |
| `diagnostic-pass` with missing platform cases | Expected for an explicit command filter; not release proof |

Do not set a partial-coverage allowance for a full run. Use `--command` only for diagnosis, fix the demonstrated layer, then rerun without filters.

## Provider-call failure

Any nonzero `provider_calls` or `paid_provider_calls` is a failed safety contract.

1. Preserve the raw platform report.
2. Identify the exact case and argv that reached the loopback counter.
3. Trace why dry-run/read-only/provider routing did not stop the call.
4. Fix the product or audit harness.
5. Rerun the full platform matrix and require zero.

Do not add real credentials, raise a budget, whitelist a call, or reinterpret it as harmless.

## Command filter did not match

`--command` requires the exact `name` published by the selected manifest. Obtain names from the target, not from memory:

```bash
node dist/cli/main.js usage --json > /tmp/martool-usage.json
node -e '
  const fs = require("node:fs");
  const x = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  console.log([...new Set([
    ...x.commands.map(c => c.name),
    ...x.platform_commands.map(c => c.name)
  ])].sort().join("\n"));
' /tmp/martool-usage.json
```

For Coolify, execute the same usage command inside the pinned container instead of assuming the local checkout matches.

## Deployment drift

If the post-run container/image differs from the pre-run pin:

- keep raw reports as diagnostic artifacts;
- mark the combined run failed;
- wait for or establish a stable deployment through the authorized deployment workflow; and
- rerun both matrices against one new pinned ID.

Never combine the first matrix from the old image with the second matrix from the new image.

## Runner defects

Suspect the skill runner when martool's raw report is independently valid but the combined validator rejects it. Reproduce with the bundled unit suite:

```bash
node --test "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.test.mjs"
```

Compare the current martool report schema with `validateGeneratedReport()` or `validatePlatformReport()`. Update the runner only for a verified schema change; keep the zero-failure, exact-coverage, zero-provider, and target-pinning invariants intact.
