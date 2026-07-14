#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scaffold-createagent-app.sh [target-dir] [--force]

Create a minimal LangChain.js TypeScript createAgent app.
The script refuses to overwrite existing files unless --force is passed.
EOF
}

target_dir="."
force="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --force)
      force="true"
      shift
      ;;
    *)
      target_dir="$1"
      shift
      ;;
  esac
done

target_dir="$(mkdir -p "$target_dir" && cd "$target_dir" && pwd)"

write_file() {
  local rel="$1"
  local path="$target_dir/$rel"
  mkdir -p "$(dirname "$path")"

  if [[ -e "$path" && "$force" != "true" ]]; then
    echo "Refusing to overwrite existing file: $path" >&2
    echo "Re-run with --force to replace scaffold-managed files." >&2
    exit 1
  fi

  cat > "$path"
  echo "wrote $rel"
}

write_file "package.json" <<'EOF'
{
  "name": "langchain-createagent-app",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "tsx src/index.ts",
    "check": "tsc --noEmit"
  },
  "dependencies": {
    "@langchain/core": "1.1.45",
    "@langchain/langgraph": "1.3.0",
    "@langchain/openai": "1.4.5",
    "langchain": "1.4.0",
    "zod": "4.4.3"
  },
  "devDependencies": {
    "@types/node": "20.19.40",
    "tsx": "4.21.0",
    "typescript": "5.9.3"
  }
}
EOF

write_file "tsconfig.json" <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "dist"
  },
  "include": ["src/**/*.ts"]
}
EOF

write_file ".env.example" <<'EOF'
OPENAI_API_KEY=replace-me
OPENAI_MODEL=gpt-4.1-mini
EOF

write_file "src/lib/math.ts" <<'EOF'
export function add(a: number, b: number): number {
  return a + b;
}
EOF

write_file "src/agent.ts" <<'EOF'
import { ChatOpenAI } from "@langchain/openai";
import { createAgent, tool } from "langchain";
import { z } from "zod";
import { add } from "./lib/math.js";

const addNumbers = tool(
  async ({ a, b }) => {
    return String(add(a, b));
  },
  {
    name: "add_numbers",
    description: "Add two numbers using local business logic.",
    schema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
    }),
  },
);

export const agent = createAgent({
  model: new ChatOpenAI({
    model: process.env.OPENAI_MODEL ?? "gpt-4.1-mini",
    temperature: 0,
  }),
  tools: [addNumbers],
  systemPrompt: "Use tools for arithmetic. Keep final answers concise.",
});

export async function runAgent(input: string) {
  return agent.invoke(
    { messages: [{ role: "user", content: input }] },
    { recursionLimit: 6 },
  );
}
EOF

write_file "src/index.ts" <<'EOF'
import { runAgent } from "./agent.js";

const prompt = process.argv.slice(2).join(" ") || "Add 19 and 23.";

if (!process.env.OPENAI_API_KEY) {
  throw new Error("Set OPENAI_API_KEY before running the agent.");
}

const result = await runAgent(prompt);
const lastMessage = result.messages.at(-1);
const content = lastMessage?.content ?? result;

console.log(typeof content === "string" ? content : JSON.stringify(content, null, 2));
EOF

cat <<EOF

Scaffold created in: $target_dir

Next commands:
  cd "$target_dir"
  npm install
  cp .env.example .env
  # edit .env and set OPENAI_API_KEY
  npm run check
  npm run dev -- "Add 19 and 23."

The scaffold pins LangChain package versions from references/start/version-discipline.md.
EOF
