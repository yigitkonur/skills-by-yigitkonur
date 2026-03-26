#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Example Python Command
# @raycast.mode fullOutput
# @raycast.packageName Examples

import sys


def arg(index: int, default: str = "") -> str:
    return sys.argv[index] if len(sys.argv) > index else default


value = arg(1, "world")
print(f"Hello, {value}")
