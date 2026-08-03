---
name: test-by-mcpc-cli
description: "Use skill if you are driving mcpc 0.6.x to test or smoke-check an MCP server over stdio or Streamable HTTP."
---

# Test MCP Servers with mcpc

Drive `mcpc` 0.6.x as the operator-facing harness for any MCP server — stdio or Streamable HTTP. This skill owns the released CLI contract, session-first command shape, JSON scripting, task execution, protocol-version probing, and cleanup. It does not own writing the server or client itself.

## When to use this skill

- *Connecting to a real MCP server over stdio or Streamable HTTP and verifying the live surface with `mcpc connect … @session`*
- *Inspecting tools, prompts, resources, templates, skills, logging, subscriptions, or instructions from `mcpc`*
- *Reproducing auth, proxy, cleanup, task, protocol-version, or transport failures with the released `mcpc 0.6.x` CLI*
- *Scripting repeatable smoke checks in `--json` mode, including CI assertions on exit codes and `isError`*
- *Comparing a local stdio server against a deployed Streamable HTTP target during release verification*
- *Translating pre-0.2.0 target-first examples or removed 0.2.x-era commands to current syntax*

## Do NOT use this skill when

- *Building or refactoring server code* → use `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server`
- *Building or refactoring client/agent code* → use `build-mcp-use-client` or `build-mcp-use-agent`
- *Running an agentic-quality / hardening / context-budget audit beyond CLI testing* → use `audit-agentic-mcp`
- *Porting an existing v1 server to v2* → use `convert-mcp-sdk-v1-to-v2`

## Source of truth

1. Confirm the running CLI: `mcpc --version` must report `0.6.x`. Older 0.2.x–0.5.x syntax overlaps but drifts on tasks, exit codes, x402, and login flags; pre-0.2.0 syntax is structurally different.
2. When docs and `mcpc --help` disagree, trust `mcpc help <command>` on the version actually installed. `mcpc help --skill` prints upstream's own agent guide.
3. This skill was verified against `0.6.0` and live-tested against `https://research-mcp.yigitkonur.com/mcp` (mcp-researchpowerpack v9) and `@modelcontextprotocol/server-everything` over stdio and Streamable HTTP.
4. If `mcpc` is missing, older, or your config shape is wrong, start with `references/guides/installation.md`. Establish the plain CLI path first, then layer wrappers back in only after the raw command path already works.

## Load-bearing rules

These rules apply across every workflow below. Each one is live-verified against 0.6.0; violating one is the most common failure mode.

| # | Rule | Why |
|---|---|---|
| 1 | Always `connect` to a named `@session` before any MCP operation | mcpc is session-first; target-first one-shot commands do not exist |
| 2 | Session reuse is name-keyed, not URL-keyed | `connect <url> @existing` reuses; `connect <url> @new` creates a second independent session; omitted `@name` auto-generates and reuses a per-server name |
| 3 | Interpret exit codes together with output shape: `1` = CLI/session failure (and `grep` no-match); `2` = either an MCP `isError:true` result on stdout or a timeout/no-result `{error,code}` on stderr; `3`/`4` are documented network/auth codes but were not reproduced in this audit | Exit code identifies a broad class, not the exact cause; capture both streams and parse JSON |
| 4 | A connection attempt to an unreachable target can exit `0` while creating a `reconnecting` session | `connect` success can mean “record created,” not “handshake live”; inspect exact-name status and run a real command |
| 5 | `mcpc clean` with no args removes stale data only; **named** targets (`clean sessions`, `clean logs`, `clean profiles`) delete ALL records of that kind, including live ones | `mcpc clean all` and named targets are destructive on shared machines |
| 6 | Use only stdio or Streamable HTTP targets | mcpc 0.6.0 exposes no first-class HTTP+SSE test path |
| 7 | Use `--no-profile` to force anonymous HTTP tests when saved OAuth would pollute the result | Profiles silently inject auth; anonymous reproduction needs explicit opt-out |
| 8 | If a tool is `task:required`, plain `tools-call` fails until you add `--task` or `--detach` — and 0.6.0 fails loudly instead of silently falling back on non-task tools/servers | The error is the contract; read it instead of retrying |
| 9 | Recover detached results with `tasks-result <taskId>` — it works across process invocations; `tasks-get` is status only | Cancelled tasks correctly fail `tasks-result` with “has no result stored” (exit 2) |
| 10 | Distinguish bridge failure from stdio-child failure: a dead bridge self-heals on the next command; a dead stdio child self-heals only through `ping`; other commands fail `Not connected` (exit 2) until `mcpc restart @session` | The JSON `pid` is the bridge, status can remain misleadingly `live`, and restart loses tasks/added tools while restoring subscriptions |
| 11 | Reach for `--insecure` only when the endpoint truly uses an untrusted certificate | It hides legitimate TLS regressions |
| 12 | Trust the `Input:` type annotations from `tools-get` over its printed “Call example” — the example can render array args as plain strings | `urls:='"x"'` for an `array<string>` field fails the tool's own schema |
| 13 | Treat x402 wallet import/removal, signing, approval, and `--x402` calls as financial/credential actions: isolate state, prefer `x402 init` with a throwaway Base Sepolia wallet, and obtain explicit authorization before using real keys or funds | `upto` may approve `MAX_UINT256` and calls can spend funds/gas; 0.6.0 imports keys only through positional argv, so do not import real production keys for routine testing |

Stale syntax to refuse outright:

```text
mcpc mcp.example.com tools-list          # pre-0.2.0 target-first — drop
mcpc mcp.example.com connect @demo       # pre-0.2.0 — drop
mcpc --clean=sessions                    # pre-0.2.0 flag — use: mcpc clean sessions
mcpc @demo tools                         # shorthand aliases removed in 0.3.0 — use tools-list
mcpc shell @demo                         # shell removed in 0.4.0 — no replacement
```

Translate to current shape using `references/patterns/session-first-syntax.md`. Raw JSON-RPC method names can work as silent aliases in 0.6.0 (`tools/list` and `logging/setLevel` are the documented pairs; others are live-confirmed but no complete alias table is published), so teach the hyphenated CLI form first.

## Minimal read sets

Do not load the whole skill by default. Pick one bundle, then widen only if the task forces you to.

| Branch | Read first |
|---|---|
| Remote Streamable HTTP | `references/commands/quick-reference.md`, `references/guides/http-testing.md` |
| Local stdio | `references/commands/quick-reference.md`, `references/guides/stdio-testing.md` |
| Tool, prompt, resource, template, or grep requirements | `references/guides/discovery-search.md`, `references/guides/tool-resource-testing.md` |
| Async tasks or Everything-server behavior | `references/guides/async-tasks.md`, `references/guides/everything-server.md` |
| OAuth or headers | `references/guides/authentication.md`, `references/patterns/auth-precedence.md` |
| Local proxy | `references/guides/proxy-testing.md` |
| x402 payments | `references/guides/x402-payments.md`, `references/patterns/auth-precedence.md` |
| CI / scripted smoke tests | `references/guides/ci-cd-integration.md`, `references/guides/scripting-automation.md`, `references/patterns/output-formatting.md` |
| Protocol version or skills extension | `references/guides/protocol-versions.md`, `references/guides/skills-testing.md` |
| Failure diagnosis or destructive reset | `references/troubleshooting/common-errors.md`, then `references/patterns/logging-debugging.md` or `references/guides/cleanup-maintenance.md` only if the failure requires it |

## Standard workflow

### 1. Verify the syntax family

- `mcpc --version` reports `0.6.x`.
- Examples use `mcpc connect <server-or-file:entry> @session` shape.
- Validate the contract with plain `mcpc`, not a wrapper that may mangle quoting, TTY, or session state.

### 2. Connect a stable session

Default to a fresh `connect` with a name you chose. Reach for the session inventory only when reuse, cleanup, or stale-state diagnosis is the actual job.

```bash
# Remote URL; https:// is added automatically for non-local hosts
mcpc connect research-mcp.yigitkonur.com/mcp @research

# Localhost keeps http:// by default
mcpc connect 127.0.0.1:3011/mcp @everything-http

# Stdio via mcpServers config entry
mcpc connect /tmp/everything-mcp.json:everything @everything-stdio
```

Use `--no-profile` when anonymous HTTP testing matters on a machine with saved OAuth profiles. Re-running `connect` with the same `@name` reuses the session; a new `@name` always creates a second one (rule 2). Because an unreachable target can still produce exit `0`, verify the exact-name session is `live` before treating the connection as ready (rule 4).

To inspect an existing session, narrow the lookup to a single name instead of dumping the whole inventory:

```bash
mcpc
mcpc --json | jq '.sessions[] | select(.name == "@research")'
```

If an older session is not `live`, do not reuse it for a smoke test. Either `mcpc restart @session` or create a fresh session with a new name. If `mcpc restart @session` returns `Session not found` (exit 1), stop retrying that name and create a fresh session immediately.

### 3. Inspect before deep testing

```bash
mcpc @research
mcpc @research help
mcpc @research grep search
mcpc @research tools-list --full
mcpc @research resources-list
mcpc @research prompts-list
mcpc @research skills-list        # experimental SEP-2640 servers only
```

Prefer `help` and `grep` before heavy `jq` pipelines. The `mcpc @research` banner shows the negotiated MCP protocol version — on `2026-07-28` connections `server-discover` also works (`references/guides/protocol-versions.md`). If acceptance criteria explicitly mention prompts, resources, or templates, add those list calls in the first pass instead of widening the read set later.

### 4. Validate schema and argument shape

```bash
mcpc @research tools-get web-search
mcpc --json @research tools-get web-search | jq '.inputSchema'
mcpc @research tools-get web-search --schema ./expected-tool-schema.json
```

`--schema`/`--schema-mode` are scoped to `tools-get` and `tools-call` only — `prompts-get` has no schema flags. A client-side schema mismatch exits `1` (it never reaches the server). `key:=value` still works, but arrays and objects should be sent as inline JSON literals or full JSON payloads. Route quoting edge cases to `references/patterns/argument-parsing.md`.

### 5. Reality-check advertised capabilities

Do not trust `capabilities` alone. Check server info, tool metadata, and one real call.

```bash
mcpc --json @research | jq '.capabilities'
mcpc --json @everything-http tools-list | jq '.[] | {name, taskSupport: (.execution.taskSupport // "unspecified")}'
```

- If `completions` appears in server info, treat it as informational — there is no `mcpc completions` command.
- mcpc does **not** advertise `sampling`, `roots`, or `elicitation`, so servers that register demo tools conditionally (like Everything) will not expose them at all.
- If tasks appear in capabilities, still inspect per-tool `execution.taskSupport`, and prove `task:required` with one `--task` or `--detach` call before writing automation around it.

### 6. Exercise the capability you care about

```bash
mcpc --json @research tools-call web-search 'queries:=["OpenAI MCP"]'
mcpc @everything-http prompts-get args-prompt city:=Paris state:=Texas
mcpc @everything-http resources-read demo://resource/static/document/features.md
mcpc @everything-http resources-subscribe demo://resource/dynamic/text/1 /tmp/text-sync.json
mcpc @everything-http logging-set-level debug
```

`resources-subscribe` requires a target file and syncs updates into it. `logging-set-level` may print a deprecation warning about MCP `2026-07-28` — the current call still succeeded (exit 0); read past the `⚠`.

### 7. Treat JSON payloads as truth

```bash
RESULT=$(mcpc --json @research tools-call web-search 'queries:=["mcpc"]') || echo "exit=$?"
echo "$RESULT" | jq '.isError // false'
```

Since 0.5.0 an `isError:true` result also exits `2`, so scripts may assert on the exit code — but still inspect the payload for failure detail. JSON mode also exposes fields human rendering can omit (for example active tasks, subscription state, and experimental capability payloads); do not assume either mode is a strict structural superset of the other. A timeout can also exit `2`, but with `{error,code}` on stderr rather than an `isError` payload on stdout (rule 3).

### 8. Use task mode deliberately

```bash
mcpc @everything-http tools-list --full
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' ambiguous:=false --task
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' ambiguous:=false --detach
mcpc @everything-http tasks-get <taskId>
mcpc @everything-http tasks-result <taskId>
```

Use `--task` when you need the final result inline. Use `--detach` when you want the taskId immediately and will fetch the body later with `tasks-result` — it works even from a different process. On tools or servers without task support, both flags fail loudly instead of falling back to a sync call.

### 9. Close or clean explicitly

```bash
mcpc close @research
mcpc clean
```

`mcpc clean` (no args) removes stale data only. Any named target — including `clean sessions logs` — removes **all** records of that kind and belongs only in an intentional reset inside an isolated `MCPC_HOME_DIR` (rule 5). Do not run `close` and `clean` for the same session in parallel; a repeated `close` returns exit `1`, not a no-op success.

## Capability boundary

What `mcpc 0.6.0` can and cannot test as a first-class workflow:

| Bucket | Coverage |
|---|---|
| **First-class** | stdio and Streamable HTTP transports; tools, prompts, resources, resource templates, file-synced subscriptions, logging, grep, proxy, x402; JSON scripting with a reliable exit-code contract; full task lifecycle (`--task`, `--detach`, `tasks-list`, `tasks-get`, `tasks-result`, `tasks-cancel`); protocol-version pinning (`--protocol-version`, 2024-10-07…2026-07-28); experimental MCP skills (`skills-list`, `skills-get`) |
| **Nuanced / partial** | `server-discover` (2026-07-28 connections only — educational error otherwise); `completions` (advertised in server info, no CLI command); `roots`/`sampling` (mcpc deliberately does not advertise them, so capability-gated demo tools never register); `logging-set-level` (works on ≤2025-11-25, removed by the 2026-07-28 spec) |
| **Not first-class** | HTTP+SSE transport testing; elicitation commands from the CLI; standalone completion browsing |

Map advertised capabilities to actual CLI commands using `references/guides/capability-coverage.md`.

## Reference routing

Read the smallest relevant set for the branch you are in.

### Core guides

| File | Read when |
|---|---|
| `references/guides/installation.md` | Installing `mcpc` (npm/bun/Homebrew), Node ≥22.12 requirement, version drift, keychain notes, or config format confusion. |
| `references/guides/stdio-testing.md` | Testing a local stdio server from `mcpServers` config using `file:entry` syntax, stderr capture, or bulk `--stdio` gating. |
| `references/guides/http-testing.md` | Testing remote or localhost Streamable HTTP endpoints, path issues, TLS, headers, or `--insecure`. |
| `references/guides/discovery-search.md` | Discovering tools, resources, prompts, skills, and instructions with `help`, `grep`, and list calls. |
| `references/guides/tool-resource-testing.md` | Running tools, prompts, resources, templates, file-synced subscriptions, and logging checks. |
| `references/guides/async-tasks.md` | Using `--task`, `--detach`, and `tasks-*` including `tasks-result`, or debugging task-required tools. |
| `references/guides/authentication.md` | OAuth (authorization-code, client-credentials, id-jag), bearer headers, profiles, callback flags, and anonymous mode. |
| `references/guides/session-management.md` | Session lifecycle, name-keyed reuse, stateless servers, bridge-vs-child recovery, and multi-session workflows. |
| `references/guides/cleanup-maintenance.md` | Safe cleanup, the stale-only vs delete-all distinction, hard resets, the `logs` command, and local mcpc hygiene. |
| `references/guides/proxy-testing.md` | Exposing a session as a local MCP proxy: `/health`, bearer enforcement, DNS-rebinding protection, sandbox use. |
| `references/guides/x402-payments.md` | Wallet inspection (`mcpc x402`), payment schemes (auto/upto/exact), `x402 sign`, and `--x402` session behavior. |
| `references/guides/ci-cd-integration.md` | CI smoke tests, isolated `MCPC_HOME_DIR`, exit-code assertions, Node/CI image requirements, and cleanup traps. |
| `references/guides/scripting-automation.md` | Shell automation patterns, the exit-code contract, JSON parsing, and reproducible scripts. |
| `references/guides/everything-server.md` | Verifying current `mcpc` behavior against the official Everything reference server, including conditional tool registration. |
| `references/guides/capability-coverage.md` | Mapping advertised capabilities to actual `mcpc` commands and known gaps. |
| `references/guides/skills-testing.md` | Testing the experimental MCP skills extension (SEP-2640): `skills-list`, `skills-get`, and the `skill://` convention. |
| `references/guides/protocol-versions.md` | Protocol negotiation, `--protocol-version` pinning, `server-discover`, and JSON-RPC method aliases. |
| `references/guides/architecture.md` | High-level `mcpc` design, session-first routing, and capability negotiation. |
| `references/guides/bridge-internals.md` | Bridge process lifecycle, bridge-vs-child recovery (including the `ping` exception), reconnect caveats, and log locations. |

### Commands, examples, and troubleshooting

| File | Read when |
|---|---|
| `references/commands/quick-reference.md` | You need exact `0.6.0` syntax, flags, aliases, or cleanup forms fast. |
| `references/examples/real-world-workflows.md` | You want complete end-to-end workflows for real targets like Research Powerpack or Everything. |
| `references/examples/testing-recipes.md` | You want short copy-paste checks for smoke tests, schemas, tasks, grep, or cleanup. |
| `references/troubleshooting/common-errors.md` | You hit stale syntax, bad config shape, task-required failures, expired sessions, or transport mismatches. |

### Patterns and advanced details

| File | Read when |
|---|---|
| `references/patterns/session-first-syntax.md` | Translating pre-0.2.0 examples, removed aliases, or wire-protocol method names to current syntax. |
| `references/patterns/argument-parsing.md` | Quoting arrays, objects, inline JSON, stdin, and `key:=value` edge cases. |
| `references/patterns/schema-validation.md` | Validating tool schemas with `--schema`/`--schema-mode` in regression checks. |
| `references/patterns/config-resolution.md` | `mcpServers` config shape, `file:entry`, auto-discovery, bulk connect, and URL normalization. |
| `references/patterns/auth-precedence.md` | Choosing between explicit headers, named profiles, default profile, `--no-profile`, and `--x402`. |
| `references/patterns/output-formatting.md` | Human vs JSON mode, stdout/stderr routing, the exit-code contract, and `isError`. |
| `references/patterns/jq-patterns.md` | Advanced JSON filtering after native `grep` and `help` are not enough. |
| `references/patterns/tool-filtering.md` | Complementing `grep` with `tools-list --json \| jq` workflows. |
| `references/patterns/logging-debugging.md` | Using `--verbose`, the `logs` command, and bridge logs to explain failures. |
| `references/patterns/notification-handling.md` | Testing list-changed notifications, file-synced subscriptions, and server log messages. |
| `references/patterns/pagination-caching.md` | Auto-pagination, stateless cache TTL, tool cache refresh, and dynamic discovery behavior. |
| `references/patterns/python-integration.md` | Driving `mcpc` from Python subprocess workflows with correct returncode handling. |
| `references/patterns/data-model.md` | JSON shapes behind session info, task status, cached metadata, profiles, and storage. |

## Guardrails

- Do not teach pre-0.2.0 target-first syntax, removed shorthand aliases, or the removed `shell` command unless explicitly documenting migration.
- Do not tell users to test HTTP+SSE with `mcpc`; use Streamable HTTP or stdio instead.
- Do not treat `tasks-get` status output as the task result — fetch detached bodies with `tasks-result`.
- Do not treat `connect` exit `0` or a green banner as proof that the handshake is live; an unreachable target can leave a `reconnecting` session, so verify exact-name status and exercise the capability.
- Do not assume advertised capabilities always mean polished CLI support, nor that missing demo tools mean a broken server — mcpc's non-advertised `sampling`/`roots`/`elicitation` capabilities suppress gated tools by design.
- Do not run `mcpc clean all` — or any *named* `clean` target — casually on machines with saved profiles or live sessions; only no-args `clean` is stale-only.
- Treat proxy `/health` as an unauthenticated liveness probe only — verify proxy auth with a real MCP request carrying (or omitting) the bearer token.
- Do not read a `⚠` deprecation warning as a failed call; check the exit code and payload of the current invocation.
