import os
import sys


CF_TEXT = 1
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class ClipboardError(RuntimeError):
    pass


def _windows_clipboard_api():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p
    return ctypes, user32, kernel32


def _windows_error(ctypes, operation):
    error_code = ctypes.get_last_error()
    return OSError(error_code, f"{operation}: {ctypes.FormatError(error_code).strip()}")


def _set_windows_clipboard(text):
    ctypes, user32, kernel32 = _windows_clipboard_api()
    opened = False
    memory = None
    try:
        if not user32.OpenClipboard(None):
            raise _windows_error(ctypes, "Unable to open clipboard")
        opened = True
        if not user32.EmptyClipboard():
            raise _windows_error(ctypes, "Unable to clear clipboard")

        data = (text + "\0").encode("utf-16-le")
        memory = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not memory:
            raise _windows_error(ctypes, "Unable to allocate clipboard memory")
        pointer = kernel32.GlobalLock(memory)
        if not pointer:
            raise _windows_error(ctypes, "Unable to lock clipboard memory")
        try:
            ctypes.memmove(pointer, data, len(data))
        finally:
            ctypes.set_last_error(0)
            unlocked = kernel32.GlobalUnlock(memory)
            if not unlocked and ctypes.get_last_error():
                raise _windows_error(ctypes, "Unable to unlock clipboard memory")

        if not user32.SetClipboardData(CF_UNICODETEXT, memory):
            raise _windows_error(ctypes, "Unable to set clipboard data")
        memory = None
    finally:
        if memory:
            kernel32.GlobalFree(memory)
        if opened:
            user32.CloseClipboard()


def _get_windows_clipboard():
    ctypes, user32, kernel32 = _windows_clipboard_api()
    if not user32.OpenClipboard(None):
        raise _windows_error(ctypes, "Unable to open clipboard")

    try:
        clipboard_format = CF_UNICODETEXT
        data_handle = user32.GetClipboardData(clipboard_format)
        if not data_handle:
            clipboard_format = CF_TEXT
            data_handle = user32.GetClipboardData(clipboard_format)
        if not data_handle:
            raise ClipboardError("No text data in clipboard.")

        pointer = kernel32.GlobalLock(data_handle)
        if not pointer:
            raise _windows_error(ctypes, "Unable to lock clipboard data")
        try:
            if clipboard_format == CF_UNICODETEXT:
                return ctypes.wstring_at(pointer)
            return ctypes.string_at(pointer).decode("mbcs", errors="replace")
        finally:
            ctypes.set_last_error(0)
            unlocked = kernel32.GlobalUnlock(data_handle)
            if not unlocked and ctypes.get_last_error():
                raise _windows_error(ctypes, "Unable to unlock clipboard data")
    finally:
        user32.CloseClipboard()


def _set_tk_clipboard(text):
    import tkinter as tk

    root = tk.Tk()
    try:
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
    except tk.TclError as error:
        raise ClipboardError(f"Unable to set clipboard: {error}") from error
    finally:
        root.destroy()


def _get_tk_clipboard():
    import tkinter as tk

    root = tk.Tk()
    try:
        root.withdraw()
        return root.clipboard_get()
    except tk.TclError as error:
        raise ClipboardError(f"Unable to get text from clipboard: {error}") from error
    finally:
        root.destroy()


def set_clipboard(text):
    if os.name == "nt":
        _set_windows_clipboard(text)
    else:
        _set_tk_clipboard(text)


def get_clipboard():
    if os.name == "nt":
        return _get_windows_clipboard()
    return _get_tk_clipboard()


def show_usage(program):
    print(
        f"Usage:\n"
        f"  {program} -s <strings...>\n"
        f"  {program} -f <filename>\n"
        f"  {program} (no options: print clipboard)",
        file=sys.stderr,
    )


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    program = os.path.basename(sys.argv[0])

    try:
        if not args:
            print(get_clipboard())
            return 0

        if args[0] == "-s":
            set_clipboard(" ".join(args[1:]))
            return 0

        if args[0] == "-f" and len(args) > 1:
            try:
                with open(args[1], "r", encoding="utf-8", newline="") as file:
                    content = file.read()
            except (OSError, UnicodeError) as error:
                print(f"Error: Cannot read file {args[1]}: {error}", file=sys.stderr)
                return 1
            set_clipboard(content)
            return 0
    except (ClipboardError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    show_usage(program)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
