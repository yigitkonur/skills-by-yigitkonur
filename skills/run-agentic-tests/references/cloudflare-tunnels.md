# Cloudflare Tunnel for remote HTTP access

Use this branch only when the executor's actual HTTP client cannot reach an
owned application/report endpoint directly. This procedure is self-contained;
no other installed tunnel skill is required. The CLI does not provision tunnels
or implement a reverse proxy.

## Choose a compatible transport

Quick Tunnels supply random public `trycloudflare.com` URLs for development.
They have a 200 in-flight-request limit, return 429 when exceeded, provide no
uptime/SLA guarantee, and do not support Server-Sent Events. See the verified
provenance in [Sources](sources.md). Agent count and HTTP concurrency are distinct.

Inspect the target's actual transport before selecting Quick Tunnel. An MCP
Streamable HTTP server may return JSON or SSE; an SSE-dependent server/app needs
a suitable authenticated/named tunnel or another proven route. Do not change the
application to JSON-only to make the test pass. If the required route is absent,
record `TUNNEL_PROTOCOL_UNSUPPORTED` and block affected cases.

Named tunnels need the available account/domain/access configuration. Give
independent runtime versions distinct routing identities. Replicas sharing one
tunnel UUID serve one endpoint, so they cannot identify which independent source
version answered a case. Resolve public exposure and auth requirements from
task authority before publishing an endpoint.

## Launch with explicit ownership

1. Inspect installed `cloudflared --help`/version and the host's supported process
   supervisor. Preserve existing user configuration and credentials.
2. Reserve one target generation, origin/proxy/metrics ports, log paths, and a
   tunnel process identity. Use a campaign-owned directory for this tunnel.
3. Run the supported command under the chosen supervisor. A Quick Tunnel command
   shape is:

   ```bash
   cloudflared tunnel --url "$ORIGIN_URL" --no-autoupdate --logfile "$TUNNEL_LOG"
   ```

   Bind `$ORIGIN_URL` to the recorded target, never a shared default port. Retain
   the supervisor handle and actual PID/creation identity. Adapt documented flags
   to the installed version; do not depend on Linux-only `setsid` on every host.
4. Extract the URL from this process's fresh log, verify that the process remains
   owned/alive, and attach the endpoint to the environment handoff. A URL in a log
   is a discovery result, not a readiness verdict.

If local configuration conflicts with Quick Tunnel, use a documented isolated
configuration mechanism for the installed version or another authorized route.
Do not remove `~/.cloudflared/` or reset other tunnels. QUIC requires UDP 7844;
HTTP/2 transport requires TCP 7844. Port 443 alone is not HTTP/2 tunnel egress.

## Three distinct reachability checks

1. **Origin:** from the tunnel host, reach the exact application port/path with
   the declared status and semantic marker. Check necessary dependent services.
2. **Public route:** resolve the assigned hostname and reach the intended target
   through the tunnel. Use bounded retries and retain actual errors. Do not treat
   fixed DNS propagation/negative-cache durations as universal guarantees.
3. **Actual client:** from the browser/device/MCP client that will execute tests,
   prove the same application identity and required auth/API/socket behavior.
   Origin-host curl cannot substitute for this check.

HTTP 200 from a proxy's fallback page, an auth redirect, an error JSON envelope,
or a different worktree is not success. Use the declared readiness contract.
Global DNS publication alone does not prove client resolution or application
access. Diagnose the failing layer rather than repeatedly changing tunnel URLs.

## Lifecycle and exposure

Keep source/config fixed during the evidence lease. Tunnel replacement or a URL
change affecting auth/callback configuration creates a new environment generation
and invalidates current reachability proof. Give executor retries the new exact
endpoint and reason; retain the old endpoint only as history.

Stop only this tunnel's verified owned process/handle; remove only its owned
temporary files after preserving useful logs. Never use global process matching
or broad `/tmp/cloudflared*` cleanup. Keep the final app/report route available
for inspection when requested by the campaign's delivery protocol.

For reports, expose only the generated `report/` directory through the owned
report server. Do not serve the repository, campaign record root, secrets, or
an unauthenticated arbitrary-file upload endpoint.
