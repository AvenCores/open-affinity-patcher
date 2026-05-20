"""
Windows registry checks and version verification routines.
"""

import os
from core.config import AFFINITY_REGISTRY_SUBKEY, SUPPORTED_AFFINITY_VERSION


def parse_version_parts(version_text):
    """
    Parse a dotted version string (e.g. '1.2.3.4') into an integer tuple.
    """
    if not version_text:
        return None

    parts = version_text.strip().split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def compare_version_parts(left_version, right_version):
    """
    Compare two integer tuples representing version parts.
    """
    max_len = max(len(left_version), len(right_version))
    left_padded = left_version + (0,) * (max_len - len(left_version))
    right_padded = right_version + (0,) * (max_len - len(right_version))

    if left_padded < right_padded:
        return -1
    if left_padded > right_padded:
        return 1
    return 0


def get_installed_affinity_version():
    """
    Query registry subkey to find installed Affinity display version string.
    """
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
    """
    Formulate version info dictionary detailing compatibility status and warnings.
    """
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
