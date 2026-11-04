# YtAudio GUI

Download YouTube audio offline with a simple GUI interface.

## Features

- Paste YouTube URL directly from clipboard
- Choose audio format (MP3/M4A/OPUS) or download video as MP4
- Select MP4 resolution (best / 720p / 1080p / 1440p / 2160p)
- Select output folder
- Playlist mode support with a configurable item limit (default: 50)
- Download progress bar
- Recover completed downloads from abandoned temporary folders before a new download

## Installation

```bash
pip install -r requirements.txt
```

### System Dependencies

FFmpeg is required for audio conversion and video merging. The GUI uses `ffmpeg.exe` and `ffprobe.exe` when they are bundled with the Windows executable; when running from Python, install FFmpeg and make both tools available on `PATH`.

YouTube extraction also requires a supported JavaScript runtime. `requirements.txt` installs yt-dlp with its default dependencies, including the EJS challenge scripts. Install [Deno](https://docs.deno.com/runtime/getting_started/installation/) and make it available on `PATH`; yt-dlp recommends Deno. The project also installs `ytdlp-jsc`, but it does not replace the runtime requirement.

- **Windows:** `winget install ffmpeg` or download from https://www.gyan.dev/ffmpeg/builds/
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg` (Debian/Ubuntu) or equivalent for your distro

## Usage

### GUI

```bash
python YtAudioGUI.py
```

Check **Download as playlist** to download a playlist. The **Max items** control limits that GUI download (default: 50, range: 1–1000). If a previous run was interrupted, the next download recovers completed media files from old YtAudio temporary folders into the selected output folder and removes leftover temporary files.

### Command-Line Interface

```bash
python YtAudio.py "https://youtube.com/watch?v=VIDEO_ID"

# Specify format and output directory
python YtAudio.py "https://youtube.com/watch?v=VIDEO_ID" -f opus -o ~/music

# Download an entire playlist
python YtAudio.py "https://youtube.com/playlist?list=PLAYLIST_ID" --playlist
```

**CLI Arguments:**

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `url` (positional) | — | *(required)* | YouTube video or playlist URL |
| `--format`, `-f` | — | `mp3` | Audio format: `mp3`, `m4a`, `opus` |
| `--output`, `-o` | — | `downloads` | Output folder path |
| `--playlist` | — | `false` | Download all videos in a playlist |

## Build Executable

Build the Windows executable from a Windows machine, using the same Python environment where the project requirements are installed. Install PyInstaller first:

```powershell
python -m pip install pyinstaller
```

Place `ffmpeg.exe` and `ffprobe.exe` in the project directory, then run:

```powershell
python -m PyInstaller --clean --onefile --windowed --name YtAudioGUI --hidden-import=ytdlp_jsc --collect-all yt_dlp_ejs --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." YtAudioGUI.py
```

The executable is created at `dist\YtAudioGUI.exe`. This command bundles FFmpeg and yt-dlp's EJS scripts, but does not bundle Deno; install Deno on each target computer and make it available on `PATH`. PyInstaller builds are platform-specific, so create separate builds on Windows, macOS, and Linux with the appropriate FFmpeg binaries for each platform.