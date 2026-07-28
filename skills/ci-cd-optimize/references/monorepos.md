# Monorepos

Use this file for Nx, Turborepo, package graphs, task graphs, remote caches, and distributed execution.

## First principle

A monorepo CI is fast when it runs the minimal affected subgraph with correct cache keys, not when it merely adds more runners.

## Nx pattern

```bash
nx affected -t lint,typecheck,test,build --base="$BASE_SHA" --head="$HEAD_SHA"
```

Requirements:

- accurate base/head or full history,
- complete project graph,
- `targetDefaults` with complete `inputs`, `outputs`, runtime, and environment dependencies,
- cacheable targets before distributed execution,
- protected remote-cache write boundaries.

Nx lockfile changes can mark every project affected; treat that as a safe escalation, not a bug to bypass.

## Turborepo pattern

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["$TURBO_DEFAULT$", "!**/*.test.ts", ".env*"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"],
      "env": ["NEXT_PUBLIC_API_URL"]
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "outputs": []
    }
  }
}
```

Do not add `dependsOn` unless the task consumes the dependency's output. Lint and typecheck often run in parallel with build; unnecessary edges serialize the graph.

Use task-level input-aware affected filtering where supported. Package-level affected detection can miss files outside package roots that feed code generation or schemas.

## Remote-cache security

A remote cache is a trust boundary:

- PR/untrusted jobs: read-only or isolated namespace.
- Protected branches: write trusted entries.
- Enable artifact signatures/integrity when available.
- Never put secrets in envs that affect cache keys unless they genuinely change output; use pass-through runtime secrets.
- If correctness is uncertain, bypass the cache for release artifacts and verify the digest.

## Distributed execution

Distributed execution helps only after:

- task graph is fine-grained,
- setup is not duplicated more than execution saves,
- every target in the distributed chain is cacheable or explicitly coordinated,
- deployment/secrets stay on the trusted coordinator,
- logs, artifacts, and test results are merged back.

Start workers/agents before long dependency installation when the platform supports it so provisioning overlaps setup.

## Common failures

| Failure | Cause | Fix |
|---|---|---|
| Cache hit but stale output | Missing input/env/output | Complete declarations; invalidate namespace. |
| Every PR runs everything | Lockfile/global input changes or bad base | Correct base; separate global escalation from package work. |
| Affected skips codegen | External schema not in task inputs | Add input or enable task-input-aware affected. |
| Distributed run not faster | Setup dominates fine tasks | Coarser tasks or fewer workers. |
| Cache poisoning | Untrusted write to trusted cache | Read-only PR access or isolated namespace. |

## Sources

- Nx affected: https://nx.dev/docs/features/ci-features/affected (accessed 2026-07-28)
- Nx cache security: https://nx.dev/docs/kb/cache-security (accessed 2026-07-28)
- Nx distributed execution: https://nx.dev/docs/features/ci-features/distribute-task-execution (accessed 2026-07-28)
- Turborepo configuration: https://turbo.build/repo/docs/reference/configuration (accessed 2026-07-28)
- Turborepo caching: https://turbo.build/repo/docs/crafting-your-repository/caching (accessed 2026-07-28)
- Turborepo CI: https://turbo.build/repo/docs/crafting-your-repository/constructing-ci (accessed 2026-07-28)
