import datetime
import inspect
import os
import shutil
import subprocess
import string
import sys

subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
    check=True,
)
subprocess.run(['yt-dlp', '-U'], check=True)


def cbget():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        return root.clipboard_get()
    finally:
        root.destroy()

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
         @py %~dpn0.py %*
         ''')
         w_scmd.write(str)

def spr(cmd):
    spr = subprocess.run(cmd, check=True, 
          stdout=subprocess.PIPE, 
          universal_newlines=True)
    spr = spr.stdout
    return spr

default_options = [
    "--no-config",
    "-c",
    "-i",
    "--geo-bypass-country", "US",
    "--restrict-filenames",
    "-o", "F:/music/%(playlist_title)s/%(playlist_index)s.%(artist)s.%(title)s.%(ext)s",
    "--ffmpeg-location", f"C:{os.sep}ProgramData{os.sep}chocolatey{os.sep}bin",
]

def download_youtube(url):
    """Downloads a YouTube playlist or single video using built-in options."""
    print(f'--current url: \033[033m{url}\033[0m')
    print(f'--options: \n1.download video \n2.download audio \n3.download-playlist')
    yc = input(f'--your command: ')
    if yc == '1':
       command = [sys.executable, "-m", "yt_dlp", *default_options, "--no-playlist", "-f", "mp4", "--remote-components", "ejs:github", "--js-runtimes", "deno", url]
    if yc == '2':
       command = [sys.executable, "-m", "yt_dlp", *default_options, "--no-playlist",
                  "-x", "--audio-format", "mp3", "--remote-components", "ejs:github", "--js-runtimes", "deno", url]
    if yc == '3':
       command = [sys.executable, "-m", "yt_dlp", *default_options, "--yes-playlist",
                  "-x", "--audio-format", "mp3", "--max-filesize", "16M", "--remote-components", "ejs:github", "--js-runtimes", "deno", url]
    print(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        print("Download complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error during download: {e}")

if  __name__ == "__main__":
    yturl = cbget()
    if  yturl.startswith('http'):
        youtube_url = yturl
    elif  not len(sys.argv[1:]) == 0:
          youtube_url == sys.argv[1]
    else:
        youtube_url = input("Enter YouTube playlist or video URL: ")
    if  youtube_url:
        download_youtube(youtube_url)
    else:
        print("No URL provided.")
