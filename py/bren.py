import inspect
import os
import sys
import time

sdn = os.path.dirname(sys.argv[0])
sbn = os.path.basename(sys.argv[0])
sne = sbn.rsplit('.', 1)[0]
scf = f'{sdn}{os.sep}{sne}.cmd'
nfo = inspect.cleandoc(f'''
      sne: {sne}
      scf: {scf}
      ''')

def usg():
    usg = inspect.cleandoc(f'''
    usage: {sbn} [argument]
    ''')
    print(f'{usg}')

print(f'os.name: {os.name}\n{nfo}')
if not os.path.exists(f'{sdn}{os.sep}{sne}.cmd'):
    print(f'creating cmd file for current script ({sne})')
    with open(scf, 'w') as oscfw:
        scont = inspect.cleandoc(f'''
        @echo off
        setLocal enableDelayedExpansion
        title %CD%
        @py "%~dpn0.py" %* 
        ''')
        oscfw.write(scont)
        print(f'new_cmd: {scf}')
        
try:
    sa1 = sys.argv[1]
    print(f'argument: {sa1}')
except:
    print(f'no_argument')

import os
import re

def batch_rename_files():
    """
    Batch renames files in the current directory based on user input.
    Provides a preview and confirmation before execution.
    """

    # Get working directory
    working_dir = os.getcwd()  #Use current directory by default
    print(f'current workdir: {working_dir}')
    if r'C:' in working_dir:
       if r"C:\Users\Admin\OneDrive" in working_dir:
          print(f'whitelisted: {working_dir}')
       elif not r"C:\Users\Admin\OneDrive" in working_dir:
          print(f'blacklisted: {working_dir}')
          input(f'press Enter')
          sys.exit()
        
    #List all files in the directory.
    files = [f for f in os.listdir(working_dir) if os.path.isfile(os.path.join(working_dir, f))]
    if not files:
        print("No files found in the directory.")
        return

    print("Files in the directory:")
    for i, file in enumerate(files):
        print(f"{i+1}. {file}")


    # Get user input for replacement
    while True:
        try:
            old_word = input("Enter the word to replace: ")
            new_word = input("Enter the replacement word: ")
            if not old_word or not new_word:
                raise ValueError("Both words cannot be empty.")
            break
        except ValueError as e:
            print(f"Error: {e}")

    # Find files matching the pattern and create a preview
    files_to_rename = []
    for file in files:
        if old_word in file:
            new_name = file.replace(old_word, new_word)
            if new_name != file:  #Skip if names are identical
                files_to_rename.append((file, new_name))

    if not files_to_rename:
        print("No files found matching the replacement pattern.")
        return


    print("\nPreview of files to be renamed:")
    for old_name, new_name in files_to_rename:
        print(f"{old_name} -> {new_name}")

    # Confirmation before renaming
    confirmation = input("\nConfirm rename (y/n)? ")
    if confirmation.lower() != 'y':
        print("Rename cancelled.")
        return

    # Perform the renaming
    for old_name, new_name in files_to_rename:
        try:
            os.rename(os.path.join(working_dir, old_name), os.path.join(working_dir, new_name))
            print(f"Renamed '{old_name}' to '{new_name}' successfully.")
        except OSError as e:
            print(f"Error renaming '{old_name}': {e}")

    print("\nBatch renaming complete.")


if __name__ == "__main__":
    batch_rename_files()

print(f'all done')
time.sleep(4)
#input(f'press ENTER')
