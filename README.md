# YtAudio GUI

Download YouTube audio offline with a simple GUI interface.

![GUI Screenshot](gui_screenshot.png)

**Features:**
- Paste YouTube URL directly from clipboard
- Choose audio format (MP3/M4A/OPUS)
- Select output folder
- Playlist mode support
- Download progress bar

**Usage:**
1. Paste YouTube link into URL field
2. Select desired format (default: mp3)
3. Choose output folder (default: ~/downloads)
4. Toggle "Download as playlist" for video playlists
5. Click "Download" to start

**Build Instructions:**
bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name=YtAudioGUI YtAudioGUI.py


**Distributed Executable:**
- Contains all required dependencies
- Runs on Windows/macOS/Linux
- No installation needed