# Git-hook CI/CD without GitHub Actions

For teams that want zero-CI-vendor lock-in: run the same checks Actions would, locally on every commit/push. Faster feedback, no Actions minutes burned.

## The hook trio

| Hook | Runs | Blocks | Speed |
|---|---|---|---|
| `pre-commit` | format + lint-staged | Bad commits | Fast (< 5s) |
| `pre-push` | typecheck + lint + test | Bad pushes | Slow (30s-2min) |
| `post-merge` | `npm install` if package.json changed | Nothing — silent fixup | < 1s detection |

Hooks live in `scripts/git-hooks/` (committed to repo) and are symlinked into `.git/hooks/` (not committed).

## Installer

`scripts/install-hooks.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$REPO_ROOT/scripts/git-hooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOKS_SRC" ]; then
  echo "✗ $HOOKS_SRC not found"; exit 1
fi

mkdir -p "$HOOKS_DST"

for hook in "$HOOKS_SRC"/*; do
  name=$(basename "$hook")
  dst="$HOOKS_DST/$name"

  # Backup existing non-symlinked hooks
  if [ -f "$dst" ] && [ ! -L "$dst" ]; then
    mv "$dst" "$dst.bak"
    echo "→ backed up existing $name to $name.bak"
  fi

  ln -sf "../../scripts/git-hooks/$name" "$dst"
  chmod +x "$hook"
  echo "✓ installed $name"
done

echo ""
echo "Done. Hooks active. Uninstall: rm .git/hooks/{pre-commit,pre-push,post-merge}"
```

`make install-hooks` calls this. Idempotent: re-running re-creates symlinks (no-op if unchanged), preserves any pre-existing user hooks as `.bak`.

## pre-commit hook

`scripts/git-hooks/pre-commit`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Format staged files only (lint-staged style)
STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx|js|jsx|json|css|md)$' || true)
if [ -z "$STAGED" ]; then exit 0; fi

# Run prettier on the staged files
echo "→ formatting $(echo "$STAGED" | wc -l | tr -d ' ') files"
echo "$STAGED" | xargs npx prettier --write --log-level warn

# Re-stage what we just formatted
echo "$STAGED" | xargs git add

# Lint the staged files (cheaper than whole-repo lint)
echo "→ linting"
echo "$STAGED" | grep -E '\.(ts|tsx|js|jsx)$' | xargs --no-run-if-empty npx eslint --max-warnings=0
```

Bypass with `git commit --no-verify` (devs do this in emergencies).

## pre-push hook

`scripts/git-hooks/pre-push`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Skip checks for --no-verify or specific protected branches
if [ -n "${SKIP_HOOKS:-}" ]; then exit 0; fi

echo "→ typecheck"
npx tsc --noEmit

echo "→ lint"
npm run lint --silent

echo "→ test"
npm test --silent

echo "✓ pre-push checks passed"
```

Bypass with `git push --no-verify` or `SKIP_HOOKS=1 git push`.

For long-running test suites, gate the test step:

```bash
# Skip tests when pushing to a non-main branch (faster)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  npm test --silent
fi
```

## post-merge hook

`scripts/git-hooks/post-merge`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Detect changes to package.json or lockfile in the just-merged commit
if git diff HEAD@{1} HEAD --name-only | grep -qE '^(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb)$'; then
  echo "→ package.json/lockfile changed — running npm install"
  npm install
fi

# Detect Prisma schema changes; regenerate client
if git diff HEAD@{1} HEAD --name-only | grep -qE '^prisma/schema\.prisma$'; then
  echo "→ prisma/schema.prisma changed — running prisma generate"
  npx prisma generate
fi
```

Silent unless something changed. Saves the "huh, nothing's working — oh, I forgot npm install" cycle.

## Discoverability

Mention the installer in the project's CLAUDE.md / AGENTS.md / README:

> **First-time setup:** `make install-hooks` — installs pre-commit, pre-push, post-merge hooks.

And in the Makefile help:

```
make install-hooks    install pre-commit / pre-push / post-merge git hooks
```

## Husky-free philosophy

These hooks don't need [husky](https://github.com/typicode/husky). Husky's value is auto-installation on `npm install` — but that hides what's running and adds a dependency. The explicit `make install-hooks` makes it obvious + auditable.

If you DO want auto-install, add to `package.json`:

```json
{
  "scripts": {
    "postinstall": "make install-hooks 2>/dev/null || true"
  }
}
```

The `|| true` keeps `npm install` from failing in environments where `make` isn't available (some CI runners).

## CI parity

If the team also has GitHub Actions, the workflows should run the same commands as the hooks (typecheck, lint, test). Don't drift — when a hook updates, update the workflow.

## Hook bypass discipline

Allow but track bypasses:

```bash
# In pre-push:
if [ -n "${SKIP_HOOKS:-}" ]; then
  echo "⚠ skipping checks (SKIP_HOOKS=1)" >&2
  echo "$(date -u +%FT%TZ) $USER skipped pre-push" >> "$REPO_ROOT/.git/hook-bypasses.log"
  exit 0
fi
```

Then occasionally `tail .git/hook-bypasses.log` to see who's pushing past checks. Cultural, not enforced.
