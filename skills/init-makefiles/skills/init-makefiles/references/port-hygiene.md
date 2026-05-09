# Port hygiene — kill our own only, never blindly clobber

The inviolable rule: **never blindly kill a process on a port. Confirm it belongs to this project before reclaiming it. If foreign, refuse and suggest `+10`.** Every Makefile that opens a port uses the `_free-port-%` helper from this file. The cost of getting it wrong is a developer's OrbStack helper / Postgres / Redis dying mid-task and the project getting blamed.

## The `_free-port-%` recipe

```makefile
_free-port-%: # %=PORT — free a port if held by our own dev process; refuse otherwise
	@pid=$$(lsof -ti :$* 2>/dev/null || true); \
	if [ -z "$$pid" ]; then exit 0; fi; \
	for p in $$pid; do \
	  cmd=$$(ps -p $$p -o comm= 2>/dev/null | sed 's/^.*\///' | tr -d ' \t'); \
	  case "$$cmd" in \
	    node|next-server|turbo|turbopack|next|bun|deno) \
	      printf "$(Y)→ :$* held by stale dev (pid $$p, $$cmd) — reclaiming$(Z)\n"; \
	      kill -TERM $$p 2>/dev/null || true; \
	      sleep 0.5; \
	      if kill -0 $$p 2>/dev/null; then \
	        printf "$(D)  pid $$p still alive after SIGTERM — escalating to SIGKILL$(Z)\n"; \
	        kill -9 $$p 2>/dev/null || true; \
	      fi ;; \
	    *) \
	      next=$$(( $* + 10 )); \
	      printf "$(R):$* held by $$cmd (pid $$p). Won't clobber.$(Z)\n"; \
	      printf "$(D)  • If you know it's safe:  kill $$p$(Z)\n"; \
	      printf "$(D)  • Or pick another port:    make <target> PORT=$$next$(Z)\n"; \
	      exit 1 ;; \
	  esac; \
	done
```

Use as a prerequisite: `local: _free-port-$(PORT) _print-banner-local`. The `%` matches the port number, so `_free-port-3456` runs against port 3456.

### Why each piece is the way it is

| Piece | Reason |
|---|---|
| `lsof -ti :$*` | `-t` prints PIDs only (terse); `-i :PORT` filters by network port. `\|\| true` keeps the recipe alive when the port is unheld (no PIDs is not an error in this context). |
| `for p in $$pid` | `lsof` returns multiple PIDs when a process forked (Next.js dev workers are common). Iterate; never assume a single PID. |
| `ps -p $$p -o comm=` | `comm=` (with the trailing `=`) suppresses the header. Returns the command name only — no args, no pid. The trailing `=` is required (BSD/macOS quirk). |
| `sed 's/^.*\///'` | Strips any path prefix so `cmd` is just the binary name. macOS `ps` may return `/usr/local/bin/node` while Linux returns `node` — this normalises. |
| `tr -d ' \t'` | Strips leading/trailing whitespace `ps` sometimes adds. |
| `case` with **anchored exact-match names** | Matches `node` exactly, NOT `*node`. Globs would catch `node-exporter`, `node-red`, `gnome-shell` (any `*node`-like binary). The price of one regex laziness here is killing a Prometheus exporter or a desktop session. |
| `kill -TERM` first | Graceful. Lets the dev server flush logs, close sockets, drop child processes cleanly. Most Node frameworks register SIGTERM handlers; SIGKILL skips them. |
| `sleep 0.5` | 500ms is enough for a healthy `next-server` / `turbo` to exit. Tighter timing leaves tail-of-life processes; looser blocks the developer's terminal. |
| `kill -0 $$p` | Pure liveness check — `kill -0` sends signal 0, which only validates "can I signal this PID?" without delivering anything. Returns 0 if alive, non-zero if gone. |
| `kill -9` only after the liveness check | Reserved for the rare hung process. If `kill -TERM` worked, `-9` is never sent. |
| `next=$$(( $* + 10 ))` | Helpful refusal message: 3456 → 3466. `+10` (not `+1`) avoids landing on another popular port adjacent to the squatter. |
| `exit 1` on foreign holder | The recipe fails. The caller (`local`, `tunnel`) does NOT proceed past `_free-port-`. The user reads the refusal, picks a port, retries. |

### Allowlist — exactly the binaries we own

```
node              # plain node, plain next dev (legacy)
next-server       # Next.js production-style worker process
turbo             # Turborepo runner
turbopack         # Next.js's new bundler in worker mode
next              # Next.js CLI (rare; usually rebrands to next-server)
bun               # Bun runtime, includes `bun --hot`
deno              # Deno, includes `deno run`
```

If a project uses a framework whose process name isn't in this list (e.g. Vite spawns its own watcher under `node` so it's covered; Astro the same; Remix runs as `node`), the allowlist is correct. If a brand-new bundler emerges, add it explicitly here — never relax to a glob.

## Default-port squatters on macOS dev machines

Avoid these defaults. The `_free-port-` helper would refuse them anyway, but choosing a non-conflicting port up front saves a confusing first-run experience.

| Port | Typical squatter | Why it's there |
|---|---|---|
| 3000 | OrbStack helper, default for many frameworks | OrbStack's local Docker proxy uses 3000; Next.js's old default; Express templates default to 3000 |
| 5000 | macOS AirPlay Receiver | macOS Monterey+ binds AirPlay Receiver to 5000 by default — toggle off in System Settings if you want it back |
| 5432 | Postgres | Docker Postgres or `postgresql.app` |
| 6379 | Redis | Docker Redis or `redis-server` via Homebrew |
| 8080 | Misc dev servers | Common alt port; Tomcat, Jenkins, Confluence, lots of "default" Docker containers |
| 8000 | Python `http.server`, Django | `python -m http.server` default; `manage.py runserver` default |

**Recommended dev-default ports** (used by this skill's templates):

| Port | Use |
|---|---|
| 3456 | `make local` / `make local-lan` default |
| 4321 | secondary app in monorepo |
| 5174 | tertiary app, or `tunnel` upstream when 3456 is busy |

These are deliberately memorable but uncommon — no major tool defaults to them as of May 2026. Pick from this set when seeding new Makefiles; document the choice in `make help`.

## Banner conventions

Every recipe that opens a port prints a banner with all reachable URLs **before** the dev server starts. The user shouldn't have to run `ifconfig` or `tailscale status` to find out where the server is reachable.

### `_print-banner-local` — localhost only

```makefile
_print-banner-local:
	@printf "\n$(B)$(G)$(PROJECT) dev$(Z)  $(D)localhost only$(Z)\n"
	@printf "  $(C)→$(Z) http://localhost:$(PORT)\n"
	@printf "  $(D)stop:  make stop      cache panic:  make clean$(Z)\n\n"
```

### `_print-banner-lan` — LAN access

```makefile
_print-banner-lan:
	@printf "\n$(B)$(G)$(PROJECT) dev$(Z)  $(D)direct $(HOST):$(PORT) (LAN)$(Z)\n"
	@printf "  $(C)→$(Z) http://localhost:$(PORT)\n"
	@ifconfig 2>/dev/null | awk '/inet / && $$2 != "127.0.0.1" {print $$2}' | head -4 \
	  | while read ip; do printf "  $(C)→$(Z) http://$$ip:$(PORT)  $(D)(LAN)$(Z)\n"; done
	@printf "  $(D)stop:  make stop      cache panic:  make clean$(Z)\n\n"
```

The `ifconfig | awk` enumerator returns every IPv4 interface that isn't loopback — LAN, tailnet, USB-C ethernet, virtual interfaces. `head -4` caps the printout (a Mac with VPN + tailnet + USB-C + Wi-Fi can have eight addresses). The phone-on-Wi-Fi user picks the matching IP without thinking; the tailnet-only user sees their `100.x.x.x` address.

### `_print-banner-tunnel` — Tailscale Serve

```makefile
_print-banner-tunnel:
	@scheme=$$([ "$(TUNNEL_TLS)" = "1" ] && printf https || printf http); \
	node=$$(tailscale status --json 2>/dev/null \
	         | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Self']['DNSName'].rstrip('.'))" 2>/dev/null); \
	short=$${node%%.*}; \
	printf "\n$(B)$(G)$(PROJECT) dev$(Z)  $(D)Tailscale Serve · tailnet only$(Z)\n"; \
	printf "  $(C)→$(Z) $(B)$$scheme://$$node$(Z)\n"; \
	printf "  $(C)→$(Z) $$scheme://$$short  $(D)(short MagicDNS)$(Z)\n"; \
	printf "  $(C)→$(Z) http://localhost:$(TUNNEL_PORT)\n"; \
	printf "  $(D)stop:  make tunnel-stop      Funnel is OFF      try TUNNEL_TLS=1 for HTTPS$(Z)\n\n"
```

The banner makes the trust model explicit: "tailnet only", "Funnel is OFF". Users who want public exposure are routed to `make funnel` — which has its own gate.

## `stop` recipe — kill our own on `$(PORT)`

```makefile
stop: ## kill our own dev process on $(PORT)
	@pid=$$(lsof -ti :$(PORT) 2>/dev/null || true); \
	if [ -z "$$pid" ]; then printf "$(D)nothing on :$(PORT)$(Z)\n"; exit 0; fi; \
	for p in $$pid; do \
	  cmd=$$(ps -p $$p -o comm= 2>/dev/null | sed 's/^.*\///' | tr -d ' \t'); \
	  case "$$cmd" in \
	    node|next-server|turbo|turbopack|next|bun|deno) \
	      kill -TERM $$p 2>/dev/null || true; \
	      sleep 0.5; \
	      if kill -0 $$p 2>/dev/null; then kill -9 $$p 2>/dev/null || true; fi; \
	      printf "$(Y)stopped pid $$p ($$cmd) on :$(PORT)$(Z)\n" ;; \
	    *) \
	      printf "$(R):$(PORT) held by $$cmd (pid $$p) — not ours, leaving alone$(Z)\n" ;; \
	  esac; \
	done
```

The killed PID is printed for forensic value — if a developer's dev server crashed weirdly, having the PID in the terminal lets them grep their system log. The same allowlist applies as in `_free-port-%`: foreign processes are reported, never killed.

## macOS `lsof` quirks

- `lsof -ti :PORT` may return **multiple PIDs** when the held process has forked workers. Always iterate (`for p in $$pid`); never assume a single PID. The `_free-port-%` and `stop` recipes above do this correctly.
- `lsof` on macOS Sonoma 14+ requires no special permission for ports owned by the current user. Cross-user kills require sudo (out of scope — refuse instead).
- `ps -p $$p -o comm=` is the portable form. The trailing `=` suppresses the header on both BSD (macOS) and GNU (Linux) `ps`. Without it, the first line of output is the literal `COMMAND` and the matching breaks.
- On macOS, `comm` is truncated to 16 characters in some `ps` builds. The names in our allowlist (`node`, `next-server`, `turbo`, `turbopack`, `next`, `bun`, `deno`) all fit comfortably.

## Ports the user shouldn't pick

| Range | Why |
|---|---|
| **0–1023** | Privileged ports. Binding requires `sudo` on macOS / Linux. Generated Makefiles assume non-privileged dev — refuse to use these as defaults. The exception is `make funnel TUNNEL_PORT=443` (gated, opt-in, public). |
| **5353** | mDNS / Bonjour broadcasts. Binding here breaks discovery for the whole machine. |
| **3306** | MySQL default. Even if no MySQL is running, devs muscle-memory `mysql -P 3306` and confusion follows. |
| **27017** | MongoDB default. Same muscle-memory argument. |
| **49152–65535** | OS ephemeral range — your kernel hands these out for outgoing connections. Binding here works but risks a TIME_WAIT collision under load. |
| **0** | Make Make pick a random port at bind time? Not portable across frameworks (Next.js refuses; Vite accepts). Skip. |

When in doubt, pick from the recommended dev-default list (3456 / 4321 / 5174). They are uncommon but memorable.

## Override pattern

Every fixed port must be overridable per-invocation:

```bash
make local PORT=4000
make tunnel TUNNEL_PORT=4321
```

Implementation in the Makefile: `PORT ?= 3456` and `TUNNEL_PORT ?= 3457`. The `?=` makes each one overridable from environment or command line. The default must be one that works without any user intervention — the agent never generates a Makefile where a missing env var causes a hard failure on first run.

## Multi-port targets

When the Makefile has multiple targets binding different ports (`PORT` for `local-lan`, `TUNNEL_PORT` for `tunnel`), each gets its own variable:

```makefile
PORT        ?= 3456
TUNNEL_PORT ?= 3457
```

Both can run simultaneously without collision (different ports, different upstream targets, different `_free-port-%` invocations: `_free-port-3456` and `_free-port-3457`).

## Quick checklist before declaring port hygiene correct

- [ ] `_free-port-%` uses **anchored exact-match** in the case statement (`node`, not `*node`)
- [ ] `_free-port-%` sends **SIGTERM first**, sleeps 500ms, escalates to SIGKILL only on liveness check
- [ ] `_free-port-%` iterates over `$$pid` (handles forked workers)
- [ ] `lsof` invocation has `\|\| true` so unheld ports are non-fatal
- [ ] `ps -p $$p -o comm=` (with trailing `=`) is used, not `ps aux | grep`
- [ ] Foreign holder → `exit 1` with a `+10` suggestion
- [ ] `stop` recipe uses the same allowlist as `_free-port-%`
- [ ] Banner enumerator uses `ifconfig | awk` (or equivalent) to list all reachable interfaces
- [ ] Default port chosen from {3456, 4321, 5174} or documented why otherwise
- [ ] No privileged port (≤1023) used unless the target is `funnel` and `PUBLIC_FUNNEL=1` was acked
