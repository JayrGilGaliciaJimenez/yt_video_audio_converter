## ytdl.py — simple YouTube downloader

`ytdl.py` wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download YouTube videos or extract audio with a single command. It picks sensible defaults (MP4 for video, MP3 for audio), shows a clean progress line, and supports playlists, thumbnails, and metadata embedding.

## Requirements
- Python 3.8+
- `yt-dlp` (install via `pip install -r requirements.txt`)
- `ffmpeg` (needed for merging and audio conversion; e.g., `brew install ffmpeg` on macOS)

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
- Download best MP4 video + audio to `~/Downloads`:
  ```bash
  python ytdl.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ~/Downloads
  ```
- Download audio only as MP3 to `~/Music`:
  ```bash
  python ytdl.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --audio --audio-format mp3 -o ~/Music
  ```
- Download an entire playlist as M4A:
  ```bash
  python ytdl.py "https://www.youtube.com/playlist?list=PL..." --audio --audio-format m4a --allow-playlist -o ./downloads
  ```
- Limit video resolution (max height):
  ```bash
  python ytdl.py "https://www.youtube.com/watch?v=..." -r 1080
  ```

## Common flags
- `--audio` / `--video` — choose audio-only or video (default).
- `--audio-format mp3|m4a|aac|opus|vorbis|wav|flac` — target audio codec when using `--audio`.
- `--audio-quality 0` — bitrate/quality for audio conversion (`0` = best).
- `-r/--resolution` — maximum video height (e.g., `1080`).
- `--allow-playlist` — allow playlist URLs (otherwise treated as single).
- `--embed-meta` / `--embed-thumb` — add metadata or thumbnails (needs ffmpeg).
- `--safe-names` — restrict file names to ASCII/safe characters.
- `--ignore-errors` — continue when some playlist items fail.
- `--template` — filename template (defaults to `%(title)s.%(ext)s`).

## Notes
- Output directory defaults to `./downloads`; it is created if missing.
- Progress shows as a single updating line; yt-dlp logs are suppressed with `--quiet`.
- Only download content you own or have permission to save, and obey the source platform's Terms of Service.
