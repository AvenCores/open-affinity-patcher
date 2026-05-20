"""
Russian localization check and installation utilities.
"""

import os
import shutil
from core.config import DEFAULT_DIR, RUSSIAN_LOCALE_DIR_NAME
from core.ansi import color, COLOR_CYAN, COLOR_YELLOW, COLOR_RED, COLOR_GREEN
from core.paths import (
    get_app_base_dirs,
    default_location_available,
    directory_contains_files,
)


def get_russian_locale_source_dir():
    """
    Get the directory containing translation resources inside package source/distribution.
    """
    for base_dir in get_app_base_dirs():
        candidate = os.path.join(base_dir, RUSSIAN_LOCALE_DIR_NAME)
        if os.path.isdir(candidate):
            return candidate
    return os.path.join(get_app_base_dirs()[0], RUSSIAN_LOCALE_DIR_NAME)


def get_russian_locale_target_dir():
    """
    Get the localization target folder under the default Affinity directory.
    """
    return os.path.join(DEFAULT_DIR, RUSSIAN_LOCALE_DIR_NAME)


def get_russian_locale_status():
    """
    Evaluate the status of the Russian localization files and target.
    """
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


def install_russian_locale():
    """
    Copy Russian localization resources to the Affinity directory.
    """
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
