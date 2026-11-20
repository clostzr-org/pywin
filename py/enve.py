import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
import winreg


SYSTEM_ENVIRONMENT_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
USER_ENVIRONMENT_KEY = r"Environment"
SCRIPT_PATH = Path(__file__).resolve()
LAUNCHER_PATH = SCRIPT_PATH.with_suffix(".cmd")


def ensure_launcher():
    if not LAUNCHER_PATH.is_file():
        LAUNCHER_PATH.write_text(
            '@echo off\n@py "%~dp0enve.py" %*\n',
            encoding="utf-8",
        )


def print_path_entries(label, path_value):
    entries = [entry.strip() for entry in path_value.split(";") if entry.strip()]
    print(f"\n{label} ({len(entries)} entries):")
    if not entries:
        print("  (empty)")
        return
    for index, entry in enumerate(entries, start=1):
        print(f"  {index:02}. {entry}")


def read_registry_path(root, key_path, label):
    try:
        with winreg.OpenKey(root, key_path, 0, winreg.KEY_READ) as key:
            path_value, _ = winreg.QueryValueEx(key, "Path")
    except FileNotFoundError:
        print(f"{label} is not set in the registry.")
        return ""
    except OSError as error:
        print(f"[ERROR] Could not read {label}: {error}")
        return None

    if not isinstance(path_value, str):
        print(f"[ERROR] {label} has an unexpected registry value type.")
        return None
    return path_value


def print_current_paths():
    print("=== Current PATH configuration ===")
    print("This script updates the current user's PATH, not the machine PATH.")

    system_path = read_registry_path(
        winreg.HKEY_LOCAL_MACHINE,
        SYSTEM_ENVIRONMENT_KEY,
        "System PATH",
    )
    if system_path is not None:
        print_path_entries("System PATH (HKLM)", system_path)

    user_path = read_registry_path(
        winreg.HKEY_CURRENT_USER,
        USER_ENVIRONMENT_KEY,
        "User PATH",
    )
    if user_path is not None:
        print_path_entries("User PATH (HKCU)", user_path)

    print_path_entries("Current process PATH", os.environ.get("PATH", ""))


def add_path_to_windows(new_path):
    new_path = os.path.normpath(new_path)

    print("\n=== Updating user PATH ===")
    print(f"Selected directory: {new_path}")

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            USER_ENVIRONMENT_KEY,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        ) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""

            if not isinstance(current_path, str):
                print("[ERROR] User PATH has an unexpected registry value type.")
                return False

            paths = [path.strip() for path in current_path.split(";") if path.strip()]
            print_path_entries("User PATH before update (HKCU)", current_path)

            normalized_new_path = os.path.normcase(os.path.normpath(new_path))
            if any(
                os.path.normcase(os.path.normpath(path)) == normalized_new_path
                for path in paths
            ):
                print(f"\nNo change: directory is already in the user PATH: {new_path}")
                print_path_entries("User PATH unchanged (HKCU)", current_path)
                return False

            paths.append(new_path)
            updated_path = ";".join(paths)

            print(f"\nChange: appending this entry to the user PATH:\n  + {new_path}")
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, updated_path)

    except OSError as error:
        print(f"[ERROR] Could not update the user PATH registry value: {error}")
        return False

    print("\nUser PATH registry update completed.")
    print_path_entries("User PATH after update (HKCU)", updated_path)
    print("Machine PATH (HKLM) was not changed.")

    import ctypes

    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002
    result = ctypes.c_size_t()
    try:
        sent = ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            ctypes.c_wchar_p("Environment"),
            SMTO_ABORTIFHUNG,
            5000,
            ctypes.byref(result),
        )
    except OSError as error:
        print(f"[WARNING] PATH was saved, but Windows notification failed: {error}")
    else:
        if sent:
            print("Windows was notified that the environment changed.")
        else:
            print("[WARNING] PATH was saved, but Windows did not confirm the notification.")

    print_path_entries(
        "Current process PATH (unchanged until a new process starts)",
        os.environ.get("PATH", ""),
    )
    return True


def pick_directory():
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
        print("\nOpening the folder picker...")
        return filedialog.askdirectory(
            parent=root,
            title="Select Folder to Add to User PATH",
            mustexist=True,
        )
    finally:
        root.destroy()


def show_environment_variables():
    print("Opening the Windows Environment Variables dialog...")
    rundll32 = os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"),
        "System32",
        "rundll32.exe",
    )
    try:
        subprocess.Popen([rundll32, "sysdm.cpl,EditEnvironmentVariables"])
    except OSError as error:
        print(f"[ERROR] Could not open the Environment Variables dialog: {error}")
        return 1
    return 0


def main(args):
    ensure_launcher()

    if not args:
        return show_environment_variables()
    if len(args) not in (1, 2) or args[0].lower() != "a":
        print(f"Usage: {SCRIPT_PATH.name} [a [directory]]")
        return 2

    print_current_paths()
    selected_dir = args[1] if len(args) == 2 else pick_directory()
    if selected_dir:
        add_path_to_windows(selected_dir)
    else:
        print("\nNo folder selected. PATH was not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
