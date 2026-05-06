# Port hygiene — kill our own only

Inspired by `vercel-labs/portless`'s philosophy: stable named URLs eliminate port juggling, but when you DO bind a port directly (`make local-lan`), be smart about what's already there.

## The rule

1. Inspect what's holding the port before clobbering.
2. If it's `node` / `next` / `next-server` / `turbopack` → it's our stale process; kill it.
3. If it's anything else (OrbStack, Postgres, Redis, browser tunnel, GitHub Actions runner) → refuse and tell the user.

## Implementation

```sh
_free-port:
	@pid=$$(lsof -ti :$(PORT) 2>/dev/null || true); \
	if [ -z "$$pid" ]; then exit 0; fi; \
	cmd=$$(ps -p $$pid -o comm= 2>/dev/null | tr -d ' \t'); \
	case "$$cmd" in \
	  *node|*node\ *|*next*|*turbopack*|next-server) \
	    printf "→ port $(PORT) busy with stale dev (pid $$pid, $$cmd) — reclaiming\n"; \
	    kill -9 $$pid 2>/dev/null || true; \
	    sleep 0.4 ;; \
	  *) \
	    next=$$(( $(PORT) + 10 )); \
	    printf "port $(PORT) held by $$cmd (pid $$pid). Won't clobber.\n"; \
	    printf "  • If you know it's safe:  kill -9 $$pid\n"; \
	    printf "  • Or pick another port:    make local-lan PORT=$$next\n"; \
	    exit 1 ;; \
	esac
```

## Why this matters

Without classification, `make local-lan` would silently kill OrbStack's helper, Postgres, or whatever is on the port. Beginner devs run `make local`, get inscrutable database errors 30 minutes later, blame the project.

## Banner conventions

Print every URL the dev server is reachable at — the user shouldn't `ifconfig`:

```sh
_print-local-lan-banner:
	@printf "PROJECT dev  direct $(HOST):$(PORT) (LAN)\n"
	@printf "  → http://localhost:$(PORT)\n"
	@ifconfig 2>/dev/null | awk '/inet / && $$2 != "127.0.0.1" {print $$2}' | head -4 \
	  | while read ip; do printf "  → http://$$ip:$(PORT)  (LAN)\n"; done
	@printf "  stop:  make stop      cache panic:  make clean\n"
```

This enumerates every IPv4 interface (LAN, tailnet, USB-C ethernet, virtual). The phone-on-Wi-Fi user picks the matching IP without thinking.

## Override pattern

Every fixed port must be overridable per-invocation:

```sh
make local-lan PORT=4000
```

Implementation: `PORT ?= 3456` in the Makefile (the `?=` makes it overridable from environment or command line).

## Multi-port targets

When the Makefile has multiple targets binding different ports (`PORT` for `local-lan`, `TUNNEL_PORT` for `tunnel`), each gets its own variable:

```makefile
PORT        ?= 3456
TUNNEL_PORT ?= 3001
```

Both can run simultaneously without collision (different ports, different upstream targets).

## "Stop" target convention

```makefile
stop:
	@pid=$$(lsof -ti :$(PORT) 2>/dev/null || true); \
	if [ -n "$$pid" ]; then kill -9 $$pid 2>/dev/null; printf "killed pid $$pid on :$(PORT)\n"; \
	else printf "nothing on :$(PORT)\n"; fi

clean: stop
	@rm -rf .next/cache && printf "wiped .next/cache\n"
```

`make clean` is the recovery-from-Turbopack-panic command. Mention it in the help banner — devs hit `Every task must have a task type` panics often enough that this is worth the muscle-memory.

## Choosing default ports

Avoid these on macOS dev machines:

| Port | Common squatter |
|---|---|
| 3000 | OrbStack helper, default for many tools |
| 5000 | macOS AirPlay Receiver |
| 5432 | Postgres (host or docker) |
| 6379 | Redis |
| 8080 | many alternative dev servers |
| 8000 | python -m http.server, default Django |

Pick a non-obvious 4-digit port (`3456`, `4321`, `5174`). Don't pick something cute that another dev already uses.
