#!/usr/bin/env python3
"""
Interactive libaffinity.dll patcher.
Changes XOR AL, AL (return 0) -> MOV AL, 1 (return 1) at file offset 0x0043E451.
"""

import ctypes
import os
import shutil
import sys
import webbrowser

VERSION = "1.0.1"
DEFAULT_DIR = r"C:\Program Files\Affinity\Affinity"
DEFAULT_DLL_NAME = "libaffinity.dll"
RUSSIAN_LOCALE_DIR_NAME = "ru"
PATCH_OFFSET = 0x0043E451
ORIGINAL_BYTES = b"\x32\xC0"
PATCHED_BYTES = b"\xB0\x01"
AFFINITY_REGISTRY_SUBKEY = (
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    r"\{D5B4183A-DE48-405A-A106-D3E48EBFE23F}"
)
SUPPORTED_AFFINITY_VERSION = "3.2.0.4351"
TELEGRAM_URL = "t.me/avencoresyt"
YOUTUBE_URL = "youtube.com/@avencores"
GITHUB_URL = "https://github.com/AvenCores/open-affinity-patcher"

CSI = "\x1b["
COLOR_RESET = CSI + "0m"
COLOR_CYAN = CSI + "36m"
COLOR_GREEN = CSI + "32m"
COLOR_YELLOW = CSI + "33m"
COLOR_RED = CSI + "31m"
COLOR_BOLD = CSI + "1m"
USE_COLOR = False


def enable_ansi():
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
    global USE_COLOR
    if os.name == "nt":
        os.system("chcp 65001 >nul")
    USE_COLOR = enable_ansi()


def color(text, *styles):
    if not USE_COLOR or not styles:
        return text
    return "".join(styles) + text + COLOR_RESET


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print()
    print(color("  ============================================================", COLOR_CYAN, COLOR_BOLD))
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
    print(color("  ============================================================", COLOR_CYAN, COLOR_BOLD))
    print()


def is_admin():
    try:
        if os.name == "posix":
            return os.getuid() == 0
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin():
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


def get_default_target_path():
    return os.path.join(DEFAULT_DIR, DEFAULT_DLL_NAME)


def get_app_base_dirs():
    base_dirs = []
    if getattr(sys, "frozen", False):
        base_dirs.extend(
            [
                getattr(sys, "_MEIPASS", ""),
                os.path.dirname(sys.executable),
            ]
        )
    else:
        base_dirs.append(os.path.dirname(os.path.abspath(__file__)))

    unique_dirs = []
    for base_dir in base_dirs:
        if base_dir and base_dir not in unique_dirs:
            unique_dirs.append(base_dir)
    return unique_dirs


def get_russian_locale_source_dir():
    for base_dir in get_app_base_dirs():
        candidate = os.path.join(base_dir, RUSSIAN_LOCALE_DIR_NAME)
        if os.path.isdir(candidate):
            return candidate
    return os.path.join(get_app_base_dirs()[0], RUSSIAN_LOCALE_DIR_NAME)


def get_russian_locale_target_dir():
    return os.path.join(DEFAULT_DIR, RUSSIAN_LOCALE_DIR_NAME)


def clean_path(raw_path):
    return raw_path.strip().strip('"').strip("'")


def resolve_target_path(raw_path):
    if not raw_path:
        return ""

    cleaned = clean_path(raw_path)
    if not cleaned:
        return ""

    expanded = os.path.expandvars(os.path.expanduser(cleaned))
    resolved = os.path.abspath(expanded)

    if os.path.isdir(resolved):
        return os.path.join(resolved, DEFAULT_DLL_NAME)

    return resolved


def default_location_available():
    return os.path.isdir(DEFAULT_DIR)


def default_target_exists():
    return os.path.isfile(get_default_target_path())


def directory_contains_files(dirpath):
    if not os.path.isdir(dirpath):
        return False

    for _, _, filenames in os.walk(dirpath):
        if filenames:
            return True
    return False


def get_russian_locale_status():
    source_dir = get_russian_locale_source_dir()
    target_dir = get_russian_locale_target_dir()

    if not default_location_available():
        return "default_dir_missing"
    if not os.path.isdir(source_dir):
        return "source_missing"
    if not directory_contains_files(source_dir):
        return "source_empty"
    if os.path.isfile(target_dir):
        return "target_blocked"
    if directory_contains_files(target_dir):
        return "already_installed"
    return "ready"


def parse_version_parts(version_text):
    if not version_text:
        return None

    parts = version_text.strip().split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def compare_version_parts(left_version, right_version):
    max_len = max(len(left_version), len(right_version))
    left_padded = left_version + (0,) * (max_len - len(left_version))
    right_padded = right_version + (0,) * (max_len - len(right_version))

    if left_padded < right_padded:
        return -1
    if left_padded > right_padded:
        return 1
    return 0


def get_installed_affinity_version():
    if os.name != "nt":
        return None, "unsupported_os"

    try:
        import winreg
    except ImportError:
        return None, "registry_unavailable"

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, AFFINITY_REGISTRY_SUBKEY) as key:
            display_version, _ = winreg.QueryValueEx(key, "DisplayVersion")
    except OSError:
        return None, "not_found"

    if not isinstance(display_version, str):
        return None, "invalid_value"

    display_version = display_version.strip()
    if not display_version:
        return None, "invalid_value"

    return display_version, None


def get_affinity_version_info():
    installed_version, error_code = get_installed_affinity_version()
    if not installed_version:
        return {
            "installed_version": None,
            "status": error_code,
            "warning": "Could not read Affinity DisplayVersion from the system registry. Patcher may work incorrectly.",
        }

    installed_parts = parse_version_parts(installed_version)
    supported_parts = parse_version_parts(SUPPORTED_AFFINITY_VERSION)
    if installed_parts is None or supported_parts is None:
        return {
            "installed_version": installed_version,
            "status": "parse_error",
            "warning": "Could not parse the installed Affinity version. Patcher may work incorrectly.",
        }

    comparison = compare_version_parts(installed_parts, supported_parts)
    if comparison < 0:
        return {
            "installed_version": installed_version,
            "status": "below_minimum",
            "warning": (
                f"Installed version is below {SUPPORTED_AFFINITY_VERSION}. "
                "Patcher may work incorrectly."
            ),
        }

    if comparison > 0:
        return {
            "installed_version": installed_version,
            "status": "different",
            "warning": (
                f"Installed version differs from tested {SUPPORTED_AFFINITY_VERSION}. "
                "Patcher may work incorrectly."
            ),
        }

    return {
        "installed_version": installed_version,
        "status": "supported",
        "warning": "",
    }


def get_launch_example():
    script_name = os.path.basename(sys.argv[0]) or "main.py"
    if getattr(sys, "frozen", False):
        return f'{script_name} "C:\\path\\to\\libaffinity.dll"'
    return f'python {script_name} "C:\\path\\to\\libaffinity.dll"'


def print_default_target_info():
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
    input("  Press Enter to return to menu...")


def get_patch_status(filepath):
    try:
        with open(filepath, "rb") as file_obj:
            file_obj.seek(PATCH_OFFSET)
            current_bytes = file_obj.read(len(ORIGINAL_BYTES))
    except Exception:
        return "unreadable", b""

    if len(current_bytes) < len(ORIGINAL_BYTES):
        return "too_small", current_bytes
    if current_bytes == PATCHED_BYTES:
        return "patched", current_bytes
    if current_bytes == ORIGINAL_BYTES:
        return "original", current_bytes
    return "unexpected", current_bytes


def format_patch_status_text(patch_status, current_bytes):
    if patch_status == "patched":
        return color("already patched", COLOR_YELLOW)
    if patch_status == "original":
        return color("not patched", COLOR_GREEN)
    if patch_status == "too_small":
        return color("file is too small", COLOR_RED)
    if patch_status == "unreadable":
        return color("cannot read patch bytes", COLOR_RED)
    return color(f"unexpected bytes: {current_bytes.hex().upper()}", COLOR_RED)


def print_affinity_version_info(version_info=None):
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


def patch_dll(filepath):
    target_path = resolve_target_path(filepath)
    if not target_path:
        print(color("  [!] No target path was provided.", COLOR_RED))
        return False

    version_info = get_affinity_version_info()
    print_target_info(target_path)
    print_affinity_version_info(version_info)

    if not os.path.exists(target_path):
        print(color(f"  [!] File not found: {target_path}", COLOR_RED))
        return False

    patch_status, current_bytes = get_patch_status(target_path)
    if patch_status == "patched":
        print(color("  [i] File is already patched. Nothing to do.", COLOR_YELLOW))
        print(f"  [i] Offset: 0x{PATCH_OFFSET:08X}")
        print(f"  [i] Bytes:  {current_bytes.hex().upper()}")
        return True
    if patch_status == "too_small":
        print(color("  [!] File is too small for this patch.", COLOR_RED))
        return False
    if patch_status == "unreadable":
        print(color("  [!] Could not read patch bytes from file.", COLOR_RED))
        return False
    if patch_status == "unexpected":
        print(color(f"  [!] Unexpected bytes at offset 0x{PATCH_OFFSET:08X}", COLOR_RED))
        print(f"  [!] Expected: {ORIGINAL_BYTES.hex().upper()}")
        print(f"  [!] Found:    {current_bytes.hex().upper()}")
        return False

    try:
        with open(target_path, "rb") as file_obj:
            data = bytearray(file_obj.read())
    except Exception as exc:
        print(color(f"  [!] Read error: {exc}", COLOR_RED))
        return False

    if len(data) < PATCH_OFFSET + len(ORIGINAL_BYTES):
        print(color(f"  [!] File is too small: {len(data)} bytes", COLOR_RED))
        return False

    if bytes(data[PATCH_OFFSET:PATCH_OFFSET + len(ORIGINAL_BYTES)]) != ORIGINAL_BYTES:
        print(color("  [!] File contents changed during verification. Try again.", COLOR_RED))
        return False

    backup_path = target_path + ".bak"
    if not os.path.exists(backup_path):
        try:
            shutil.copy2(target_path, backup_path)
            print(f"  [+] Backup created: {color(backup_path, COLOR_GREEN)}")
        except Exception as exc:
            print(color(f"  [!] Backup error: {exc}", COLOR_RED))
            return False
    else:
        print(f"  [i] Using existing backup: {color(backup_path, COLOR_YELLOW)}")

    data[PATCH_OFFSET:PATCH_OFFSET + len(PATCHED_BYTES)] = PATCHED_BYTES

    try:
        with open(target_path, "wb") as file_obj:
            file_obj.write(data)
    except Exception as exc:
        print(color(f"  [!] Write error: {exc}", COLOR_RED))
        return False

    print(color("  [+] Patch applied successfully.", COLOR_GREEN))
    print(f"  [+] Offset: 0x{PATCH_OFFSET:08X}")
    print(f"  [+] Changed: {ORIGINAL_BYTES.hex().upper()} -> {PATCHED_BYTES.hex().upper()}")
    print("  [+] Instruction: XOR AL, AL -> MOV AL, 1")
    print("  [+] Effect: Function now returns 1 instead of 0")
    return True


def install_russian_locale():
    source_dir = get_russian_locale_source_dir()
    target_dir = get_russian_locale_target_dir()

    print(f"  [*] Source: {color(source_dir, COLOR_CYAN)}")
    print(f"  [*] Target: {color(target_dir, COLOR_CYAN)}")
    print()
    print(
        color(
            "  [!] Warning: This is not a full translation. A complete Russian translation does not exist yet.",
            COLOR_YELLOW,
        )
    )
    print()

    locale_status = get_russian_locale_status()
    if locale_status == "default_dir_missing":
        print(color(f"  [!] Affinity folder not found: {DEFAULT_DIR}", COLOR_RED))
        return False
    if locale_status == "source_missing":
        print(color(f"  [!] Russian localization folder not found: {source_dir}", COLOR_RED))
        return False
    if locale_status == "source_empty":
        print(color("  [!] Russian localization files were not found in the bundled ru folder.", COLOR_RED))
        return False
    if locale_status == "target_blocked":
        print(color(f"  [!] Cannot install localization because a file already exists here: {target_dir}", COLOR_RED))
        return False
    if locale_status == "already_installed":
        print(color("  [i] Russian localization is already installed. Installation cancelled.", COLOR_YELLOW))
        return False

    try:
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    except Exception as exc:
        print(color(f"  [!] Install error: {exc}", COLOR_RED))
        return False

    print(color("  [+] Russian localization installed successfully.", COLOR_GREEN))
    print()
    print(color("  [i] Note: this is a partial translation, not a complete localization.", COLOR_YELLOW))
    return True


def prompt_for_custom_target():
    raw_path = input("  Enter a DLL path or a folder path: ").strip()
    if not raw_path:
        print(color("  [i] No path entered.", COLOR_YELLOW))
        return ""
    return resolve_target_path(raw_path)


def redraw_main_screen():
    clear_screen()
    print_banner()
    print_default_target_info()


def run_menu():
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
            webbrowser.open(GITHUB_URL)
            print(f"  [+] Opening: {color(GITHUB_URL, COLOR_CYAN)}")
            print()
            pause()
            continue

        print(color("  [!] Invalid choice.", COLOR_RED))
        print()
        pause()


def run_cli_mode(target_arg):
    clear_screen()
    print_banner()
    target_path = resolve_target_path(target_arg)
    return 0 if patch_dll(target_path) else 1


def main():
    setup_console()

    if len(sys.argv) > 1:
        target_arg = " ".join(sys.argv[1:])
        return run_cli_mode(target_arg)

    return run_menu()


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
