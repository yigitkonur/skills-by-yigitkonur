# Setup — provision backends & build golden images (the one-time work)

The skill is the easy part. This is the "altyapıyı hazır hale getirmek" the user asked about. Do it
once per backend, then per project you only rebuild a golden when the lockfile changes.

## 0. Install the entry point
```bash
cp config.example.sh ~/.config/offload-run/config.sh   # then edit
chmod +x scripts/offload.sh scripts/*.sh scripts/backends/*.sh
ln -s "$(pwd)/scripts/offload.sh" ~/bin/offload         # or add scripts/ to PATH
```

## A. Sprites (default Linux backend — node/python)
1. Account + CLI: install `sprite` (docs.sprites.dev), `sprite login` (Fly.io auth), `sprite org auth` token.
2. The skill auto-bootstraps a golden on first run (installs pnpm/python, runs `pnpm install`/`pip install`
   from your lockfile, then `sprite checkpoint create`). To pre-bake agents for Pattern B set
   `OFFLOAD_INSTALL_AGENTS=1`.
3. **Pilot** (the honest verification step — do this before trusting it):
   ```bash
   cd ~/some-node-project
   offload -- node -e 'process.exit(3)'   # expect exit code 3 → exit-code propagation works
   offload -- npm test                    # real run; first call builds the golden, later calls are warm
   ```
4. Cost note: idle-free billing — a mostly-sleeping per-project sprite costs ~storage. node_modules
   lives in the golden checkpoint; restores are ~ms (filesystem). No RAM-warm fork (fine here).

## B. E2B (alt Linux backend — parallel fork / agent templates)
1. `npm i -g e2b`; set `E2B_API_KEY`.
2. Build a template per lockfile hash that runs `npm ci`/`pip install` (and optionally installs Codex/
   Claude Code). Name it to match `golden-<type>-<hash>` (see `lib.sh:golden_name`) or adapt `e2b.sh`.
3. Use when you need to **fork one warm template into many parallel sandboxes** (50-wide test fan-out)
   or want E2B's prebuilt agent templates. Switch with `OFFLOAD_LINUX_BACKEND=e2b` or `--backend e2b`.

## C. Tart (macOS + Linux-on-Apple-Silicon backend)
**Key constraint:** macOS can only be built on Apple hardware, and Apple's license caps **2 macOS VMs
per host**. To keep YOUR Mac free, run Tart on a SEPARATE host and set `OFFLOAD_TART_HOST`.

Host options (pick one — all are "a found tool" per our research):
- **Spare Apple Silicon Mac** you own (a Mac mini dedicated as build box). Cheapest if you have one.
- **Orchard** (cirruslabs/orchard) across several Macs — REST scheduler; for a real farm.
- **Managed** (no hardware of your own): Cirrus Runners (managed Tart), MacStadium Orka, AWS EC2 Mac,
  Namespace/Depot macOS runners. Point `OFFLOAD_TART_HOST` / SSH at the managed host.

Build a golden macOS image once (on the host):
```bash
# on the Tart host
tart clone ghcr.io/cirruslabs/macos-sequoia-xcode:latest golden-macos-base
tart run golden-macos-base --no-graphics &
ip=$(tart ip golden-macos-base)
ssh admin@$ip 'brew install node python@3.12 && npm i -g pnpm'   # bake your toolchain + deps
tart stop golden-macos-base
# rename/keep as your golden; the skill clones it per job. Re-bake when Xcode/deps change.
```
Name the golden so `golden_name macos <hash>` matches, or hardcode the base in `tart.sh`.

**Pilot:**
```bash
cd ~/some-mac-project
offload -- swift build          # clones golden → boots → ssh build → returns exit code
```
For Linux-on-Mac (cheap, no 2-VM cap) use a Linux Tart image and `OFFLOAD_LINUX_BACKEND=tart`.

## D. Per-project rollout (the "all my projects" goal)
- Drop nothing in each repo — routing is automatic from manifest files.
- First `offload` run in a repo builds its golden (keyed to that repo's lockfile hash); subsequent
  runs are warm. Changing the lockfile transparently triggers a one-time rebuild.
- For agents: install the PATH shims (SKILL.md) once; every agent's `npm test`/`pytest` then offloads.

## What you still own (true on every backend)
- The golden bootstrap content (which toolchain/deps to bake).
- Artifact archival if you need build outputs back (tar in-sandbox → pull/push to R2/S3).
- Choosing the Mac host for macOS work.
