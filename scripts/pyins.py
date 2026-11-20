import importlib.util
import os
import subprocess
import sys


def choose_script():
    from tkinter import Tk, filedialog

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.askopenfilename(
            parent=root,
            title="Select a Python script to package",
            filetypes=(("Python scripts", "*.py"), ("All files", "*.*")),
        )
    finally:
        root.destroy()


def ensure_pyinstaller():
    if importlib.util.find_spec("PyInstaller") is not None:
        return True

    print("PyInstaller is not installed; installing it now...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller"],
        check=False,
    )
    if result.returncode != 0:
        print(f"PyInstaller installation failed with exit code {result.returncode}.")
        return False
    return True


def main():
    if len(sys.argv) > 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} [script.py]")
        return 2

    script_path = sys.argv[1] if len(sys.argv) == 2 else choose_script()
    if not script_path:
        print("No script selected.")
        return 0

    script_path = os.path.abspath(script_path)
    if not script_path.lower().endswith(".py"):
        print(f"Expected a .py file: {script_path}")
        return 2
    if not os.path.isfile(script_path):
        print(f"Script not found: {script_path}")
        return 2

    if not ensure_pyinstaller():
        return 1

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        script_path,
    ]
    print(f"Building one-file executable for {os.path.basename(script_path)}...")
    result = subprocess.run(command, cwd=os.path.dirname(script_path), check=False)
    if result.returncode != 0:
        print(f"PyInstaller failed with exit code {result.returncode}.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
