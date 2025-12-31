
"""
ytdl.py — Simple YouTube video/audio downloader using yt-dlp.

Usage examples:
  # Download best MP4 video + audio
  python ytdl.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ~/Downloads

  # Download audio only as MP3
  python ytdl.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --audio --audio-format mp3 -o ~/Music

  # Download an entire playlist as M4A
  python ytdl.py "https://www.youtube.com/playlist?list=PL..." --audio --audio-format m4a -o ./downloads

Notes:
- Requires: yt-dlp (Python) and ffmpeg installed on your system for audio conversions.
- Respect copyright & platform Terms of Service. Only download content you own or have permission to save.
"""
import argparse
import os
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp is not installed. Install with:\n  pip install -U yt-dlp\nor (macOS) brew install yt-dlp", file=sys.stderr)
    sys.exit(1)


def progress_hook(d):
    if d.get('status') == 'downloading':
        pct = d.get('_percent_str', '').strip()
        spd = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        line = f"\rDownloading: {pct:>6}  Speed: {spd:>8}  ETA: {eta:>6}"
        print(line, end='', flush=True)
    elif d.get('status') == 'finished':
        print("\nDownload finished, post-processing...")


def build_opts(args):
    # Output template
    outtmpl = os.path.join(os.path.expanduser(args.output), args.template)

    # Base options
    opts = {
        "outtmpl": {"default": outtmpl},
        "noplaylist": not args.allow_playlist,
        "nocheckcertificate": True,
        "progress_hooks": [progress_hook],
        "restrictfilenames": args.safe_names,
        "ignoreerrors": args.ignore_errors,
        "concurrent_fragment_downloads": args.concurrent,
        "quiet": args.quiet,
        "no_warnings": args.quiet,
    }

    # Format selection
    if args.audio:
        # Best audio; convert with ffmpeg to selected format
        opts["format"] = "bestaudio/best"
        post = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": args.audio_format,
            "preferredquality": str(args.audio_quality),
        }]
        # Optionally embed metadata & thumbnail
        if args.embed_meta:
            post.append({"key": "FFmpegMetadata"})
        if args.embed_thumb:
            post.append({"key": "EmbedThumbnail"})
        opts["postprocessors"] = post
    else:
        # Prefer MP4 video+audio, fallback to best
        # If resolution provided, try to honor it.
        if args.resolution:
            # Prefer the closest matching height with mp4 container if possible
            fmt = f"bestvideo[ext=mp4][height<={args.resolution}]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        opts["format"] = fmt

        # Merge using ffmpeg to MP4 if needed
        opts["merge_output_format"] = "mp4"

        if args.embed_meta:
            opts.setdefault("postprocessors", []).append({"key": "FFmpegMetadata"})
        if args.embed_thumb:
            opts.setdefault("postprocessors", []).append({"key": "EmbedThumbnail"})

    # Network/retry
    opts.update({
        "retries": args.retries,
        "file_access_retries": args.retries,
        "fragment_retries": args.retries,
        "socket_timeout": args.timeout,
    })

    return opts


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Download YouTube videos or audio with yt-dlp.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("url", help="Video or playlist URL")
    p.add_argument("-o", "--output", default="./downloads", help="Output directory")
    p.add_argument("-t", "--template", default="%(title)s.%(ext)s", help="Filename template (yt-dlp outtmpl)")
    p.add_argument("-q", "--quiet", action="store_true", help="Reduce yt-dlp output (show only our progress lines)")

    # Mode
    m = p.add_mutually_exclusive_group()
    m.add_argument("--audio", action="store_true", help="Download audio only")
    m.add_argument("--video", action="store_true", help="Download video (default)")

    # Audio options
    p.add_argument("--audio-format", default="mp3", choices=["mp3", "m4a", "aac", "opus", "vorbis", "wav", "flac"], help="Audio format when using --audio")
    p.add_argument("--audio-quality", default=0, type=int, help="Audio bitrate/quality for conversion (0=best)")

    # Video options
    p.add_argument("-r", "--resolution", type=int, help="Max video height (e.g., 1080)")

    # Misc
    p.add_argument("--allow-playlist", action="store_true", help="Allow playlist downloads")
    p.add_argument("--safe-names", action="store_true", help="Restrict file names to ASCII and safe characters")
    p.add_argument("--ignore-errors", action="store_true", help="Continue on download errors in playlists")
    p.add_argument("--embed-meta", action="store_true", help="Embed metadata tags")
    p.add_argument("--embed-thumb", action="store_true", help="Embed thumbnail into media file (needs ffmpeg)")
    p.add_argument("--retries", type=int, default=5, help="Number of retries for network errors")
    p.add_argument("--timeout", type=int, default=30, help="Socket timeout in seconds")
    p.add_argument("--concurrent", type=int, default=4, help="Concurrent fragment downloads for DASH/HLS")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Ensure output dir exists
    outdir = Path(os.path.expanduser(args.output))
    outdir.mkdir(parents=True, exist_ok=True)

    # Build options
    ydl_opts = build_opts(args)

    # Run download
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(args.url, download=True)
    except yt_dlp.utils.DownloadError as e:
        print(f"\nDownloadError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    # Print a simple summary
    # info can be a dict (single) or a playlist dict with 'entries'
    def summarize(entry):
        title = entry.get('title', 'Unknown Title')
        fn = ydl.prepare_filename(entry)
        return f"Saved: {title}\n -> {fn}"

    if info is None:
        print("Nothing was downloaded.")
    elif info.get('_type') == 'playlist':
        print(f"\nPlaylist: {info.get('title','(unknown)')}")
        for e in info.get('entries', []):
            if e:
                print(summarize(e))
    else:
        print("\n" + summarize(info))


if __name__ == "__main__":
    main()
