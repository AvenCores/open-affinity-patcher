"""
Console ANSI styling, color definition, and setup utilities.
"""

import ctypes
import os

CSI = "\x1b["
COLOR_RESET = CSI + "0m"
COLOR_CYAN = CSI + "36m"
COLOR_GREEN = CSI + "32m"
COLOR_YELLOW = CSI + "33m"
COLOR_RED = CSI + "31m"
COLOR_BOLD = CSI + "1m"
USE_COLOR = False


def enable_ansi():
    """
    Enable ANSI escape sequences in Windows console if applicable.
    """
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        new_mode = mode.value | 0x0004
        if new_mode == mode.value:
            return True
        return bool(kernel32.SetConsoleMode(handle, new_mode))
    except Exception:
        return False


def setup_console():
    """
    Configure active code page and color capabilities of the console.
    """
    global USE_COLOR
    if os.name == "nt":
        os.system("chcp 65001 >nul")
    USE_COLOR = enable_ansi()


def color(text, *styles):
    """
    Wrap text in specified ANSI styles if coloring is supported.
    """
    if not USE_COLOR or not styles:
        return text
    return "".join(styles) + text + COLOR_RESET


def clear_screen():
    """
    Clear terminal console screen.
    """
    os.system("cls" if os.name == "nt" else "clear")
