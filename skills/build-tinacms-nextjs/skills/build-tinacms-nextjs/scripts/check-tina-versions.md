# check-tina-versions.sh

Read-only project inspection for TinaCMS + Next.js version and routing assumptions.

## Run

```bash
bash scripts/check-tina-versions.sh /path/to/project
```

Omit the argument to inspect the current directory.

## What It Checks

- `package.json` dependency declarations for `tinacms`, `@tinacms/cli`, `next`, `react`, and `react-dom`.
- Package-manager signal from `packageManager` and lockfiles.
- `dev`, `build`, and `start` scripts, including whether they visibly use `tinacms dev` and `tinacms build`.
- Likely App Router, Pages Router, `tina/config.*`, and `tina/tina-lock.json` presence.

## Expected Output

The script prints findings plus the next reference routes to read. Warnings mean "inspect before implementation"; they do not prove the project is broken.

## Limitations

- It does not install packages, query npm, edit files, or parse every lockfile format deeply.
- It reports package ranges from `package.json`; use `npm view` or the package manager when you need current registry versions.
- Mixed App Router and Pages Router projects still require manual judgment. This skill treats Pages Router as legacy/fallback.
