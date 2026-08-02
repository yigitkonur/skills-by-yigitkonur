# Sessions in v2: Stateless Truth

*Read this when understanding state management and scaling.*

## The v2 fact: No session stores shipped

mcp-use v2.0.0-beta.66 **does not export session stores** (`InMemorySessionStore`, `RedisSessionStore`, `FileSystemSessionStore`). The beta docs describe these APIs, but they are **not in the shipped package**.

v2 is **stateless by default**: every HTTP request is independent; no server-side session affinity, no carry-over between requests, no persistent connection.

### Why stateless?

1. **Horizontal scaling:** Requests can route to any instance; no sticky sessions required.
2. **Serverless/edge compatibility:** Instances may be killed or spun up on every request.
3. **Simplicity:** No session cleanup, no TTL management, no store failures.

### Session store docs (not shipped)

Beta docs at `/tmp/mcp-use-beta/docs/typescript/server/session-management/` describe:
- `InMemorySessionStore` for in-process sessions
- `RedisSessionStore` + `RedisStreamManager` for distributed sessions
- `FileSystemSessionStore` for restart persistence

These are **planned features** for a future v2 release, not beta.66.

> Documented but not shipped in 2.0.0-beta.66 — verify against your installed version.

See `02-session-storage-roadmap.md` for what is planned.

## Cross-cluster references

- State codec for round-trip validation: `../09-transports/03-stateless-and-request-state.md`
- External state patterns: `03-state-patterns-without-sessions.md`
- Scaling without session affinity: `04-multi-instance-and-scaling.md`
