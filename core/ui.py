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
    COLOR_CYAN,
    COLOR_BOLD,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
)
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


def print_banner():
    """
    Print the application brand banner and links.
    """
    print()
    print(color("  ==================================================================", COLOR_CYAN, COLOR_BOLD))
    print(
        color("  ", COLOR_CYAN, COLOR_BOLD)
        + color("Affinity DLL Patcher", COLOR_BOLD)
        + color(" v", COLOR_CYAN)
        + color(VERSION, COLOR_GREEN, COLOR_BOLD)
    )
    print(color("  Patch libaffinity.dll or install the partial Russian localization.", COLOR_CYAN))
    print(
        color("  Telegram Channel: ", COLOR_YELLOW)
        + color(TELEGRAM_URL, COLOR_GREEN)
    )
    print(
        color("  YouTube Channel:  ", COLOR_YELLOW)
        + color(YOUTUBE_URL, COLOR_GREEN)
    )
    print(color("  ==================================================================", COLOR_CYAN, COLOR_BOLD))
    print()


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
    raw_path = input("  Enter a DLL path or a folder path: ").strip()
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
            print(color("  1. Patch default libaffinity.dll", COLOR_GREEN))
        elif default_location_available():
            print(color("  1. Patch default libaffinity.dll (not found)", COLOR_YELLOW))
        else:
            print(color("  1. Patch default libaffinity.dll (folder not found)", COLOR_YELLOW))

        print(color("  2. Patch a custom file or folder", COLOR_CYAN))
        russian_locale_status = get_russian_locale_status()
        if russian_locale_status == "ready":
            print(color("  3. Install Russian localization (partial translation)", COLOR_CYAN))
        elif russian_locale_status == "already_installed":
            print(color("  3. Install Russian localization (already installed)", COLOR_YELLOW))
        elif russian_locale_status == "default_dir_missing":
            print(color("  3. Install Russian localization (Affinity folder not found)", COLOR_YELLOW))
        elif russian_locale_status == "target_blocked":
            print(color("  3. Install Russian localization (target path is blocked)", COLOR_YELLOW))
        elif russian_locale_status == "source_empty":
            print(color("  3. Install Russian localization (bundled files are empty)", COLOR_YELLOW))
        else:
            print(color("  3. Install Russian localization (files not found)", COLOR_YELLOW))

        print(color("  4. Open GitHub repository", COLOR_YELLOW))
        print(color("  0. Exit", COLOR_RED))

        choice = input(color("\n  > ", COLOR_CYAN, COLOR_BOLD)).strip()
        print()

        if choice in ("0", ""):
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
