# HTTP Testing

This guide is for Streamable HTTP targets, not SSE.

## Canonical connect forms

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @research
mcpc connect mcp.apify.com @apify
mcpc --insecure connect https://self-signed.internal/mcp @internal
```

`https://` is auto-added for a bare host; `localhost`/`127.0.0.1` targets default to `http://` instead.

## Path discipline

Test the real MCP path.
A working host root does not guarantee the MCP endpoint is on `/`.

Known-good example:

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @research
```

Known-bad example for that server:

```bash
mcpc connect https://research-mcp.yigitkonur.com @wrong
```

That can create a session record, but live use fails because the upstream path is wrong.

## Fast remote checklist

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @research
mcpc @research
mcpc @research help
mcpc @research grep search
mcpc @research tools-list --full
mcpc @research ping
```

## Headers and anonymous mode

```bash
mcpc connect https://mcp.example.com/mcp @auth -H 'Authorization: Bearer token'
mcpc connect https://mcp.example.com/mcp @anon --no-profile
```

Use `--no-profile` when you want to prove anonymous behavior on a machine that already has saved OAuth profiles.

## TLS debugging

Use `--insecure` only for self-signed or otherwise untrusted certificates.
Do not document it as a normal production path.

## Transport boundary

`mcpc 0.6.0` supports stdio and Streamable HTTP only — the README's feature table lists no other
transport. Route HTTP+SSE (legacy) servers to a different client; do not test them with `mcpc`.

## Protocol version and statefulness

mcpc negotiates the newest MCP version both sides support, `2026-07-28` down to `2024-10-07`; `mcpc @session` prints the result on one line (`MCP: version 2025-11-25 / Streamable HTTP (stateful)`). Pin an exact version with `--protocol-version <version>` on `connect` — the connection fails if the server doesn't offer it, no fallback:

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @pinned --protocol-version 2025-11-25
```

Full 2026-07-28 stateless-protocol coverage: `references/guides/protocol-versions.md`.
