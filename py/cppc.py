import os
import sys
import shutil
import subprocess

# Initialize Windows virtual terminal processing safely
os.system("")

import os
import sys
import inspect

# Resolve script path safely
script_path = os.path.abspath(sys.argv[0])
if os.path.islink(script_path):
    script_path = os.readlink(script_path)

# Extract components
sdn   = os.path.dirname(script_path)
sbn   = os.path.basename(script_path)
sne   = os.path.splitext(sbn)[0]   # filename without extension
sdbne = os.path.join(sdn, sne)
scmd  = f"{sdbne}.cmd"

# Optional verbose info
verbose = False
if verbose:
    snfo = inspect.cleandoc(f"""
    script_dirname : {sdn}
    script_basename: {sbn}
    script_w/o_ext : {sne}
    script_sdbne   : {sdbne}
    script_cmd     : {scmd}
    """)
    print(f"info:\n{snfo}")

# Ensure .cmd launcher exists
if not os.path.isfile(scmd):
    cmd_str = inspect.cleandoc(f"""
    @py "%~dp0%~n0.py" %*
    """)
    with open(scmd, 'w', encoding='utf-8') as w_scmd:
        w_scmd.write(cmd_str)


def compile_cpp_file(cpp_path, forced_exe_name=None):
    """Compiles a single C++ file into an optimized, stripped .exe"""
    file_dir = os.path.dirname(cpp_path)
    base_name, _ = os.path.splitext(os.path.basename(cpp_path))
    
    final_exe_name = forced_exe_name if forced_exe_name else f"{base_name}.exe"
    exe_path = os.path.join(file_dir, final_exe_name)
    
    print(f"\033[96m[Compiling]\033[0m {os.path.basename(cpp_path)} -> {final_exe_name}...")
    
    if shutil.which("g++"):
        compile_cmd = [
            "g++", "-Os", "-s",
            "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
            cpp_path, "-o", exe_path,
            "-luser32", "-lole32", "-lkernel32"
        ]
        res = subprocess.run(compile_cmd, cwd=file_dir,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"\033[91m[COMPILER ERROR] for {os.path.basename(cpp_path)}:\033[0m\n{res.stderr}")
            return False
            
    elif shutil.which("cl"):
        compile_cmd = [
            "cl.exe", "/O1", "/MD", "/EHsc",
            cpp_path, "/link", "/OPT:REF", "/OPT:ICF",
            "user32.lib", "ole32.lib", "kernel32.lib", f"/OUT:{exe_path}"
        ]
        res = subprocess.run(compile_cmd, cwd=file_dir,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        obj_path = os.path.splitext(cpp_path)[0] + ".obj"
        if os.path.exists(obj_path):
            os.remove(obj_path)
            
        if res.returncode != 0:
            print(f"\033[91m[COMPILER ERROR] for {os.path.basename(cpp_path)}:\033[0m\n{res.stderr}")
            return False
    else:
        print("\033[91m[ERROR]\033[0m No native compiler (g++ or cl.exe) found in your PATH.")
        return False

    if os.path.exists(exe_path):
        print(f"\033[92m[Success]\033[0m Generated optimized binary: {final_exe_name}")
        return True
    else:
        print(f"\033[91m[ERROR]\033[0m Verification failed. Binary missing.")
        return False

def main():
    interactive = len(sys.argv) == 1
    if interactive:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        try:
            selected_files = filedialog.askopenfilenames(
                parent=root,
                title="Select C++ source file(s) to compile",
                filetypes=(("C++ source files", "*.cpp"), ("All files", "*.*")),
            )
        finally:
            root.destroy()
        provided_cpp_files = [os.path.abspath(path) for path in selected_files]
    else:
        provided_cpp_files = [
            os.path.abspath(arg) for arg in sys.argv[1:]
            if arg.lower().endswith('.cpp')
        ]
    
    if not provided_cpp_files:
        if interactive:
            print("\033[93m[Cancelled]\033[0m No .cpp files selected.")
            return
        print("\033[91m[ERROR]\033[0m No .cpp files provided.")
        sys.exit(1)
    
    print(f"\033[95m{'='*60}\n Batch C++ Compilation Mode Active ({len(provided_cpp_files)} file[s])\n{'='*60}\033[0m")
    success_count = 0
    last_compiled_exe = None
    
    for cpp_file in provided_cpp_files:
        if not os.path.exists(cpp_file):
            print(f"\033[91m[Missing File]\033[0m {cpp_file} does not exist. Skipping.")
            continue
        
        f_base = os.path.splitext(os.path.basename(cpp_file))[0]
        target_exe_name = f"{f_base}.exe"
        
        if compile_cpp_file(cpp_file, forced_exe_name=target_exe_name):
            success_count += 1
            last_compiled_exe = os.path.join(os.path.dirname(cpp_file), target_exe_name)
            
    print(f"\033[95m{'='*60}\n Summary: {success_count}/{len(provided_cpp_files)} processed cleanly.\n{'='*60}\033[0m")
    
    # If compiling a single file, run it immediately after success
    if len(provided_cpp_files) == 1 and last_compiled_exe and os.path.exists(last_compiled_exe):
        print(f"\033[94m[Executing]\033[0m Launching {os.path.basename(last_compiled_exe)}...\n")
        try:
            extra_args = [arg for arg in sys.argv[1:] if not arg.lower().endswith('.cpp')]
            subprocess.run([last_compiled_exe] + extra_args)
        except KeyboardInterrupt:
            pass
    else:
        input('\nPress ENTER to close.')

if __name__ == "__main__":
    main()
