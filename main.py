#!/usr/bin/env python3
"""
Interactive libaffinity.dll patcher.
Changes XOR AL, AL (return 0) -> MOV AL, 1 (return 1) at file offset 0x0043E451.
"""

import os
import sys

from core.admin import is_admin, run_as_admin
from core.ansi import color, COLOR_YELLOW
from core.ui import main

if __name__ == "__main__":
    if os.name == "nt" and not is_admin():
        if run_as_admin():
            sys.exit(0)
        print(color("  [!] Could not elevate privileges. Write errors are possible.", COLOR_YELLOW))
        print()

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n  [i] Exiting...")
        sys.exit(0)