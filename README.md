# ytdl - YouTube downloader

Interactive command-line tool that downloads YouTube **videos** or **audio** with [yt-dlp](https://github.com/yt-dlp/yt-dlp).
Python 3.9+, one runtime dependency (`yt-dlp`), installable as a `ytdl` command.

```bash
ytdl                      # interactive menu
python3 -m ytdl           # same, without installing (Windows: python -m ytdl)
```

```text
Download folder [current folder]
1) Playlist   2) Single   3) Multiple
1) Video      2) Audio
Format: pick from the list (see below)
```

Files are saved as `<index>_<title>.<ext>`, for example `01_My Song.mp3`.

- **Playlist**: index is the position in the playlist (zero-padded to the playlist size).
- **Single / Multiple**: index is the position of the link in your list (`01`, `02`, ...).

## Requirements

Works on **Linux, Windows and macOS** (tested on Windows; Linux steps are the ones used originally).

| Requirement | Why | Linux (Debian/Ubuntu) | Windows |
| ----------- | --- | --------------------- | ------- |
| Python 3.9+ | runs the tool | `sudo apt install python3 python3-pip` | `winget install Python.Python.3.13` |
| `yt-dlp[default]` | the downloader and its default extras | pip (see Setup) | pip (see Setup) |
| FFmpeg | audio conversion, merging video + audio | `sudo apt install ffmpeg` | `winget install Gyan.FFmpeg` |
| Deno or Node.js | JavaScript runtime yt-dlp needs for YouTube | https://deno.com or https://nodejs.org | `winget install DenoLand.Deno` or `OpenJS.NodeJS.LTS` |
| `secretstorage`, `jeepney` | read encrypted browser cookies | pip (Linux only) | not needed |
| `python3-secretstorage python3-dbus python3-jeepney` | system versions of those cookie libraries | `sudo apt install ...` | not needed |

FFmpeg and Deno/Node must be on `PATH`. Open a new terminal after installing them.

## Setup

### Linux

```bash
sudo apt update
sudo apt install python3-secretstorage python3-dbus python3-jeepney -y
python3 -m pip install -U "yt-dlp[default]" secretstorage jeepney
# install FFmpeg and Deno (or Node.js), make sure they are on PATH
python3 -m pip install .          # gives you the `ytdl` command
```

### Windows (PowerShell)

```powershell
winget install Python.Python.3.13 Gyan.FFmpeg DenoLand.Deno
# open a new terminal, then from the project folder:
python -m pip install .           # gives you the `ytdl` command
```

`pip install .` also installs `yt-dlp[default]`; the cookie libraries are installed on Linux only.

### Cookies

- **Linux**: read through the keyring; use `--browser brave+gnomekeyring` if auto-detection fails.
- **Windows**: close the browser first (its cookie file is locked). Recent Chrome/Edge may not be readable;
  use Firefox or Brave, or no cookies.
- **macOS**: allow Keychain access when asked.

## Use

Run `ytdl` and answer the prompts: folder, playlist/single/multiple, video/audio, format, link(s), cookies, confirm.
Any prompt can be skipped with a flag:

```bash
ytdl --dir ~/Music/YouTube --mode single --kind audio --format mp3 --url "<link>" --browser brave -y
ytdl --mode multiple --kind audio --format mp3 --file links.txt
ytdl --mode playlist --kind video --format 720 --url "<playlist link>"
```

| Flag | Values |
| ---- | ------ |
| `--dir` | download folder (default: current) |
| `--mode` | `playlist`, `single`, `multiple` |
| `--kind` | `video`, `audio` |
| `--format` | audio: `mp3`, `mp3-192`, `m4a`, `opus`, `flac`, `wav`, `original`. video: `best`, `1080`, `720`, `480`, `360`, `best-mkv` |
| `--url` | link, repeatable |
| `--file` | text file, one link per line (`#` comments allowed) |
| `--browser` | `brave`, `chrome`, `chromium`, `edge`, `firefox`, ... optional `+KEYRING` / `:PROFILE`; `none` to disable. Default: env `YTDL_BROWSER`, else asked |
| `--js-runtime` | `auto` (deno, then node), `deno`, `node`, `none` |
| `-y` | skip confirmation |

Exit code: `0` all downloaded, `1` some failed, `130` cancelled.

## Distribute

| Goal | Command |
| ---- | ------- |
| Install from source | `pipx install .` or `pip install .` |
| Build a wheel to share | `python -m pip install build` then `python -m build`; install with `pip install dist/ytdl_cli-*.whl` |
| Standalone executable | `pip install pyinstaller` then `pyinstaller --onefile -n ytdl ytdl/__main__.py` (build on each OS: `ytdl` / `ytdl.exe`) |

FFmpeg and Deno/Node must be installed on every target machine, including for the standalone executable.
## Layout

```text
ytdl/cli.py          entry point: flags + interactive flow
ytdl/prompt.py       numbered menus and prompts (stdlib only)
ytdl/options.py      format presets, link/cookie parsing, yt-dlp option building (no network)
ytdl/downloader.py   runs yt-dlp per link, collects failures
pyproject.toml       packaging, `ytdl` command, dependencies
```

## Notes

- Re-running skips files that already exist (yt-dlp behaviour).
- In a playlist, a failing video is skipped and the rest continue.
- Keep yt-dlp current (`python3 -m pip install -U "yt-dlp[default]"`); YouTube changes often.
- Only download content you have the right to download.
- Development was done offline: menus, option building and argument handling were checked without
  contacting any site. The first real download is the first network use.

## Possible next improvements

- Download archive (`--download-archive`) to skip videos fetched in earlier runs.
- Embed thumbnail and metadata in MP3/M4A, optional subtitles for video.
- Start/end index for playlists and a parallel-download option.
- Remember last folder/format in a small config file.
- Show a real format list per video (`-F` style) for advanced users.
