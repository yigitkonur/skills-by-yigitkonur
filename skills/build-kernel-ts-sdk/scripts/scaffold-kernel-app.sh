#!/usr/bin/env bash
set -euo pipefail

mode="embed"
target_dir="kernel-app"
force=0

usage() {
  cat <<'EOF'
Usage:
  scaffold-kernel-app.sh [--mode embed|deploy] [--dir DIR] [--force]

Options:
  --mode    embed creates src/index.ts; deploy creates src/app.ts.
  --dir     target directory to create or populate. Default: kernel-app.
  --force   allow writing into a non-empty directory.
  -h, --help
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --dir)
      target_dir="${2:-}"
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$mode" in
  embed|deploy) ;;
  *)
    printf 'Invalid --mode: %s (expected embed or deploy)\n' "$mode" >&2
    exit 2
    ;;
esac

if [ -z "$target_dir" ]; then
  printf 'Missing --dir value\n' >&2
  exit 2
fi

if ! command -v node >/dev/null 2>&1; then
  printf 'BLOCKER: node is required\n' >&2
  exit 2
fi

if ! command -v npm >/dev/null 2>&1; then
  printf 'BLOCKER: npm is required\n' >&2
  exit 2
fi

if [ -e "$target_dir" ] && [ ! -d "$target_dir" ]; then
  printf 'Target exists and is not a directory: %s\n' "$target_dir" >&2
  exit 2
fi

if [ -d "$target_dir" ] && [ -n "$(find "$target_dir" -mindepth 1 -maxdepth 1 -print -quit)" ] && [ "$force" -ne 1 ]; then
  printf 'Refusing to overwrite non-empty directory: %s\n' "$target_dir" >&2
  printf 'Pass --force to overwrite scaffold-managed files.\n' >&2
  exit 2
fi

latest_range() {
  local pkg="$1"
  npm view "$pkg" version --json | node -e '
const fs = require("node:fs");
const version = JSON.parse(fs.readFileSync(0, "utf8"));
process.stdout.write(`^${version}`);
'
}

sdk_range="$(latest_range @onkernel/sdk)"
playwright_range="$(latest_range playwright)"
tsx_range="$(latest_range tsx)"
typescript_range="$(latest_range typescript)"
types_node_range="$(latest_range @types/node)"
cli_range="$(latest_range @onkernel/cli)"

mkdir -p "$target_dir/src"

cat > "$target_dir/.gitignore" <<'EOF'
node_modules/
.env
dist/
shot.png
EOF

cat > "$target_dir/.env.example" <<'EOF'
KERNEL_API_KEY=replace_with_your_kernel_api_key
# Optional project scoping:
# KERNEL_PROJECT=proj_replace_me
EOF

cat > "$target_dir/tsconfig.json" <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "types": ["node"]
  },
  "include": ["src/**/*.ts"]
}
EOF

if [ "$mode" = "embed" ]; then
  cat > "$target_dir/package.json" <<EOF
{
  "name": "kernel-embed-demo",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "check": "tsc --noEmit",
    "start": "tsx src/index.ts"
  },
  "dependencies": {
    "@onkernel/sdk": "$sdk_range",
    "playwright": "$playwright_range"
  },
  "devDependencies": {
    "@types/node": "$types_node_range",
    "tsx": "$tsx_range",
    "typescript": "$typescript_range"
  }
}
EOF

  cat > "$target_dir/src/index.ts" <<'EOF'
import Kernel from '@onkernel/sdk';
import { chromium } from 'playwright';
import fs from 'node:fs/promises';

const kernel = new Kernel();

const session = await kernel.browsers.create({
  stealth: true,
  timeout_seconds: 300,
  viewport: { width: 1280, height: 800 },
});

console.log('session_id:', session.session_id);
console.log('live_view_url:', session.browser_live_view_url ?? '(headless)');

try {
  const browser = await chromium.connectOverCDP(session.cdp_ws_url);
  const context = browser.contexts()[0];
  const page = context.pages()[0];

  await page.goto('https://example.com', { waitUntil: 'networkidle' });
  console.log('title:', await page.title());

  const png = await page.screenshot();
  await fs.writeFile('shot.png', png);
  console.log('artifact: shot.png');
} finally {
  await kernel.browsers.deleteByID(session.session_id);
  console.log('deleted:', session.session_id);
}
EOF
else
  cat > "$target_dir/package.json" <<EOF
{
  "name": "kernel-deploy-demo",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "check": "tsc --noEmit",
    "deploy": "kernel deploy src/app.ts --version 0.1.0",
    "invoke:sync": "kernel invoke kernel-scaffold analyze --sync --payload '{\"url\":\"https://example.com\"}'"
  },
  "dependencies": {
    "@onkernel/sdk": "$sdk_range",
    "playwright": "$playwright_range"
  },
  "devDependencies": {
    "@onkernel/cli": "$cli_range",
    "@types/node": "$types_node_range",
    "tsx": "$tsx_range",
    "typescript": "$typescript_range"
  }
}
EOF

  cat > "$target_dir/src/app.ts" <<'EOF'
import Kernel, { type KernelContext } from '@onkernel/sdk';
import { chromium } from 'playwright';

const kernel = new Kernel();
const app = kernel.app('kernel-scaffold');

app.action(
  'analyze',
  async (ctx: KernelContext, payload?: { url?: string }) => {
    const url = payload?.url ?? 'https://example.com';
    const session = await kernel.browsers.create({
      stealth: true,
      timeout_seconds: 300,
      invocation_id: ctx.invocation_id,
    });

    console.log('session_id:', session.session_id);

    try {
      const browser = await chromium.connectOverCDP(session.cdp_ws_url);
      const context = browser.contexts()[0];
      const page = context.pages()[0];
      await page.goto(url, { waitUntil: 'networkidle' });

      return {
        url,
        title: await page.title(),
        session_id: session.session_id,
      };
    } finally {
      await kernel.browsers.deleteByID(session.session_id);
      console.log('deleted:', session.session_id);
    }
  },
);
EOF
fi

printf 'Created %s Kernel scaffold in %s\n' "$mode" "$target_dir"
printf 'Pinned ranges: @onkernel/sdk %s, playwright %s\n' "$sdk_range" "$playwright_range"
printf 'Next: cd %s && npm install && npm run check\n' "$target_dir"
if [ "$mode" = "embed" ]; then
  printf 'Run with: export KERNEL_API_KEY=... && npm run start\n'
else
  printf 'Deploy with: export KERNEL_API_KEY=... && npm run deploy\n'
fi
