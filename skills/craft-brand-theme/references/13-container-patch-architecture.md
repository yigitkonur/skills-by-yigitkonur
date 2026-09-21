# Container Patch Architecture: Delivering Themes to Production

This reference documents the end-to-end architecture for deploying brand themes into containerized applications running on Docker/Dokploy without rebuilding images.

---

## 1. The Core Challenge

Pre-built container images (from Docker Hub, GHCR, or private registries) ship with compiled frontend assets. You cannot modify source code and rebuild — the image is immutable. Instead, you must:

1. Mount patch scripts and assets into the container at runtime.
2. Execute patches on container startup, before the application serves requests.
3. Ensure patches survive container restarts but are cleanly re-applied on redeployment.

---

## 2. Volume Mount Architecture

### Docker Compose Configuration

```yaml
services:
  app:
    image: ghcr.io/org/platform:latest
    volumes:
      - ./patches:/app/data/patches:ro          # Patch scripts + font binaries
      - ./entrypoint-wrapper.sh:/entrypoint.sh  # Optional: custom entrypoint
    entrypoint: ["/entrypoint.sh"]
```

### Directory Structure on Host

```
/root/dev/project/
├── patches/
│   ├── 01_first_patch.py
│   ├── 05_zeo_custom_theme.py    # Theme engine
│   └── fonts/
│       ├── AkagiPro-Book.woff2
│       ├── AkagiPro-SemiBold.woff2
│       ├── AkagiPro-Bold.woff2
│       ├── Gilroy-Regular.woff2
│       ├── Gilroy-SemiBold.woff2
│       ├── Gilroy-Bold.woff2
│       └── Gilroy-ExtraBold.woff2
└── patch-orchestrator.py          # Runs all patches in order
```

### Inside the Container

```
/app/data/patches/          ← Read-only bind mount from host
/app/frontend/.next/        ← Compiled Next.js assets (writable)
/app/frontend/public/       ← Static files served by Next.js (writable)
/app/backend/dist/          ← Compiled backend modules (writable)
```

The `patches/` directory is mounted **read-only** (`:ro`) — patches read their source assets (fonts, SVGs) from here but write modifications directly into the application's writable filesystem.

---

## 3. Patch Orchestrator

The orchestrator discovers and runs all patch scripts in filename order:

```python
#!/usr/bin/env python3
"""Patch Orchestrator — runs all patches in /app/data/patches/ sequentially."""

import importlib.util
import os
import sys
import glob

def run_patches():
    patch_dir = "/app/data/patches"
    if not os.path.exists(patch_dir):
        print("[patch-orchestrator] No patches directory found.")
        return

    scripts = sorted(glob.glob(os.path.join(patch_dir, "*.py")))
    for script_path in scripts:
        name = os.path.basename(script_path)
        print(f"[patch-orchestrator] Running {name}...")
        try:
            spec = importlib.util.spec_from_file_location(name, script_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "apply_patch"):
                mod.apply_patch()
        except Exception as e:
            print(f"[patch-orchestrator] Error in {name}: {e}")
            # Continue to next patch — never block container boot

if __name__ == "__main__":
    run_patches()
```

### Execution Order Contract

Patches are sorted alphabetically by filename. Use numeric prefixes to enforce ordering:

```
01_base_config.py         # Runs first
05_zeo_custom_theme.py    # Runs after base config
10_telemetry_disable.py   # Runs last
```

---

## 4. Safe Instance Guard

In multi-tenant deployments (e.g., separate Dokploy stacks for different clients), a theme patch must **only execute on the correct instance**:

```python
def is_target_instance():
    """Prevents accidental theme application to wrong tenant."""
    frontend_url = os.environ.get("APP_FRONTEND_URL", "")
    api_url = os.environ.get("APP_API_BASE_URL", "")
    
    if "mybrand.com" in frontend_url or "mybrand.com" in api_url:
        return True
    
    print("[patch] Guard: Not target instance. Skipping brand-specific patches.")
    return False
```

Place this check at the top of `apply_patch()`. If the guard fails, return `True` (success) to indicate the patch was intentionally skipped, not broken.

---

## 5. Execution Order Dependency Graph

Within a single theme patch, sub-steps have dependencies:

```
apply_patch()
  │
  ├── 1. Instance Guard          [Abort if wrong tenant]
  │
  ├── 2. Backend Schema Patch    [No dependencies]
  │
  ├── 3. Frontend Array Patch    [No dependencies]
  │
  ├── 4. Registry Metadata       [No dependencies]
  │
  ├── 5. Font Deployment         [No dependencies — copies files]
  │
  ├── 6. SSR Layout Injection    [Depends on: CSS content finalized]
  │
  ├── 7. Client Hook Patch       [Depends on: CSS content finalized]
  │
  ├── 8. Public CSS Fallback     [No dependencies]
  │
  ├── 9. Database Branding       [No dependencies]
  │
  └── 10. Process Restart        [Depends on: steps 5, 6 completed]
         ↑ Only if SSR or fonts changed
```

---

## 6. Idempotency Guard Pattern

Every patch function must be safe to run unlimited times:

```python
def patch_something(filepath):
    content = open(filepath, "r").read()
    
    # Guard: check for our marker
    MARKER = '"my-custom-id"'
    if MARKER in content:
        print(f"Already patched: {filepath}")
        return True  # Idempotent success
    
    # Find target and replace
    if TARGET in content:
        content = content.replace(TARGET, REPLACEMENT, 1)
        open(filepath, "w").write(content)
        return True
    
    print(f"Target anchor not found in {filepath}")
    return False
```

### Why Idempotency Matters

- Containers may restart unexpectedly (OOM kill, node drain, Dokploy redeploy).
- The patch orchestrator runs on every container boot.
- Without idempotency, each restart would duplicate injected code, eventually corrupting the compiled bundles.

---

## 7. Granular Error Isolation

Each patch step must be wrapped in its own `try/except`:

```python
def apply_patch():
    if not is_target_instance():
        return True

    try:
        ok_backend = patch_backend()
    except Exception as e:
        print(f"Backend patch failed: {e}")
        ok_backend = False

    try:
        ok_fonts = deploy_fonts()
    except Exception as e:
        print(f"Font deployment failed: {e}")
        ok_fonts = False

    # ... more steps ...

    # Container must ALWAYS boot, even if patches fail
    return True
```

**Critical rule**: A patch failure must **never prevent the container from starting**. The application should boot with default styling rather than crash entirely.

---

## 8. Process Restart (Hot V8 Memory Reload)

After modifying compiled SSR chunks or deploying static assets, the running Node.js process has stale files cached in V8 memory.

```python
def restart_server():
    """Kill next-server; supervisord/container init respawns it automatically."""
    import subprocess, os, time
    
    p = subprocess.Popen(["pgrep", "-f", "next-server"], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    pids = [l.strip() for l in out.decode().splitlines() if l.strip()]
    
    for pid in pids:
        try:
            os.kill(int(pid), 9)  # SIGKILL
        except ProcessLookupError:
            pass
    
    time.sleep(2)  # Wait for supervisor to respawn
```

### Conditional Restart

Only restart if files that affect runtime behavior changed:

```python
if ok_ssr or ok_fonts:
    restart_server()
# Database-only or registry-only changes don't need restart
```

### Restart Timing

- **~2 seconds**: Supervisord detects the dead process and spawns a new one.
- **~3 seconds**: Next.js standalone server completes startup and begins serving.
- **Total downtime**: ~5 seconds of 502 errors during the switchover.

---

## 9. Dokploy-Specific Notes

When deploying on Dokploy with `sourceType: raw`:

- The Docker Compose YAML is stored in Dokploy's PostgreSQL database, not on disk.
- Volume paths must be absolute on the host (e.g., `/root/dev/project/patches`).
- The `patches/` directory must exist on the host before the container starts.
- Use `restart: unless-stopped` to ensure patches re-apply after host reboots.
- Dokploy redeploys pull fresh images but preserve volume mounts — patches are durable.
