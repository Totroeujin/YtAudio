import wx
import yt_dlp
import threading
from pathlib import Path

class DownloadProgress:
    def __init__(self, frame):
        self.frame = frame
        self.prev_msg = ""

    def __call__(self, d):
        wx.CallAfter(self._update, d)

    def _update(self, d):
        if d['status'] == 'downloading':
            msg = f"[DOWNLOADING] {d.get('_percent_str', '')} - ETA {d.get('_eta_str', '')}"
            if msg != self.prev_msg:
                self.frame.status_bar.SetStatusText(msg, 0)
                self.prev_msg = msg
        elif d['status'] == 'finished':
            self.frame.status_bar.SetStatusText("Conversion complete!", 0)
        elif d['status'] == 'error':
            self.frame.status_bar.SetStatusText(f"[ERROR] {d.get('msg', 'Unknown')}", 0)

class MainFrame(wx.Frame):
    def __init__(self, parent, title="YtAudio GUI"):
        super().__init__(parent, title=title)
        self.CreateStatusBar()
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Create controls
        self.url_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.format_choice = wx.Choice(self, choices=["mp3", "m4a", "opus"])
        self.output_path = wx.TextCtrl(self)
        self.output_button = wx.Button(self, label="Browse")
        self.playlist_checkbox = wx.CheckBox(self, label="Download as playlist")
        self.start_button = wx.Button(self, label="Download")
        self.paste_button = wx.Button(self, label="Paste")

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
        sizer.Add(format_sizer, 0, wx.EXPAND)

        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        output_sizer.Add(wx.StaticText(self, label="Output:"), 0, wx.ALL, 5)
        output_sizer.Add(self.output_path, 1, wx.EXPAND | wx.ALL, 5)
        output_sizer.Add(self.output_button, 0, wx.ALL, 5)
        sizer.Add(output_sizer, 0, wx.EXPAND)

        sizer.Add(self.playlist_checkbox, 0, wx.ALL, 5)
        sizer.Add(self.start_button, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(sizer)

        # Initialize settings
        self.url_input.Bind(wx.EVT_TEXT_ENTER, self.on_start)
        self.format_choice.SetSelection(0)
        self.output_path.SetValue(str(Path.home() / "downloads"))
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start)
        self.output_button.Bind(wx.EVT_BUTTON, self.on_browse)
        self.paste_button.Bind(wx.EVT_BUTTON, self.on_paste)

    def on_paste(self, event):
        if wx.TheClipboard.Open():
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    self.url_input.SetValue(data.GetText())
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Could not access clipboard", "Error", wx.OK)

    def on_browse(self, event):
        dialog = wx.DirDialog(self, "Choose output folder", style=wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.output_path.SetValue(dialog.GetPath())
        dialog.Destroy()

    def on_start(self, event):
        url = self.url_input.GetValue().strip()
        if not url:
            wx.MessageBox("Please enter a YouTube URL", "Error", wx.OK)
            return

        format = self.format_choice.GetString(self.format_choice.GetSelection())
        output = self.output_path.GetValue().strip()
        playlist = self.playlist_checkbox.GetValue()

        # Start download thread
        self.download_thread = threading.Thread(
            target=self.download_audio,
            args=(url, format, output, playlist)
        )
        self.download_thread.start()

    def download_audio(self, url, fmt, output_folder, playlist):
        try:
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
                "progress_hooks": [DownloadProgress(self)],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            wx.MessageBox("Download completed successfully!", "Success", wx.OK)
        except Exception as e:
            wx.MessageBox(f"Download failed: {str(e)}", "Error", wx.OK)

    def on_close(self, event):
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame(None)
    frame.Show()
    app.MainLoop()


