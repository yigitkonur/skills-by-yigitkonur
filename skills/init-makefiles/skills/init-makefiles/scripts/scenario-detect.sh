#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
cd "$root"

has_jq=0
if command -v jq >/dev/null 2>&1; then
  has_jq=1
fi

declare -a signals=()
declare -a candidates=()

add_signal() {
  signals+=("$1")
}

pkg_has() {
  key="$1"
  file="${2:-package.json}"
  [ -f "$file" ] || return 1
  if [ "$has_jq" -eq 1 ]; then
    jq -e --arg key "$key" '(.dependencies // {})[$key] or (.devDependencies // {})[$key]' "$file" >/dev/null 2>&1
  else
    grep -q "\"$key\"" "$file"
  fi
}

pkg_has_any_regex() {
  regex="$1"
  file="${2:-package.json}"
  [ -f "$file" ] || return 1
  if [ "$has_jq" -eq 1 ]; then
    jq -r '((.dependencies // {}) + (.devDependencies // {})) | keys[]' "$file" 2>/dev/null | grep -Eq "$regex"
  else
    grep -Eq "$regex" "$file"
  fi
}

count_paths() {
  find "$@" 2>/dev/null | wc -l | tr -d ' '
}

any_file() {
  for path in "$@"; do
    [ -e "$path" ] && return 0
  done
  return 1
}

frontend=0
if compgen -G 'next.config.*' >/dev/null || compgen -G 'vite.config.*' >/dev/null || compgen -G 'astro.config.*' >/dev/null || compgen -G 'nuxt.config.*' >/dev/null || compgen -G 'svelte.config.*' >/dev/null || compgen -G 'remix.config.*' >/dev/null; then
  frontend=1
  add_signal "frontend config present"
fi
if pkg_has_any_regex '^(next|vite|astro|nuxt|svelte|@remix-run/)' package.json; then
  frontend=1
  add_signal "frontend dependency present"
fi
if find . -maxdepth 3 \( -path './node_modules' -o -path './.git' \) -prune -o \( -path './app/page.*' -o -path './src/app/page.*' -o -path './pages/_app.*' -o -path './src/pages/_app.*' \) -type f -print -quit 2>/dev/null | grep -q .; then
  frontend=1
  add_signal "frontend app/pages route present"
fi

mcp=0
if pkg_has '@modelcontextprotocol/sdk' package.json || pkg_has 'mcp-use' package.json; then
  mcp=1
  add_signal "MCP dependency present"
fi
if grep -RIl --include='*.ts' --include='*.js' '@modelcontextprotocol/sdk' src >/dev/null 2>&1; then
  mcp=1
  add_signal "MCP SDK import in source"
fi

supabase=0
if [ -d supabase ] || [ -f supabase/config.toml ]; then
  supabase=1
  add_signal "supabase directory/config present"
fi
if pkg_has_any_regex '^@supabase/' package.json; then
  supabase=1
  add_signal "Supabase dependency present"
fi

backend_count=0
for package_file in $(find apps server services -maxdepth 3 -name package.json 2>/dev/null | sort); do
  if pkg_has express "$package_file" || pkg_has hono "$package_file" || pkg_has fastify "$package_file" || pkg_has koa "$package_file" || pkg_has '@nestjs/core' "$package_file"; then
    backend_count=$((backend_count + 1))
    add_signal "HTTP backend dependency in ${package_file}"
  fi
done

railway_count=$(count_paths . -maxdepth 4 -name railway.toml -not -path './node_modules/*')
if [ "$railway_count" -gt 0 ]; then
  add_signal "${railway_count} railway.toml file(s)"
fi

native_artifact=0
mac_artifact=0
if any_file Cargo.toml go.mod CMakeLists.txt Makefile.am; then
  native_artifact=1
  add_signal "native build config present"
fi
if compgen -G '*.xcodeproj' >/dev/null || compgen -G '*.xcworkspace' >/dev/null; then
  mac_artifact=1
  add_signal "Xcode project/workspace present"
fi
if [ -f Package.swift ]; then
  if grep -Eq 'macOS|\.app|executableTarget' Package.swift; then
    native_artifact=1
    add_signal "Package.swift present"
  fi
  if grep -Eq 'macOS|\.app' Package.swift; then
    mac_artifact=1
    add_signal "Package.swift has macOS/app signal"
  fi
fi
if pkg_has_any_regex '^(electron|electron-builder|electron-forge)$' package.json; then
  mac_artifact=1
  add_signal "Electron mac app dependency present"
fi

ssh_mac=0
if [ "$mac_artifact" -eq 1 ] && grep -iE '^Host[[:space:]]+macbook([[:space:]]|$)' ~/.ssh/config >/dev/null 2>&1; then
  ssh_mac=1
  add_signal "SSH Host macbook present"
fi

if [ "$frontend" -eq 1 ] && [ "$backend_count" -eq 0 ] && [ "$supabase" -eq 0 ] && [ "$mcp" -eq 0 ]; then
  candidates+=("A — Frontend-only | high | frontend signals without backend, Supabase, or MCP exclusions")
fi
if [ "$mcp" -eq 1 ] && [ "$frontend" -eq 0 ] && [ "$backend_count" -eq 0 ]; then
  candidates+=("B — MCP server | high | MCP signal without public frontend/backend signal")
elif [ "$mcp" -eq 1 ]; then
  candidates+=("B — MCP server | medium | MCP signal mixed with other app signals; inspect hosted-MCP ambiguity")
fi
if [ "$frontend" -eq 1 ] && [ "$backend_count" -gt 0 ] && [ "$supabase" -eq 0 ]; then
  candidates+=("C — Frontend + backend | high | frontend plus custom HTTP backend")
fi
if [ "$frontend" -eq 1 ] && [ "$supabase" -eq 1 ] && [ "$backend_count" -eq 0 ]; then
  candidates+=("D — Frontend + Supabase | high | frontend plus Supabase without custom backend")
elif [ "$frontend" -eq 1 ] && [ "$supabase" -eq 1 ] && [ "$backend_count" -gt 0 ]; then
  candidates+=("C+D — Frontend + backend + Supabase | medium | supported combined shape; confirm backend deploys separately")
fi
if { [ "$railway_count" -gt 1 ] || [ "$backend_count" -gt 1 ]; } && [ "$frontend" -eq 0 ]; then
  candidates+=("E — Multi-service Railway | high | multiple Railway/backend services without frontend")
elif { [ "$railway_count" -gt 1 ] || [ "$backend_count" -gt 1 ]; }; then
  candidates+=("E — Multi-service Railway | medium | multiple backend services present inside mixed repo")
fi
if [ "$native_artifact" -eq 1 ] && [ "$mac_artifact" -eq 0 ] && [ "$frontend" -eq 0 ]; then
  candidates+=("F — Build-artifact | high | native build artifact without Mac app or web signals")
elif [ "$native_artifact" -eq 1 ] && [ "$mac_artifact" -eq 0 ]; then
  candidates+=("F — Build-artifact | low | native build config mixed with web signals")
fi
if [ "$mac_artifact" -eq 1 ] && [ "$ssh_mac" -eq 1 ]; then
  candidates+=("G — MacBook ship | high | Mac app artifact plus Host macbook")
elif [ "$mac_artifact" -eq 1 ]; then
  candidates+=("G — MacBook ship | medium | Mac app artifact present; remote Mac alias not detected")
fi

printf 'init-makefiles scenario detector (read-only, heuristic only)\n'
printf 'root: %s\n\n' "$(pwd)"

printf 'Observed signals:\n'
if [ "${#signals[@]}" -eq 0 ]; then
  printf '  - none from built-in heuristics\n'
else
  for signal in "${signals[@]}"; do
    printf '  - %s\n' "$signal"
  done
fi

printf '\nCandidate scenarios:\n'
if [ "${#candidates[@]}" -eq 0 ]; then
  printf '  - ambiguous | low | no scenario reached a confident heuristic threshold\n'
else
  for candidate in "${candidates[@]}"; do
    printf '  - %s\n' "$candidate"
  done
fi

printf '\nNext step:\n'
printf '  Produce the Classification result block manually. Use this output as evidence, not as the final decision.\n'
