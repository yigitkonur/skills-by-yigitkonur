# check-kernel-sdk-version.sh

Run this before editing or reviewing an existing Kernel TypeScript project:

```bash
bash skills/build-kernel-ts-sdk/scripts/check-kernel-sdk-version.sh
```

From inside an installed skill, run the script relative to the skill directory:

```bash
bash scripts/check-kernel-sdk-version.sh
```

## What it checks

- Node and npm availability.
- Local `./node_modules` versions for `@onkernel/sdk`, `@onkernel/managed-auth-react`, and `@onkernel/cli` when installed.
- Current npm latest versions for those packages.
- Whether `node_modules/@onkernel/sdk/client.d.ts` exists, and prints the top-level resources plus the `browsers` method list read straight out of the shipped declarations. These are the authoritative generated surface; `@onkernel/sdk` does **not** ship `api.md` in its npm tarball, despite the relative link in the SDK's own README.
- Whether `KERNEL_API_KEY` is set, without printing the value.

## Interpreting output

- `BLOCKER` means the check cannot run, usually because Node or npm is missing. Fix that before continuing.
- `WARN` means continue with caution. Stale package versions, a missing SDK install, or a missing `KERNEL_API_KEY` do not make documentation edits invalid, but they do limit runtime verification.
- If an installed package differs from npm latest, do not update blindly. Check the repo's lockfile policy and the installed `node_modules/@onkernel/sdk/client.d.ts` plus `node_modules/@onkernel/sdk/resources/**/*.d.ts` before changing code. The upstream repo's human-readable index at https://github.com/kernel/kernel-node-sdk/blob/main/api.md is a convenient cross-check, but it is not part of the installed package and can drift from the version you have.

The script exits non-zero only for true local blockers. It does not fail solely because a package is stale or absent.
