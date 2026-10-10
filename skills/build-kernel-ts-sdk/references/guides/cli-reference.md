# Kernel CLI Reference

Complete reference for `@onkernel/cli@0.47.0` (`kernel`). The CLI surfaces the exact same underlying API as the TypeScript SDK (`@onkernel/sdk@0.123.0`).

Install or upgrade:

```bash
npm install -g @onkernel/cli@0.47.0
# or brew install kernel/tap/kernel
# or pnpm install -g @onkernel/cli@0.47.0
kernel upgrade
```

## Global Flags

Available across all `kernel` subcommands:

| Flag | Description |
|---|---|
| `--project <project-id>` | Scope command to a project ID (`proj_...`; also reads `KERNEL_PROJECT` env var). Project names are accepted only by commands whose arguments explicitly say `<id-or-name>`. |
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

# Non-interactive / scripted (pass -y, --yes to overwrite existing directory without prompt):
kernel create --name my-app --language typescript --template sample-app --yes
kernel create -n my-agent -l ts -t stagehand -y
```

### Supported Templates
- `sample-app` — Minimal Kernel app with Playwright integration [ts, py]
- `stagehand` — Stagehand v4 SDK integration (`@browserbasehq/stagehand^4`) [ts]
- `magnitude` — Magnitude SDK integration [ts]
- `claude-agent-sdk` — Claude Agent SDK browser automation agent [ts, py]
- `anthropic-computer-use` — Anthropic Computer Use agent [ts, py]
- `openai-computer-use` — OpenAI Computer Using Agent [ts, py]
- `gemini-computer-use` — Google Gemini computer use agent [ts, py]
- `tzafon` — Tzafon Northstar CUA Fast computer use agent [ts, py]
- `yutori` — Yutori n1.5 computer use agent [ts, py]
- `captcha-solver` — Auto-CAPTCHA solving demonstration [ts, py]
- `browser-use` — Browser Use SDK [py]

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
  --proxy-name us-east-isp \
  --proxy-route "api.example.com=name:res-proxy" \
  --telemetry=all

# Create GPU session with video memory selection
kernel browsers create --gpu --video-memory 4GiB

# Direct internet egress (bypass default stealth proxy)
kernel browsers create --proxy-mode direct --stealth

# Zero Data Retention with OTLP export
kernel browsers create --telemetry-storage off --telemetry-export-otlp prod-datadog

# Update a running browser session
kernel browsers update <id-or-name> \
  --name new-name \
  --tag env=staging \
  --start-url "https://example.com/checkout"

# Delete a session
kernel browsers delete <id-or-name>

# In-VM Browser REPL (code passed as positional argument or piped via stdin)
kernel browsers repl <id-or-name>
kernel browsers repl <id-or-name> "await gotoUrl('https://example.com'); repl.write(await pageInfo());"

# WebMCP Tool Discovery & Invocation
kernel browsers webmcp list <id-or-name> [--exclude-custom]
kernel browsers webmcp invoke <id-or-name> --tool-ref <tool_ref> --input '{"sku":"ABC-123"}'

# In-VM Process Execution
kernel browsers process exec <id-or-name> -- uname -a

# Browser Telemetry
kernel browsers telemetry stream <id-or-name>
kernel browsers telemetry events <id-or-name> --category network --type proxy_error
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
kernel profiles download <id-or-name> --to ./extracted-profile-dir
kernel profiles delete <id-or-name>
```

---

## 6. Proxies: `kernel proxies`

Manage dedicated ISP, residential, mobile, and custom proxy configurations.

```bash
kernel proxies list
kernel proxies get <id>
kernel proxies create --name my-isp --type isp --country US
kernel proxies create --name my-res --type residential --country US --state CA --city losangeles
kernel proxies create --name corp-mitm --type custom --host proxy.corp.net --port 8080 --ca-bundle ./ca.pem
kernel proxies check <id> [--url https://target.com]   # test reachability
kernel proxies delete <id> [--yes]
```

---

## 7. Extensions: `kernel extensions`

Pre-install unpacked or packed Chrome extensions into sessions.

```bash
kernel extensions list
kernel extensions get <id-or-name>
kernel extensions upload ./adblock-dir-or-zip --name adblock
kernel extensions download <id-or-name> --to ./downloaded-ext
kernel extensions build-web-bot-auth --to ./built-ext [--upload web-bot-auth-v1]
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
  --region aws.us-east-1a

# Stream build/runtime logs
kernel deploy logs <deployment_id> --follow
kernel deploy history [app_name]
kernel deploy get <deployment_id>
kernel deploy delete <deployment_id> --yes

# Invoke actions
# Note: CLI returns immediately upon queueing by default; pass --sync (-s) to wait and stream logs until completion
kernel invoke my-app analyze --payload '{"url":"https://example.com"}' --sync
kernel invoke my-app analyze --payload-file ./payload.json
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

## 9. Managed Auth, Credentials & Providers

Manage end-user authentication into upstream SaaS applications, encrypted credentials, and external credential providers.

```bash
# Authentication Connections
kernel auth connections list
kernel auth connections get <id>
kernel auth connections create \
  --domain netflix.com \
  --profile-name netflix-user-1 \
  --health-check-interval 3600
kernel auth connections login <id>
kernel auth connections follow <id>
kernel auth connections timeline <id>
kernel auth connections delete <id>

# Stored Credentials
kernel credentials list
kernel credentials get <name>
kernel credentials create \
  --name netflix-creds \
  --domain netflix.com \
  --value username=user@example.com \
  --value password="secret" \
  --totp-secret "JBSWY3DPEHPK3PXP"
kernel credentials totp-code <name>
kernel credentials delete <name>

# Credential Providers (1Password)
kernel credential-providers list
kernel credential-providers get <id>
kernel credential-providers create \
  --name onepassword \
  --provider-type onepassword \
  --token $OP_TOKEN
kernel credential-providers list-items <id>
kernel credential-providers test <id>
kernel credential-providers delete <id>
```

---

## 10. Web Search: `kernel search`

Perform multi-provider search queries and page content extraction.

```bash
# Discover active search providers
kernel search providers

# Auto-routed search
kernel search "kernel browser sdk tutorial" --max-results 5

# Search pinned to Exa provider
kernel search "deep web research agents" --provider exa --max-results 5

# Advanced search with domain filter and content using --request JSON
kernel search --request '{"query":"deep web research agents","strategy":{"provider":"exa"},"include_domains":["github.com","arxiv.org"],"content":{"format":"markdown"}}'

# Inspect retained search without incurring provider cost
kernel search get srch_01jsearch12345

# Deferred browser rendering of top search results
kernel search contents srch_01jsearch12345 --limit 3 --content-source browser --content-browser-mode render
```

---

## 11. Vaults: `kernel vaults` & `kernel vault-provider-configs`

Manage secure credential and payment vaults, Link wallets, and AgentCards.

```bash
kernel vaults list
kernel vaults create --name checkout-vault
kernel vaults get checkout-vault
kernel vaults items list checkout-vault
kernel vaults credentials create checkout-vault user-login --spec-file ./creds.json
kernel vaults wallets create checkout-vault wallet-1 --provider link --spec '{"authorization":{"method":"oauth","client":{"type":"kernel_managed"}}}'
kernel vaults cards create checkout-vault card-1 --provider agentcard --spec '{"wallet":"wallet-1","merchant":"Example Shop","amount":1234,"currency":"usd","checkout_origin":"https://store.example.com"}'
# Invocations use --spec or --spec-file:
kernel vaults items invoke checkout-vault user-login fill --spec-file ./fill-spec.json
kernel vaults items invoke checkout-vault card-1 prepare_checkout --spec '{"browser_id":"<id>","environment":"production","merchant_origin":"https://store.example.com","psp":"square"}'

# Organization-scoped Vault Provider Configurations (Link & AgentCard)
kernel vault-provider-configs list
kernel vault-provider-configs get <id-or-name>
kernel vault-provider-configs create --name link-prod --provider link --credentials-file ./link-creds.json
kernel vault-provider-configs update <id-or-name> --credentials-file ./updated.json
kernel vault-provider-configs delete <id-or-name>
```

---

## 12. Projects & API Keys: `kernel projects` / `kernel api-keys`

```bash
# Projects (all routed under /org/projects)
kernel projects list
kernel projects get <id-or-name>
kernel projects create production
kernel projects update <id-or-name> --name prod-v2
kernel projects delete <id-or-name>
kernel projects limits get <id-or-name>

# API Keys
kernel api-keys list
kernel api-keys get <id>
kernel api-keys create --name ci-key [--project-id <proj_id>]
# Rotation requires days_to_expire >= expire_in_days:
kernel api-keys rotate <id> --days-to-expire 30 --expire-in-days 7
# Deleting current authenticating key is prohibited (HTTP 400 cannot_delete_current_key):
kernel api-keys delete <id>
```

---

## 13. Organization & Audit Logs: `kernel org` / `kernel audit-logs`

```bash
kernel org entitlements
kernel org limits get
kernel audit-logs search --start "2026-10-01T00:00:00Z" --end "2026-10-08T00:00:00Z" --search 403
# Download outputs a gzip-compressed archive (.jsonl.gz):
kernel audit-logs download --start "2026-10-01T00:00:00Z" --end "2026-10-08T00:00:00Z" --to ./audit-logs.jsonl.gz

# Continuous S3 Export Destinations
kernel audit-logs export list
kernel audit-logs export create --name s3-stream --bucket my-bucket --prefix audit/
kernel audit-logs export test <id>
kernel audit-logs export pause <id>
kernel audit-logs export resume <id>
kernel audit-logs export delete <id>
```

---

## 14. MCP Server & Utility: `kernel mcp` / `status`

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
