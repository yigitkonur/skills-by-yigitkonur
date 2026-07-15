# run-agent-device

An agent skill for driving the `agent-device` CLI to test iOS apps on a simulator or device — the settle-first interaction loop, evidence capture, cross-layer bug triage, and the fix-rebuild-retest cycle that keeps you from fixing the wrong layer.

The official upstream skill is dynamic: the installed CLI supplies version-matched guidance through `agent-device help workflow` (plus `help manual-qa`, `help debugging`, `help react-native`, and ten more modes). This skill layers a product-testing methodology on top instead of freezing an upstream command catalog — the loop, the layer-triage tables, the runtime-freshness discipline, and the hard-won rules that only show up after a real end-to-end test run.

Last reconciled against `agent-device 0.19.3`. Always refresh from `agent-device help workflow` and `agent-device <command> --help` when the CLI changes — if this skill ever conflicts with current help, the CLI wins.

## What it adds

- the serial settle-first loop (`snapshot -i` → `press/fill --settle` → read the settled diff), with ref/selector discipline;
- a **layer-triage table** — most empty-screen and wrong-data bugs live in the backend, API, or environment, not the screen; probe cheapest-first before editing;
- **runtime-freshness** discipline — proving the running app actually contains your fix before you retest (the #1 false-negative source: wrong Metro/worktree/port, un-redeployed backend, deploy-time env snapshots);
- a fresh-state matrix (foreground → process → local storage → server account → permissions) so onboarding/auth retests aren't silently reusing state;
- the multi-account backend-probe trap, async job terminal-state polling, and RLS credential-class pitfalls;
- an annotated map of all 65 subcommands and RN/Expo dev-loop hazards, routed into `references/`.

## Install

As a Codex/Claude plugin:

```text
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-agent-device@yigitkonur
```

With the Skills CLI:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-agent-device
```

## First check

```bash
agent-device --version
agent-device devices --platform ios
agent-device help workflow
```

Read `SKILL.md` first. The three files under `references/` are routed detail (full command map, cross-layer bug triage, React Native dev loop), not optional duplicated documentation.
