import wx
import yt_dlp
try:
    import ytdlp_jsc  # noqa: F401
except ImportError:
    ytdlp_jsc = None
import threading
from pathlib import Path
import re
import os
import sys
import shutil

# Strip ANSI escape codes (color/formatting from yt_dlp) that the status bar can't render
# Handles both full form (\x1b[0m) and true-color form (\x1b[38;2;R;G;Bm)
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Safely prepend the path so local ffmpeg takes priority
    os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ.get("PATH", "")

def _strip_ansi(text: str) -> str:
    if not isinstance(text, str):
        return text or ''
    return _ANSI_RE.sub('', text)


class DownloadProgress:
    """Thread-safe download progress tracker.
    
    Stores status updates that are read by the main thread via OnUpdateUI.
    This avoids calling wx functions from background threads.
    """
    def __init__(self):
        self.message = ""
        self.is_downloading = False
        self.percent = 0  # 0..100 for wx.Gauge

    def __call__(self, d):
        if d['status'] == 'downloading':
            pct_str = d.get('_percent_str', '')
            eta_str = d.get('_eta_str', '')
            self.message = f"Downloading: {pct_str} - ETA {eta_str}"
            # Extract numeric percentage for the gauge (yt_dlp may give "10.50%")
            if pct_str and '%' in pct_str:
                try:
                    self.percent = int(float(pct_str.split('%')[0].strip().replace(',', '').replace(' ', '')))
                except ValueError:
                    pass
            self.is_downloading = True
        elif d['status'] == 'finished':
            self.message = "Conversion complete!"
            self.percent = 100
            self.is_downloading = False
        elif d['status'] == 'error':
            self.message = f"Error: {d.get('msg', 'Unknown')}"
            self.percent = 0
            self.is_downloading = False


class MainFrame(wx.Frame):
    def __init__(self, parent, title="YtAudio GUI"):
        super().__init__(parent, title=title)
        self.CreateStatusBar()
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Threading lock & download guard
        self._download_lock = threading.Lock()
        self._is_downloading = False
        
        # Progress tracker for main-thread UI updates
        self._progress = DownloadProgress()

        # Create controls
        self.url_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.format_choice = wx.Choice(self, choices=["mp3", "m4a", "opus", "mp4"])
        self.resolution_choice = wx.Choice(self, choices=["best", "720p", "1080p", "1440p", "2160p"])
        self.output_path = wx.TextCtrl(self)
        self.output_button = wx.Button(self, label="Browse")
        self.playlist_checkbox = wx.CheckBox(self, label="Download as playlist")
        self.start_button = wx.Button(self, label="Download")
        self.paste_button = wx.Button(self, label="Paste")

        # Progress bar (wx.Gauge) — initially at 0%
        self.gauge = wx.Gauge(self, range=100, size=(250, 20))

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        url_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_sizer.Add(wx.StaticText(self, label="URL:"), 0, wx.ALL, 5)
        url_sizer.Add(self.url_input, 1, wx.EXPAND | wx.ALL, 5)
        url_sizer.Add(self.paste_button, 0, wx.ALL, 5)
        sizer.Add(url_sizer, 0, wx.EXPAND)

        format_sizer = wx.BoxSizer(wx.HORIZONTAL)
        format_sizer.Add(wx.StaticText(self, label="Format:"), 0, wx.ALL, 5)
        format_sizer.Add(self.format_choice, 0, wx.ALL, 5)
        format_sizer.Add(wx.StaticText(self, label="Resolution:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        format_sizer.Add(self.resolution_choice, 0, wx.ALL, 5)
        sizer.Add(format_sizer, 0, wx.EXPAND)

        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        output_sizer.Add(wx.StaticText(self, label="Output:"), 0, wx.ALL, 5)
        output_sizer.Add(self.output_path, 1, wx.EXPAND | wx.ALL, 5)
        output_sizer.Add(self.output_button, 0, wx.ALL, 5)
        sizer.Add(output_sizer, 0, wx.EXPAND)

        sizer.Add(self.playlist_checkbox, 0, wx.ALL, 5)
        sizer.Add(self.start_button, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(self.gauge, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        # Initialize settings
        self.url_input.Bind(wx.EVT_TEXT_ENTER, self.on_start)
        self.format_choice.SetSelection(0)
        self.resolution_choice.SetSelection(0)
        self.resolution_choice.Enable(False)
        self.output_path.SetValue(str(Path.home() / "downloads"))
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start)
        self.output_button.Bind(wx.EVT_BUTTON, self.on_browse)
        self.paste_button.Bind(wx.EVT_BUTTON, self.on_paste)
        self.format_choice.Bind(wx.EVT_CHOICE, self.on_format_change)
        
        # Periodic UI update for status bar (runs on main thread)
        self.Bind(wx.EVT_IDLE, self.on_idle)

    def on_idle(self, event):
        """Read progress from background thread and update status bar & gauge safely."""
        msg = self._progress.message
        if msg:
            # Strip ANSI escape codes (e.g. [0m, [32m) that yt_dlp injects for color
            self.SetStatusText(_strip_ansi(msg))
            # Reset message after showing once to avoid flickering
            self._progress.message = ""
        
        # Update the gauge with current percentage
        pct = self._progress.percent
        if self._progress.is_downloading or pct > 0:
            self.gauge.SetValue(pct)

        event.Skip()

    def on_paste(self, event):
        if wx.TheClipboard.Open():
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    self.url_input.SetValue(data.GetText())
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Could not access clipboard", "Error", wx.OK)

    def on_format_change(self, event):
        fmt = self.format_choice.GetString(self.format_choice.GetSelection())
        self.resolution_choice.Enable(fmt == "mp4")

    def on_browse(self, event):
        dialog = wx.DirDialog(self, "Choose output folder", style=wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.output_path.SetValue(dialog.GetPath())
        dialog.Destroy()

    def on_start(self, event):
        # Guard against multiple simultaneous downloads
        with self._download_lock:
            if self._is_downloading:
                wx.MessageBox("A download is already in progress!", "Warning", wx.OK | wx.ICON_WARNING)
                return
            
            url = self.url_input.GetValue().strip()
            if not url:
                wx.MessageBox("Please enter a YouTube URL", "Error", wx.OK)
                return

            # Mark as downloading before spawning thread
            self._is_downloading = True
            self.start_button.Enable(False)  # Disable button during download

        format_name = self.format_choice.GetString(self.format_choice.GetSelection())
        resolution = self.resolution_choice.GetString(self.resolution_choice.GetSelection())
        output = self.output_path.GetValue().strip()
        playlist = self.playlist_checkbox.GetValue()

        # Start download thread (daemon=True so it doesn't block app exit)
        threading.Thread(
            target=self.download_audio,
            args=(url, format_name, output, playlist, resolution),
            daemon=True
        ).start()

    def download_audio(self, url, fmt, output_folder, playlist, resolution):
        # Use a temp directory so intermediate files never leak into user's output folder
        import tempfile
        with tempfile.TemporaryDirectory(prefix="ytaudio_") as tmp_dir:
            try:
                if fmt == "mp4":
                    format_selector = self._build_video_format(resolution)
                    ydl_opts = {
                        "outtmpl": f"{tmp_dir}/%(title)s.%(ext)s",
                        "format": format_selector,
                        "merge_output_format": "mp4",
                        "nocheckcertificate": True,
                        "noplaylist": not playlist,
                        "progress_hooks": [self._progress],
                    }
                else:
                    ydl_opts = {
                        "outtmpl": f"{tmp_dir}/%(title)s.%(ext)s",
                        "format": "bestaudio/best",
                        "nocheckcertificate": True,
                        "noplaylist": not playlist,
                        "postprocessors": [
                            {
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": fmt,
                                "preferredquality": "192",
                            }
                        ],
                        "progress_hooks": [self._progress],
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # After successful extraction, copy the final file(s) to output_folder
                ext_pattern = "*.mp4" if fmt == "mp4" else f"*.{fmt}"
                downloaded_files = list(Path(tmp_dir).glob(ext_pattern))
                output_path = Path(output_folder)
                output_path.mkdir(parents=True, exist_ok=True)

                for downloaded_file in downloaded_files:
                    dest = output_path / downloaded_file.name
                    shutil.move(str(downloaded_file), str(dest))
                    wx.CallAfter(self.SetStatusText, f"Saved to: {dest}")

                wx.CallAfter(self._show_success, "Download completed successfully!")
            except Exception as e:
                wx.CallAfter(self._show_error, f"Download failed: {str(e)}")
            finally:
                # Always re-enable button and reset state (on main thread)
                wx.CallAfter(self._on_download_finished)

    def _build_video_format(self, resolution):
        if resolution == "best":
            return "bestvideo+bestaudio/best"

        height_map = {
            "720p": 720,
            "1080p": 1080,
            "1440p": 1440,
            "2160p": 2160,
        }
        max_height = height_map.get(resolution, None)
        if max_height is None:
            return "bestvideo+bestaudio/best"

        return f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best"

    def _show_success(self, msg):
        self.SetStatusText(msg)
        wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)

    def _show_error(self, msg):
        self.SetStatusText(msg)
        wx.MessageBox(msg, "Error", wx.OK | wx.ICON_ERROR)

    def _on_download_finished(self):
        """Called on main thread when download finishes (success or error)."""
        self._is_downloading = False
        self._progress.percent = 0
        self.gauge.SetValue(0)
        self.start_button.Enable()

    def on_close(self, event):
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame(None)
    frame.Show()
    app.MainLoop()


