# scaffold-createagent-app.sh

Create a minimal LangChain.js TypeScript `createAgent` app for greenfield demos and smoke tests.

## Usage

```bash
bash /path/to/build-langchain-ts-app/scripts/scaffold-createagent-app.sh ./my-agent
```

Overwrite scaffold-managed files only when that is intentional:

```bash
bash /path/to/build-langchain-ts-app/scripts/scaffold-createagent-app.sh ./my-agent --force
```

## Files Created

- `package.json` with pinned LangChain, TypeScript, `tsx`, and Zod versions.
- `tsconfig.json` configured for strict ESM TypeScript.
- `.env.example` with `OPENAI_API_KEY` and `OPENAI_MODEL`.
- `src/lib/math.ts` as real local business logic.
- `src/agent.ts` with `createAgent`, a Zod-backed tool, and `recursionLimit`.
- `src/index.ts` as the runnable CLI entrypoint.

## Safety Behavior

The script creates the target directory if needed. It refuses to overwrite existing files unless `--force` is passed.

It does not run `npm install`, execute the agent, or write secrets. It prints the exact next commands after creating files.

## Verification

After scaffolding:

```bash
npm install
cp .env.example .env
npm run check
npm run dev -- "Add 19 and 23."
```

Set `OPENAI_API_KEY` in `.env` or the shell before the runtime command.
