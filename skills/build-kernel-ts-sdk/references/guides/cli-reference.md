# Kernel CLI Reference

Complete reference for `@onkernel/cli` (`kernel`). The CLI surfaces the same underlying API as the TypeScript SDK (`@onkernel/sdk`).

Install or upgrade:

```bash
npm install -g @onkernel/cli
# or brew install kernel/tap/kernel
# or pnpm install -g @onkernel/cli
kernel upgrade
```

## Global Flags

Available across all `kernel` subcommands:

| Flag | Description |
|---|---|
| `--project <project-id-or-name>` | Scope command to a project ID or name (also reads `KERNEL_PROJECT` env var). |
| `--output json`, `-o json` | Output machine-readable JSON or streaming JSONL. |
| `--log-level <level>` | Log level: `trace`, `debug`, `info`, `warn`, `error`, `fatal`, `print`. |
| `--no-color` | Disable ANSI color formatting. |
| `--version`, `-v` | Print CLI version. |

---

## 1. App Scaffolding: `kernel create`

Scaffold a new Kernel project from a curated template.

```bash
# Interactive mode:
kernel create

# Non-interactive / scripted (all three flags required; no --yes flag exists):
kernel create --name my-app --language typescript --template sample-app
kernel create -n my-agent -l ts -t stagehand
```

### TypeScript Templates
- `sample-app` — Minimal Kernel app with Playwright integration
- `captcha-solver` — Auto-CAPTCHA solving demonstration
- `anthropic-computer-use` — Anthropic Computer Use agent
- `openai-computer-use` — OpenAI Computer Using Agent (CUA)
- `gemini-computer-use` — Google Gemini computer use agent
- `claude-agent-sdk` — Claude Agent SDK browser automation agent
- `stagehand` — Stagehand v4 SDK integration (`@browserbasehq/stagehand^4`)
- `magnitude` — Magnitude SDK integration
- `tzafon` — Tzafon Northstar CUA Fast computer use agent
- `yutori` — Yutori n1.5 computer use agent

### Python Templates
- `sample-app`, `captcha-solver`, `anthropic-computer-use`, `openai-computer-use`, `gemini-computer-use`, `claude-agent-sdk`, `openagi-computer-use`, `browser-use`, `tzafon`, `yutori`

---

## 2. Authentication: `kernel auth` / `login` / `logout`

```bash
kernel login                # Web-based or token login
kernel logout               # Clear stored credentials
kernel auth status          # Inspect current session and auth validity
kernel auth whoami          # Display authenticated user or machine identity
kernel auth token           # Print current auth token for scripts
kernel auth context         # Inspect effective scope, credential scope, and org ID
```

---

## 3. Browsers: `kernel browsers`

Drive, inspect, and debug browser sessions.

```bash
# List and inspect
kernel browsers list [--status active|all] [--region <region>] [--tag key=value]
kernel browsers get <id-or-name>

# Create a browser session
kernel browsers create \
  --stealth \
  --headless=false \
  --timeout 300 \
  --viewport 1920x1080 \
  --memory 16GiB \
  --name my-session \
  --tag env=prod \
  --start-url "https://example.com" \
  --proxy-route "*.example.com=res-proxy" \
  --private-host "10.0.0.0/8" \
  --telemetry=all

# Update a running browser session
kernel browsers update <id-or-name> \
  --name new-name \
  --tag env=staging \
  --start-url "https://example.com/checkout"

# Delete a session
kernel browsers delete <id-or-name>

# In-VM Browser REPL (requires CLI v0.38.2+)
kernel browsers repl <id-or-name>

# WebMCP Tool Discovery & Invocation
kernel browsers webmcp list <id-or-name>
kernel browsers webmcp invoke <id-or-name> --tool-ref <ref> --input '{"query":"laptop"}'

# Custom WebMCP Tools (v0.118.0+)
kernel browsers webmcp custom-tools list <id-or-name>
kernel browsers webmcp custom-tools add <id-or-name> --namespace mytools --source-file ./tools.js [--force-overwrite]
kernel browsers webmcp custom-tools remove <id-or-name> <custom_tool_id>

# In-VM Process Execution
kernel browsers process <id-or-name> --command "uname -a"

# Browser Telemetry
kernel browsers telemetry stream <id-or-name> [--last-event-id <id>]
kernel browsers telemetry events <id-or-name> [--category control,captcha] [--type proxy_error]
```

---

## 4. Browser Pools: `kernel browser-pools`

Manage pre-warmed pools of browsers for high concurrency.

```bash
# List and inspect
kernel browser-pools list
kernel browser-pools get <id-or-name>

# Create a pool (memory supports 8GiB or 16GiB; auto-standby enabled)
kernel browser-pools create my-pool \
  --size 10 \
  --fill-rate 25 \
  --memory 16GiB \
  --stealth \
  --timeout 600 \
  --profile-name baseline-prof \
  --refresh-on-profile-update

# Update pool configuration
kernel browser-pools update my-pool \
  --size 20 \
  --fill-rate 50 \
  --memory 16GiB \
  --discard-all-idle \
  --clear-start-url

# Acquire a browser with dynamic profile binding
kernel browser-pools acquire my-pool --timeout 30 --profile-name user-42 --start-url "https://app.com"

# Release a browser back to pool
kernel browser-pools release my-pool --session-id <session_id> [--reuse=true|false]

# Flush idle instances (refills automatically)
kernel browser-pools flush my-pool

# Delete a pool
kernel browser-pools delete my-pool [--force]
```

---

## 5. Profiles: `kernel profiles`

Persist and reuse cookies, localStorage, and authentication state.

```bash
kernel profiles list [--query <text>]
kernel profiles get <id-or-name>
kernel profiles create --name user-42
kernel profiles update <id-or-name> --name new-name
kernel profiles download <id-or-name> --format tar.zst --output ./profile.tar.zst
kernel profiles upload --name restored-user --file ./profile.tar.zst
kernel profiles delete <id-or-name>
```

---

## 6. Proxies: `kernel proxies`

Manage dedicated ISP, residential, mobile, and custom proxy configurations.

```bash
kernel proxies list
kernel proxies get <id>
kernel proxies create --name my-proxy --type residential --country US --state CA
kernel proxies update <id> --name new-name
kernel proxies check <id> [--url https://target.com]   # test reachability
kernel proxies delete <id>
```

---

## 7. Extensions: `kernel extensions`

Pre-install unpacked or packed Chrome extensions into sessions.

```bash
kernel extensions list
kernel extensions get <id-or-name>
kernel extensions upload --name adblock --file ./adblock.zip
kernel extensions download <id-or-name> --output ./ext.zip
kernel extensions build ./src --output ./dist.zip
kernel extensions delete <id-or-name>
```

---

## 8. Apps & Deployments: `kernel deploy` / `invoke` / `app`

Deploy long-running code directly co-located with browser VMs.

```bash
# Deploy local code
kernel deploy app.ts \
  --version 1.0.0 \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env-file .env \
  --force \
  -o json

# Deploy from GitHub
kernel deploy github \
  --url https://github.com/org/repo \
  --ref main \
  --entrypoint app.ts \
  --path services/worker \
  --github-token $GITHUB_TOKEN \
  --region aws.us-east-1a

# Stream build/runtime logs
kernel deploy logs <deployment_id> --follow --since 5m --with-timestamps
kernel deploy history [app_name]
kernel deploy get <deployment_id>
kernel deploy delete <deployment_id> --yes

# Invoke actions
# Note: CLI defaults to async queueing unless --sync is passed!
kernel invoke my-app analyze --payload '{"url":"https://example.com"}'
kernel invoke my-app analyze --payload-file ./payload.json --sync
kernel invoke get <invocation_id>
kernel invoke history
kernel invoke update <invocation_id> --status failed
kernel invoke delete-browsers <invocation_id>

# Apps catalog & logs
kernel app list
kernel app history <app_name>
kernel app delete <app_name>
kernel logs <app_name> --follow
```

---

## 9. Managed Auth: `kernel managed-auth`

Manage end-user authentication into upstream SaaS applications.

```bash
# Connections
kernel managed-auth connections list
kernel managed-auth connections get <id>
kernel managed-auth connections create \
  --domain netflix.com \
  --profile-name netflix-user-1 \
  --save-credentials \
  --health-checks \
  --auto-reauth \
  --health-check-interval 3600
kernel managed-auth connections login <id>
kernel managed-auth connections timeline <id> --type login|reauth|health_check
kernel managed-auth connections delete <id>

# Stored Credentials
kernel managed-auth credentials list
kernel managed-auth credentials get <name>
kernel managed-auth credentials create \
  --name netflix-creds \
  --domain netflix.com \
  --username user@example.com \
  --password "secret" \
  --totp-secret "JBSWY3DPEHPK3PXP"
kernel managed-auth credentials delete <name>

# Credential Providers (1Password)
kernel managed-auth providers list
kernel managed-auth providers get <id-or-name>
kernel managed-auth providers connect 1password --token $OP_TOKEN
kernel managed-auth providers delete <id-or-name>
```

---

## 10. Projects: `kernel projects`

Manage project environments. All project routes operate under `/org/projects`.

```bash
kernel projects list
kernel projects get <id-or-name>
kernel projects create --name production
kernel projects update <id-or-name> --name prod-v2
kernel projects delete <id-or-name>

# Per-Project Limits
kernel projects limits get <id-or-name>
kernel projects limits update <id-or-name> --max-concurrent-sessions 20
```

---

## 11. API Keys: `kernel api-keys`

Provision, inspect, rotate, and revoke API keys under `/org/api_keys`.

```bash
kernel api-keys list
kernel api-keys get <id>
kernel api-keys create --name ci-key [--project-id <proj_id>]
kernel api-keys update <id> --name new-name
kernel api-keys rotate <id> --expire-in-days 7   # issues replacement key, sets grace period
kernel api-keys delete <id>                     # returns 400 cannot_delete_current_key if self
```

---

## 12. Organization: `kernel org`

Inspect plan entitlements and concurrency limits.

```bash
# View active plan features, regional permissions, and add-ons
kernel org entitlements

# Concurrency & usage limits (unified on-demand + pool concurrency)
kernel org limits get
kernel org limits set --default-project-concurrency 10
```

---

## 13. Audit Logs: `kernel audit-logs`

Search and export organization security audit logs.

```bash
kernel audit-logs search --start "2026-10-01T00:00:00Z" --end "2026-10-08T00:00:00Z" --status 403
kernel audit-logs download --start "2026-10-01T00:00:00Z" --end "2026-10-08T00:00:00Z" --output ./audit.jsonl
kernel audit-logs export --destination s3://my-bucket/audit/
```

---

## 14. Web Search: `kernel search`

Search the web and retrieve ranked results or contents.

```bash
kernel search "kernel unikernel browser"
kernel search get <search_id>
kernel search providers
```

---

## 15. Vaults: `kernel vaults`

Manage secure credential and payment vaults, Link/AgentCard wallets, and autofill.

```bash
kernel vaults list
kernel vaults create --name checkout-vault
kernel vaults wallets connect --vault checkout-vault --provider link
kernel vaults cards request --vault checkout-vault --amount 5000 --currency USD
kernel vaults items list --vault checkout-vault
kernel vaults items fill --vault checkout-vault --item <item_id> --browser <session_id>
```

---

## 16. MCP Server & Utility: `kernel mcp` / `status`

```bash
# Install Kernel MCP configuration into client environments
kernel mcp install --target antigravity   # Google Antigravity
kernel mcp install --target claude        # Claude Desktop / Code
kernel mcp install --target cursor        # Cursor
kernel mcp install --target windsurf      # Windsurf
kernel mcp server                         # Start stdio MCP server

# Platform health & shell completion
kernel status [--output json]
kernel upgrade [--dry-run]
source <(kernel completion zsh)
```
