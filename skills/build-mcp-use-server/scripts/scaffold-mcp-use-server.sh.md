# scaffold-mcp-use-server.sh

**What it does:** Drives `create-mcp-use-app@2.0.0-beta.14` non-interactively with real CLI flags from the v2 beta.

**When to use:** Starting a new MCP server project from scratch.

## Usage

```bash
bash scripts/scaffold-mcp-use-server.sh [template] [project-name] [package-manager]
```

### Arguments

| Arg | Default | Options | Notes |
|-----|---------|---------|-------|
| `template` | `mcp-server` | `mcp-server`, `mcp-apps`, `blank` | `mcp-server`: tools + prompts; `mcp-apps`: includes React views; `blank`: empty server |
| `project-name` | `my-mcp-server` | any string | Directory name; must not exist |
| `package-manager` | `npm` | `npm`, `pnpm`, `bun` | Dependency installer to use |

### Examples

**Basic tool server:**
```bash
bash scripts/scaffold-mcp-use-server.sh mcp-server weather-server
# Creates: weather-server/ with tools + prompts
```

**MCP Apps (with views):**
```bash
bash scripts/scaffold-mcp-use-server.sh mcp-apps my-app npm
# Creates: my-app/ with tools + React views
```

**Minimal blank server:**
```bash
bash scripts/scaffold-mcp-use-server.sh blank empty-server pnpm
# Creates: empty-server/ with skeleton; user adds tools
```

## Output

**Success:**
```
✓ Scaffold complete!

Next steps:
  1. cd my-mcp-server
  2. npm run dev  (or: pnpm dev / bun run dev)
  3. Open http://localhost:3000/mcp/inspector in browser

To deploy:
  git init && git add -A && git commit -m 'Initial commit'
  git remote add origin <your-github-url>
  git push -u origin main
  npm run deploy
```

**Error (directory exists):**
```
✗ Directory 'my-mcp-server' already exists. Refusing to overwrite.
```

**Error (invalid template):**
```
✗ Unknown template: widgets
   Valid: mcp-server, mcp-apps, blank
```

## Generated structure

### mcp-server template
```
my-mcp-server/
├── index.ts          # Server entry with weather tool + prompt examples
├── package.json      # Scripts: dev, build, typecheck, start, deploy
├── tsconfig.json     # ESM + strict types
├── mcp-env.d.ts      # Generated tool types (empty until first typecheck)
└── .gitignore
```

### mcp-apps template
```
my-mcp-server/
├── index.ts          # Server + my-view tool
├── views/
│   └── my-view/
│       └── view.tsx  # React component for tool output
├── package.json      # Includes react@19, react-dom@19
├── tsconfig.json
├── mcp-env.d.ts
└── .gitignore
```

### blank template
```
my-mcp-server/
├── index.ts          # Empty MCPServer with no tools/prompts
├── package.json      # mcp-use only
├── tsconfig.json
├── mcp-env.d.ts
└── .gitignore
```

## Key features

- **Non-interactive:** No prompts; all flags explicit in command line
- **Beta versions:** Uses `@2.0.0-beta.14` scaffolder (matches CLI 4.0.0-beta.15)
- **Auto-install:** `--install` flag runs package manager after generation
- **Safe:** Refuses to overwrite existing directories
- **Guided output:** Prints next steps and deploy instructions

## Dev server

After generation, start the dev server:
```bash
npm run dev
```

**Default endpoints:**
- MCP server: `http://localhost:3000/mcp`
- Inspector UI: `http://localhost:3000/mcp/inspector`
- Auto-reload on file changes (HMR)

## Deployment

After dev validation:
```bash
git init
git add -A
git commit -m "Initial MCP server"
git remote add origin https://github.com/your-org/your-repo
git push -u origin main
npm run deploy
```

Result: `https://{your-slug}.run.mcp-use.com/mcp`
