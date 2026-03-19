# Securing Your MCP Server

Security requirements differ dramatically between a local dev tool and a remote production server. This tree routes you through the right defenses based on your deployment model and threat surface.

## Decision Tree

```
START: Is the server local (stdio) or remote (HTTP)?
|
+-- LOCAL (stdio, same machine)
|   +-- Runs with the user's own permissions
|   +-- Minimal attack surface -- no network exposure
|   +-- Still apply:
|       +-- Human confirmation for destructive ops (delete, send, modify)
|       +-- Read-only tools: auto-approve (search_, list_, get_)
|       +-- Write/delete tools: always require confirmation
|       +-- --> security.md
|
+-- REMOTE (Streamable HTTP, multi-user)
    |
    +-- Authentication & Authorization
    |   +-- Implement OAuth2 with granular scopes
    |   |   mcp:read (search, list)
    |   |   mcp:write (create, update)
    |   |   mcp:delete (destructive, rarely granted)
    |   |   mcp:admin (config, never auto-granted)
    |   +-- Validate token audience matches YOUR server
    |   +-- Use delegated permissions (user's scope, not superuser)
    |   +-- Session IDs via CSPRNG (uuid4), bind to user identity
    |   +-- Rotate on privilege escalation; TTL 15min elevated, 1hr read
    |   +-- --> security.md
    |
    +-- Network Security
    |   +-- Block SSRF to private IP ranges
    |   |   (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8)
    |   +-- Require HTTPS in production
    |   +-- Set CORS headers for browser clients
    |   +-- --> security.md
    |
    +-- Does the server process user-generated content?
    |   +-- YES --> Apply sanitization defense-in-depth:
    |   |   1. Label user content as untrusted in response metadata
    |   |   2. Strip instruction-like patterns from user data
    |   |   3. Never expose raw stack traces (log to stderr instead)
    |   |   --> security.md
    |   +-- Does the content contain PII?
    |       +-- YES --> Tokenize PII before model exposure
    |       |   Replace emails/phones/SSNs with [EMAIL_1], [PHONE_1]
    |       |   Untokenize in the response path before showing to user
    |       |   Add response interceptor as second line of defense
    |       |   --> security.md
    |       +-- NO  --> Standard sanitization is sufficient
    |
    +-- Does the deployment involve multiple MCP servers?
        +-- YES --> Defend against cross-tool hijacking
        |   A malicious tool description can influence OTHER tools
        |   via shared context -- without ever being called.
        |   Mitigations:
        |   1. Separate contexts: high-trust (email, DB) vs low-trust
        |      (third-party integrations) in isolated sessions
        |   2. Sanitize external tool descriptions for injected instructions
        |   3. Per-tool allowlists for interaction boundaries
        |   4. Signed manifests to verify description integrity
        |   --> security.md
        +-- NO  --> Single-server defenses are sufficient
```

## Key Decision Factors

| Factor | Options | Recommendation |
|---|---|---|
| Deployment model | Local stdio vs remote HTTP | Remote needs OAuth2, SSRF blocking, HTTPS |
| User content | Not present vs present | If present, always sanitize and label as untrusted |
| PII exposure | None vs contains PII | Tokenize before model sees it; never rely on prompts |
| Multi-server | Single vs multiple MCPs | Isolate high-trust from low-trust in separate contexts |
| Destructive ops | Read-only vs write/delete | Require human confirmation for all state-changing ops |
| Permission model | Superuser vs delegated | Always use the requesting user's scoped permissions |

## When to Re-evaluate

- When moving from local dev to remote deployment (add full auth layer)
- When adding a third-party MCP server to the environment (context isolation)
- When tool starts processing external user input (add sanitization)
- When handling regulated data (PII tokenization becomes mandatory)
