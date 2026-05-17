#!/usr/bin/env python3
"""DEPRECATED: forwards to audit.py worktrees.

Removed in v3.0. Use:
    python3 audit.py worktrees [--cwd <d>] [--json]
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

try:
    sys.path.insert(0, str(_HERE))
    from _lib import log_ledger_line
    log_ledger_line(level="WARN", msg="deprecated_script", script="list-worktrees.py",
                    reason="forwarding to audit.py worktrees")
except Exception:
    pass

os.execvp(
    "python3",
    ["python3", str(_HERE / "audit.py"), "worktrees"] + sys.argv[1:],
)
