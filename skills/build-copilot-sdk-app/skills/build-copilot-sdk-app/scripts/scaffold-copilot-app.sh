#!/usr/bin/env bash
set -euo pipefail

target_dir="copilot-sdk-app"
auth_mode="github"
provider="openai"
install_deps=0
force=0

usage() {
  cat <<'EOF'
Usage: scaffold-copilot-app.sh [target-dir] [options]

Options:
  --auth github|byok       Template auth path (default: github)
  --provider NAME          BYOK provider: openai, azure, foundry, anthropic, ollama
  --install                Run npm install after writing files
  --force                  Overwrite existing package.json/src/index.ts
  -h, --help               Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auth)
      auth_mode="${2:?missing auth mode}"
      shift 2
      ;;
    --provider)
      provider="${2:?missing provider}"
      shift 2
      ;;
    --install)
      install_deps=1
      shift
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
      target_dir="$1"
      shift
      ;;
  esac
done

case "$auth_mode" in
  github|byok) ;;
  *) echo "FAIL: --auth must be github or byok" >&2; exit 1 ;;
esac

case "$provider" in
  openai|azure|foundry|anthropic|ollama) ;;
  *) echo "FAIL: --provider must be openai, azure, foundry, anthropic, or ollama" >&2; exit 1 ;;
esac

mkdir -p "$target_dir/src"

if [[ "$force" -ne 1 && ( -e "$target_dir/package.json" || -e "$target_dir/src/index.ts" ) ]]; then
  echo "FAIL: target already contains package.json or src/index.ts. Use --force to overwrite." >&2
  exit 1
fi

cat > "$target_dir/package.json" <<'EOF'
{
  "name": "copilot-sdk-app",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "tsx src/index.ts",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@github/copilot-sdk": "latest",
    "zod": "^4.3.6"
  },
  "devDependencies": {
    "@types/node": "^25.0.0",
    "tsx": "^4.20.0",
    "typescript": "^5.0.0"
  }
}
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

if [[ "$auth_mode" == "github" ]]; then
  cat > "$target_dir/src/index.ts" <<'EOF'
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient();

try {
  await client.start();
  const auth = await client.getAuthStatus();
  if (!auth.isAuthenticated) {
    throw new Error(
      "Authenticate with `npx copilot login` / `copilot login`, or set COPILOT_GITHUB_TOKEN, GH_TOKEN, or GITHUB_TOKEN."
    );
  }

  const session = await client.createSession({
    model: process.env.COPILOT_MODEL ?? "gpt-5",
    onPermissionRequest: approveAll,
  });

  try {
    const response = await session.sendAndWait({ prompt: "What is 2 + 2?" });
    console.log(response?.data.content ?? "(no response)");
  } finally {
    await session.disconnect();
  }
} finally {
  await client.stop();
}
EOF
else
  case "$provider" in
    openai)
      provider_block='{
      type: "openai",
      baseUrl: "https://api.openai.com/v1",
      apiKey: needEnv("OPENAI_API_KEY"),
    }'
      model_default='gpt-4.1'
      ;;
    azure)
      provider_block='{
      type: "azure",
      baseUrl: needEnv("AZURE_OPENAI_ENDPOINT"),
      apiKey: needEnv("AZURE_OPENAI_KEY"),
      azure: {
        apiVersion: process.env.AZURE_OPENAI_API_VERSION ?? "2024-10-21",
      },
    }'
      model_default='YOUR-AZURE-DEPLOYMENT'
      ;;
    foundry)
      provider_block='{
      type: "openai",
      baseUrl: needEnv("FOUNDRY_BASE_URL"),
      apiKey: needEnv("FOUNDRY_API_KEY"),
      wireApi: "responses",
    }'
      model_default='YOUR-FOUNDRY-DEPLOYMENT'
      ;;
    anthropic)
      provider_block='{
      type: "anthropic",
      baseUrl: "https://api.anthropic.com",
      apiKey: needEnv("ANTHROPIC_API_KEY"),
    }'
      model_default='claude-sonnet-4.5'
      ;;
    ollama)
      provider_block='{
      type: "openai",
      baseUrl: process.env.OLLAMA_BASE_URL ?? "http://localhost:11434/v1",
    }'
      model_default='llama3.1'
      ;;
  esac

  cat > "$target_dir/src/index.ts" <<EOF
import { CopilotClient, approveAll } from "@github/copilot-sdk";

function needEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(\`Missing required env var: \${name}\`);
  return value;
}

const client = new CopilotClient();

try {
  const session = await client.createSession({
    model: process.env.COPILOT_MODEL ?? "$model_default",
    provider: $provider_block,
    onPermissionRequest: approveAll,
  });

  try {
    const response = await session.sendAndWait({ prompt: "What is 2 + 2?" });
    console.log(response?.data.content ?? "(no response)");
  } finally {
    await session.disconnect();
  }
} finally {
  await client.stop();
}
EOF
fi

if [[ "$install_deps" -eq 1 ]]; then
  npm install --prefix "$target_dir"
fi

echo "Created $target_dir"
echo "Next:"
echo "  cd $target_dir"
if [[ "$install_deps" -ne 1 ]]; then
  echo "  npm install"
fi
echo "  npm run typecheck"
echo "  npm start"
