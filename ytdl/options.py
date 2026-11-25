"""Format presets, URL/cookie parsing and yt-dlp option building. No network access here."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

MODES = [
    ("Playlist  - download a whole playlist", "playlist"),
    ("Single    - one video", "single"),
    ("Multiple  - several video links", "multiple"),
]

KINDS = [
    ("Video", "video"),
    ("Audio (extracted with FFmpeg)", "audio"),
]

BROWSERS = ["brave", "chrome", "chromium", "edge", "firefox", "opera", "vivaldi", "safari", "whale"]


@dataclass(frozen=True)
class Format:
    key: str
    label: str
    codec: str = ""        # audio: target codec ("" = keep original stream)
    quality: str = ""      # audio: FFmpeg quality (0 = best VBR for mp3, or a bitrate like 192)
    height: int = 0        # video: max height (0 = no limit)
    container: str = ""    # video: merge container ("" = let yt-dlp decide)


AUDIO_FORMATS: List[Format] = [
    Format("mp3", "MP3  - best quality (VBR 0)", codec="mp3", quality="0"),
    Format("mp3-192", "MP3  - 192 kbps (smaller)", codec="mp3", quality="192"),
    Format("m4a", "M4A  (AAC)", codec="m4a", quality="0"),
    Format("opus", "Opus - best size/quality ratio", codec="opus", quality="0"),
    Format("flac", "FLAC - lossless", codec="flac"),
    Format("wav", "WAV  - uncompressed", codec="wav"),
    Format("original", "Original - best stream, no conversion", codec=""),
]

VIDEO_FORMATS: List[Format] = [
    Format("best", "Best available (MP4)", container="mp4"),
    Format("1080", "Up to 1080p (MP4)", height=1080, container="mp4"),
    Format("720", "Up to 720p (MP4)", height=720, container="mp4"),
    Format("480", "Up to 480p (MP4)", height=480, container="mp4"),
    Format("360", "Up to 360p (MP4)", height=360, container="mp4"),
    Format("best-mkv", "Best available (MKV, any codec)", container="mkv"),
]


def formats_for(kind: str) -> List[Format]:
    return AUDIO_FORMATS if kind == "audio" else VIDEO_FORMATS


def find_format(kind: str, key: str) -> Optional[Format]:
    return next((f for f in formats_for(kind) if f.key == key), None)


# ---------------------------------------------------------------- URLs

def parse_urls(text: str) -> List[str]:
    """Split on whitespace/commas, keep http(s) links, drop duplicates (order kept)."""
    seen, urls = set(), []
    for token in re.split(r"[\s,]+", text):
        if re.match(r"^https?://", token, re.I) and token not in seen:
            seen.add(token)
            urls.append(token)
    return urls


def read_url_file(path: str) -> List[str]:
    with open(path, encoding="utf-8-sig") as fh:
        lines = [ln for ln in fh.read().splitlines() if not ln.strip().startswith("#")]
    return parse_urls("\n".join(lines))


# ---------------------------------------------------------------- cookies

_BROWSER_RE = re.compile(
    r"(?P<name>[^+:]+)(?:\s*\+\s*(?P<keyring>[^:]+))?(?:\s*:\s*(?P<profile>.+?))?(?:\s*::\s*(?P<container>.+))?"
)


def parse_browser(spec: str):
    """'brave', 'brave+gnomekeyring', 'chrome:Profile 1' -> yt-dlp cookiesfrombrowser tuple.

    Returns None for ''/'none'. Raises ValueError for unknown browsers.
    """
    spec = (spec or "").strip()
    if not spec or spec.lower() == "none":
        return None
    m = _BROWSER_RE.fullmatch(spec)
    name = m.group("name").strip().lower() if m else ""
    if not m or name not in BROWSERS:
        raise ValueError(f"Unknown browser '{spec}'. Use one of: {', '.join(BROWSERS)} (optional +KEYRING, :PROFILE).")
    keyring = m.group("keyring")
    return (name, m.group("profile"), keyring.strip().upper() if keyring else None, m.group("container"))


# ---------------------------------------------------------------- JS runtime / tools

def detect_js_runtime(choice: str = "auto") -> Optional[str]:
    """Return 'deno' / 'node' / None. 'auto' prefers deno, then node."""
    choice = (choice or "auto").lower()
    if choice == "none":
        return None
    if choice in ("deno", "node"):
        return choice
    for name in ("deno", "node"):
        if shutil.which(name):
            return name
    return None


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


# ---------------------------------------------------------------- yt-dlp options

def output_template(mode: str, index: int, total: int) -> str:
    """Return the yt-dlp outtmpl: <index>_<title>.<ext>.

    Playlist: yt-dlp's own playlist_index (already zero-padded to the playlist size).
    Single/multiple: position of the link in the list, padded to at least 2 digits.
    """
    if mode == "playlist":
        return "%(playlist_index)s_%(title)s.%(ext)s"
    width = max(2, len(str(total)))
    return f"{index:0{width}d}_%(title)s.%(ext)s"


def format_selector(kind: str, fmt: Format) -> str:
    if kind == "audio":
        return "bestaudio/best"
    if fmt.container == "mkv":
        return "bv*+ba/b"
    h = f"[height<={fmt.height}]" if fmt.height else ""
    # Prefer MP4/M4A streams so no re-encode is needed, fall back to anything.
    return f"bv*{h}[ext=mp4]+ba[ext=m4a]/bv*{h}+ba/b{h}"


def build_ydl_opts(
    *,
    kind: str,
    fmt: Format,
    mode: str,
    folder: str,
    template: str,
    browser: Optional[tuple] = None,
    js_runtime: Optional[str] = None,
) -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "paths": {"home": folder},
        "outtmpl": template,
        "format": format_selector(kind, fmt),
        "noplaylist": mode != "playlist",
        "trim_file_name": 180,
        "ignoreerrors": "only_download" if mode == "playlist" else False,
        "retries": 10,
        "fragment_retries": 10,
    }
    if kind == "audio":
        if fmt.codec:
            pp: Dict[str, Any] = {"key": "FFmpegExtractAudio", "preferredcodec": fmt.codec}
            if fmt.quality:
                pp["preferredquality"] = fmt.quality
            opts["postprocessors"] = [pp]
    elif fmt.container:
        opts["merge_output_format"] = fmt.container
    if browser:
        opts["cookiesfrombrowser"] = browser
    if js_runtime:
        opts["js_runtimes"] = {js_runtime: {}}
    return opts
