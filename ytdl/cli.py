"""Command-line entry point: interactive menus, or flags for everything."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from ytdl import __version__, prompt
from ytdl.options import (
    BROWSERS,
    KINDS,
    MODES,
    detect_js_runtime,
    find_format,
    formats_for,
    has_ffmpeg,
    parse_browser,
    parse_urls,
    read_url_file,
)

DESCRIPTION = """\
Download YouTube videos or audio with yt-dlp.
Run without arguments for the interactive menu. Any value not given as a flag is asked.
Files are saved as  <index>_<title>.<ext>  (e.g. 01_My Song.mp3).
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ytdl", description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", help="download folder (default: current folder)")
    p.add_argument("--mode", choices=[m for _, m in MODES], help="playlist | single | multiple")
    p.add_argument("--kind", choices=[k for _, k in KINDS], help="video | audio")
    p.add_argument("--format", dest="fmt", help="format key. audio: mp3, mp3-192, m4a, opus, flac, wav, original; "
                   "video: best, 1080, 720, 480, 360, best-mkv")
    p.add_argument("--url", action="append", default=[], help="video/playlist link (repeat for several)")
    p.add_argument("--file", help="text file with one link per line (# comments allowed)")
    p.add_argument("--browser", help=f"take cookies from a browser: {', '.join(BROWSERS)}; optional +KEYRING and :PROFILE, "
                   "e.g. brave+gnomekeyring. Use 'none' to disable. Default: env YTDL_BROWSER or none")
    p.add_argument("--js-runtime", default="auto", choices=["auto", "deno", "node", "none"],
                   help="JavaScript runtime for YouTube (default: auto = deno, then node)")
    p.add_argument("-y", "--yes", action="store_true", help="do not ask for confirmation")
    p.add_argument("--version", action="version", version=f"ytdl {__version__}")
    return p


def resolve_folder(value: Optional[str]) -> str:
    default = os.getcwd()
    raw = value if value else prompt.ask("Download folder", default)
    raw = raw.strip().strip("\"'")  # Windows "Copy as path" / drag-and-drop adds quotes
    folder = os.path.abspath(os.path.expanduser(os.path.expandvars(raw)))
    os.makedirs(folder, exist_ok=True)
    if not os.access(folder, os.W_OK):
        raise SystemExit(f"  Folder is not writable: {folder}")
    return folder


def collect_urls(mode: str, given: List[str], file: Optional[str]) -> List[str]:
    urls = parse_urls(" ".join(given))
    if file:
        urls += [u for u in read_url_file(file) if u not in urls]
    if not urls:
        if mode == "multiple":
            urls = parse_urls(" ".join(prompt.ask_lines("Paste the video links, one per line")))
        else:
            label = "Playlist link" if mode == "playlist" else "Video link"
            urls = parse_urls(prompt.ask(label))
    if not urls:
        raise SystemExit("  No valid http(s) links given.")
    if mode != "multiple" and len(urls) > 1:
        print(f"  Mode '{mode}' uses one link; using the first one. Pick 'multiple' for several links.")
        urls = urls[:1]
    return urls


def run(args: argparse.Namespace) -> int:
    print("\n  ytdl - YouTube downloader")

    folder = resolve_folder(args.dir)
    mode = args.mode or prompt.menu("What do you want to download?", MODES)
    kind = args.kind or prompt.menu("Video or audio?", KINDS)

    if args.fmt:
        fmt = find_format(kind, args.fmt)
        if not fmt:
            keys = ", ".join(f.key for f in formats_for(kind))
            raise SystemExit(f"  Unknown {kind} format '{args.fmt}'. Choose one of: {keys}")
    else:
        fmt = prompt.menu(f"Choose the {kind} format", [(f.label, f) for f in formats_for(kind)])

    urls = collect_urls(mode, args.url, args.file)

    browser_spec = args.browser
    if browser_spec is None:
        browser_spec = os.environ.get("YTDL_BROWSER")
    if browser_spec is None:
        choices = [("No cookies", "none")] + [(b, b) for b in BROWSERS[:5]]
        browser_spec = prompt.menu("Use browser cookies? (needed for age/login-restricted videos)", choices)
    try:
        browser = parse_browser(browser_spec)
    except ValueError as err:
        raise SystemExit(f"  {err}")

    if browser and browser[2] and not sys.platform.startswith("linux"):
        print(f"  Note: keyring '{browser[2]}' is Linux-only; ignored on this system.")
        browser = (browser[0], browser[1], None, browser[3])

    js_runtime = detect_js_runtime(args.js_runtime)

    print("\n  Summary")
    print(f"    Folder  : {folder}")
    print(f"    Mode    : {mode}  ({len(urls)} link{'s' if len(urls) != 1 else ''})")
    print(f"    Type    : {kind} - {fmt.label}")
    print(f"    Cookies : {browser_spec if browser else 'none'}")
    print(f"    JS      : {js_runtime or 'none found (some videos may fail)'}")
    if not has_ffmpeg() and not (kind == "audio" and not fmt.codec):
        print("    WARNING : ffmpeg not found on PATH - conversion/merging will fail.")

    if not args.yes and not prompt.confirm("Start download?"):
        print("  Cancelled.")
        return 0

    from ytdl.downloader import run_downloads

    failures = run_downloads(urls=urls, mode=mode, kind=kind, fmt=fmt, folder=folder,
                             browser=browser, js_runtime=js_runtime)
    print()
    if failures:
        print(f"  Done with {len(failures)} failure(s):")
        for url, msg in failures:
            print(f"    - {url}\n      {msg}")
        return 1
    print(f"  Done. Files are in {folder}")
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        code = run(args)
    except prompt.Cancelled:
        print("  Cancelled.")
        code = 130
    sys.exit(code)


if __name__ == "__main__":
    main()
