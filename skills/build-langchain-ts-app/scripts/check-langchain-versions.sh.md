# check-langchain-versions.sh

Read a user repo's `package.json` and `node_modules` to print detected `langchain` and `@langchain/*` versions.

## Usage

From a user project:

```bash
bash /path/to/build-langchain-ts-app/scripts/check-langchain-versions.sh
```

Or pass a project directory explicitly:

```bash
bash /path/to/build-langchain-ts-app/scripts/check-langchain-versions.sh /path/to/project
```

## What It Checks

- `package.json` dependency specs from `dependencies`, `devDependencies`, `peerDependencies`, and `optionalDependencies`.
- Installed versions under `node_modules` when present.
- Major-version mismatches across core packages: `langchain`, `@langchain/core`, `@langchain/langgraph`, and `@langchain/openai`.
- Duplicate specs for the same package across dependency buckets.

## Output

The script prints a markdown table with package specs and installed versions, then prints warnings when the detected state is risky.

The script is read-only. It does not install, update, delete, or rewrite files.

## Related Reference

Use `references/start/version-discipline.md` to decide whether to pin, refresh, or upgrade packages after reading this script's output.
