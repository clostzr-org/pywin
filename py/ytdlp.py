import datetime
import inspect
import os
import shutil
import subprocess
import string
import sys
script_path = sys.argv[0]
if  os.path.islink(script_path):
    script_path = os.readlink(script_path)
sdn   = os.path.dirname(script_path)
sbn   = os.path.basename(script_path)
sne   = os.path.splitext(sbn)[0]
sdbne = sdn + os.sep + sne
scmd  = sdbne + '.cmd'

snfo = inspect.cleandoc(f'''
script_dirname : {sdn}
script_basename: {sbn}
script_w/o_ext : {sne}
script_sdbne   : {sdbne}
script_cmd     : {scmd}
''')

verbose = 'true'
verbose = 'false'

if  verbose == 'true':
    print(f'info:\n{snfo}')

#add a hashtag prefix to the following line when you done
#sys.exit()

if  os.path.isfile(scmd):
    print(f'file exists: \033[33m{scmd}\033[0m')
else:
    print(f'file-to-create: {scmd}')
    with open(scmd, 'w') as w_scmd:
         str = inspect.cleandoc(f'''
         %~dpn0.py %*
         ''')
         w_scmd.write(str)

def spr(cmd):
    spr = subprocess.run(cmd, check=True, 
          stdout=subprocess.PIPE, 
          universal_newlines=True)
    spr = spr.stdout
    return spr

import subprocess
import os
import platform

subprocess.run(['python', '-m', 'pip', 'install','--upgrade', 'yt-dlp'])

default_config = inspect.cleandoc(f"""
-c -i --geo-bypass-country US --restrict-filenames
-o "F:/music/%(playlist_title)s/%(playlist_index)s.%(artist)s.%(title)s.%(ext)s"
--ffmpeg-location "C:{os.sep}ProgramData{os.sep}chocolatey{os.sep}bin"
""")
def create_config_file(config_path):
    """Creates the ytdlp config file with default settings using micro editor."""
    if not os.path.exists(config_path):
        print(f"Updating: {config_path}")
        try:
            if  platform.system() == "Windows":
                subprocess.run(["micro", config_path], input=default_config, text=True, check=True)
            else:
                # For Linux/macOS, you might need to ensure 'micro' is in PATH
                subprocess.run(["micro", config_path], input=default_config, text=True, check=True)
            print(f"Default configuration written to {config_path}. Please edit if needed.")
        except FileNotFoundError:
            print("Error: 'micro' editor not found. Please install it or create the config file manually.")
            with open(config_path, "w") as f:
                f.write(default_config)
            print(f"Default configuration written to {config_path}. Please edit it manually.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating config file with micro: {e}")
            print("Falling back to writing default config directly.")
            with open(config_path, "w") as f:
                f.write(default_config)
    else:
        print(f"Config file already exists at: {config_path}")

def download_youtube(url, config_path):
    """Downloads a YouTube playlist or single video using ytdlp with the specified config."""
    print(f'--current url: \033[033m{url}\033[0m')
    print(f'--options: \n1.download video \n2.download audio \n3.download-playlist')
    yc = input(f'--your command: ')
    if yc == '1':
       command = ["yt-dlp", "--config-location", config_path, "--no-playlist", "-f", "mp4", url]
    if yc == '2':
       command = ["yt-dlp", "--config-location", config_path, "--no-playlist",
                  "-x", "--audio-format", "mp3", url]
    if yc == '3':
       command = ["yt-dlp", "--config-location", config_path, "--yes-playlist",
                  "-x", "--audio-format", "mp3", "--max-filesize", "16M", "--js-runtimes", "deno", url]
    print(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        print("Download complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error during download: {e}")

if  __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = "ytdlp_config.txt"
    config_path = os.path.join(script_dir, config_file)

    create_config_file(config_path)
    from tkcbget import cbget
    yturl = cbget()
    if  yturl.startswith('http'):
        youtube_url = yturl
    elif  not len(sys.argv[1:]) == 0:
          youtube_url == sys.argv[1]
    else:
        youtube_url = input("Enter YouTube playlist or video URL: ")
    if  youtube_url:
        download_youtube(youtube_url, config_path)
    else:
        print("No URL provided.")
