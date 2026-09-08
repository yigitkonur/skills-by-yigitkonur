# Cloudflare Access API recipes

All calls are account-scoped against `https://api.cloudflare.com/client/v4`. There are no
zone-scoped Access permissions.

```bash
API=https://api.cloudflare.com/client/v4
AUTH=(-H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json")
```

> Request-body shapes on this API change between versions. Read the current schema before
> scripting anything you have not seen return `"success": true` in this account.

## Inspect before you create

```bash
curl -s "$API/accounts/$CF_ACCOUNT_ID/access/apps"       "${AUTH[@]}" | jq '.result[] | {id,name,domain,type}'
curl -s "$API/accounts/$CF_ACCOUNT_ID/access/policies"   "${AUTH[@]}" | jq '.result[] | {id,name,decision,reusable}'
curl -s "$API/accounts/$CF_ACCOUNT_ID/access/identity_providers" "${AUTH[@]}" | jq '.result[] | {id,name,type}'
```

`reusable: false` on a policy means it is legacy and app-scoped. See "Migrate a legacy policy".

## Reusable policies

```bash
curl -sX POST "$API/accounts/$CF_ACCOUNT_ID/access/policies" "${AUTH[@]}" -d '{
  "name": "Allow example.com email domain",
  "decision": "allow",
  "include": [{"email_domain": {"domain": "example.com"}}]
}'
```

`decision` is one of `allow`, `deny`, `bypass`, `non_identity`. Rule blocks:

| Block | Meaning |
|---|---|
| `include` | Any one match qualifies the user |
| `require` | Every listed rule must also match |
| `exclude` | Any match disqualifies, overriding `include` |

Common selectors:

```jsonc
{"email_domain": {"domain": "example.com"}}
{"email": {"email": "person@example.com"}}
{"group": {"id": "<access-group-id>"}}          // Cloudflare Access Group, not an IdP group
{"login_method": {"id": "<idp-id>"}}            // force one IdP
{"ip": {"ip": "203.0.113.0/24"}}
{"service_token": {"token_id": "<token-id>"}}
{"any_valid_service_token": {}}
{"everyone": {}}                                // only ever inside a bypass policy you meant to write
```

Group selectors depend on IdP group claims or SCIM. Without group sync, do not invent them — use
`email_domain` or explicit emails.

Contractors and partners: a second Allow policy with an `email` include list, or an `include`
`email_domain` plus a `require` on `login_method`, keeps the audit trail readable. Do not widen the
main policy.

## Self-hosted application

```bash
curl -sX POST "$API/accounts/$CF_ACCOUNT_ID/access/apps" "${AUTH[@]}" -d "{
  \"name\": \"Internal Dashboard\",
  \"domain\": \"app.example.com\",
  \"type\": \"self_hosted\",
  \"session_duration\": \"24h\",
  \"auto_redirect_to_identity\": false,
  \"allowed_idps\": [\"$IDP_ID\"],
  \"app_launcher_visible\": true,
  \"policies\": [{\"id\": \"$POLICY_ID\", \"precedence\": 1}]
}"
```

- `domain` covers a single hostname (optionally `app.example.com/path`). Newer API versions expose
  a `destinations` array for multi-hostname apps; check the schema before using it, and note the
  default limit is a small number of hostnames per app.
- `session_duration` accepts `30m`, `6h`, `24h`, `1w`, or `0s` to force re-auth on every request.
- `allowed_idps` empty/omitted = every configured IdP is offered. Setting it plus
  `auto_redirect_to_identity: true` skips the chooser and goes straight to the single IdP.
- **Reusable and inline policies are mutually exclusive.** Passing `policies` as full objects
  instead of `{id, precedence}` links creates legacy app-scoped policies.

Precedence is evaluation order, lowest first. A `bypass` at precedence 1 wins over an `allow` at 2.

## Attach, detach, reorder

```bash
# replace the app's policy links wholesale
curl -sX PUT "$API/accounts/$CF_ACCOUNT_ID/access/apps/$APP_ID" "${AUTH[@]}" -d "{
  \"policies\": [{\"id\":\"$BYPASS_ID\",\"precedence\":1},{\"id\":\"$ALLOW_ID\",\"precedence\":2}]
}"
```

`PUT` on an application replaces the whole object — send every field you want to keep, not just the
changed one.

## Migrate a legacy policy

```bash
curl -sX PUT "$API/accounts/$CF_ACCOUNT_ID/access/apps/$APP_ID/policies/$POLICY_ID/make_reusable" \
  "${AUTH[@]}"
```

Then verify `reusable: true` in the policies list before editing it further.

## Carve-outs

**Health checks / webhooks** — a `bypass` policy scoped to a path plus a source IP list:

```bash
curl -sX POST "$API/accounts/$CF_ACCOUNT_ID/access/policies" "${AUTH[@]}" -d '{
  "name": "Bypass health endpoint",
  "decision": "bypass",
  "include": [{"ip": {"ip": "203.0.113.10/32"}}]
}'
```

A `bypass` with `{"everyone": {}}` disables Access for whatever it covers. Only ever scope it to a
specific path on a specific app, and say so in the policy name.

**CI / machine clients** — service tokens, not a bypass:

```bash
curl -sX POST "$API/accounts/$CF_ACCOUNT_ID/access/service_tokens" "${AUTH[@]}" \
  -d '{"name": "ci-deploy"}'
# client_secret is returned ONCE — pipe it straight into the CI secret store
```

Callers send `CF-Access-Client-Id` and `CF-Access-Client-Secret`. Add
`{"service_token": {"token_id": "<id>"}}` to an Allow policy's `include`, or use
`any_valid_service_token`. Service tokens have their own expiry — put the rotation date in the
repo docs.

## Audit an existing setup

```bash
# apps with no attached policy = deny-all, or worse, a stale bypass
curl -s "$API/accounts/$CF_ACCOUNT_ID/access/apps" "${AUTH[@]}" \
  | jq '.result[] | select((.policies|length)==0) | {id,name,domain}'

# every bypass policy in the account
curl -s "$API/accounts/$CF_ACCOUNT_ID/access/policies" "${AUTH[@]}" \
  | jq '.result[] | select(.decision=="bypass") | {id,name,include}'
```

Access authentication logs (Zero Trust → Logs → Access) show which policy matched for each login —
the fastest way to answer "why did that person get in".
