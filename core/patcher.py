"""
Core patching routines for libaffinity.dll.
"""

import os
import shutil
from core.config import PATCH_OFFSET, ORIGINAL_BYTES, PATCHED_BYTES
from core.ansi import color, COLOR_YELLOW, COLOR_RED, COLOR_GREEN
from core.paths import resolve_target_path
from core.version import get_affinity_version_info


def get_patch_status(filepath):
    """
    Check the current patch status of the target file at PATCH_OFFSET.
    """
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
    """
    Format patch status into styled color string.
    """
    if patch_status == "patched":
        return color("already patched", COLOR_YELLOW)
    if patch_status == "original":
        return color("not patched", COLOR_GREEN)
    if patch_status == "too_small":
        return color("file is too small", COLOR_RED)
    if patch_status == "unreadable":
        return color("cannot read patch bytes", COLOR_RED)
    return color(f"unexpected bytes: {current_bytes.hex().upper()}", COLOR_RED)


def patch_dll(filepath):
    """
    Apply XOR AL, AL -> MOV AL, 1 patch to target libaffinity.dll file.
    Creates a .bak backup beforehand.
    """
    target_path = resolve_target_path(filepath)
    if not target_path:
        print(color("  [!] No target path was provided.", COLOR_RED))
        return False

    # Avoid circular imports via runtime local import
    from core.ui import print_target_info, print_affinity_version_info

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
