import os
import sys
import tkinter as tk
from tkinter import filedialog
import winreg

def add_path_to_windows(new_path):
    # Normalize the path
    new_path = os.path.normpath(new_path)
    
    try:
        # Open the Environment Variables key in the Windows Registry for the current user
        reg_path = r"Environment"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""
            
            # Check if path is already in PATH
            paths = [p.strip() for p in current_path.split(";") if p.strip()]
            if new_path in paths:
                print(f"Directory is already in the Path: {new_path}")
                return False
            
            # Append new path
            paths.append(new_path)
            updated_path = ";".join(paths)
            
            # Save back to registry
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, updated_path)
            
        # Broadcast the WM_SETTINGCHANGE message so Windows updates environment variables without a reboot
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, 
            ctypes.c_wchar_p("Environment"), 
            SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
        )
        
        print(f"Successfully added to Path: {new_path}")
        return True

    except Exception as e:
        print(f"Error updating registry: {e}")
        return False

def main():
    # Hide the main Tkinter root window
    root = tk.Tk()
    root.withdraw()
    
    # Bring the dialog to the front
    root.attributes('-topmost', True)
    
    # Open the native folder picker dialog
    selected_dir = filedialog.askdirectory(title="Select Folder to Add to System Path")
    
    if selected_dir:
        add_path_to_windows(selected_dir)
    else:
        print("No folder selected.")

if __name__ == "__main__":
    main()