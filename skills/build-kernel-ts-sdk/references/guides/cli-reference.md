# Kernel CLI Reference

Reference for `@onkernel/cli@0.47.0` (`kernel`), checked against `cmd/*.go` at tag v0.47.0. The CLI calls the same API as `@onkernel/sdk@0.123.0`. Run `kernel <command> --help` for flags not listed here.

```bash
npm install -g @onkernel/cli@0.47.0     # or: brew install kernel/tap/kernel / pnpm install -g @onkernel/cli
kernel upgrade [--dry-run]              # refreshes the Homebrew tap first when installed via brew
```

## Global flags and environment

| Flag / env | Meaning |
|---|---|
| `--project <id-or-name>` / `KERNEL_PROJECT` | Scope every request to a project. Sends `X-Kernel-Project`, which accepts a project ID **or an exact project name** (CLI source + `project_scope_test.go`). The docs page `reference/cli/projects` still says "ID only" and `X-Kernel-Project-Id`; the shipped CLI does not. |
| `--log-level <level>` | `trace`, `debug`, `info`, `warn` (default), `error`, `fatal`, `print`. |
| `--no-color` / `NO_COLOR` | Disable ANSI styling. |
| `-v`, `--version` | Print the CLI version (on `kernel invoke`, `-v` is `--version <app version>`). |
| `KERNEL_API_KEY` | API key; takes priority over `kernel login` OAuth tokens. |
| `KERNEL_BASE_URL` | Override the API base URL. |
| `KERNEL_NO_UPDATE_CHECK=1` | Disable the update notice. |
| `-o json`, `--output json` | **Per-command**, not global: most list/get/create commands accept it (JSON object/array); `deploy`/`invoke` emit JSONL events. Check `--help`. |

**Non-interactive shells:** any command that would show a confirmation fails fast instead of hanging. Pass `--yes`/`-y` on destructive commands (`deploy delete`, `app delete`, `profiles delete`, `extensions delete`, `credentials delete`, `credential-providers delete`, `auth connections delete`, `proxies delete`, `api-keys rotate|delete`, `telemetry destinations delete`, `vault-provider-configs delete`, `vaults delete`, `vaults items delete`, `browsers create`) and supply every required flag (`kernel create` lists all missing inputs in one error).

**Command groups in v0.47.0** (26 top-level commands besides `help`/`completion`): `create`, `login`, `logout`, `auth`, `browsers`, `browser-pools`, `profiles`, `proxies`, `extensions`, `deploy`, `invoke`, `app`, `logs`, `credentials`, `credential-providers`, `vaults`, `vault-provider-configs`, `search`, `projects`, `api-keys`, `org`, `audit-logs`, `telemetry`, `mcp`, `status`, `upgrade`. Aliases (cobra `Aliases`): `browser`, `browser-pool|pool|pools`, `profile`, `proxy`, `extension`, `apps`, `log`, `credential|creds|cred`, `credential-provider|cred-providers|cred-provider`, `vault`, `api-key|apikeys|apikey`, `audit-log|auditlogs|auditlog`, `organization`, `upgrade` = `update`.

---

## 1. App scaffolding: `kernel create`

```bash
kernel create                                   # interactive
kernel create -n my-agent -l ts -t stagehand -y # non-interactive; -y overwrites an existing directory
```

Flags: `--name/-n`, `--language/-l` (`typescript|ts`, `python|py`), `--template/-t`, `--yes/-y`. Templates (`pkg/create/templates.go`):

| Template | Languages |
|---|---|
| `sample-app`, `captcha-solver` | ts, py |
| `anthropic-computer-use`, `openai-computer-use`, `gemini-computer-use` | ts, py |
| `claude-agent-sdk`, `yutori`, `tzafon` | ts, py |
| `stagehand` (Stagehand v4, `@browserbasehq/stagehand ^4`) | ts |
| `browser-use`, `openagi-computer-use` | py |

There is no `magnitude` template in 0.47.0 (docs list one). `kernel create --help` still describes `stagehand` as "Stagehand v3"; the shipped template depends on `@browserbasehq/stagehand ^4.0.0`. The command runs `pnpm install` (TS) or `uv venv` (Python) itself if the tool is on PATH; TS templates keep the entrypoint at the project root (`index.ts`).

## 2. Authentication: `login`, `logout`, `auth`

```bash
kernel login [--force]      # browser OAuth (PKCE); `--force` re-runs the flow
kernel logout
kernel auth                 # status: auth method, API URL, scope, token expiry
kernel auth context [-o json]  # principal, auth method/source, credential scope, effective scope
```

There is no `kernel auth status|whoami|token`. `KERNEL_API_KEY` bypasses OAuth. OAuth logins are org-wide; use `--project` to narrow.

## 3. Browsers: `kernel browsers`

```bash
kernel browsers list [--status active|deleted|all] [--region us-east|us-west|eu-west|ap-southeast] [--tag k=v] [--query t] [--limit n] [--offset n]
kernel browsers get <id-or-name> [--include-deleted]
kernel browsers view <id-or-name>             # live view URL
kernel browsers create \
  --stealth --headless=false --timeout 300 --viewport 1920x1080 --memory 16GiB \
  --name my-session --tag env=prod --start-url "https://example.com" \
  --proxy-name us-east-isp --proxy-route "api.example.com=name:res-proxy" --telemetry=all
kernel browsers create --gpu --video-memory 4GiB      # --video-memory requires --gpu
kernel browsers create --proxy-mode direct --stealth  # or --proxy-id / --proxy-name / --proxy-mode default
kernel browsers create --telemetry-storage off --telemetry-export-otlp prod-datadog  # destination from `kernel telemetry destinations`
kernel browsers update <id-or-name> --name new-name --tag env=staging --start-url "https://example.com/checkout"
kernel browsers delete <id-or-name> [more ids...]     # no --yes flag in 0.47.0 (the docs page lists one); it never prompts
```

Other `create` flags: `--kiosk`, `--region`, `--invocation-id`, `--profile-id|--profile-name` (+ `--save-changes`), `--extension` (repeatable), `--vault` (repeatable, max 20, create-only), `--pool-id|--pool-name` (acquire from a pool instead), `--private-host`, `--allowed-host` (egress allowlist; requires proxy v3, not with pools), `--chrome-policy|--chrome-policy-file`, `--telemetry-cdp-exclude`, `--viewport-interactive`, `-y`. `--timeout` defaults to 60. `update` also takes `--proxy-id|--proxy-name|--proxy-mode|--clear-proxy|--disable-default-proxy`, `--telemetry`, `--save-changes`, `--profile-*`, `--viewport` (+ `--force` during live view/recording), `--clear-name`, `--clear-tags`, `--allowed-host|--clear-allowed-hosts`.

Drive and inspect a running browser (all take `<id-or-name>`):

```bash
kernel browsers repl <id> "await gotoUrl('https://example.com'); repl.write(await pageInfo());"  # code arg or stdin; --reset, --timeout-sec, --image-dir
kernel browsers playwright execute <id> "await page.goto('https://example.com'); return await page.title();" [--executor name] [--timeout s] [-o json]
kernel browsers playwright executors list|delete <id> [<executor>]   # up to 8 named executors
kernel browsers webmcp list <id> [--exclude-custom] [--json]
kernel browsers webmcp invoke <id> --tool-ref <tool_ref> --input '{"sku":"ABC-123"}' [--input-file f] [--timeout-sec 1-120]
kernel browsers webmcp custom-tools list|add|remove <id> ...        # add: --namespace, --source-file, --force-overwrite-namespace
kernel browsers computer click-mouse|move-mouse|screenshot|type|press-key|scroll|drag-mouse|set-cursor|get-mouse-position|batch|read-clipboard|write-clipboard <id> ...
kernel browsers curl <id> <url> [-X m] [-H "K: V"] [-d body] [--data-file f] [--max-time 30] [-o file] [-I] [-i] [-f] [-s]
kernel browsers process exec <id> -- uname -a            # also: spawn (--allocate-tty), kill, status, stdin, stdout-stream, resize
kernel browsers fs new-directory|delete-directory|delete-file|download-dir-zip|file-info|list-files|move|read-file|set-permissions|upload|upload-zip|write-file <id> ...  # plus: fs watch start|stop|events
kernel browsers replays list|start|stop|download <id> ...   # start: --framerate --max-duration --record-audio; download <id> <replay-id> -f <file> (docs say -o/--output; the binary has -f/--output-file)
kernel browsers logs stream <id> --source path|supervisor [--path p | --supervisor-process chromium] [--follow]
kernel browsers telemetry stream <id> [--categories a,b] [--types x,y] [--seq n] [--replay all] [-o json]
kernel browsers telemetry events <id> --categories network --types proxy_error [--since 5m] [--until t] [--order asc|desc] [--limit n] [--offset n] [--all]
kernel browsers extensions upload <id> <extension-path>...   # restarts Chromium
kernel browsers ssh <id> [-i key] [-L spec] [-R spec] [--setup-only]   # needs websocat
```

Telemetry categories: `console,network,page,interaction,control,platform,connection,system,screenshot,captcha,monitor`. Flags are plural: `--categories`, `--types`.

Required flags (cobra `MarkFlagRequired`; omitting them fails before any request): `logs stream --source`; `webmcp invoke --tool-ref` plus one of `--input|--input-file`; `webmcp custom-tools add --namespace --source-file`; `process stdin --data-b64`; `process resize --cols --rows`; `fs` commands `--path` (`move`: `--src --dest`; `upload-zip`: `--zip --dest-dir`; `write-file`: `--path --source`; `set-permissions`: `--path --mode`); `computer` `click-mouse|move-mouse|scroll --x --y`, `screenshot --to`, `type --text`, `press-key --key`, `set-cursor --hidden`, `batch --actions`, `write-clipboard --text`.

## 4. Browser pools: `kernel browser-pools`

```bash
kernel browser-pools list [--name n] [--query t] [--region r] [--limit n] [--offset n]
kernel browser-pools get <id-or-name>
kernel browser-pools create my-pool --size 10 --fill-rate 25 --memory 16GiB --stealth --timeout 600 \
  --profile-name baseline-prof --refresh-on-profile-update      # --memory: 8GiB (default) or 16GiB
kernel browser-pools update my-pool --size 20 --discard-all-idle --clear-start-url
kernel browser-pools acquire my-pool --timeout 30 --profile-name user-42 --save-changes --start-url "https://app.com" [--name n] [--tag k=v]
kernel browser-pools release my-pool --session-id <session_id> [--reuse=true|false]
kernel browser-pools flush my-pool
kernel browser-pools delete my-pool [--force]
```

`create|update` also take `--headless`, `--kiosk`, `--proxy-id`, `--proxy-route`, `--private-host`, `--extension`, `--viewport`, `--chrome-policy[-file]`, `--telemetry`; `create` also takes `--region` (fixed at creation; no `--region` on `update`); `update` adds `--clear-profile|--clear-proxy|--clear-extensions|--clear-private-hosts|--clear-proxy-routes|--clear-chrome-policy`. `--save-changes` exists on `acquire` only (it requires `--profile-id|--profile-name`); the docs page lists it on `create`/`update`, the CLI does not have it there.

## 5. Profiles: `kernel profiles`

```bash
kernel profiles list [--name n] [--query text] [--page n] [--per-page n]
kernel profiles get <id-or-name>
kernel profiles create --name user-42
kernel profiles update <id-or-name> --name new-name
kernel profiles download <id-or-name> --to ./extracted-profile-dir [--format tar.zst|tar]
kernel profiles delete <id-or-name> [-y]
```

## 6. Proxies: `kernel proxies`

```bash
kernel proxies list [--name n] [--query t] [--limit n] [--offset n]
kernel proxies get <id>
kernel proxies create --name my-isp --type isp --country US
kernel proxies create --name my-res --type residential --country US --state CA --city losangeles
kernel proxies create --name corp-mitm --type custom --host proxy.corp.net --port 8080 --ca-bundle ./ca.pem
kernel proxies update <id> --name new-name          # only the name can change
kernel proxies check <id> [--url https://target.com]
kernel proxies delete <id> [-y]
```

`create` also takes `--protocol http|https` (default https), `--zip`, `--asn`, `--os windows|macos|android` (mobile), `--username/--password` (custom), `--bypass-host`. Types: `isp|residential|mobile|custom`.

## 7. Extensions: `kernel extensions`

```bash
kernel extensions list [--name n] [--query t] [--limit n] [--offset n]
kernel extensions get <id-or-name>
kernel extensions upload ./unpacked-extension-dir --name adblock   # directory only in 0.47.0 (docs also claim zip)
kernel extensions download <id-or-name> --to ./downloaded-ext      # extracts into an empty directory (the --help text says "zip file path"; the code unzips)
kernel extensions download-web-store <chrome-web-store-url> --to ./ext [--os mac|win|linux]
kernel extensions build-web-bot-auth --to ./built-ext [--upload web-bot-auth-v1] [--key jwk] [--url u] [--signature-agent u]
kernel extensions delete <id-or-name> [-y]
```

## 8. Apps: `deploy`, `invoke`, `app`, `logs`

```bash
# Deploy: zips the ENTRYPOINT'S DIRECTORY (honours .gitignore, includes hidden files); package.json + a lockfile must be in it
kernel deploy app.ts --version 1.0.0 --env OPENAI_API_KEY=$OPENAI_API_KEY --env-file .env --force -o json
kernel deploy github --url https://github.com/org/repo --ref main --entrypoint app.ts [--path apps/api] [--github-token t] [--region aws.us-east-1a]   # --url, --ref, --entrypoint are required
kernel deploy logs <deployment_id> [--follow] [--since 5m] [--with-timestamps]
kernel deploy history [app_name] [--limit 20] [--app-version v] [--query q]
kernel deploy get <deployment_id>
kernel deploy delete <deployment_id> --yes

# Invoke
kernel invoke my-app analyze --payload '{"url":"https://example.com"}'     # default: async invocation, then follows the SSE stream and prints logs + result
kernel invoke my-app analyze --payload-file ./payload.json                  # '-' reads stdin
kernel invoke my-app analyze --sync --payload '{...}'                       # single POST, times out after 60 s, no log stream
kernel invoke my-app analyze --async-timeout 1800 --since 5m -v 1.0.0
kernel invoke get <invocation_id>
kernel invoke history [--app a] [--action a] [--status queued|running|succeeded|failed] [--deployment-id id] [--version v] [--since t] [--limit 100] [--offset n]
kernel invoke browsers <invocation_id>
kernel invoke update <invocation_id> --status succeeded|failed [--output '<json>']
kernel invoke delete-browsers <invocation_id>

# Apps and logs
kernel app list [--name n] [--version v] [--query q] [--limit 20]
kernel app history <app_name> [--limit 20]
kernel app delete <app_name> [--version v] --yes
kernel logs <app_name> [--version v] [-i <invocation-id-or-prefix>] [--follow] [--since 5m] [--with-timestamps]
```

`deploy github` accepts only its own flags in 0.47.0: `--env`, `--env-file`, `--force`, `--version` and `-o` belong to `deploy <entrypoint>` and are rejected there, and the CLI reads the token from `--github-token` only (the docs say the `GITHUB_TOKEN` env var also works; the shipped CLI does not read it for deploys). `--version` defaults to `latest` on `deploy`, `invoke`, `logs`. `--payload` is documented as max 64 KB. Ctrl+C on a following `kernel invoke` marks the invocation failed and deletes its browsers. `KERNEL_API_KEY` and `ENTRYPOINT_RELPATH` are reserved env names; the CLI warns and Kernel overrides them. `--output json` on `deploy`/`invoke` emits JSONL events. Log lines over 64 KiB are truncated; without `--follow`, `kernel logs` stops after ~3 s idle.

## 9. Managed Auth, credentials, providers

```bash
kernel auth connections list [--domain d] [--profile-name p] [--query q] [--limit n] [--offset n]
kernel auth connections get <id>
kernel auth connections create --domain netflix.com --profile-name netflix-user-1 --health-check-interval 3600
kernel auth connections update <id> [--login-url u] [--health-checks|--no-health-checks] [--auto-reauth|--no-auto-reauth] [--region r] ...
kernel auth connections login <id> [--proxy-* ...] [--region r] [--record-session] [--skill-mode enabled|disabled]
kernel auth connections submit <id> --field-value <field-id>=<value> | --choice-id <id> [--interaction-id i]   # legacy: --field k=v, --mfa-option-id, --sign-in-option-id, --sso-button-selector, --sso-provider
kernel auth connections follow <id>
kernel auth connections timeline <id> [--type login|reauth|health_check] [--page n] [--per-page n]
kernel auth connections delete <id> [-y]
```

`create` also takes `--login-url`, `--allowed-domain`, `--credential-name`, `--credential-provider`, `--credential-path`, `--credential-auto`, `--proxy-*`, `--region`, `--stealth` (default true), `--no-save-credentials`, `--no-health-checks`, `--no-auto-reauth`, `--record-session`, `--telemetry*`. `--health-check-interval` default 3600 or the plan minimum (Enterprise 300, Startup 1200, Hobbyist 3600, Free 21600), max 86400.

```bash
kernel credentials list [--domain d] [--query q]
kernel credentials get <id-or-name>
kernel credentials create --name netflix-creds --domain netflix.com \
  --value username=user@example.com --value password="secret" --totp-secret "JBSWY3DPEHPK3PXP"
kernel credentials update <id-or-name> [--name n] [--value k=v] [--remove-value-key k] [--totp-secret s] [--totp-algorithm SHA1|SHA256|SHA512] [--totp-digits 6-9] [--totp-period 15-300] [--sso-provider p]
kernel credentials totp-code <id-or-name>
kernel credentials delete <id-or-name> [-y]

kernel credential-providers create --name onepassword --provider-type onepassword --token $OP_TOKEN [--cache-ttl 300]
kernel credential-providers list|get <id>|update <id> [--name --token --enabled --priority]|list-items <id>|test <id>|delete <id> [-y]
```

## 10. Search: `kernel search`

Requires Search API access for the org (rollout flag; `kernel org entitlements -o json` shows `features.search.enabled`).

```bash
kernel search providers [--slug exa]
kernel search "kernel browser sdk tutorial" --max-results 5          # auto routing
kernel search "deep web research agents" --provider exa --max-results 5   # pinned: strategy {type:"pinned",provider:{provider:"exa"}}
kernel search --request '{"query":"deep web research agents","strategy":{"type":"pinned","provider":{"provider":"exa"}},"include_domains":["github.com","arxiv.org"],"content":{"format":"markdown"}}'
kernel search get srch_01jsearch12345                                 # retained search, no new provider call
kernel search contents srch_01jsearch12345 --limit 3 --content-source browser --content-browser-mode render
```

`contents` needs exactly one of `--result-ids a,b` or `--limit 1-100`; also `--timeout-ms 1000-120000`, `--content-format markdown|text`, `--content-max-chars`, `--content-max-age-hours`, `--content-timeout-ms`, `--content-browser-id`. Query: 1-2048 chars. `--request` cannot be combined with `--provider`/`--max-results`. Search POSTs are never retried by the CLI (billable).

## 11. Vaults: `kernel vaults`, `kernel vault-provider-configs`

```bash
kernel vaults create --name checkout-vault        # idempotent by immutable name; also: list [--query], get <vault>, get-encryption-key <vault>
kernel vaults items list checkout-vault
kernel vaults items get checkout-vault user-login [--wait 60] [--expand payment_methods]
kernel vaults items events checkout-vault card-1 [--after id] [--wait 60]
kernel vaults credentials create checkout-vault user-login --spec-file ./creds.json   # also: update (--version required), connect <vault> <account-key> --provider 1password
kernel vaults wallets create checkout-vault wallet-1 --provider link --spec '{"authorization":{"method":"oauth","client":{"type":"kernel_managed"}}}'
kernel vaults cards create checkout-vault card-1 --provider agentcard --spec '{"wallet":"wallet-1","merchant":"Example Shop","amount":1234,"currency":"usd","checkout_origin":"https://store.example.com"}'
# Operations take --params '<json>' or --spec-file (max 128 KiB):
kernel vaults items invoke checkout-vault user-login fill --spec-file ./fill-spec.json
kernel vaults items invoke checkout-vault card-1 prepare_checkout --params '{"checkout":{"browser_id":"<id>","environment":"production","merchant_origin":"https://store.example.com","psp":"square"}}'
kernel vaults items webmcp invoke <vault> <key> --browser-id <id> --tool-ref <ref> --page-url <url> --input '{"password":null}' --bind password=/password

kernel vault-provider-configs create --name link-prod --provider link|agentcard --credentials-file ./link-creds.json [--publishable-key pk_...]
kernel vault-provider-configs list|get <id-or-name>|update <id-or-name> [--credentials-file f --name n]|delete <id-or-name> [-y]
```

Also: `vaults list [--query] [--limit] [--offset]`, `vaults delete <vault> [-y]`, `vaults items delete <vault> <key> [-y]`, `vaults wallets payment-methods <vault> <key>`, `vaults cards update` (same flags as `create`; Kernel-provider cards cannot be updated), `vaults wallets create --provider-config-id|--provider-config-name|--tokens-file`. `--provider` for wallets and cards is `link|agentcard|kernel` (the examples above use link/agentcard). `browsers create --vault <id-or-name>` attaches a vault at creation (immutable afterwards).

## 12. Projects, API keys, organization

```bash
kernel projects list [--name n] [--query q] [--limit 100] [--offset n]
kernel projects get <id-or-name>
kernel projects create production
kernel projects update <id-or-name> --name prod-v2 [--status active|archived]
kernel projects delete <id-or-name>
kernel projects limits get <id-or-name>
kernel projects limits set <id-or-name> --max-concurrent-sessions 5 --max-concurrent-invocations 10   # 0 removes a cap; --max-pooled-sessions is deprecated (the CLI still sends it, the API rejects it with 400)

kernel api-keys list [--name n] [--query q] [--status active|deleted|all] [--sort-by created_at|name|expires_at] [--sort-direction asc|desc]
kernel api-keys get <id> [--include-deleted]
kernel api-keys create --name ci-key [--project-id <proj_id>] [--days-to-expire 1-3650]
kernel api-keys update <id> --name new-name
kernel api-keys rotate <id> --days-to-expire 30 --expire-in-days 7 --yes   # --expire-in-days 0 revokes the old key now; default grace 7 days
kernel api-keys delete <id> --yes           # deleting the authenticating key fails with 400 cannot_delete_current_key

kernel org entitlements
kernel org limits get
kernel org limits set --default-project-max-concurrent-sessions 20        # 0 removes the default
```

## 13. Audit logs and telemetry destinations

```bash
kernel audit-logs search --start "2026-10-01T00:00:00Z" --end "2026-10-08T00:00:00Z" --search 403 \
  [--method M] [--exclude-method M] [--include-get] [--service s] [--auth-strategy a] [--user-id u] [--limit 100]
# Windows are capped at 30 days; GET requests are excluded unless --include-get.
kernel audit-logs download --start 2026-10-01 --end 2026-10-08 --to ./audit-logs.jsonl.gz [--format jsonl.gz|jsonl] [--force]

# S3 export destinations: created paused. Required: --region --bucket --prefix --role-arn. Org-level credential only.
kernel audit-logs export create --region us-east-1 --bucket my-bucket --prefix audit/ --role-arn arn:aws:iam::123456789012:role/audit-export [--kms-key-id k] -o json
kernel audit-logs export list|get <id>|update <id>|test <id>|pause <id>|resume <id>|delete <id>

# OTLP destinations for browser telemetry export (org-scoped)
kernel telemetry destinations create --name prod-datadog --endpoint https://otlp.example.com [--header NAME=VALUE] [--description d]
kernel telemetry destinations list|get <id-or-name>|update <id-or-name> [--remove-header NAME]|delete <id-or-name> [-y]
```

The endpoint is the collector's base URL without a signal path (Kernel appends it).

## 14. MCP and utilities

```bash
kernel mcp install --target cursor|claude|claude-code|antigravity|windsurf|vscode|goose|zed|fx
kernel mcp server       # prints the hosted endpoint and mcp-remote command; starts nothing
kernel status [-o json]
source <(kernel completion zsh)
```

`--target claude` is Claude Desktop only; `claude-code` is the Claude Code CLI; `goose` prints YAML to paste. See [mcp-server.md](mcp-server.md).
