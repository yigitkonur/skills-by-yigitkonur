#!/bin/bash
# scaffold-mcp-use-server.sh
# Drive create-mcp-use-app@beta non-interactively with real CLI flags.

set -euo pipefail

TEMPLATE="${1:-mcp-server}"
PROJECT_NAME="${2:-my-mcp-server}"
PACKAGE_MANAGER="${3:-npm}"

echo "=== mcp-use v2 Server Scaffold ==="
echo ""

if [ -d "$PROJECT_NAME" ]; then
    echo "✗ Directory '$PROJECT_NAME' already exists. Refusing to overwrite."
    exit 1
fi

echo "Project: $PROJECT_NAME"
echo "Template: $TEMPLATE"
echo "Package manager: $PACKAGE_MANAGER"
echo ""

# Validate template
case "$TEMPLATE" in
    mcp-server|mcp-apps|blank)
        ;;
    *)
        echo "✗ Unknown template: $TEMPLATE"
        echo "   Valid: mcp-server, mcp-apps, blank"
        exit 1
        ;;
esac

# Validate package manager
case "$PACKAGE_MANAGER" in
    npm|pnpm|bun)
        ;;
    *)
        echo "✗ Unknown package manager: $PACKAGE_MANAGER"
        echo "   Valid: npm, pnpm, bun"
        exit 1
        ;;
esac

echo "Running: npx create-mcp-use-app@2.0.0-beta.14 $PROJECT_NAME --template $TEMPLATE --${PACKAGE_MANAGER} --install"
echo ""

# Run create-mcp-use-app with flags
# Flags from /tmp/audit/facts-v2-cli.md:
#   --template, --install, --npm/pnpm/bun (to select package manager)
npx create-mcp-use-app@2.0.0-beta.14 "$PROJECT_NAME" \
    --template "$TEMPLATE" \
    --"$PACKAGE_MANAGER" \
    --install

echo ""
echo "✓ Scaffold complete!"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. npm run dev  (or: pnpm dev / bun run dev)"
echo "  3. Open http://localhost:3000/mcp/inspector in browser"
echo ""
echo "To deploy:"
echo "  git init && git add -A && git commit -m 'Initial commit'"
echo "  git remote add origin <your-github-url>"
echo "  git push -u origin main"
echo "  npm run deploy"
