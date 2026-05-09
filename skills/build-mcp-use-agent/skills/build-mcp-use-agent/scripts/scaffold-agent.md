# scaffold-agent.sh

Scaffold a minimal TypeScript `MCPAgent` project in an explicit target directory.

## Usage

```bash
bash scripts/scaffold-agent.sh --target ./agent-demo
```

Use `--force` only when replacing generated files is intentional:

```bash
bash scripts/scaffold-agent.sh --target ./agent-demo --force
```

## Generated project

- `package.json` with `dev` and `typecheck` scripts
- `tsconfig.json`
- `.env.example`
- `src/index.ts` using simplified-mode `MCPAgent`

The script does not run `npm install`. It avoids overwriting existing files unless `--force` is supplied.
