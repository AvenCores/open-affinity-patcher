"""
Administrative check and privilege elevation helpers.
"""

import ctypes
import os
import sys


def is_admin():
    """
    Check if the current process is running with administrative rights.
    """
    try:
        if os.name == "posix":
            return os.getuid() == 0
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin():
    """
    Relaunch the current script/executable with administrative privileges.
    """
    if os.name != "nt" or is_admin():
        return True

    if getattr(sys, "frozen", False):
        executable = sys.executable
        args_str = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    else:
        executable = sys.executable
        args = [sys.argv[0]] + sys.argv[1:]
        args_str = " ".join(f'"{arg}"' for arg in args)

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            args_str,
            None,
            1,
        )
        return result > 32
    except Exception:
        return False
