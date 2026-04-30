# Find-or-create Vercel projects

Vercel's `link` command is the find-or-create entrypoint. By default interactive; with flags, scriptable.

## Listing existing projects

```bash
vercel projects ls
# Project Name             Latest Production URL    Updated
# my-blog                  my-blog-abc.vercel.app   2 days ago
# acme-marketing           acme.com                 1 hour ago
```

Filter by name:

```bash
vercel projects ls | grep -iw "my-app"
```

## Linking to existing

```bash
# Interactive: shows a picker
vercel link

# Non-interactive: pick by exact project name
vercel link --project my-existing-project --yes
```

After link, `.vercel/project.json` holds the IDs:

```json
{
  "projectId": "prj_abc123...",
  "orgId": "team_xyz789...",
  "projectName": "my-existing-project"
}
```

## Creating new

`vercel link` will offer to create if no match. Or be explicit:

```bash
# Bare new-project init in current directory
vercel link --yes
# Picks defaults: project name = directory name, framework = auto-detected
```

For full control:

```bash
vercel link --project my-new-name --yes --confirm
# Confirms creation if name doesn't exist
```

## Selecting team/org

By default `vercel` operates in your personal account. For team projects:

```bash
vercel switch team-name        # changes scope for subsequent commands
vercel link                    # links to a project under team-name
```

Or pass per-command:

```bash
vercel link --scope team-name --project my-app --yes
```

## Naming conventions

- Lowercase, dash-separated: `acme-marketing`, `my-blog-v2`
- Avoid environment in the name: `my-app` (not `my-app-prod`) — Vercel handles environments inside one project
- For monorepos: prefix with the app: `acme-web`, `acme-admin`

## When to NOT use the same project

Multi-tenant deployments where you want separate analytics, separate domains, separate scaling: use separate Vercel projects. Same Git repo can link to multiple projects (each contributor's `.vercel/` points to a different one).

## Detecting link state in the Makefile

```sh
_check-prereqs:
	@[ -d .vercel ] || { \
	  printf "project not linked  $(D)vercel link$(Z)\n"; exit 1; \
	}
```

If `.vercel/` is missing, refuse to deploy. The user must `vercel link` first; don't auto-link from a recipe.

## CI/CD: linking from a token

For GitHub Actions / similar, you can't `vercel login` interactively. Use a project token:

```bash
# Generate a token: https://vercel.com/account/tokens
export VERCEL_TOKEN=...

# Link non-interactively
vercel link --token=$VERCEL_TOKEN --yes --project my-app

# Or skip linking and pass IDs directly
vercel deploy --token=$VERCEL_TOKEN --yes --org-id $ORG_ID --project-id $PROJECT_ID
```

The IDs come from `.vercel/project.json` (after a one-time manual link from a dev's machine).

## Renaming projects

```bash
vercel projects rename my-app new-name
```

Local `.vercel/project.json` will mismatch. Re-`vercel link --project new-name --yes` to fix.

## Deletion

```bash
vercel projects rm my-app
```

Destructive. Never bake into a Makefile.

## Workspaces vs personal projects

Vercel supports two scopes: personal (free tier per-user) and team workspaces (Pro/Enterprise). The `--scope` flag toggles which one a CLI command operates against.

For a team's first Vercel deployment of a project, the lead links once with `--scope team-name`. Other contributors do the same; their local `.vercel/project.json` will resolve to the same project.
