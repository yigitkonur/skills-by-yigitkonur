# check-npm-auth.sh

Diagnose token-auth wiring without printing secrets.

## Usage

```bash
bash scripts/check-npm-auth.sh
bash scripts/check-npm-auth.sh --token
bash scripts/check-npm-auth.sh --token --whoami
```

## Behavior

- explains that trusted publishing cannot be validated with `npm whoami`
- checks whether `NODE_AUTH_TOKEN` or `NPM_TOKEN` is set
- never prints token values
- maps `NPM_TOKEN` to `NODE_AUTH_TOKEN` for the diagnostic process
- runs `npm whoami` only when `--whoami` is explicitly passed
- uses a temporary npm userconfig file with a `${NODE_AUTH_TOKEN}` placeholder

Use this script only for token-auth lanes. Pure trusted publishing has no npm token and authenticates only during `npm publish`.
