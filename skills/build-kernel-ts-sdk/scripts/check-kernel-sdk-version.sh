#!/usr/bin/env bash
set -u

packages=(
  "@onkernel/sdk"
  "@onkernel/managed-auth-react"
  "@onkernel/cli"
)

warn_count=0

warn() {
  printf 'WARN: %s\n' "$*" >&2
  warn_count=$((warn_count + 1))
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'BLOCKER: missing required command: %s\n' "$1" >&2
    exit 2
  fi
}

need_cmd node
need_cmd npm

printf 'Kernel SDK preflight\n'
printf 'node: %s\n' "$(node --version)"
printf 'npm: %s\n' "$(npm --version)"
printf '\n'

installed_version() {
  local pkg="$1"
  node - "$pkg" <<'NODE'
const pkg = process.argv[2];
try {
  const meta = require(`./node_modules/${pkg}/package.json`);
  process.stdout.write(meta.version || "");
} catch {
  process.exit(42);
}
NODE
}

latest_version() {
  local pkg="$1"
  npm view "$pkg" version --json 2>/dev/null | node -e '
const fs = require("node:fs");
const raw = fs.readFileSync(0, "utf8").trim();
if (!raw) process.exit(1);
const parsed = JSON.parse(raw);
process.stdout.write(String(parsed));
' 2>/dev/null
}

printf 'Package versions\n'
for pkg in "${packages[@]}"; do
  if installed="$(installed_version "$pkg" 2>/dev/null)"; then
    printf -- '- installed %-30s %s\n' "$pkg" "$installed"
  else
    installed=""
    printf -- '- installed %-30s %s\n' "$pkg" "not found in ./node_modules"
  fi

  if latest="$(latest_version "$pkg")"; then
    printf '  npm latest %-28s %s\n' "$pkg" "$latest"
    if [ -n "$installed" ] && [ "$installed" != "$latest" ]; then
      warn "$pkg installed $installed differs from npm latest $latest"
    fi
  else
    warn "could not query npm latest for $pkg"
  fi
done
printf '\n'

if [ -f "node_modules/@onkernel/sdk/api.md" ]; then
  printf 'api.md: found at node_modules/@onkernel/sdk/api.md\n'
else
  warn "node_modules/@onkernel/sdk/api.md not found; install @onkernel/sdk before relying on generated method names"
fi

if [ -n "${KERNEL_API_KEY:-}" ]; then
  printf 'KERNEL_API_KEY: set (value hidden)\n'
else
  warn "KERNEL_API_KEY is not set"
fi

printf '\n'
if [ "$warn_count" -gt 0 ]; then
  printf 'Completed with %s warning(s). Warnings are not hard failures.\n' "$warn_count"
else
  printf 'Completed with no warnings.\n'
fi
