import datetime, inspect, os, shutil, subprocess, string, sys
import inspect
import sys
from pathlib import Path

# 1. Resolve script path and components
script = Path(sys.argv[0]).resolve()
sdn, sbn, sne = script.parent, script.name, script.stem
sdbne = script.with_suffix('')
scmd = script.with_suffix('.cmd')

# 2. Format and print info if verbose
verbose = False
if verbose:
    snfo = inspect.cleandoc(f"""
        script_dirname : {sdn}
        script_basename: {sbn}
        script_w/o_ext : {sne}
        script_sdbne : {sdbne}
        script_cmd : {scmd}
    """)
    print(f"info:\n{snfo}")

# sys.exit()

# 3. Create the .cmd file if it does not exist
if not scmd.is_file():
    scmd.write_text("@py %~dpn0.py %*\n")

def cbget():
    import tkinter as tk

    # Initialize tkinter and hide the main window
    root = tk.Tk()
    root.withdraw()

    # Retrieve clipboard content
    text = root.clipboard_get()

    return text


#your main program starts here

if  __name__ == "__main__":
    cbc = cbget()
    print(f'{cbc}')
