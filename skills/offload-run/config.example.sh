# config.example.sh — copy to ~/.config/offload-run/config.sh and edit.
# offload.sh sources this if present. All values have safe defaults; override what you use.

# Which backend handles each project class.
#   linux work (node/python/generic): sprites | e2b | tart   (tart = Linux VM on Apple Silicon)
#   macos work (xcode/swift/pods):     tart                  (only Apple hardware can build macOS)
export OFFLOAD_LINUX_BACKEND=sprites
export OFFLOAD_MACOS_BACKEND=tart

# Work directory created inside every remote env.
export OFFLOAD_WORKDIR=/work

# --- Sprites (Fly.io) ---  requires: sprite CLI + `sprite login`
export OFFLOAD_SPRITE_PREFIX=offload          # sprite named offload-node / offload-python
# export OFFLOAD_INSTALL_AGENTS=1             # bake Codex+Claude Code into golden (Pattern B)

# --- Tart (macOS / Linux on Apple Silicon) ---
# Leave OFFLOAD_TART_HOST empty to use a local `tart`; set it to run on a REMOTE Mac so YOUR
# machine stays free (a spare Apple Silicon Mac, an Orchard cluster node, or a managed host).
export OFFLOAD_TART_HOST=""                    # e.g. you@build-mac.local  (SSH to the host)
export OFFLOAD_TART_SSH_USER=admin            # SSH user INSIDE the Tart VM (macOS default: admin)

# --- E2B (alt Linux backend with warm-fork + agent templates) ---
# export E2B_API_KEY=...                       # needed only if OFFLOAD_LINUX_BACKEND=e2b
