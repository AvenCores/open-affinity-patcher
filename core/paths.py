"""
Path verification, cleaning, and resolution utilities.
"""

import os
import sys
from core.config import DEFAULT_DIR, DEFAULT_DLL_NAME


def get_default_target_path():
    """
    Get the default target file path for libaffinity.dll.
    """
    return os.path.join(DEFAULT_DIR, DEFAULT_DLL_NAME)


def get_app_base_dirs():
    """
    Find base directories for locate operations.
    Handles both source-level running and compiled PyInstaller executable runtime paths.
    """
    base_dirs = []
    if getattr(sys, "frozen", False):
        base_dirs.extend(
            [
                getattr(sys, "_MEIPASS", ""),
                os.path.dirname(sys.executable),
            ]
        )
    else:
        # In source-level run, this file is under <root>/core/paths.py
        # We need the parent directory of 'core' package to find localization etc.
        core_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(core_dir)
        base_dirs.append(project_root)

    unique_dirs = []
    for base_dir in base_dirs:
        if base_dir and base_dir not in unique_dirs:
            unique_dirs.append(base_dir)
    return unique_dirs


def clean_path(raw_path):
    """
    Strip surrounding whitespace, quotes, and double quotes from path strings.
    """
    return raw_path.strip().strip('"').strip("'")


def resolve_target_path(raw_path):
    """
    Clean path inputs and resolve directories to the target DLL path if target is directory.
    """
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
    """
    Check if the default installation directory for Affinity exists.
    """
    return os.path.isdir(DEFAULT_DIR)


def default_target_exists():
    """
    Check if libaffinity.dll exists at the default installation path.
    """
    return os.path.isfile(get_default_target_path())


def directory_contains_files(dirpath):
    """
    Walk directory to verify it contains one or more non-empty files.
    """
    if not os.path.isdir(dirpath):
        return False

    for _, _, filenames in os.walk(dirpath):
        if filenames:
            return True
    return False
