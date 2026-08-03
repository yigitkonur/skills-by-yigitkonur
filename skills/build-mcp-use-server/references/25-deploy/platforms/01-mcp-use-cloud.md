# Manufact Cloud (mcp-use Cloud)

*Deploy to the official mcp-use platform for managed Node.js hosting, preview environments, and GitHub integration.*

## Prerequisites and Source Mode

Build the server and sign in to a Manufact organization before deploying. Then choose one shipped CLI source mode:

- **GitHub (default):** deploy the current `origin`. If no origin exists, an interactive run can create a private GitHub repository; `--yes` authorizes the same repository/Git mutations without prompts. For an existing origin, push the branch you intend to deploy and ensure the Manufact GitHub App can access the repository.
- **Managed upload:** pass `--no-github` on the first deploy. The CLI archives local source (excluding `.git`, dependencies, build output, `.mcp-use`, `.env*`, caches, coverage, OS metadata, and symlinks) and uploads at most 80 MB compressed. Linked managed projects auto-detect this source mode on later deploys.

Inspect Git state before a GitHub-backed deploy:

```bash
git remote get-url origin
git branch --show-current
git status --short
```

Use `--no-github` when you intentionally want the managed-upload path rather than allowing repository creation/mutation.

## First Deploy

```bash
npm run build
mcp-use login
mcp-use deploy --name my-server
```

The first deploy resolves the repository from `origin`, confirms GitHub App access, creates a Git-backed cloud server, starts a deployment, and writes the non-secret project link to `.mcp-use/cloud/link.json`. It starts the deployment; it does not wait for the build to finish.

## Deployment Completion Gate

Capture the deployment ID printed by the CLI or shown in the dashboard. Do not test the public endpoint or claim the new revision is live until that exact deployment reaches a terminal successful conclusion:

```bash
mcp-use deployments get <deployment-id>
mcp-use deployments logs <deployment-id> --build --follow
```

Confirm the deployment record points at the intended source branch/revision (or managed upload), and treat failure, cancellation, or timeout as a failed deploy. A healthy response from the public URL before this gate may come from the previous deployment and is not evidence for the new change.

After success, copy the exact MCP URL from the dashboard and perform the tools-only or View verification branch in `references/25-deploy/02-pre-deploy-checklist.md`.

**Do not infer a hostname from the server slug.** No fixed URL pattern (subdomain, preview-branch format, or otherwise) is documented or guaranteed — the Manufact dashboard is the sole authoritative source for a server's generated and custom domains. Copy the exact MCP URL from the dashboard after each deploy; never construct it from the slug or branch name.

`.mcp-use/cloud/link.json` saves the deployment link; commit it so CI redeploys reuse the same server.

## How Deploys Work

**GitHub (default):**
- CLI deploys the configured `origin`, or can create a private repository when none exists
- The cloud platform runs the configured build and start commands from the selected Git branch
- Existing repositories require the branch to be pushed before deployment; local unpushed file changes are not the deployed source
- `--watch-paths` and `--wait-for-ci` are available only in this source mode

**Managed upload (`--no-github`):**
- CLI uploads an archive of local source to platform-managed storage
- Platform runs the build pipeline
- Works in CI or onboarding without GitHub integration
- `--watch-paths` and `--wait-for-ci` are rejected

## Redeploy and Additional Servers

With a link file present, a plain `mcp-use deploy` starts another deployment on the linked server. Pass `--new` to ignore the link and create a separate cloud server instead — combine with `--yes` for non-interactive confirmation:

```bash
mcp-use deploy --new --yes
```

Branch previews and their URL scheme are dashboard-managed; do not construct or assume a preview URL pattern (see the "Do not infer a hostname" warning above) — read the actual preview URL from the dashboard or `mcp-use deployments get <id>`.

## Environment Variables

Use deploy flags to set environment variables when creating a server:

```bash
mcp-use deploy --env API_KEY=sk-xxx --env-file .env.production
```

For an existing server, use the dedicated commands instead of assuming deploy-time creation flags mutate it:

```bash
mcp-use servers env set <server-id-or-slug> API_KEY=sk-xxx
mcp-use servers env unset <server-id-or-slug> API_KEY
mcp-use servers env list <server-id-or-slug>
```

Values are stored by the platform; the CLI does not echo uploaded secret values.

## Link File

`.mcp-use/cloud/link.json` links this checkout to a specific cloud server. Without it, the CLI cannot reuse that local linkage and may create or select a separate server depending on the source-mode flow. Commit the link file so future deploys target the intended server.

Commit it:

```bash
git add -f .mcp-use/cloud/link.json
git commit -m "chore: track cloud deployment"
git push
```

## Connect a Client

Copy the exact generated MCP URL from the Manufact dashboard — never construct it from the slug:

```bash
export MCP_URL="PASTE_THE_GENERATED_MCP_URL"
npx mcp-use client connect production "${MCP_URL}"
npx mcp-use client production tools list
```

## After Deploy

```bash
# Verify with screenshot (use the dashboard-copied URL from above)
npx mcp-use@beta screenshot \
  --mcp "${MCP_URL}" \
  --tool <tool-name> \
  --output deployed-view.png

# Follow the build, then read runtime logs
mcp-use deployments get <deployment-id>
mcp-use deployments logs <deployment-id> --build --follow
mcp-use deployments logs <deployment-id>
```

Update client configs with the new URL.

---

See `references/25-deploy/04-cli-and-org-management.md` for login, orgs, and CI patterns.
