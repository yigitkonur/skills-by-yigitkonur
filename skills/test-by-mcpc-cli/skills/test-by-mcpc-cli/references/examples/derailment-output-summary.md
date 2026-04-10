# Derailment Output Summary

This file collects the live outputs and normalized agent findings that drove the latest `test-by-mcpc-cli` fixes.

## Local command outputs

### Installed CLI version

```text
$ mcpc --version
0.2.4
```

### Skill validation

```text
$ python3 scripts/validate-skills.py
Validated 42 skills

✅ All validations passed
```

### Proxy bearer-token reality check

Observed with a fresh isolated `MCPC_HOME_DIR` and a local Everything Streamable HTTP server on `127.0.0.1:3011`.

```text
$ mcpc connect 127.0.0.1:3011/mcp @proxy-auth-test --proxy 127.0.0.1:8790 --proxy-bearer-token demo-token
✓ Session @proxy-auth-test created
[@proxy-auth-test → http://127.0.0.1:3011/mcp (HTTP) [proxy: 127.0.0.1:8790]]
```

```text
$ curl http://127.0.0.1:8790/health
200
BODY={"status":"ok"}
```

```text
$ curl -H 'Authorization: Bearer wrong-token' http://127.0.0.1:8790/health
200
BODY={"status":"ok"}
```

```text
$ curl -H 'Authorization: Bearer demo-token' http://127.0.0.1:8790/health
200
BODY={"status":"ok"}
```

The funny but useful result: `/health` was so friendly it accepted every bearer token we threw at it.
That made it a solid liveness probe and a bad auth-enforcement test.

## Round 1 output

### Euler

- `[STUCK]` none
- `[GUESSED]` had to choose between reusing an old disconnected `@everything-http` session and starting a fresh Everything target
- `[BROKE]` none
- `[NICE]` session-first syntax, capability boundaries, and `MCPC_HOME_DIR` isolation were already strong

## Round 2 outputs

### Banach

- `[STUCK]` none
- `[GUESSED]` assumed the intended hosted target was `https://research.yigitkonur.com/mcp`
- `[BROKE]` parallelized `mcpc close` and `mcpc clean all`, which raced cleanup and produced `Session not found`
- `[NICE]` remote smoke-test read set, `/mcp` path guidance, `MCPC_HOME_DIR` isolation, session-first syntax, and `isError` checks all held up

### Copernicus

- `[STUCK]` none
- `[GUESSED]` treated global `mcpc --json` as the most reliable live-session assertion when `@session` JSON was thinner than expected
- `[BROKE]` wrapper-level `rtk find` and nested `rtk bash -lc` quoting were unreliable
- `[NICE]` routing to HTTP, CI, scripting, and recipe docs was accurate, and the examples matched `https://research.yigitkonur.com/mcp`

### Godel

- `[STUCK]` none
- `[GUESSED]` widened beyond the original stdio minimal read set to include discovery and tool-resource docs because prompts, resources, and templates were explicit acceptance criteria
- `[BROKE]` `rtk mcpc --json` hung in that run, so the generic session-inspection path was not stable under wrappers
- `[NICE]` fresh-session guidance, Everything stdio guidance, capability-boundary warnings, and `resources-templates-list` verification were useful

### Ptolemy

- `[STUCK]` none
- `[GUESSED]` none
- `[BROKE]` session inspection around `mcpc --json`, `@session`, and wrapper variants was inconsistent enough that a global dump was not a good first move
- `[NICE]` explicit `/mcp` path discipline and the warning not to trust advertised capabilities focused the task on real `task:required` behavior

### Helmholtz

- `[STUCK]` global session listings and executable session behavior disagreed, so cleanup could not proceed safely without deeper verification
- `[GUESSED]` combined quick reference, session management, cleanup, Everything, and stdio guides because no single minimal read set matched the task
- `[BROKE]` `rtk mcpc` and `rtk mcpc --json | jq ...` were unreliable, and wrapper-visible sessions did not behave like plain `mcpc` sessions
- `[NICE]` the skill already prevented unsafe reuse of non-`live` sessions and pushed fresh stdio sessions for Everything

### Gauss

- `[STUCK]` none
- `[GUESSED]` interpreted “bearer token” as the local proxy guard, not upstream server auth
- `[BROKE]` `rtk mcpc --json` needed a wrapper timeout, and `/health` did not enforce bearer auth despite `--proxy-bearer-token`
- `[NICE]` session-first syntax and `/health` as the stable probe were still useful once `/health` was reframed as liveness-only

### Carson

- `[STUCK]` none
- `[GUESSED]` none
- `[BROKE]` wrapper-driven cleanup and global session dumps were noisy, and a previously visible Everything session disappeared before reuse
- `[NICE]` the local stdio read set was accurate, and the capability reality-check prevented false confidence from advertised features

### Carver

- `[STUCK]` none
- `[GUESSED]` initially treated `rtk mcpc` as an execution requirement rather than a shell preference
- `[BROKE]` `rtk mcpc` did not act like a clean passthrough, and wrapper-mediated session visibility diverged from plain `mcpc`
- `[NICE]` the remote smoke-test read set, session-first flow, `/mcp` path guidance, and native discovery-first approach all worked

## Derived fixes

These outputs directly led to the current skill guidance:

- use plain `mcpc` first when validating the CLI contract
- do not start with an unfiltered global session dump on a busy machine
- if `restart` says `Session not found`, create a fresh session name immediately
- treat proxy `/health` as liveness only, not bearer-auth proof
- include prompts, resources, and templates in the first stdio inspection pass when acceptance requires them
- sequence `close` and `clean`; do not race them
