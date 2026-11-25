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

### Linux (the steps we did)

```bash
# 1. system packages for reading browser cookies
sudo apt update
sudo apt install python3-secretstorage python3-dbus python3-jeepney -y

# 2. yt-dlp and the cookie libraries
python3 -m pip install -U "yt-dlp[default]" secretstorage jeepney

# 3. FFmpeg and Deno (or Node.js) installed and available on PATH

# 4. this tool (from the project folder)
python3 -m pip install .          # gives you the `ytdl` command
```

### Windows (PowerShell)

```powershell
winget install Python.Python.3.13 Gyan.FFmpeg DenoLand.Deno
# new terminal, then from the project folder:
python -m pip install .           # gives you the `ytdl` command
```

`pip install .` pulls `yt-dlp[default]` automatically; the Linux cookie libraries are only installed on Linux.
Without installing: `python -m pip install "yt-dlp[default]"` then `python -m ytdl`.

### Internal package index (company network)

If your pip is set up for an internal repository (JFrog Artifactory or similar), nothing special is needed:
`pip install .` uses it through your pip configuration. To set it explicitly for one command:

```bash
python -m pip install . --index-url <your internal PyPI simple URL>
```

Keep the URL in your user pip config (`pip config set global.index-url ...`), not in this repository.

### Cookies on each system

- **Linux**: Brave/Chrome cookies are read through the keyring; use `--browser brave+gnomekeyring` if auto-detection fails.
- **Windows**: close the browser before downloading, otherwise its cookie database is locked. Recent Chrome and
  Edge versions use encryption that yt-dlp may not be able to read; if so, use Firefox or Brave, or choose "No cookies".
- **macOS**: the system asks for Keychain access the first time.
Your original command, for comparison, is what the tool runs for you:

```bash
yt-dlp --cookies-from-browser brave --js-runtimes deno \
  -x --audio-format mp3 --audio-quality 0 \
  -o "$HOME/Music/YouTube/%(title)s.%(ext)s" "<url>" ...
```

## Use

### Interactive

Run `ytdl`. You are asked, in order: download folder, playlist/single/multiple, video/audio, format,
link(s), browser cookies, then a summary to confirm.

**Audio formats**: `mp3` (best, VBR 0), `mp3-192`, `m4a`, `opus`, `flac`, `wav`, `original` (no conversion).
**Video formats**: `best` (MP4), `1080`, `720`, `480`, `360` (MP4, up to that height), `best-mkv`.

For *Multiple*, paste one link per line and finish with an empty line.

### With flags

Anything not given as a flag is asked.

```bash
ytdl --dir ~/Music/YouTube --mode single --kind audio --format mp3 \
     --url "https://www.youtube.com/watch?v=CvP_hfZvH0o" --browser brave -y

ytdl --mode multiple --kind audio --format mp3 --file links.txt --browser brave+gnomekeyring

ytdl --mode playlist --kind video --format 720 --url "https://www.youtube.com/playlist?list=..."
```

| Flag | Meaning |
| ---- | ------- |
| `--dir` | download folder (default: current folder) |
| `--mode` | `playlist`, `single`, `multiple` |
| `--kind` | `video`, `audio` |
| `--format` | format key from the lists above |
| `--url` | a link; repeat for several |
| `--file` | text file with one link per line (`#` comments allowed) |
| `--browser` | `brave`, `chrome`, `chromium`, `edge`, `firefox`, ... Optional `+KEYRING` and `:PROFILE`, e.g. `brave+gnomekeyring`, `chrome:Profile 1`. `none` disables. Default: env `YTDL_BROWSER`, else asked |
| `--js-runtime` | `auto` (deno, then node), `deno`, `node`, `none` |
| `-y`, `--yes` | skip the confirmation |

Exit code is `0` when everything downloaded, `1` if any link failed, `130` if cancelled.
Set `YTDL_BROWSER=brave` once (e.g. in `~/.bashrc`) to stop being asked about cookies.

## Distribute

- **pip / pipx**: `pipx install .` (or `pip install .`). To share, build a wheel with
  `python3 -m pip install build && python3 -m build`, then install `dist/*.whl` anywhere.
- **Single executable (no Python needed)**: `pip install pyinstaller && pyinstaller --onefile -n ytdl ytdl/__main__.py`\n  (run it on each OS you target: gives `ytdl` on Linux and `ytdl.exe` on Windows).
  FFmpeg and Deno/Node still have to be installed on the target machine.

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
