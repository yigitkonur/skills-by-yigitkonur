# scaffold-copilot-app.sh

Create a minimal ESM TypeScript Copilot SDK project:

```bash
bash path/to/scaffold-copilot-app.sh my-copilot-app
```

Default output:

- `package.json` with `"type": "module"`, `start`, and `typecheck` scripts.
- `tsconfig.json` using `NodeNext` ESM settings.
- `src/index.ts` using `CopilotClient`, `approveAll`, `getAuthStatus()`, `sendAndWait()`, `session.disconnect()`, and `client.stop()`.
- Dependencies declared for `@github/copilot-sdk`, `zod`, `tsx`, TypeScript, and Node types.

BYOK templates:

```bash
bash path/to/scaffold-copilot-app.sh my-openai-app --auth byok --provider openai
bash path/to/scaffold-copilot-app.sh my-azure-app --auth byok --provider azure
bash path/to/scaffold-copilot-app.sh my-foundry-app --auth byok --provider foundry
bash path/to/scaffold-copilot-app.sh my-anthropic-app --auth byok --provider anthropic
bash path/to/scaffold-copilot-app.sh my-ollama-app --auth byok --provider ollama
```

Use `--install` to run `npm install` immediately. Use `--force` only when overwriting a disposable scaffold.

The script does not run Copilot; after scaffolding, validate with:

```bash
npm install
npm run typecheck
npm start
```
