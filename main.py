#!/usr/bin/env python3
"""
Patch libaffinity.dll
Changes XOR AL, AL (return 0) -> MOV AL, 1 (return 1) at file offset 0x0043E451
"""

import sys
import os
import shutil

def patch_dll(filepath):
    """Apply patch to libaffinity.dll"""
    
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found!")
        return False
    
    # Read original file
    with open(filepath, 'rb') as f:
        data = bytearray(f.read())
    
    # Patch offset (file offset in .text section)
    patch_offset = 0x0043E451
    
    # Verify file is large enough
    if len(data) < patch_offset + 2:
        print(f"Error: File too small ({len(data)} bytes)")
        return False
    
    # Original bytes: 32 C0 (XOR AL, AL)
    original_bytes = bytes([0x32, 0xC0])
    
    # Patched bytes: B0 01 (MOV AL, 1)
    patched_bytes = bytes([0xB0, 0x01])
    
    # Verify original bytes
    if data[patch_offset:patch_offset+2] != original_bytes:
        current = data[patch_offset:patch_offset+2]
        print(f"Error: Unexpected bytes at offset 0x{patch_offset:08X}")
        print(f"  Expected: {original_bytes.hex().upper()}")
        print(f"  Found:    {current.hex().upper()}")
        
        # Check if already patched
        if current == patched_bytes:
            print("File appears to be already patched!")
        return False
    
    # Apply patch
    data[patch_offset] = 0xB0
    data[patch_offset + 1] = 0x01
    
    # Create backup
    backup_path = filepath + '.bak'
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
        print(f"Backup created: {backup_path}")
    
    # Write patched file
    with open(filepath, 'wb') as f:
        f.write(data)
    
    print(f"Patch applied successfully!")
    print(f"  Offset: 0x{patch_offset:08X}")
    print(f"  Changed: {original_bytes.hex().upper()} -> {patched_bytes.hex().upper()}")
    print(f"  Instruction: XOR AL, AL -> MOV AL, 1")
    print(f"  Effect: Function now returns 1 instead of 0")
    
    return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = 'libaffinity.dll'
    
    print(f"Patching: {target}")
    if patch_dll(target):
        sys.exit(0)
    else:
        sys.exit(1)