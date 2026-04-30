# Find-or-create services

Railway's CLI doesn't have one verb for "find this service or create it if missing". Compose it yourself.

## The contract

```bash
ensure_service() {
  local name="$1"
  if railway service status --all 2>/dev/null | awk '{print $1}' | grep -qx "$name"; then
    echo "  ✓ service $name exists"
  else
    echo "  → creating service $name"
    railway service create --name "$name"
  fi
}

for svc in $WEB_SERVICES; do
  ensure_service "$svc"
done
```

## Detection details

`railway service status --all` output (TSV-like):

```
geo-tracker-redis    | 84f85c61-... | SUCCESS
zeo-radar-auth       | 2630c15e-... | SUCCESS
zeo-radar-noauth     | 08d9ae66-... | SUCCESS
geo-tracker-db       | 2ca0d760-... | SUCCESS
```

Use `awk '{print $1}'` to extract names. `grep -qx "$name"` for exact match (the `x` flag prevents `app` from matching `app-staging`).

## TTY vs non-TTY

`railway service create` is non-interactive when `--name` is provided. Without `--name`, it prompts → fails in CI. Always pass `--name` from a script.

```bash
# Right
railway service create --name web

# Wrong (will hang in non-TTY)
railway service create
```

## Linking after create

A new service starts with no source linked. The next `railway up --service web` from a project root will use the local source. Make sure the user's `railway link` is current:

```bash
railway status 2>&1 | head -3
# Project: my-project
# Environment: production
# Service: None    ← no service linked, but `up --service NAME` overrides
```

You don't need to `railway service NAME` (the linker) before `up --service NAME`. The `--service` flag on `up` is sufficient.

## Domain assignment after create

A new service has no public URL by default. After first `railway up --detach -s web`:

```bash
railway domain --service web        # interactive: prompts for port + custom domain
railway domain --service web --port 3000   # non-interactive
```

This generates a `<svc>.up.railway.app` URL. For custom domains:

```bash
railway domain add example.com --service web
# follow Railway's instructions for DNS records
```

## Cross-environment shape

Services exist per-environment. `production` and `staging` are separate registries:

```bash
railway environment production
railway service status --all          # production services

railway environment staging
railway service status --all          # different list
```

The Makefile's `WEB_SERVICES` list applies to whichever environment is currently active. Switch with `railway environment <name>` before `make prod` if needed, or pass `-e <env>` per command.

## When to NOT create

- The user already has services and just wants to deploy. Don't auto-create — that confuses team setups.
- Generic name guessing (`web`, `api`) collides with existing patterns. Always confirm with the user before creating.
- In monorepos with established service-per-app conventions.

The right default: detect existing, refuse to create unless the user explicitly asks (`make prod CREATE_MISSING=1` or similar).

## Service deletion

Out of scope. The CLI has `railway service delete --service NAME` but that's destructive. Never bake into a Makefile.
