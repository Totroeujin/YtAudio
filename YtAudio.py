import argparse
import yt_dlp
import os
import sys

def print_status(d):
    if d['status'] == 'downloading':
        print(f"[DOWNLOADING] {d.get('_percent_str', '').strip()} - ETA {d.get('_eta_str', '')}", end="\r")
    elif d['status'] == 'finished':
        print("\n[INFO] Download complete, converting...")
    elif d['status'] == 'error':
        print("\n[ERROR] Something went wrong.")

def download_audio(url, fmt, output_folder, playlist):
    os.makedirs(output_folder, exist_ok=True)

    # yt-dlp config
    ydl_opts = {
        "outtmpl": f"{output_folder}/%(title)s.%(ext)s",
        "format": "bestaudio/best",
        "noplaylist": not playlist,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": fmt,
                "preferredquality": "192",
            }
        ],
        "progress_hooks": [print_status],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def parse_args():
    parser = argparse.ArgumentParser(
        description="YtAudio - Download YouTube audio as MP3/M4A/OPUS",
    )

    parser.add_argument(
        "url",
        help="The YouTube video or playlist URL"
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["mp3", "m4a", "opus"],
        default="mp3",
        help="Audio format to convert into (default: mp3)"
    )

    parser.add_argument(
        "--output",
        "-o",
        default="downloads",
        help="Output folder (default: downloads)"
    )

    parser.add_argument(
        "--playlist",
        action="store_true",
        help="Download as playlist (default: off)"
    )

    return parser.parse_args()

def main():
    args = parse_args()

    print(f"\n[YtAudio] Starting download...")
    print(f"- URL: {args.url}")
    print(f"- Format: {args.format}")
    print(f"- Output folder: {args.output}")
    print(f"- Playlist mode: {args.playlist}\n")

    try:
        download_audio(
            url=args.url,
            fmt=args.format,
            output_folder=args.output,
            playlist=args.playlist,
        )
        print("\n[✓] Done!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
