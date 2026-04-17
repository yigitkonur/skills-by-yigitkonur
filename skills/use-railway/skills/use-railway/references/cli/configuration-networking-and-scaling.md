# Configuration, Networking, and Scaling

Use this file when the user wants to create or switch environments, inspect or change config, manage variables, attach domains, or scale service replicas across regions.

All commands below are confirmed in the local `railway 4.29.0` snapshot. For exact flags and possible values, pair this file with `references/cli/railway-cli-command-reference.md`.

## Environment lifecycle

Use the `environment` family for scope changes and config changes.

```bash
railway environment link <ENVIRONMENT>
railway environment new <NAME>
railway environment new <NAME> --duplicate <SOURCE_ENVIRONMENT>
railway environment config --json
railway environment edit --service-config <SERVICE> <PATH> <VALUE>
railway environment delete <ENVIRONMENT> --yes
```

Choose among them like this:

| If the user wants to... | Prefer | Why |
|---|---|---|
| Switch the active environment | `railway environment link [ENVIRONMENT]` | Scope change only |
| Create a new environment | `railway environment new [NAME]` | New environment path |
| Copy an existing environment while creating a new one | `railway environment new [NAME] --duplicate <SOURCE>` | Local help confirms `--duplicate` and alias `--copy` |
| Inspect current environment config | `railway environment config` | Read-only config view |
| Change service config with dot-path notation | `railway environment edit --service-config <SERVICE> <PATH> <VALUE>` | Main config mutation path in local CLI |
| Delete an environment | `railway environment delete [ENVIRONMENT] --yes` | Remote destructive action |

High-value `environment edit` details:

- `--service-config <SERVICE> <PATH> <VALUE>` applies a dot-path config mutation
- `--message <MESSAGE>` adds a commit-style message for the changes
- `--stage` stages changes without committing them yet
- `--json` returns structured output

If the user is unsure what path to edit, read config first:

```bash
railway environment config --json
```

If the user wants the broader platform rules behind config edits, pair this file with `references/upstream/operations/configure.md` after checking `references/research/version-drift.md`.

## Variables

The `variable` family is the local env-var command set.

```bash
railway variable list --service <SERVICE> --environment <ENVIRONMENT> --json
railway variable list --service <SERVICE> --kv
railway variable set KEY=VALUE --service <SERVICE> --environment <ENVIRONMENT>
railway variable set SECRET_KEY --stdin --service <SERVICE>
railway variable delete KEY --service <SERVICE> --environment <ENVIRONMENT>
```

Choose among them like this:

| Need | Command |
|---|---|
| List variables | `railway variable list` |
| Set one or more variables | `railway variable set` |
| Set one variable from stdin | `railway variable set <KEY> --stdin` |
| Delete a variable | `railway variable delete <KEY>` |

Local nuances worth preserving:

- `variable set` accepts one or more `KEY=VALUE` pairs
- `--skip-deploys` exists both on the parent `variable` command and on `variable set`
- `--kv` is the compact output mode for `variable list`
- The parent command still exposes legacy `--set` and `--set-from-stdin`, but the explicit subcommands are clearer

Upstream Railway behavior worth knowing when the user moves beyond raw `variable set` syntax:

| Pattern | Why it matters |
|---|---|
| `${{shared.KEY}}` and `${{service.VAR}}` interpolation | Useful for service wiring and shared config patterns. |
| `RAILWAY_PRIVATE_DOMAIN` versus public domains | Distinguishes service-to-service traffic from browser-facing traffic. |
| frontend cannot use private networking directly | Helps avoid giving impossible browser-side wiring advice. |

For those platform details, read `references/upstream/operations/configure.md`.

## Domains

Use `railway domain` for Railway-provided or custom domains.

```bash
railway domain --service <SERVICE>
railway domain example.com --service <SERVICE>
railway domain example.com --service <SERVICE> --port 8080 --json
```

Important local facts from help:

- Supplying no positional domain generates a Railway-provided domain
- Supplying `[DOMAIN]` means a custom domain flow and returns DNS records
- There is a maximum of one Railway-provided domain per service
- `--port` targets the service port behind the domain

## Scaling

Local `4.29.0` exposes two closely related scale paths.

### `railway scale`

Use this when the user wants explicit region instance counts:

```bash
railway scale --service <SERVICE> --environment <ENVIRONMENT> --us-west2 2 --us-east4-eqdc4a 1 --json
```

Local region flags exposed by help:

- `--europe-west4-drams3a <INSTANCES>`
- `--us-west2 <INSTANCES>`
- `--asia-southeast1-eqsg3a <INSTANCES>`
- `--us-east4-eqdc4a <INSTANCES>`

### `railway service scale`

Use this when the user is already in the `service` namespace or wants the service-oriented command path:

```bash
railway service scale --service <SERVICE> --environment <ENVIRONMENT> --json
```

Local nuance:

- `railway service scale` exposes service and environment selectors in help
- `railway scale` is the command that exposes explicit per-region instance flags in local `4.29.0`

If the user is asking about richer multi-region config objects, JSON config patching, service wiring, or upstream networking features, route to `references/upstream/operations/configure.md` after `references/research/version-drift.md`.

## Nearby-command traps

| Confusion | Correct choice | Why |
|---|---|---|
| "Switch to another environment" versus "edit environment config" | `environment link` to switch, `environment edit` to mutate | One changes scope, the other changes settings |
| "Read config" versus "change config" | `environment config` to inspect, `environment edit` to mutate | Always inspect first when possible |
| "Set vars" versus "delete vars" | `variable set` and `variable delete` | Separate explicit subcommands |
| "Generate a Railway domain" versus "add a custom domain" | Omit `[DOMAIN]` for a Railway-provided domain, pass `[DOMAIN]` for a custom domain | Same command, different positional usage |
| "Scale by region counts" versus "service-oriented scaling path" | `scale` for explicit region flags, `service scale` for service namespace flow | This is a real local CLI split |

## Guardrails

- Use `environment config --json` before and after structural config edits.
- Treat `environment edit --service-config <SERVICE> <PATH> <VALUE>` as the installed local mutation path, but use the upstream configure guide for cross-service wiring and larger config-schema questions.
- `environment delete` is destructive and may require `--2fa-code` in non-interactive mode.
- If the user asks about upstream-only networking or storage commands not present locally, read `references/research/version-drift.md`.
