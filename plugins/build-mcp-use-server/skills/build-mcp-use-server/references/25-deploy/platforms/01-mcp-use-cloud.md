# Manufact Cloud (mcp-use Cloud)

*Deploy to the official mcp-use platform for managed Node.js hosting, preview environments, and GitHub integration.*

## First Deploy

```bash
npm run build
mcp-use login
mcp-use deploy
```

Browser opens for GitHub App auth. After success, your server lives at:

```
https://<slug>.deploy.mcp-use.com/mcp
```

`.mcp-use/cloud/link.json` saves the deployment link; commit it so CI redeploys reuse the same server.

## How Deploys Work

**GitHub auto-detect (default):**
- CLI finds your GitHub remote
- Runs build and start commands on GitHub's servers
- Deploys from remote HEAD (not your local working tree)
- Requires push before deploy: `git push && mcp-use deploy`

**Without GitHub (`--no-github`):**
- CLI uploads your local source to platform-managed storage
- Platform runs the build pipeline
- Works in CI/onboarding without GitHub integration

## Preview URLs (Hobby+)

Every branch gets a stable preview URL:

```
https://<slug>--br-<branch>.deploy.mcp-use.com/mcp
```

Push to a branch, CLI auto-detects and deploys.

## Environment Variables

```bash
mcp-use deploy --env API_KEY=sk-xxx --env-file .env.production
```

Stored in dashboard; set once, reused on future deploys.

## Link File

`.mcp-use/cloud/link.json` links this repo to a specific cloud server. Without it, every deploy from a different checkout creates a new subdomain (breaks custom domains and cached URLs).

Commit it:

```bash
git add -f .mcp-use/cloud/link.json
git commit -m "chore: track cloud deployment"
git push
```

## After Deploy

```bash
# Verify with screenshot
npx mcp-use@beta screenshot \
  --mcp https://<slug>.deploy.mcp-use.com/mcp \
  --tool <tool-name> \
  --output deployed-view.png

# View logs
mcp-use deployments logs <id> --build --follow
```

Update client configs with the new URL.

---

See `04-cli-and-org-management.md` for login, orgs, and CI patterns.
