"""Runs yt-dlp. The only module that imports yt_dlp (lazily) and touches the network."""

from __future__ import annotations

from typing import List, Tuple

from ytdl.options import Format, build_ydl_opts, output_template


def run_downloads(
    *,
    urls: List[str],
    mode: str,
    kind: str,
    fmt: Format,
    folder: str,
    browser,
    js_runtime,
) -> List[Tuple[str, str]]:
    """Download every URL. Returns a list of (url, error message) for failures."""
    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
    except ImportError:
        raise SystemExit("yt-dlp is not installed. Run:  python3 -m pip install -U \"yt-dlp[default]\"")

    failures: List[Tuple[str, str]] = []
    total = len(urls)
    for i, url in enumerate(urls, 1):
        print(f"\n  [{i}/{total}] {url}")
        opts = build_ydl_opts(
            kind=kind,
            fmt=fmt,
            mode=mode,
            folder=folder,
            template=output_template(mode, i, total),
            browser=browser,
            js_runtime=js_runtime,
        )
        try:
            with YoutubeDL(opts) as ydl:
                code = ydl.download([url])
            if code:
                failures.append((url, "yt-dlp reported errors (see above)"))
        except DownloadError as err:
            failures.append((url, str(err)))
        except KeyboardInterrupt:
            print("\n  Interrupted.")
            failures.append((url, "interrupted"))
            break
    return failures
