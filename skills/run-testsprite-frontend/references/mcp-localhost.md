# Localhost-Only MCP Routing

Read only when the frontend target is localhost/private-only or the task explicitly requests TestSprite MCP. Public targets should use pinned CLI 0.4.0.

## Default decision: blocked in a real checkout

`@testsprite/testsprite-mcp@0.0.39` is not a read-only/no-persistence tool. It can persist key/config and application credentials; create `testsprite_tests/`, generated code, logs, reports, and other local state; change `.gitignore`; open a UI/browser and tunnel; mutate TestSprite cloud state; and drive application side effects.

Therefore:

- never launch it in the real repository checkout by default;
- never give it a durable normal user HOME/config directory by default;
- never assume cleanup from older documentation;
- never describe localhost MCP as release proof.

If explicit authorization and a disposable containment boundary cannot both be established, report MCP blocked and retain repository-native evidence only.

## Package and environment facts

Verified package metadata:

- package: `@testsprite/testsprite-mcp@0.0.39`;
- executable: `testsprite-mcp-plugin`;
- Node engine: `>=22`;
- standard package command: `npx -y @testsprite/testsprite-mcp@0.0.39`;
- child credential variable: `API_KEY`, not `TESTSPRITE_API_KEY`;
- child endpoint variable: `API_URL`.

The parent agent may already receive `TESTSPRITE_API_KEY`. Map that existing secret to child `API_KEY` only inside the active runtime's authorized secret-injection/launcher mechanism. Never put the literal key in repository config, MCP JSON, command arguments, screenshots, generated instructions, or transcripts. Do not create a second plaintext secret file merely to translate the variable name.

Do not rely on undocumented environment interpolation syntax. Inspect the active runtime's supported secret mapping and pass only `API_KEY` to the MCP child. If a disposable authenticated child cannot be launched without literal persistence/exposure, report MCP blocked.

## Credential-routing controls

Treat each as a credential destination control:

- inherited CLI `TESTSPRITE_API_URL`;
- CLI `--endpoint-url`;
- MCP child `API_URL`;
- tunnel endpoint/host override.

Reject inherited/custom overrides by default. Authorize only an exact TLS endpoint and matching TestSprite credential environment. Never route production credentials to staging/custom infrastructure. Record expected tunnel origin and callback/return origins before application credentials are introduced.

Application login/project credentials must be bound to the explicitly authorized frontend origin. Do not use credential-bearing target URLs. Do not follow an origin-changing redirect with credentials unless that exact destination is authorized.

## General authorization gate

Before MCP configuration or launch, require explicit scope for:

- TestSprite identity/account and credential endpoint;
- disposable repository copy source revision and destination;
- local dev command, target origin, tunnel/UI/browser behavior;
- TestSprite project/test/plan/code/cloud writes and billable runs;
- application account/role/tenant and every browser side effect;
- concurrency and account isolation;
- files/config/`.gitignore` mutations;
- cleanup, rollback/restoration, retention, and deletion timing.

MCP tool discovery is not authorization to invoke a tool. A stale tool name is not authority.

## Required disposable boundary

Use MCP only after explicit authorization in a disposable repository copy with all of these properties:

1. Create an unpredictable parent directory under `umask 077`; set the copy and working directories to mode `0700`.
2. Copy only the required repository revision and required ignored development inputs; do not point MCP at the real checkout.
3. Use an ephemeral `HOME` and `XDG_CONFIG_HOME` inside the disposable parent, both mode `0700`.
4. Set the MCP process working directory to the disposable repository copy.
5. Supply `API_KEY` through the runtime secret mechanism mapped from the already-injected CLI secret.
6. Reject/omit `API_URL` and tunnel overrides unless exact TLS destinations were authorized.
7. Use only synthetic/non-sensitive application credentials bound to the authorized target origin.
8. Assume the server may write credentials/config, app state, `testsprite_tests/`, logs/reports/code, and `.gitignore`, and may open UI/tunnel/browser/cloud resources.
9. Inventory created files and cloud/browser resources without printing sensitive contents.
10. Clean local state, tunnels, UI/browser sessions, cloud resources, and application mutations according to the recorded rollback/retention plan.

Do not retain the disposable HOME/repository as a convenient authenticated cache. Retention requires separate explicit authorization.

## Live tool inventory is syntax authority

Tool names and schemas can differ from stale documentation. After the authorized disposable server connects:

1. Inspect its version, live server status, and advertised tool inventory through the runtime's native MCP UI/command.
2. Use only advertised names and schemas.
3. Treat docs as workflow intent when they conflict with live package 0.0.39.
4. Never fabricate a call from a Portal button/tutorial.
5. Apply the general authorization gate independently to every mutating/billable/browser tool call.

## Contained localhost workflow

1. Read repository policy and map the frontend contract.
2. Establish the disposable 0700 repository/HOME/config/working-directory boundary.
3. Start the repository frontend only through its approved workflow inside that boundary.
4. Confirm target origin, revision, account/role, mutations, concurrency, cleanup, rollback, and retention.
5. Configure package 0.0.39 with child `API_KEY` secret mapping; reject unauthorized `API_URL`/tunnel overrides.
6. Inspect live tools.
7. Generate/reuse plans, then review them with the same plan auditor and authorization rules as CLI plans.
8. Invoke only authorized MCP tools; capture exact run/report identities and local/cloud side effects.
9. Store raw outputs under `umask 077` in unpredictable temporary paths. Do not print raw DOM, screenshots, video, forms, URLs/data, reports, code, or credentials to transcripts.
10. Classify product, plan, generated-code, auth/environment, external-gate, and runner failures separately.
11. Clean every authorized local/cloud/browser/application effect or record the explicit rollback gate.
12. For release, deploy the exact CI-proven artifact publicly and use CLI trigger-then-wait fresh runs.

MCP localhost success is development evidence only.

## Native agent installation is separate

`testsprite agent install --target ...` writes local instructions and can overwrite/add repository guidance. It does not configure MCP. Run it only when explicitly requested and authorized for the disposable or intended repository.

Persistent CLI setup is also separate and uses the pinned CLI command `--profile PROFILE setup --no-agent --from-env`; it persists the inherited key and needs separate authorization.

## Fail-closed report

Report MCP blocked when any of these remains infeasible:

- no disposable repository copy;
- no ephemeral 0700 HOME/config/working directory;
- no safe runtime secret mapping from `TESTSPRITE_API_KEY` to child `API_KEY`;
- unavoidable literal credential storage/config;
- unauthorized endpoint/tunnel routing;
- unclear file/cloud/browser/application mutations;
- no cleanup/rollback path;
- application credentials cannot be bound to one authorized origin.

State which containment/authentication probe failed and continue only with non-MCP evidence.

## Vendor references

- [MCP create tests for new projects](https://docs.testsprite.com/mcp/core/create-tests-new-project)
- [CLI command reference](https://docs.testsprite.com/cli/reference/command-reference)

Package metadata and persistence findings target `@testsprite/testsprite-mcp@0.0.39` as reviewed on 2026-08-03. Re-verify live inventory and side effects before changing versions.
