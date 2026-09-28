# Runtime generations and isolation

The environment operator owns setup/lifecycle. Executors use its proven target;
verifiers inspect saved evidence. Use dev runtimes; a production deployment or
production web build is not a campaign prerequisite. Native compilation required
to install/launch an app is allowed.

## Wave 0 readiness contract

1. Declare the actual source provider, revision, and working directory. The CLI
   computes the manifest; record command argv/cwd and required environment-variable
   names, not values or a manually invented fingerprint.
2. Inspect available tools and versions, auth/access, ports, runtime dependencies,
   client location, and fixture/reset capabilities. Record unavailable capabilities
   precisely before assigning dependent tests.
3. Allocate resource names and owners. Worktrees isolate files, not database
   schemas, accounts, browser sessions, queues, storage, external callbacks, or
   native devices. Assign namespaces/leases and prove the reset procedure.
4. Prepare an [environment draft](../assets/templates/environment.yaml) and use
   `runtime start`. It publishes the environment record with owned process and
   log identity after the declared readiness check.
5. Verify application semantics through the actual executor client/tool, including
   auth and dependent services needed by the case. Keep the observations/logs
   referenced from the handoff; status 200 and process existence alone are not
   sufficient application readiness.

Done: the target, tools, data, and real client have a repeatable startup/use/reset
path; the assigned case can start without guessing which source it reaches.

## Computed source identity

For a Git checkout, use `source.provider: {type: git, root: /absolute/worktree}`
and its actual commit in `source.revision`. The manifest covers tracked and
nonignored untracked files, deletions, modes, and source symlinks. For a standalone
program, use `type: files` with the source root and explicit relative `paths`.
Declare runtime-relevant ignored configuration through `config_files`; record
paths and hashes, never secret values. The command's cwd stays inside that root.
Initialized Git submodules contribute their actual commit as a `gitlink` entry
and recursively inspected source files. Ignored build outputs remain excluded.
Integrated startup compares actual files with committed blobs; index optimization
flags cannot hide a dirty checkout. Repository discovery ignores inherited Git
directory/configuration overrides from another harness checkout.

`runtime start` computes `source.attestation`; supplied fingerprint text cannot
certify bytes. Dispatch, execution submission, and current-proof assessment check
the actual source/configuration again. These are boundary checks, not a continuous
filesystem monitor. Keep source immutable throughout execution regardless.

The recorded source digest identifies code across isolated worktrees; runtime
configuration has a separate digest. Artifact hashes, Git commits, source
digests, and round bindings serve different purposes and are not interchangeable.
Older environments remain readable, but absent attestation produces
`SOURCE_ATTESTATION_REQUIRED`. Recover into a fresh target and collect new proof;
preserve historical records instead of rewriting them to claim old verification.

## Adapter requirements

| Runtime type | Setup and readiness |
|---|---|
| `http` | Owned web dev server; expected HTTP status plus nonempty application body marker; actual browser access and required assets/API/auth/WebSocket flows |
| `cli` | Exact executable argv/cwd and environment; declared process/log handshake or real safe interface probe; exit/output/file-capture capability |
| `mcp_stdio` | Client-owned server/adapter session; actual initialization and required tool discovery; preserve stdin/stdout transport semantics |
| `mcp_http` | Exact HTTP endpoint and actual MCP initialization; verify required JSON/SSE behavior and auth from the executor client |
| `mobile` | Native build/install identity, emulator/device lease and driver access; prove app launch plus backend reachability where needed |

For CLI programs that exit after one invocation, use `runtime_type: cli` and a
real, bounded readiness probe. The helper requires the declared output marker
and exit code 0. `READY` then means the executable/setup probe succeeded;
`alive: false` and an exited process are expected. The executor launches the
case command through its declared tool. A marker followed by a nonzero exit is
not ready. Do not add a dummy persistent process just to keep the runtime alive.
A log handshake confirms only what it actually reports; protocol negotiation
and native tool access remain explicit operator checks.

The runtime helper supports `readiness.type: http` with `url`, `expected_status`,
and nonempty `body_contains`, or `readiness.type: process` with a nonempty log
handshake `body_contains`. Set a bounded `timeout_ms`. It does not infer a
protocol handshake from an alive PID, guarantee SSE, or turn a mobile viewport
into a native app. Mark missing native capability `TOOL_UNAVAILABLE`.

HTTP startup rejects an already-listening readiness port; choose a freshly
leased local listener rather than pointing readiness at another running service.

## Tool-owned sessions

For a client that owns a detached session, use `readiness.type: tool` and a
`session` descriptor. Declare `tool: {name, version}`, `owner_id`, `session_id`,
an `attachment` instruction, and `probe`, `inspect`, and `cleanup` argv arrays.
Native mobile also declares `device_id`. `command.argv` attaches the session.
All lifecycle commands use the declared cwd and a bounded timeout.

The CLI supplies `AGENTIC_RUNTIME_ACTION`, `OWNER_TOKEN`, `TARGET_ID`, `OWNER_ID`,
`SESSION_ID`, and optional `DEVICE_ID` with the `AGENTIC_RUNTIME_` prefix. The
adapter returns one JSON receipt containing the exact tool/owner/session identity
and `alive`. Probe additionally returns `ready: true` and
`evidence: {kind: protocol|device, operation, result}`. The result must contain
the declared readiness marker from a real protocol/device observation.

Keep the session descriptor immutable. The adapter records ownership at attach
and checks its stored native session identity on inspect/cleanup; merely echoing
the current environment variables does not establish ownership. Inspect is
read-only. Recovery allocates a fresh target instead of silently restarting a
session under existing proof. See the executable [MCPC session example](mcpc-session.md)
for client-owned stdio without transferring a server's stdin between processes.

## Ownership and generation

Give each environment a fresh `target_id`. Keep its source/config immutable while
tests borrow it. After failure, stop, restart, merge, source edits, or relevant
configuration changes, allocate a new generation; never silently replace G001
with a different running process. Earlier valid reports remain historical.

Use `runtime recover --campaign "$CAMPAIGN" --target-id "$TARGET" --file "$REQUEST"`
to allocate the successor/operator task. State the failed phase and changed
startup approach. Recovery preserves the integrated code identity and creates a
new runtime identity. Reaccept the target plan and independently retest the
successor before closure. Active executor leases prevent stopping or changing
the generation they use; an isolated successor can be prepared concurrently.

The helper captures PID, creation identity, argv, cwd, and owned process handle.
`runtime inspect` checks its recorded state; `runtime stop` checks ownership
before termination and preserves artifacts. POSIX macOS/Linux process groups
are supported by the helper. Separately detached descendants must be declared
unmanaged and tracked by an explicit operator lifecycle; they are not implicitly
owned merely because their parent was.

Use namespaced log/PID/config/artifact paths and leased ports. Stop only processes
whose ownership identity still matches. Global `pkill`, killing whatever owns a
port, shared credential deletion, and assuming `setsid` exists are not lifecycle
management. Prefer the host's documented supervisor/handle interface for tooling
outside the helper's supported process model.

## Remote clients and tunnels

Tunnel only HTTP services that the real client cannot otherwise reach. Read
[Cloudflare tunnels](cloudflare-tunnels.md). CLI and stdio need process access;
native mobile needs a native driver; neither requirement is solved by a web URL.
Browser localhost belongs to the browser's machine, which may differ from the
worktree/runtime host. Test dependent API/socket URLs from that actual client.

For multi-service applications, use the project's supported dev proxy or explicit
public service URLs without changing the behavior being tested. Preserve host,
cookie, callback, CORS, WebSocket, and streaming semantics. Introducing a proxy,
rewriting bundles, disabling auth/CORS, or changing server transport is a relevant
configuration change: record it and use a new target rather than silently
repairing reachability during evidence capture.

## Failure handoff

Report the failed readiness phase, command/tool, source identity, owned logs,
expected marker, actual response, affected resource, and reason code. Distinguish
missing credentials/tooling, transport failure, unsupported tunnel protocol, and
application failure. Ask only in interactive mode for a material missing access
decision; autonomous mode records a blocker and preserves independent branches.
