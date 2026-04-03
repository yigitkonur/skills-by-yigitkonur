# CI/CD Integration

Run mcpc-based MCP server tests in continuous integration pipelines. Covers GitHub Actions, Docker, headless authentication, test script templates, and parallel matrix strategies.

## Key CI principles

- Always use `--header` for authentication in CI — OAuth requires a browser, which is unavailable headless
- Set `MCPC_HOME_DIR` to an ephemeral directory for isolation between jobs
- Set `MCPC_JSON=1` globally so all output is machine-parseable
- Use unique session names per job to avoid collisions in parallel runs
- Always clean up sessions in a `trap` or post-step to prevent resource leaks

## GitHub Actions workflow

### Complete workflow for testing a remote MCP server

```yaml
name: MCP Server Tests
on:
  push:
    branches: [main]
  pull_request:

env:
  MCPC_HOME_DIR: /tmp/mcpc-ci
  MCPC_JSON: 1

jobs:
  test-mcp:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install mcpc
        run: npm install -g @apify/mcpc

      - name: Verify mcpc
        run: mcpc --version

      - name: Test MCP Server
        env:
          MCP_TOKEN: ${{ secrets.MCP_TOKEN }}
        run: |
          SESSION="ci-${{ github.run_id }}-${{ github.run_attempt }}"

          # Connect with bearer token
          mcpc https://mcp.example.com connect "@$SESSION" \
            --header "Authorization: Bearer $MCP_TOKEN"

          # Health check
          mcpc "@$SESSION" ping

          # Verify tools are exposed
          TOOL_COUNT=$(mcpc "@$SESSION" tools-list | jq 'length')
          echo "Found $TOOL_COUNT tools"
          if [ "$TOOL_COUNT" -eq 0 ]; then
            echo "::error::No tools found on MCP server"
            exit 1
          fi

          # Smoke test a known tool
          mcpc "@$SESSION" tools-call health-check | jq '.isError'

          # Cleanup
          mcpc "@$SESSION" close
```

### Workflow for testing a locally-built MCP server

```yaml
name: Test Local MCP Server
on: [push, pull_request]

env:
  MCPC_HOME_DIR: /tmp/mcpc-ci
  MCPC_JSON: 1

jobs:
  test-local:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install dependencies
        run: npm ci

      - name: Build MCP server
        run: npm run build

      - name: Install mcpc
        run: npm install -g @apify/mcpc

      - name: Start server and test
        run: |
          # Start server in background
          node dist/index.js &
          SERVER_PID=$!

          # Wait for server to be ready
          for i in $(seq 1 30); do
            if curl -sf http://localhost:3000/health > /dev/null 2>&1; then
              echo "Server ready after ${i}s"
              break
            fi
            sleep 1
          done

          # Connect mcpc
          SESSION="local-ci-$$"
          mcpc localhost:3000 connect "@$SESSION"

          # Run tests
          mcpc "@$SESSION" ping
          TOOLS=$(mcpc "@$SESSION" tools-list)
          echo "Tools: $(echo "$TOOLS" | jq 'length')"

          # Verify each tool has a schema
          FAILURES=0
          for tool in $(echo "$TOOLS" | jq -r '.[].name'); do
            SCHEMA=$(mcpc "@$SESSION" tools-get "$tool")
            if ! echo "$SCHEMA" | jq -e 'has("inputSchema")' > /dev/null; then
              echo "::error::Tool '$tool' missing inputSchema"
              FAILURES=$((FAILURES + 1))
            fi
          done

          # Cleanup
          mcpc "@$SESSION" close
          kill $SERVER_PID 2>/dev/null || true

          if [ "$FAILURES" -gt 0 ]; then
            echo "::error::$FAILURES tool(s) missing schemas"
            exit 1
          fi

      - name: Upload mcpc logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: mcpc-logs
          path: /tmp/mcpc-ci/logs/
```

### Workflow for testing a stdio MCP server

```yaml
name: Test Stdio MCP Server
on: [push, pull_request]

env:
  MCPC_HOME_DIR: /tmp/mcpc-ci
  MCPC_JSON: 1

jobs:
  test-stdio:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install dependencies
        run: npm ci && npm run build

      - name: Install mcpc
        run: npm install -g @apify/mcpc

      - name: Create mcpc config
        run: |
          cat > /tmp/mcp-ci-config.json << 'EOF'
          {
            "mcpServers": {
              "my-server": {
                "command": "node",
                "args": ["dist/index.js"],
                "env": {
                  "NODE_ENV": "test"
                }
              }
            }
          }
          EOF

      - name: Run MCP tests
        run: |
          mcpc --config /tmp/mcp-ci-config.json my-server connect @stdio-ci
          mcpc @stdio-ci ping
          mcpc @stdio-ci tools-list | jq '.[].name'
          mcpc @stdio-ci close
```

## Docker testing

### Dockerfile for mcpc test runner

```dockerfile
FROM node:22-slim

# Install mcpc globally
RUN npm install -g @apify/mcpc

# Set up isolated mcpc home
ENV MCPC_HOME_DIR=/tmp/mcpc-test
ENV MCPC_JSON=1

# Copy test scripts
WORKDIR /tests
COPY test-mcp.sh .
RUN chmod +x test-mcp.sh

ENTRYPOINT ["./test-mcp.sh"]
```

### Docker Compose for full test environment

```yaml
services:
  mcp-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=test
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 5s
      timeout: 3s
      retries: 10

  mcpc-tests:
    image: node:22-slim
    depends_on:
      mcp-server:
        condition: service_healthy
    environment:
      - MCPC_HOME_DIR=/tmp/mcpc-test
      - MCPC_JSON=1
    command: >
      bash -c "
        npm install -g @apify/mcpc &&
        mcpc mcp-server:3000 connect @test &&
        mcpc @test ping &&
        mcpc @test tools-list | jq 'length' &&
        mcpc @test close &&
        echo 'All tests passed'
      "
```

### Running Docker tests

```bash
# Build and test
docker compose up --build --exit-code-from mcpc-tests

# Or run mcpc directly in a container
docker run --rm -it --network host node:22-slim bash -c '
  npm install -g @apify/mcpc
  export MCPC_HOME_DIR=/tmp/mcpc-ci MCPC_JSON=1
  mcpc localhost:3000 connect @test
  mcpc @test ping
  mcpc @test tools-list | jq length
  mcpc @test close
'
```

## Headless authentication

CI environments cannot open browsers, so OAuth is not available. Use these alternatives:

### Bearer token via secrets

```yaml
# GitHub Actions
- name: Test with bearer token
  env:
    MCP_TOKEN: ${{ secrets.MCP_TOKEN }}
  run: |
    mcpc https://mcp.example.com connect @ci \
      --header "Authorization: Bearer $MCP_TOKEN"
```

### Custom header auth

```yaml
# API key in custom header
- name: Test with API key
  env:
    API_KEY: ${{ secrets.MCP_API_KEY }}
  run: |
    mcpc https://mcp.example.com connect @ci \
      --header "X-API-Key: $API_KEY"
```

### Multiple headers

```yaml
- name: Test with multiple auth headers
  env:
    TOKEN: ${{ secrets.TOKEN }}
    TENANT: ${{ secrets.TENANT_ID }}
  run: |
    mcpc https://mcp.example.com connect @ci \
      --header "Authorization: Bearer $TOKEN" \
      --header "X-Tenant-Id: $TENANT"
```

### Secrets management rules

- Never hardcode tokens in workflow files or scripts
- Use GitHub Actions secrets, Vault, AWS SSM, or similar secret stores
- Rotate tokens regularly; CI tokens should have minimal required scopes
- Use `MCPC_HOME_DIR` to prevent sessions.json from leaking tokens to other jobs

## Complete CI test script

Save as `scripts/test-mcp-ci.sh` and use from any CI system:

```bash
#!/bin/bash
set -euo pipefail

# === Configuration ===
SERVER="${MCP_SERVER_URL:?Set MCP_SERVER_URL}"
TOKEN="${MCP_TOKEN:-}"
SESSION="ci-$$-$(date +%s)"
TIMEOUT="${MCP_TIMEOUT:-300}"
FAILURES=0
TESTS=0

# === Output ===
pass() { TESTS=$((TESTS + 1)); echo "  PASS: $1"; }
fail() { TESTS=$((TESTS + 1)); FAILURES=$((FAILURES + 1)); echo "  FAIL: $1"; }
info() { echo "  INFO: $1"; }

# === Cleanup ===
cleanup() {
  mcpc "@$SESSION" close 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# === Environment ===
export MCPC_HOME_DIR="${MCPC_HOME_DIR:-/tmp/mcpc-ci-$$}"
export MCPC_JSON=1
mkdir -p "$MCPC_HOME_DIR"

echo "=== MCP CI Test Suite ==="
echo "Server:  $SERVER"
echo "Session: @$SESSION"
echo "Home:    $MCPC_HOME_DIR"
echo ""

# === Phase 1: Connect ===
echo "Phase 1: Connection"
CONNECT_ARGS=("$SERVER" "connect" "@$SESSION" "--timeout" "$TIMEOUT")
if [ -n "$TOKEN" ]; then
  CONNECT_ARGS+=("--header" "Authorization: Bearer $TOKEN")
fi

if mcpc "${CONNECT_ARGS[@]}" 2>/dev/null; then
  pass "Connected to server"
else
  fail "Connection failed (exit code $?)"
  exit 1
fi

# === Phase 2: Health ===
echo "Phase 2: Health"
if mcpc "@$SESSION" ping 2>/dev/null; then
  pass "Ping successful"
else
  fail "Ping failed"
fi

# === Phase 3: Capabilities ===
echo "Phase 3: Capabilities"
SERVER_INFO=$(mcpc "@$SESSION" help 2>/dev/null || echo '{}')
SERVER_NAME=$(echo "$SERVER_INFO" | jq -r '.serverInfo.name // "unknown"')
PROTOCOL=$(echo "$SERVER_INFO" | jq -r '.protocolVersion // "unknown"')
info "Server: $SERVER_NAME, Protocol: $PROTOCOL"

CAPS=$(echo "$SERVER_INFO" | jq -r '.capabilities | keys | join(", ")' 2>/dev/null || echo "unknown")
info "Capabilities: $CAPS"

# === Phase 4: Tools ===
echo "Phase 4: Tool Inventory"
TOOLS=$(mcpc "@$SESSION" tools-list 2>/dev/null || echo '[]')
TOOL_COUNT=$(echo "$TOOLS" | jq 'length')

if [ "$TOOL_COUNT" -gt 0 ]; then
  pass "Found $TOOL_COUNT tool(s)"
else
  fail "No tools found"
fi

# Check each tool has schema and description
for tool in $(echo "$TOOLS" | jq -r '.[].name'); do
  SCHEMA=$(mcpc "@$SESSION" tools-get "$tool" 2>/dev/null || echo '{}')

  if echo "$SCHEMA" | jq -e 'has("inputSchema")' > /dev/null 2>&1; then
    pass "Tool '$tool' has inputSchema"
  else
    fail "Tool '$tool' missing inputSchema"
  fi

  if echo "$SCHEMA" | jq -e '.description != null and .description != ""' > /dev/null 2>&1; then
    pass "Tool '$tool' has description"
  else
    fail "Tool '$tool' missing description"
  fi
done

# === Phase 5: Resources ===
echo "Phase 5: Resources"
RESOURCES=$(mcpc "@$SESSION" resources-list 2>/dev/null || echo '[]')
RESOURCE_COUNT=$(echo "$RESOURCES" | jq 'length')
info "Found $RESOURCE_COUNT resource(s)"

# === Phase 6: Prompts ===
echo "Phase 6: Prompts"
PROMPTS=$(mcpc "@$SESSION" prompts-list 2>/dev/null || echo '[]')
PROMPT_COUNT=$(echo "$PROMPTS" | jq 'length')
info "Found $PROMPT_COUNT prompt(s)"

# === Summary ===
echo ""
echo "=== Summary ==="
echo "Server:    $SERVER_NAME (protocol $PROTOCOL)"
echo "Tools:     $TOOL_COUNT"
echo "Resources: $RESOURCE_COUNT"
echo "Prompts:   $PROMPT_COUNT"
echo "Tests:     $TESTS run, $FAILURES failed"

if [ "$FAILURES" -eq 0 ]; then
  echo "Result: ALL PASSED"
  exit 0
else
  echo "Result: $FAILURES FAILURE(S)"
  exit 1
fi
```

### Using the script in different CI systems

```yaml
# GitHub Actions
- name: Test MCP
  env:
    MCP_SERVER_URL: https://mcp.example.com
    MCP_TOKEN: ${{ secrets.MCP_TOKEN }}
  run: bash scripts/test-mcp-ci.sh

# GitLab CI
test-mcp:
  image: node:22
  before_script:
    - npm install -g @apify/mcpc
  script:
    - bash scripts/test-mcp-ci.sh
  variables:
    MCP_SERVER_URL: https://mcp.example.com
    MCP_TOKEN: $MCP_TOKEN

# CircleCI
- run:
    name: Test MCP Server
    command: bash scripts/test-mcp-ci.sh
    environment:
      MCP_SERVER_URL: https://mcp.example.com
```

## Parallel test jobs with matrix strategy

### Test multiple MCP servers in parallel

```yaml
name: Multi-Server MCP Tests
on: [push]

jobs:
  test-mcp:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        server:
          - name: production
            url: https://mcp.prod.example.com
            token_secret: MCP_PROD_TOKEN
          - name: staging
            url: https://mcp.staging.example.com
            token_secret: MCP_STAGING_TOKEN
          - name: dev
            url: https://mcp.dev.example.com
            token_secret: MCP_DEV_TOKEN

    env:
      MCPC_HOME_DIR: /tmp/mcpc-${{ matrix.server.name }}
      MCPC_JSON: 1

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: npm install -g @apify/mcpc

      - name: Test ${{ matrix.server.name }}
        env:
          MCP_SERVER_URL: ${{ matrix.server.url }}
          MCP_TOKEN: ${{ secrets[matrix.server.token_secret] }}
        run: bash scripts/test-mcp-ci.sh
```

### Test multiple tools in parallel

```yaml
name: Per-Tool Tests
on: [push]

jobs:
  discover-tools:
    runs-on: ubuntu-latest
    outputs:
      tools: ${{ steps.list.outputs.tools }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: npm install -g @apify/mcpc
      - id: list
        env:
          MCP_TOKEN: ${{ secrets.MCP_TOKEN }}
          MCPC_JSON: 1
          MCPC_HOME_DIR: /tmp/mcpc-discover
        run: |
          mcpc https://mcp.example.com connect @discover \
            --header "Authorization: Bearer $MCP_TOKEN"
          TOOLS=$(mcpc @discover tools-list | jq -c '[.[].name]')
          echo "tools=$TOOLS" >> "$GITHUB_OUTPUT"
          mcpc @discover close

  test-tool:
    needs: discover-tools
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        tool: ${{ fromJson(needs.discover-tools.outputs.tools) }}
    env:
      MCPC_HOME_DIR: /tmp/mcpc-tool-${{ matrix.tool }}
      MCPC_JSON: 1
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: npm install -g @apify/mcpc
      - name: Test tool ${{ matrix.tool }}
        env:
          MCP_TOKEN: ${{ secrets.MCP_TOKEN }}
        run: |
          mcpc https://mcp.example.com connect @tool-test \
            --header "Authorization: Bearer $MCP_TOKEN"
          mcpc @tool-test tools-get "${{ matrix.tool }}" | jq '.'
          mcpc @tool-test close
```

## Environment isolation

### Why isolation matters

Each CI job should have its own `MCPC_HOME_DIR` to prevent:

- Session name collisions between parallel jobs
- Stale session files from previous runs
- OAuth profile leakage between environments

### Isolation pattern

```bash
# Unique home per job (using CI job ID or PID)
export MCPC_HOME_DIR="/tmp/mcpc-ci-${CI_JOB_ID:-$$}"
mkdir -p "$MCPC_HOME_DIR"

# Run tests...

# Cleanup (optional — /tmp is ephemeral in most CI)
rm -rf "$MCPC_HOME_DIR"
```

### Unique session names

```bash
# Include run ID to avoid collisions
SESSION="ci-${GITHUB_RUN_ID:-$$}-${GITHUB_RUN_ATTEMPT:-1}"

# Or use a hash of the job matrix
SESSION="ci-$(echo "$MATRIX_KEY" | md5sum | cut -c1-8)"
```

## Monitoring and artifacts

### Upload mcpc logs on failure

```yaml
- name: Upload mcpc logs
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: mcpc-logs-${{ github.run_id }}
    path: ${{ env.MCPC_HOME_DIR }}/logs/
    retention-days: 7
```

### Export test results as JSON artifact

```bash
# At end of test script, export summary
jq -n \
  --arg server "$SERVER_NAME" \
  --arg protocol "$PROTOCOL" \
  --argjson tools "$TOOL_COUNT" \
  --argjson resources "$RESOURCE_COUNT" \
  --argjson failures "$FAILURES" \
  '{server: $server, protocol: $protocol, tools: $tools, resources: $resources, failures: $failures}' \
  > "$MCPC_HOME_DIR/test-results.json"
```

## Exit code propagation

mcpc exit codes map cleanly to CI failure semantics:

| Exit code | Meaning | CI behavior |
|---|---|---|
| 0 | Success | Job passes |
| 1 | Client error (bad args) | Job fails — fix test script |
| 2 | Server error (tool failed) | Job fails — investigate server |
| 3 | Network error | Job fails — check connectivity/timeouts |
| 4 | Auth error | Job fails — rotate secrets |

Use `set -e` (or `set -euo pipefail`) in bash scripts so any non-zero exit code fails the CI job immediately. Use `trap` for cleanup to ensure sessions are closed even on failure.
