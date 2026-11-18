import inspect
import os
import string
import sys

# Generate the wrapper .cmd file dynamically
SCRIPT_PATH = os.path.abspath(__file__)
CMD_FILE = SCRIPT_PATH.replace('.py', '.cmd')

with open(CMD_FILE, 'w') as ocfw:
    lines = inspect.cleandoc(f'''
    @echo off
    @py "{SCRIPT_PATH}" %*
    exit
    ''')
    ocfw.write(f'{lines}\n')

def show_usage():
    usage_text = inspect.cleandoc(f'''
    file(s)_desymbolizer
    Batch replace white spaces and special characters in file names.
    Usage: {os.path.basename(sys.argv[0])} ["<path>"]
    Without a path, choose a file or folder interactively.
    ''')
    print(f'\n{usage_text}\n')


def choose_target_path():
    from tkinter import Tk, filedialog

    root = Tk()
    root.withdraw()
    try:
        while True:
            target_type = input(
                'Choose target type: [f]ile or [d]irectory (default d, q to cancel): '
            ).strip().lower()
            if target_type in ('q', 'quit', 'cancel'):
                return ''
            if target_type in ('', 'd', 'dir', 'directory', 'folder'):
                return filedialog.askdirectory(
                    parent=root,
                    title='Choose a folder to desymbolize',
                    mustexist=True,
                )
            if target_type in ('f', 'file'):
                return filedialog.askopenfilename(
                    parent=root,
                    title='Choose a file to desymbolize',
                )
            print('Enter f for a file, d for a directory, or q to cancel.')
    finally:
        root.destroy()


# Parse arguments cleanly
if len(sys.argv) > 1:
    target_path = sys.argv[1].strip('"')
else:
    target_path = choose_target_path()

if not target_path:
    print('No target selected. Exiting...')
    sys.exit()

if not os.path.exists(target_path):
    print(f'Path does not exist: {target_path}')
    input('Press Enter to exit...')
    sys.exit()

def reform_name(filename):
    """Replaces spaces with underscores and filters out forbidden characters."""
    filename = filename.replace(' ', '_')
    SPECIAL_CHARS = r':\/_-[].()+'
    PERMITTED_CHARS = string.digits + string.ascii_letters + SPECIAL_CHARS
    return "".join(c for c in filename if c in PERMITTED_CHARS)

def process_target(target, execute=False):
    """Scans and renames files or directories safely using absolute paths."""
    target = os.path.abspath(target)
    normalized_target = os.path.normcase(target)
    one_drive_root = os.path.normcase(os.path.abspath(r'C:\Users\Admin\OneDrive'))
    target_drive, _ = os.path.splitdrive(normalized_target)
    one_drive_drive, _ = os.path.splitdrive(one_drive_root)
    if target_drive == one_drive_drive and os.path.commonpath(
        (normalized_target, one_drive_root)
    ) != one_drive_root:
        print(f'Skipped non-whitelisted C: path: {target}')
        return

    # Handle Single File
    if os.path.isfile(target):
        dir_name = os.path.dirname(target)
        base_name = os.path.basename(target)
        new_base = reform_name(base_name)
        
        if base_name != new_base:
            new_path = os.path.join(dir_name, new_base)
            print(f'[FILE] Old: {base_name} -> New: {new_base}')
            if execute:
                os.rename(target, new_path)
        return

    # Handle Directory Scanning
    if os.path.isdir(target):
        try:
            items = os.listdir(target)
        except PermissionError:
            print(f'Permission Denied: {target}')
            return

        print(f'\nScanning directory: {target}')
        valid_count = 0
        
        for item in items:
            if item in ('$RECYCLE.BIN', 'System Volume Information'):
                continue

            valid_count += 1
            item_idx = str(valid_count).zfill(2)
            full_item_path = os.path.join(target, item)
            
            new_base = reform_name(item)
            if item == new_base:
                if not execute:
                    print(f'  [{item_idx}] Skipped (Same Name): {item}')
                continue

            new_item_path = os.path.join(target, new_base)
            print(f'  [{item_idx}] Old: {item}\n  [{item_idx}] New: {new_base}')
            
            if execute:
                try:
                    os.rename(full_item_path, new_item_path)
                    print(f'  ----> Renamed successfully.')
                except Exception as e:
                    print(f'  [ERROR] Could not rename {item}: {e}')

# --- Execution Flow ---
# Step 1: Dry run (Show what changes will be made)
print("\n--- DRY RUN: Previewing Changes ---")
process_target(target_path, execute=False)

# Step 2: Confirmation Prompt
confirm = input('\nExecute the rename operations? (yes/no): ').strip().lower()

if confirm in ('yes', 'y'):
    print('\nExecuting transformations...')
    process_target(target_path, execute=True)
else:
    print('\nOperation cancelled. Exiting...')
