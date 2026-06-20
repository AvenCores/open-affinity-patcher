"""
Configuration and global constants for the Affinity Patcher.
"""

VERSION = "1.0.3"
DEFAULT_DIR = r"C:\Program Files\Affinity\Affinity"
DEFAULT_DLL_NAME = "libaffinity.dll"
RUSSIAN_LOCALE_DIR_NAME = "ru"
PATCH_OFFSET = 0x00440ED1
ORIGINAL_BYTES = b"\x32\xC0"
PATCHED_BYTES = b"\xB0\x01"
AFFINITY_REGISTRY_SUBKEY = (
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    r"\{D5B4183A-DE48-405A-A106-D3E48EBFE23F}"
)
SUPPORTED_AFFINITY_VERSION = "3.2.2.4557"
TELEGRAM_URL = "t.me/avencoresyt"
YOUTUBE_URL = "youtube.com/@avencores"
GITHUB_URL = "https://github.com/AvenCores/open-affinity-patcher"
