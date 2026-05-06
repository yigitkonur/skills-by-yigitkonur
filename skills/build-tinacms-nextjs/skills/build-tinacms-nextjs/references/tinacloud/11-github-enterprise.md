# GitHub Enterprise Integration

TinaCloud Enterprise integrates with GitHub Enterprise (GHE) for organizations that can't use github.com.

## Available on Enterprise tier

GHE integration is Enterprise-tier only. Free / Team / Team Plus / Business require github.com.

## Setup

Contact TinaCMS sales (https://tina.io/enterprise) to begin GHE setup. The flow:

1. TinaCMS provides a GitHub App manifest
2. You install it on your GHE instance
3. TinaCloud is whitelisted to authenticate against your GHE
4. Standard project creation flow, pointing at GHE repos

## Differences from github.com

| Aspect | github.com | GHE |
|---|---|---|
| Setup | Self-serve | Sales-assisted |
| OAuth | TinaCloud's GitHub App | Custom GitHub App on your GHE |
| Webhook destinations | TinaCloud's URLs | Reach into your GHE |
| Tier | All | Enterprise only |

## Network requirements

Your GHE instance must be reachable from TinaCloud's IPs. For air-gapped GHE:

- Whitelist TinaCloud egress IPs (provided by TinaCMS sales)
- Or run TinaCloud's enterprise on-prem version (separate offering)

## Authentication

Editors sign in via OAuth against your GHE instance, not github.com. SSO via GHE → TinaCloud is supported.

## Migration from github.com to GHE

If you started on github.com and need to move:

1. Set up GHE integration (Enterprise tier)
2. Create a new TinaCloud project pointing at the GHE repo
3. Push content to the GHE repo
4. Switch app's env vars to the new project's credentials
5. Decommission the old github.com project

Migration mostly = re-pointing the connection, since content is git-native.

## Documentation

For specifics, refer to your TinaCMS sales/support contact. The setup is bespoke per organization.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Tried to use GHE on free/Team tier | Not available | Upgrade to Enterprise |
| GHE not reachable from TinaCloud | Webhooks fail | Whitelist TinaCloud IPs |
| Mixed github.com and GHE in one project | Confusing OAuth | Separate projects |
| GHE OAuth not whitelisted | Login fails | Configure GitHub App correctly |
