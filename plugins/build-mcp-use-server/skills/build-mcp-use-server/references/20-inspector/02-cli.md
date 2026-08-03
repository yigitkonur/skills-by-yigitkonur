# Inspector CLI

*Read this when running the Inspector standalone with command-line flags.*

## Quick start

```bash
npx @mcp-use/inspector
```

This starts the Inspector on port 8080 and opens it in your browser at `http://localhost:8080`.

## Command-line flags

### `--url <url>`

Auto-connect to an MCP server when the Inspector starts.

```bash
npx @mcp-use/inspector --url http://localhost:3000/mcp
```

The Inspector will not wait for the server to respond before starting; it attempts the connection after the UI loads.

### `--port <port>`

Specify the starting port. Default is 8080. Valid range: 1–65535.

```bash
npx @mcp-use/inspector --port 9000
```

If the specified port is in use, the Inspector will try to find the next available port and display the actual port in the terminal.

### `--no-open`

Prevent the Inspector from automatically opening a browser tab. Useful in CI/CD pipelines and headless environments.

```bash
npx @mcp-use/inspector --no-open
```

You can combine flags:

```bash
npx @mcp-use/inspector --url http://localhost:3000/mcp --port 9000 --no-open
```

### `--version, -v`

Print the installed `@mcp-use/inspector` version and exit.

```bash
npx @mcp-use/inspector --version
```

### `--help, -h`

Display help information and available options.

```bash
npx @mcp-use/inspector --help
```

The standalone `npx @mcp-use/inspector` CLI reads no environment variables — configure it with the flags above. `MCP_URL` is a `mcp-use dev` variable (reverse-proxy base URL for the dev server's own automounted Inspector, not the standalone package); see references/03-cli/10-environment-variables.md.
