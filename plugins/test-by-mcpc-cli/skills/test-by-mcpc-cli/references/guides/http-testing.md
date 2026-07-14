# HTTP Testing

This guide is for Streamable HTTP targets, not SSE.

## Canonical connect forms

```bash
mcpc connect https://research.yigitkonur.com/mcp @research
mcpc connect mcp.apify.com @apify
mcpc --insecure connect https://self-signed.internal/mcp @internal
```

## Path discipline

Test the real MCP path.
A working host root does not guarantee the MCP endpoint is on `/`.

Known-good example:

```bash
mcpc connect https://research.yigitkonur.com/mcp @research
```

Known-bad example for that server:

```bash
mcpc connect https://research.yigitkonur.com @wrong
```

That can create a session record, but live use fails because the upstream path is wrong.

## Fast remote checklist

```bash
mcpc connect https://research.yigitkonur.com/mcp @research
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

For `mcpc 0.2.x`, treat HTTP+SSE as unsupported in practice.
Use Streamable HTTP instead.
