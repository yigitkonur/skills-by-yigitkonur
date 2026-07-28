# Security Gates

Use this file to make security scanning faster without deleting the control.

## Tier every control

| Tier | Use for | Examples |
|---|---|---|
| PR block | high-confidence, high-severity, actionable in minutes | secret push protection, critical dependency review, diff-aware high-confidence SAST |
| PR warn | useful signal with noise or slower triage | medium SAST findings, license anomalies, container lows |
| Scheduled deep | full-history/full-repo scans, DAST, fuzzing, malware hunts | nightly CodeQL full scan, DAST, dependency graph review |
| Release/deploy gate | provenance, SBOM, signed image, policy verification | attestation verify, SBOM presence, admission policy |

## Fast patterns

- Use incremental/diff-aware SAST on PRs and full scans on schedule.
- Run independent scanners in parallel with a single aggregator.
- Use severity thresholds; do not make every informational finding a merge blocker.
- Keep push protection outside CI so it costs no pipeline time.
- Share scanner caches through a backend that supports concurrent runners.
- Give inline suppressions an owner and expiry; re-scan aged suppressions.

## Unsafe shortcuts

- Disabling a scanner because it is slow.
- Using workflow path filters to imply analyzer scope is reduced when the analyzer still scans everything.
- Sharing a single-process filesystem cache across parallel scanner jobs.
- Running a must-always-run scan inside a result-cached task graph (Turborepo/Nx): a scan whose "result" replays from an unrelated task's cache is a stale assertion, not a gate. Keep such scans outside the build cache.
- Permanent `nosemgrep`, `.trivyignore`, or equivalent suppressions.
- Generating SBOM/provenance but never verifying it at release/deploy time.
- Blocking every rule on day one and training developers to bypass gates.

## TypeScript-oriented gate sketch

```yaml
security:
  runs-on: ubuntu-latest
  permissions:
    contents: read
    security-events: write
  steps:
    - uses: actions/checkout@v7
    - name: Dependency review
      if: github.event_name == 'pull_request'
      uses: actions/dependency-review-action@v4
      with:
        fail-on-severity: high
    - name: Semgrep diff scan
      run: semgrep ci --baseline-commit "${{ github.event.pull_request.base.sha }}" --json --output semgrep.json
    - name: Trivy filesystem scan
      run: trivy fs --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 .
```

Adjust scanner versions and flags against current official docs when authoring.

## Sources

- CodeQL incremental analysis: https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/scan-from-the-command-line/incremental-analysis (accessed 2026-07-28)
- Push protection: https://docs.github.com/en/code-security/concepts/secret-security/push-protection (accessed 2026-07-28)
- Dependency review action: https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configure-dependency-review-action (accessed 2026-07-28)
- Semgrep CLI: https://docs.semgrep.dev/cli-reference (accessed 2026-07-28)
- Trivy filtering: http://trivy.dev/latest/docs/configuration/filtering/ (accessed 2026-07-28)
- SLSA: https://slsa.dev/spec/v1.0/levels (accessed 2026-07-28)
