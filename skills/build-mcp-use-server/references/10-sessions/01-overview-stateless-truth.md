# Sessions in v2: Stateless Truth

*Read this when understanding state management and scaling.*

## The v2 fact: session stores are gone, not delayed

mcp-use v2.0.0-beta.66 **does not export session stores** (`InMemorySessionStore`, `RedisSessionStore`, `FileSystemSessionStore`, `RedisStreamManager`). Confirmed absent from every `dist/*.d.ts` in the shipped package (root, `node`, `next`, `oauth/*`, `react` subpaths — no session-store symbol exists anywhere in the public API surface).

This is not a beta gap awaiting a future release — the framework's own engineering spec lists session stores among the things explicitly **not being ported** to v2: "Do not port: session stores/StreamManager, registration-HMR, session recovery, SSE transport, the Express/Connect adapter... These are obsolete under the stateless model." The v2 migration guide confirms the same as a standing limitation, not a roadmap item: "Session stores, active-session registries, stream managers, session recovery, and session affinity are not part of v2." Treat this as an architectural decision, not a temporary omission.

v2 is **stateless by default**: every HTTP request is independent; no server-side session affinity, no carry-over between requests, no persistent connection.

### Why stateless?

1. **Horizontal scaling:** Requests can route to any instance; no sticky sessions required.
2. **Serverless/edge compatibility:** Instances may be killed or spun up on every request.
3. **Simplicity:** No session cleanup, no TTL management, no store failures.

### What v1 had (migration reference only)

v1's `mcp-use/server` bridge documented `InMemorySessionStore`, `RedisSessionStore` + `RedisStreamManager`, and `FileSystemSessionStore` as `sessionStore`/`streamManager` config on `MCPServer`. These APIs describe v1 behavior only — they are not a v2 target. See `02-session-storage-roadmap.md` for the corrected framing.

## Cross-cluster references

- State codec for round-trip validation: `../09-transports/03-stateless-and-request-state.md`
- External state patterns: `03-state-patterns-without-sessions.md`
- Scaling without session affinity: `04-multi-instance-and-scaling.md`
