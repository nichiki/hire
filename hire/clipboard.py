"""Clipboard utilities."""

import platform
import subprocess


def _copy_to_clipboard_windows(text: str) -> bool:
    """Copy text to clipboard using Windows API via ctypes."""
    import ctypes

    # Windows API constants
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    # Load required DLLs
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Set up function signatures (use c_void_p for handles on 64-bit)
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_bool
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = ctypes.c_bool
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = ctypes.c_bool
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p

    # Encode text as UTF-16LE with null terminator
    data = text.encode("utf-16-le") + b"\x00\x00"
    size = len(data)

    # Allocate global memory
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
    if not h_mem:
        return False

    # Lock memory and copy data
    ptr = kernel32.GlobalLock(h_mem)
    if not ptr:
        kernel32.GlobalFree(h_mem)
        return False

    ctypes.memmove(ptr, data, size)
    kernel32.GlobalUnlock(h_mem)

    # Open clipboard and set data
    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(h_mem)
        return False

    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
            kernel32.GlobalFree(h_mem)
            return False
        # Note: After successful SetClipboardData, system owns the memory
        return True
    finally:
        user32.CloseClipboard()


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            # Don't override env - let system locale handle it
            subprocess.run(
                ["pbcopy"],
                input=text,
                text=True,
                encoding="utf-8",
                check=True,
            )
        elif system == "Linux":
            # Try xclip first, fall back to xsel
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=True,
                )
            except FileNotFoundError:
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode("utf-8"),
                    check=True,
                )
        elif system == "Windows":
            return _copy_to_clipboard_windows(text)
        else:
            return False
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
