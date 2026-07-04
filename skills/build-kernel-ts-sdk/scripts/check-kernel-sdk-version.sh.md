# check-kernel-sdk-version.sh

Run this before editing or reviewing an existing Kernel TypeScript project:

```bash
bash skills/build-kernel-ts-sdk/skills/build-kernel-ts-sdk/scripts/check-kernel-sdk-version.sh
```

From inside an installed skill, run the script relative to the skill directory:

```bash
bash scripts/check-kernel-sdk-version.sh
```

## What it checks

- Node and npm availability.
- Local `./node_modules` versions for `@onkernel/sdk`, `@onkernel/managed-auth-react`, and `@onkernel/cli` when installed.
- Current npm latest versions for those packages.
- Whether `node_modules/@onkernel/sdk/api.md` exists.
- Whether `KERNEL_API_KEY` is set, without printing the value.

## Interpreting output

- `BLOCKER` means the check cannot run, usually because Node or npm is missing. Fix that before continuing.
- `WARN` means continue with caution. Stale package versions, missing `api.md`, or a missing `KERNEL_API_KEY` do not make documentation edits invalid, but they do limit runtime verification.
- If an installed package differs from npm latest, do not update blindly. Check the repo's lockfile policy and the live SDK `api.md` before changing code.

The script exits non-zero only for true local blockers. It does not fail solely because a package is stale or absent.
