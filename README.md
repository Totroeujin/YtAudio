# YtAudio GUI

Download YouTube audio offline with a simple GUI interface.

## Features

- Paste YouTube URL directly from clipboard
- Choose audio format (MP3/M4A/OPUS)
- Select output folder
- Playlist mode support
- Download progress bar

## Installation

```bash
pip install -r requirements.txt
```

### System Dependencies

You must have **[ffmpeg](https://ffmpeg.org/)** installed on your system. yt-dlp relies on it for audio extraction and conversion.

- **Windows:** `winget install ffmpeg` or download from https://www.gyan.dev/ffmpeg/builds/
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg` (Debian/Ubuntu) or equivalent for your distro

## Usage

### GUI

```bash
python YtAudioGUI.py
```

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

Build the GUI as a standalone executable with PyInstaller:

```bash
pyinstaller --onefile --windowed --name=YtAudioGUI YtAudioGUI.py
```

or

```bash
pyinstaller --onefile --windowed --name=YtAudioGUI --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." YtAudioGUI.py
```

The resulting binary includes all dependencies and runs on Windows, macOS, and Linux.