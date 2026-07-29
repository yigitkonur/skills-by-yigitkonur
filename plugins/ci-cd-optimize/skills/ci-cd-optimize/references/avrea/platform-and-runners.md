# Avrea Platform and Runners

Optional. Read when a repository already runs on Avrea, or when measured evidence points at runner hardware or queue capacity and Avrea is under consideration. Everything here is provider-specific; the decision rules in `references/runners-and-autoscaling.md` still govern whether a runner change is the right move at all.

## What it is

A CI/CD platform that executes GitHub Actions workflows on ephemeral VMs with colocated caching and step-level observability. It does not introduce a config format: workflows stay in `.github/workflows/`, GitHub remains the source of truth for events and required checks, and only the `runs-on` label changes. Only GitHub Actions is supported today.

The images derive from the official `actions/runner-images`, so the preinstalled toolchain matches GitHub-hosted runners.

## Migration surface

```yaml
jobs:
  build:
    runs-on: ubuntu-latest          # before
    runs-on: avrea-ubuntu-latest    # after
```

Bare `avrea-ubuntu-latest` maps to 2 vCPU / 8 GB, matching GitHub's default. Because the change is one label, the honest migration test is to duplicate the workflow rather than edit it, run both, and compare — which also gives the A/B data described in `references/avrea/cli-evidence.md`.

Run it at least twice. The first run measures hardware; the second measures hardware plus a warm cache. Reporting only the second as "the speedup" overstates what a cold pipeline will see.

## Runner labels (accessed 2026-07-29)

| Family | Labels | Notes |
|---|---|---|
| Linux x64 | `avrea-ubuntu-latest-{1,2,4,8,16,32,64}-vcpu` | 4 GB RAM per vCPU |
| Linux ARM | `avrea-ubuntu-latest-arm-{1,2,4,8,16}-vcpu` | 4 GB RAM per vCPU; caps at 16 vCPU |
| macOS | `avrea-macos-26-{8,16}-vcpu` | ARM only; 24 GB / 48 GB (see the RAM note below) |
| Windows | `avrea-windows-2025-{2,4,8,16}-vcpu` | 4 GB RAM per vCPU; no 1-vCPU size |
| Pinned Ubuntu | `avrea-ubuntu-{26.04,24.04,22.04}-*-vcpu`, plus `-arm-` variants | Use when image drift must be avoided |

Ubuntu 26.04 is available on both architectures (`avrea-ubuntu-26.04-4-vcpu`,
`avrea-ubuntu-26.04-arm-4-vcpu`) across the standard sizes, at the same rates
as 24.04 — there is no version premium. Two things follow: `avrea-ubuntu-latest`
**still resolves to 24.04 and does not move on its own**, so adopting 26.04 is
an explicit per-job edit; and because the change is free, a 26.04 trial is a
duplicate-the-workflow A/B like any other, not a budget decision.

**macOS RAM is a live source conflict.** The pricing page and the M5 Max
announcement both give 24 GB at 8 vCPU and 48 GB at 16 vCPU (3 GB/vCPU); the
runners reference page still says 16 GB / 32 GB (2 GB/vCPU) and appears stale
on this figure. Treat 3 GB/vCPU as current, and if a memory-bound macOS
decision depends on it, confirm against `avr job metrics` on a real job rather
than either page. The runners doc also has not yet added 26.04 to its pinned
list — the changelog leads the reference docs here, which is worth remembering
before quoting either as settled.

Billing is per minute with no minimum. Rates checked on avrea.com/pricing
(2026-07-29): Linux x64 **$0.002**/vCPU-min, Linux ARM **$0.006**/vCPU-min,
macOS **$0.01**/vCPU-min, Windows **$0.004**/vCPU-min. Rates live on the
pricing page, not in the docs — re-check before quoting, per the skill's
no-confabulation rule.


## Sizing decisions

Larger runners are the last resort in the performance order, and the measured A/B in `references/avrea/cli-evidence.md` shows why: a CPU-bound backend job improved 160s → 47s, while a lint job moved 9s → 8s. Before resizing:

1. Confirm the job is on the critical path (start offset + duration), not merely expensive in total.
2. Confirm it is CPU- or memory-bound via `avr job metrics`.
3. Confirm the workload is actually parallel — a single-threaded `tsc` or a serial test runner gains nothing from 32 vCPU and costs proportionally more.

Downsizing is the more common measured finding: the same gate on 16 vCPU/64 GB and on 8 vCPU/32 GB ran 159 s vs 158–160 s, with peak memory 7.4–7.8 GB vs 4.0 GB — identical wall clock at half the rate. The signature in `avr job metrics`: peak memory far below the allocation, CPU average well under 100%, wall clock flat across sizes → shrink.

On Avrea, ARM is a performance choice, not a cost saving: the published rate table (avrea.com/pricing, re-checked 2026-07-29) lists Linux ARM at 3× the x64 per-vCPU-minute rate ($0.006 vs $0.002), capped at 16 vCPU. The reason is visible in the hardware — Linux ARM and macOS runners are both backed by Apple M5 Max, so ARM here buys top-tier single-thread speed rather than the cheap-core economics ARM implies on other clouds. Choose it when the deploy target is ARM, when single-thread speed is the measured constraint, and when the toolchain plus native dependencies are known to build on ARM64; a cross-architecture surprise costs more than any saving. macOS runners exist in two sizes only, so Swift/Xcode pipelines have limited headroom — see `references/swift-xcode.md` for what to optimize instead, including the dependency-resolution wins that do not need a bigger runner.

## Observability

The console exposes a 30-day analytics view: flake rate, failure rate, median (p50) and p95 duration for successful runs, and run counts with 30-day trend charts. Run history drills run → jobs → steps → logs. Step logs support live tail, full-text search, collapsible `::group::` sections, and ANSI rendering.

Flake rate is defined as jobs that failed where the same step succeeded in other runs. That definition is worth stating when reporting, because it counts step-level inconsistency rather than a retry-to-green signal.

OpenTelemetry export is available as a setting (`export.otel.enabled`, `export.otel.endpoint`, plus auth-header key/value), which lets Avrea data land in the same backend as the CI/CD semantic conventions referenced in `references/measurement.md`. It is off by default and is an organization- or repository-scoped setting.

## Live debugging

SSH is built into every runner with no workflow changes; access follows repository permissions. Sessions exist only while the job runs — the VM is destroyed on completion, failure, or cancellation.

```bash
avr job ssh job-xxx
avr job ssh job-xxx --print-command
```

To hold a failed job open for inspection:

```yaml
- name: Keep job alive on failure for debugging
  if: failure()
  run: sleep 1800
```

Keep the `if: failure()` guard. An unguarded sleep burns paid runner minutes on every green run and inflates every duration measurement you later take.

## Settings worth knowing

`avr settings schema` lists definitions; values resolve repository-over-organization with inheritance. Verified keys (2026-07-28) include per-tool cache toggles (`cache.gha.enabled`, `cache.turbo.enabled`, `cache.bazel.enabled`, `cache.go-build.enabled`, `cache.xcode-build.enabled`, `cache.nx.enabled`, `cache.sccache.enabled`, `cache.ccache.enabled`, `cache.gradle.enabled`, `cache.maven.enabled`, `cache.nix.enabled`, `cache.packages.enabled` — all default true), diagnostics (`runner.diagnostics.enabled`, `runner.step-debug.enabled` — default false), and OTel export.

`cache.swift-registry.enabled` (default true) is documented by Avrea on
2026-07-29 but is newer than that schema snapshot — re-run `avr settings
schema` to confirm it before scripting against it. See
`references/avrea/caching.md` for what turning it off actually changes.

Toggling a cache off is a legitimate experiment to prove a cache is actually helping, but it is a shared, org- or repo-scoped change: get authorization first and restore it with `avr settings reset`.

## Trust boundary

Runners are ephemeral VMs on dedicated hardware. Avrea reports ISO 27001:2022 certification and SOC 2 Type 2 attestation. An egress firewall (`avr firewall`) manages allowed outbound destinations at org and repository scope.

Static IP egress gives the organization one stable public IPv4 for outbound runner traffic — useful when an integration test is slow or failing because a database or API sits behind an allowlist. It needs an org admin to enable, requires no workflow change, and does **not** replace egress firewall rules or destination-side authentication. Both static IP egress and SAML SSO are Avrea Enterprise features, so neither is a fix you can assume is available on a given plan.

Moving CI to any third party means secrets and source are handled by that party. That is a normal, documented decision — but it belongs in the recommendation's security-risk line, not omitted because the migration is one line of YAML.

## Sources

- Avrea docs home: https://docs.avrea.com/ (accessed 2026-07-29)
- Getting started: https://docs.avrea.com/getting-started/ (accessed 2026-07-28)
- Runners and pricing: https://docs.avrea.com/runners/ (accessed 2026-07-29)
- Pricing page (per-vCPU-minute rates): https://avrea.com/pricing (accessed 2026-07-29)
- Changelog (Ubuntu 26.04, M5 Max fleet): https://docs.avrea.com/changelog/ (accessed 2026-07-29)
- Static IP egress: https://docs.avrea.com/static-ip/ (accessed 2026-07-29)
- SAML SSO: https://docs.avrea.com/saml-sso/ (accessed 2026-07-29)
- Observability: https://docs.avrea.com/observability/ (accessed 2026-07-28)
- Debugging and SSH: https://docs.avrea.com/debugging/ (accessed 2026-07-28)
- Settings reference: https://docs.avrea.com/cli/reference/settings/ (accessed 2026-07-28)
- Settings keys verified via `avr settings schema` on `avr` 0.1.6 (2026-07-28)
