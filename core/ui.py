"""
User interface and console flow orchestration for Affinity Patcher.
"""

import os
import sys
import webbrowser

from core.config import (
    VERSION,
    DEFAULT_DIR,
    TELEGRAM_URL,
    YOUTUBE_URL,
    GITHUB_URL,
)
from core.ansi import (
    setup_console,
    color,
    clear_screen,
    _visible_len,
    COLOR_CYAN,
    COLOR_BOLD,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_DIM,
    COLOR_GRAY,
    COLOR_WHITE,
)

# Outer width of the banner == right edge of the menu dividers (column 49).
MENU_WIDTH = 49
_BANNER_INNER_WIDTH = 47   # between the ║ borders
_LABEL_COL = 12            # column width for banner labels (Telegram/YouTube/...)
from core.paths import (
    get_default_target_path,
    default_target_exists,
    default_location_available,
    resolve_target_path,
)
from core.version import get_affinity_version_info
from core.locale import get_russian_locale_status, install_russian_locale
from core.patcher import (
    get_patch_status,
    format_patch_status_text,
    patch_dll,
)


def _banner_border(left, fill, right):
    """
    Print a full-width banner border line: ╔═══╗ / ╟───╢ / ╚═══╝.
    Indented 2 spaces so the right edge aligns with the menu dividers/rows.
    """
    print("  " + color(left + fill * _BANNER_INNER_WIDTH + right, COLOR_CYAN, COLOR_BOLD))


def _banner_row(left, right=""):
    """
    Print a banner content line. `left` is flush-left (2-space indent after ║),
    `right` is flush-right; the gap is computed via _visible_len so the right ║
    always lands in the same column regardless of text length.
    """
    inner_left = "  " + left
    gap = _BANNER_INNER_WIDTH - _visible_len(inner_left) - _visible_len(right)
    bar = color("║", COLOR_CYAN, COLOR_BOLD)
    print("  " + bar + inner_left + " " * (gap if gap > 0 else 1) + right + bar)


def print_banner():
    """
    Print the application brand banner and links.
    """
    version_badge = color(f"v{VERSION}", COLOR_GREEN, COLOR_BOLD)
    print()
    _banner_border("╔", "═", "╗")
    _banner_row(color("Affinity DLL Patcher", COLOR_BOLD), version_badge)
    _banner_row(color("Patch libaffinity.dll or install RU locale.", COLOR_CYAN))
    features = (
        color("Hot-patch", COLOR_GREEN) + color(" • ", COLOR_CYAN)
        + color(".bak backup", COLOR_GREEN) + color(" • ", COLOR_CYAN)
        + color("RU locale", COLOR_GREEN)
    )
    _banner_row(features)
    _banner_border("╟", "─", "╢")
    _banner_row(color("Telegram".ljust(_LABEL_COL), COLOR_YELLOW), color(TELEGRAM_URL, COLOR_DIM))
    _banner_row(color("YouTube".ljust(_LABEL_COL), COLOR_YELLOW), color(YOUTUBE_URL, COLOR_DIM))
    _banner_border("╚", "═", "╝")
    print()


def print_menu_section(title):
    """
    Print a menu section header: "─ TITLE ────..." of total visible width MENU_WIDTH.
    Indented 2 spaces so its right edge aligns with the rows/dividers/banner.
    """
    label = color(f" {title} ", COLOR_CYAN, COLOR_BOLD)
    dashes = "─" * (MENU_WIDTH - _visible_len(label) - 1)
    print("  " + color("─", COLOR_GRAY) + label + color(dashes, COLOR_GRAY))


def print_menu_row(number, label, hint="", accent=COLOR_GREEN):
    """
    Print a menu row: "  [N]  <label>            <hint>".
    Brackets are gray, the number uses accent+bold, the label is white,
    and the optional hint is dim and right-aligned.
    """
    number_str = str(number)
    prefix = (
        "  "
        + color("[", COLOR_GRAY)
        + color(number_str, accent, COLOR_BOLD)
        + color("]", COLOR_GRAY)
        + "  "
        + color(label, COLOR_WHITE)
    )
    if not hint:
        print(prefix)
        return
    hint_styled = color(hint, COLOR_DIM)
    gap = max(2, MENU_WIDTH + 2 - _visible_len(prefix) - _visible_len(hint_styled))
    print(prefix + " " * gap + hint_styled)


def print_menu_divider():
    """
    Print a full-width thin divider line (indented by 2 spaces).
    """
    print("  " + color("─" * MENU_WIDTH, COLOR_GRAY))


def print_menu_footer(note):
    """
    Print a divider followed by a dim footer note (e.g. a tip).
    """
    print_menu_divider()
    print("  " + color(note, COLOR_DIM))


def get_launch_example():
    """
    Formulate run argument command-line suggestion based on runtime format.
    """
    script_name = os.path.basename(sys.argv[0]) or "main.py"
    if getattr(sys, "frozen", False):
        return f'{script_name} "C:\\path\\to\\libaffinity.dll"'
    return f'python {script_name} "C:\\path\\to\\libaffinity.dll"'


def print_default_target_info():
    """
    Display location, status, and patch state of the default target file.
    """
    default_target = get_default_target_path()
    version_info = get_affinity_version_info()

    print(f"  [*] Default folder: {color(DEFAULT_DIR, COLOR_CYAN)}")
    print(f"  [*] Default target: {color(default_target, COLOR_CYAN)}")

    if default_target_exists():
        status = color("found", COLOR_GREEN)
    elif default_location_available():
        status = color("folder found, but libaffinity.dll is missing", COLOR_YELLOW)
    else:
        status = color("folder not found", COLOR_RED)

    print(f"  [*] Status: {status}")
    if default_target_exists():
        patch_status, current_bytes = get_patch_status(default_target)
        print(f"  [*] Patch:  {format_patch_status_text(patch_status, current_bytes)}")
    print_affinity_version_info(version_info)
    print(f"  [i] Tip: you can also launch this program with a target path:")
    print(f"      {color(get_launch_example(), COLOR_YELLOW)}")
    print("  [i] You can pass either the DLL itself or a folder containing it.")
    print("  [i] Files inside Program Files may require administrator rights.")
    print()


def print_target_info(filepath):
    """
    Display location, size, and patch status of a specific target file path.
    """
    print(f"  [*] Target: {color(filepath, COLOR_CYAN)}")
    if os.path.exists(filepath):
        print(f"  [*] Size:   {color(f'{os.path.getsize(filepath):,} bytes', COLOR_GREEN)}")
        patch_status, current_bytes = get_patch_status(filepath)
        print(f"  [*] Patch:  {format_patch_status_text(patch_status, current_bytes)}")
    backup_path = filepath + ".bak"
    if os.path.exists(backup_path):
        print(f"  [*] Backup: {color(backup_path, COLOR_GREEN)}")
    else:
        print(f"  [*] Backup: {color('not created yet', COLOR_YELLOW)}")
    print()


def pause():
    """
    Pause standard output prompt before returning to main loop screen.
    """
    input("  Press Enter to return to menu...")


def print_affinity_version_info(version_info=None):
    """
    Display details on the installed Affinity application version and warning if mismatched.
    """
    if version_info is None:
        version_info = get_affinity_version_info()

    installed_version = version_info.get("installed_version")
    status = version_info.get("status")
    warning = version_info.get("warning", "")

    if status == "supported":
        version_text = color(installed_version, COLOR_GREEN)
    elif installed_version:
        version_text = color(installed_version, COLOR_YELLOW)
    else:
        version_text = color("not detected", COLOR_YELLOW)

    print(f"  [*] Version: {version_text}")
    print()

    if warning:
        warning_color = COLOR_RED if status == "below_minimum" else COLOR_YELLOW
        print(color(f"  [!] Warning: {warning}", warning_color))


def prompt_for_custom_target():
    """
    Ask user to input custom DLL or directory paths.
    """
    print_menu_section("SELECT TARGET")
    print("  " + color("Enter a DLL path or a folder path below.", COLOR_DIM))
    raw_path = input(color("\n  Path > ", COLOR_CYAN, COLOR_BOLD)).strip()
    if not raw_path:
        print(color("  [i] No path entered.", COLOR_YELLOW))
        return ""
    return resolve_target_path(raw_path)


def redraw_main_screen():
    """
    Clear terminal view, draw branding logo, and list default folder metrics.
    """
    clear_screen()
    print_banner()
    print_default_target_info()


def run_menu():
    """
    Main interactive menu selection loop.
    """
    while True:
        redraw_main_screen()

        if default_target_exists():
            patch1_hint = "found"
        elif default_location_available():
            patch1_hint = "dll not found"
        else:
            patch1_hint = "folder not found"

        russian_locale_status = get_russian_locale_status()
        locale_hints = {
            "ready": "ready",
            "already_installed": "already installed",
            "default_dir_missing": "folder not found",
            "target_blocked": "target blocked",
            "source_empty": "source empty",
            "source_missing": "files not found",
        }
        locale_hint = locale_hints.get(russian_locale_status, "unavailable")

        print_menu_section("PATCH")
        print_menu_row(1, "Patch default libaffinity.dll", patch1_hint, accent=COLOR_GREEN)
        print_menu_row(2, "Patch a custom file or folder", "manual", accent=COLOR_GREEN)

        print_menu_section("TOOLS")
        print_menu_row(3, "Install Russian localization", locale_hint, accent=COLOR_CYAN)
        print_menu_row(4, "Open GitHub repository", "link", accent=COLOR_CYAN)

        print_menu_divider()
        print_menu_row(0, "Exit", "quit", accent=COLOR_RED)
        print_menu_footer("Tip: launch with a target path argument to skip the menu.")

        choice = input(color("\n  Select option > ", COLOR_CYAN, COLOR_BOLD)).strip()
        print()

        if not choice:
            # Empty input: redraw the menu instead of exiting.
            continue

        if choice == "0":
            return 0

        clear_screen()
        print_banner()

        if choice == "1":
            if not default_target_exists():
                print(color("  [!] Default target is unavailable.", COLOR_RED))
            else:
                patch_dll(get_default_target_path())
            print()
            pause()
            continue

        if choice == "2":
            target_path = prompt_for_custom_target()
            print()
            if target_path:
                patch_dll(target_path)
            print()
            pause()
            continue

        if choice == "3":
            install_russian_locale()
            print()
            pause()
            continue

        if choice == "4":
            confirm = input(
                color("  Are you sure you want to open the GitHub repository? (y/n): ", COLOR_YELLOW)
            ).strip().lower()
            if confirm in ("y", "yes"):
                webbrowser.open(GITHUB_URL)
                print(f"  [+] Opening: {color(GITHUB_URL, COLOR_CYAN)}")
            else:
                print(color("  [i] Cancelled.", COLOR_YELLOW))
            print()
            pause()
            continue

        print(color("  [!] Invalid choice.", COLOR_RED))
        print()
        pause()


def run_cli_mode(target_arg):
    """
    Console single argument runner (direct DLL path).
    """
    clear_screen()
    print_banner()
    target_path = resolve_target_path(target_arg)
    return 0 if patch_dll(target_path) else 1


def main():
    """
    Main orchestrator booting system CLI or interactive terminal menu.
    """
    setup_console()

    if len(sys.argv) > 1:
        target_arg = " ".join(sys.argv[1:])
        return run_cli_mode(target_arg)

    return run_menu()
