#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: migrate-imports.sh [--write] <project-dir>

Dry-run by default. Rewrites only known MCP SDK v1 import paths and the
explicit class/name mappings covered by convert-mcp-sdk-v1-to-v2.
USAGE
}

WRITE=0
PROJECT_INPUT=""

while (($#)); do
  case "$1" in
    --write)
      WRITE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$PROJECT_INPUT" ]]; then
        echo "error: expected one project directory" >&2
        exit 2
      fi
      PROJECT_INPUT="$1"
      shift
      ;;
  esac
done

if [[ -z "$PROJECT_INPUT" ]]; then
  echo "error: project directory is required" >&2
  usage >&2
  exit 2
fi

if [[ ! -d "$PROJECT_INPUT" ]]; then
  echo "error: project directory not found: $PROJECT_INPUT" >&2
  exit 2
fi

PROJECT="$(cd "$PROJECT_INPUT" && pwd -P)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

search_file() {
  local file="$1"
  local pattern="$2"
  grep -Eq "$pattern" "$file" 2>/dev/null
}

warn_file() {
  local file="$1"
  local message="$2"
  printf 'warning: %s: %s\n' "${file#$PROJECT/}" "$message" >&2
}

show_relevant_lines() {
  local file="$1"
  grep -nE '@modelcontextprotocol/|StreamableHTTPServerTransport|NodeStreamableHTTPServerTransport|McpError|ErrorCode|ProtocolError' "$file" 2>/dev/null || true
}

transform_file() {
  local file="$1"
  local out="$2"
  local rename_streamable=0
  local rename_errors=0

  if search_file "$file" '@modelcontextprotocol/sdk/server/streamableHttp\.js'; then
    rename_streamable=1
  fi

  if search_file "$file" '@modelcontextprotocol/sdk/types\.js' && search_file "$file" 'McpError|ErrorCode'; then
    if search_file "$file" 'RequestSchema|ResultSchema|NotificationSchema|ResourceSchema|PromptSchema'; then
      warn_file "$file" "mixed /types.js import with schemas; split error imports manually before rewriting"
    else
      rename_errors=1
    fi
  fi

  awk -v rename_streamable="$rename_streamable" -v rename_errors="$rename_errors" '
    {
      line = $0
      gsub("@modelcontextprotocol/sdk/server/mcp.js", "@modelcontextprotocol/server", line)
      gsub("@modelcontextprotocol/sdk/server/stdio.js", "@modelcontextprotocol/server", line)
      gsub("@modelcontextprotocol/sdk/server/streamableHttp.js", "@modelcontextprotocol/node", line)
      gsub("@modelcontextprotocol/sdk/server/express.js", "@modelcontextprotocol/express", line)
      gsub("@modelcontextprotocol/sdk/client/index.js", "@modelcontextprotocol/client", line)

      if (rename_errors == "1") {
        gsub("McpError", "ProtocolError", line)
        gsub("ErrorCode", "ProtocolErrorCode", line)
        gsub("@modelcontextprotocol/sdk/types.js", "@modelcontextprotocol/server", line)
      }

      if (rename_streamable == "1") {
        gsub("StreamableHTTPServerTransport", "NodeStreamableHTTPServerTransport", line)
      }

      gsub("NodeNodeStreamableHTTPServerTransport", "NodeStreamableHTTPServerTransport", line)
      gsub("ProtocolProtocolErrorCode", "ProtocolErrorCode", line)
      gsub("ProtocolProtocolError", "ProtocolError", line)

      print line
    }
  ' "$file" > "$out"
}

changed_count=0

while IFS= read -r -d '' file; do
  if search_file "$file" '@modelcontextprotocol/sdk/server/auth/|mcpAuthRouter|requireBearerAuth|OAuthServerProvider'; then
    warn_file "$file" "auth-router usage is not rewritten by this helper"
  fi
  if search_file "$file" 'SSEServerTransport'; then
    warn_file "$file" "SSEServerTransport is removed in v2; rewrite transport flow manually"
  fi
  if search_file "$file" '@modelcontextprotocol/sdk' && search_file "$file" '@modelcontextprotocol/(server|client|node|express|hono|server-auth-legacy)'; then
    warn_file "$file" "mixed v1/v2 MCP imports detected"
  fi

  tmp="$TMP_DIR/$(basename "$file").out"
  transform_file "$file" "$tmp"

  if cmp -s "$file" "$tmp"; then
    continue
  fi

  changed_count=$((changed_count + 1))
  rel="${file#$PROJECT/}"

  if (( WRITE )); then
    cp "$tmp" "$file"
    printf 'rewrote: %s\n' "$rel"
  else
    printf 'would rewrite: %s\n' "$rel"
    echo "  before:"
    show_relevant_lines "$file" | sed 's/^/    /'
    echo "  after:"
    show_relevant_lines "$tmp" | sed 's/^/    /'
  fi
done < <(
  find "$PROJECT" \
    -type d \( -name node_modules -o -name dist -o -name build -o -name coverage \) -prune -o \
    -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' \) \
    -print0
)

if (( WRITE )); then
  printf 'done: rewrote %d file(s)\n' "$changed_count"
else
  printf 'dry run: %d file(s) would be rewritten\n' "$changed_count"
  echo "rerun with --write to modify files"
fi
