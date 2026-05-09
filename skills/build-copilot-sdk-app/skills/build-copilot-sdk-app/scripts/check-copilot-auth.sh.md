# check-copilot-auth.sh

Run this from a target project to verify the basics before debugging Copilot SDK code:

```bash
bash path/to/check-copilot-auth.sh .
```

What it checks:

- Node is installed and satisfies the installed `@github/copilot-sdk` `engines.node` range when the range is parseable.
- `@github/copilot-sdk` resolves from the project.
- GitHub auth and BYOK environment variables are present or absent without printing secret values.
- `CopilotClient.getAuthStatus()` runs unless `--skip-runtime` is passed.

Use `--skip-runtime` in CI or docs checks where starting the CLI process is not safe:

```bash
bash path/to/check-copilot-auth.sh . --skip-runtime
```

If BYOK is the intended auth path, treat a failed GitHub `getAuthStatus()` as expected and validate the provider by running a minimal session with `provider` and `model`.
