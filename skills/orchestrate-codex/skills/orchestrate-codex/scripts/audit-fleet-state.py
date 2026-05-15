#!/usr/bin/env python3
"""DEPRECATED: forwards to audit.py state.

Removed in v3.0. Use:
    python3 audit.py state [--manifest <p>] [--workspace-root <d>] [--stale-minutes <N>] [--json]
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# Best-effort ledger warn
try:
    sys.path.insert(0, str(_HERE))
    from _lib import log_ledger_line
    log_ledger_line(level="WARN", msg="deprecated_script", script="audit-fleet-state.py",
                    reason="forwarding to audit.py state")
except Exception:
    pass

os.execvp(
    "python3",
    ["python3", str(_HERE / "audit.py"), "state"] + sys.argv[1:],
)
