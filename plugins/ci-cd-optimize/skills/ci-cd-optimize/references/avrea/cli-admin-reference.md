# Avrea CLI admin and mutation reference (`avr` 0.1.6)

Read this before any Avrea command that could change shared, financial, or
security-sensitive state. The commands below are verified against the released
Avrea CLI 0.1.6; their presence here does **not** authorize running them.

Pinned release identity:

- package: `avr-cli`
- executable: `avr`
- released version: `0.1.6`
- release tag: `v0.1.6`
- source SHA: `d1c368547a8ca31fad2ec0513c6a2cfc33e3cb80`

## Mutation classes

| Class | Meaning | Examples |
|---|---|---|
| **Read-only** | Observes state only. | `status`, `health`, `workflow view`, `cache usage`, `audit-events list` |
| **Local config write** | Changes only the caller's local CLI state. | `auth switch`, `config set`, `config unset` |
| **Remote repository mutation** | Changes CI behavior or shared repo state. | `run rerun`, `run cancel`, `cache delete`, repo-scoped `settings set/reset`, `firewall` repo rules |
| **Remote organization mutation** | Changes org-wide or multi-repo state. | `org create`, org-scoped `settings set/reset`, `org install add/remove`, `firewall` org rules |
| **Financial/account mutation** | Changes payment method or billing behavior. | `billing update-settings`, `billing payment-methods add/remove/set-default` |
| **Live runner access** | Opens an interactive session on an active CI VM. | `job ssh` |
| **Credential exposure** | Emits or transmits secret material. | `auth status --show-token`, billing card-entry flags |

A confirmation prompt or `--yes` answers *how* the CLI proceeds, not *whether*
you are authorized to do it.

## Authentication and local config

### `avr auth`

| Command | Mutation class | Purpose |
|---|---|---|
| `avr auth login [--provider github|google]` | Local config write + browser OAuth | Obtain/store a token for the resolved host |
| `avr auth logout` | Local config write; attempts server-side revocation too | Clear local credentials |
| `avr auth switch [HOST]` | Local config write | Change or list the default host profile |
| `avr auth status [--show-token] [--json] [--jq]` | Read-only / **credential exposure** with `--show-token` | Inspect current auth state |

Rules:

- Never use `--show-token` in automation, logs, screenshots, or troubleshooting
  transcripts.
- A failed server-side logout still clears the local entry after warning; it
  does not guarantee revocation succeeded.
- `auth login` and `auth switch` are safe local changes, but they can make
  subsequent commands target a different host/account than expected.

### `avr config`

| Command | Mutation class | Purpose |
|---|---|---|
| `avr config` / `avr config list` | Read-only | Show resolved host/org/repo with their source |
| `avr config get org` | Read-only | Inspect stored org default |
| `avr config set org VALUE` | Local config write | Persist a default org for the current host |
| `avr config unset org` | Local config write | Remove stored org default |

These do not change Avrea state, but they do change where future commands land.
Use explicit `--org`/`--repo` for high-impact operations instead of trusting a
remembered default.

## Settings

### `avr settings schema`

Read-only. Use it to discover what setting keys exist rather than guessing.

### `avr settings list`

Read-only. Show effective values plus inheritance source; use `--prefix` to
scope to an area such as `cache.` or `runner.`.

### `avr settings set KEY VALUE`
### `avr settings reset KEY`

Mutation class:

- **Remote repository mutation** with `--repo`
- **Remote organization mutation** with `--org`

Examples of impactful verified keys include cache toggles, diagnostics, static
IP egress, and OpenTelemetry export. Rules:

- Capture the current value and scope before changing it.
- State the rollback (`settings reset KEY` or previous value) before applying.
- Never place OTel auth-header values or other secrets into reports or commit
  messages.
- A repo checkout can influence scope resolution; explicit `--org` suppresses
  repository auto-detection and targets the organization. Be deliberate.

## Runs and caches that mutate shared state

### `avr run cancel RUN_ID`

Mutation class: **remote repository mutation**.

Use only when the target run identity is already proven:

```bash
avr run view run-123 --json head_sha,status,conclusion,run_attempt
```

Cancellation is appropriate for obsolete or runaway work; it is not a
measurement technique.

### `avr run rerun RUN_ID [--failed]`

Mutation class: **remote repository mutation**.

Use to create a fresh attempt after capturing the prior attempt's exact
failure. A rerun changes the evidence set; note `run_attempt` and keep the
original attempt in the report.

### `avr cache delete`

Mutation class: **remote repository mutation**.

Rules:

- Exactly one of `--key` or `--all`.
- `--type` required with `--key`.
- `--all` clears every cache entry for the repository and will slow the next
  runs for everyone.
- Prefer the smallest scoped invalidation (`--type`, `--key`, `--ref`) after a
  proven stale/poisoned-cache diagnosis.

Do not use cache deletion as an exploratory probe without authorization and a
rollback plan.

## Firewall and network policy

### Read-only commands

| Command | Use |
|---|---|
| `avr firewall list` | List rules at a scope |
| `avr firewall show` | Show resolved org+repo rules |
| `avr firewall flow-summaries --with-drops` | Prove blocked traffic and affected destinations |
| `avr firewall flow-summaries --with-drops --vm vm-...` | Narrow observed drops to one VM in released 0.1.6; newer `--job` forms are unreleased and must stay quarantined. |

### Mutating commands

| Command | Mutation class | Notes |
|---|---|---|
| `avr firewall add` | Remote repo/org mutation | Requires one of `--cidr`, `--fqdn`, or `--any`; action/protocol/port correctness matters |
| `avr firewall delete` | Remote repo/org mutation | Removes a rule by ID |
| `avr firewall move` | Remote repo/org mutation | Reorders rules; positions are zero-indexed |
| `avr firewall set-default` | Remote repo/org mutation | Changes default policy |

Use the read-only commands first. Never treat a firewall change as a harmless
experiment; it can cut off package registries, artifact stores, or services for
other workflows.

## Organization and repository administration

### `avr repo list`

Read-only. Confirm the repository is connected and get the canonical ID before
explicit repo-targeted commands.

### `avr org`

| Command | Mutation class | Use |
|---|---|---|
| `avr org list` | Read-only | Enumerate accessible orgs |
| `avr org create NAME` | Remote organization mutation | Create a new org |
| `avr org members` | Read-only | Membership inspection |
| `avr org email-domain list` | Read-only | Inspect claimed domains |
| `avr org email-domain set DOMAINS...` | Remote organization mutation | Replaces the entire domain set |
| `avr org install list` | Read-only | GitHub App installations |
| `avr org install add` | Remote organization mutation | Add installation |
| `avr org install remove` | Remote organization mutation | Remove/suspend installation |

`email-domain set` and `install remove` are high-impact; capture the before
state and owner approval first.

## Audit and billing

### `avr audit-events list`

Read-only. Use it to correlate settings/firewall/install changes with a CI
regression. Filter by time, action, resource type, and actor. Do not dump raw
`s event_data` into shared reports if it may contain sensitive operational
context.

### `avr billing`

Read-only subcommands:

- `avr billing summary`
- `avr billing settings`
- `avr billing invoices list`
- `avr billing invoices show`
- `avr billing payment-methods list`

Mutating subcommands:

- `avr billing update-settings`
- `avr billing payment-methods add`
- `avr billing payment-methods remove`
- `avr billing payment-methods set-default`

Special case:

- `avr billing invoices download INVOICE_ID --out PATH` writes a local file but does
  not change remote state.

Important limits:

- Billing exposes account/payment/invoice state, but **not** verified per-run
  or per-job pipeline cost telemetry. Do not use it as a substitute for CI
  efficiency measurement.
- Card-entry flags (`--number`, `--cvc`, etc.) are shell-history risks and
  should never appear in automation or transcripts.

## Live VM access

### `avr job ssh JOB_ID`

Mutation class: **live runner access**.

Although it does not mutate persistent Avrea configuration, an SSH session can
change the live job VM and therefore the evidence of the run. Treat it like a
privileged debugging action. Safe usage pattern:

1. Prove the job identity first (`job view`, `head_sha`, label, state).
2. Prefer `--print-command` to inspect the connection string before using it.
3. Keep any long sleep/hold-open step behind `if: failure()` so every green run
   does not burn paid minutes.
4. Never combine SSH debugging with claims that the watched run remained
   pristine evidence.

## Safe mutation checklist

Before running any command in this file, confirm:

- [ ] exact target host/org/repo is stated explicitly or has been freshly shown
      by `avr config` / `avr auth status` / `avr repo list`
- [ ] mutation class is named in the report or notes
- [ ] rationale is tied to the measured bottleneck or failure
- [ ] rollback command or reversal is known
- [ ] any secrets remain out of logs and shell history
- [ ] the action is authorized for this scope
- [ ] the impact on other users/runs is understood

## Sources

- Release docs index: https://docs.avrea.com/cli/reference/ (accessed 2026-07-28)
- GitHub release tag: https://github.com/avrea-com/cli/releases/tag/v0.1.6 (accessed 2026-07-28)
- Release source tag: https://github.com/avrea-com/cli/tree/v0.1.6 (accessed 2026-07-28)
- Verified locally against installed `avr` 0.1.6 (2026-07-28)
