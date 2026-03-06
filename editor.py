import wx
import tempfile
import re

from pathlib import Path

class Editor(wx.EvtHandler):
    def __init__(self, opts):
        wx.EvtHandler.__init__(self)

        self._id        = wx.NewId()
        self.filetype   = opts['filetype']
        self.content    = opts['content']
        self.callback   = opts['callback']
        self.reference  = opts['reference'] or 'wxpymoo'
        self.watchTimer = wx.Timer(self, -1)

        # if it's a known type, give it an extension to give the editor a hint
        if self.filetype == "moo-code": extension = '.moo'
        else:                           extension = '.txt'

        # Create the tmpfile...
        _tempfd, tmpfilename = tempfile.mkstemp(
                prefix = self.reference+"_", suffix = extension)
        self.tmpfile = Path(tmpfilename)

        # ...write to it...
        self.tmpfile.write_text("\n".join(self.content))

        # set the "last sent" time so we don't send it instantly
        self._last_sent = self.tmpfile.stat().st_mtime

        # hands are off now, start the editor
        self.runEditor()

        # We run a timer to check the file a few times a second so that a
        # "save" will send, even without a "quit" attached.
        self.watchTimer.Start(250, False)
        self.Bind(wx.EVT_TIMER, self._send_file_if_needed, self.watchTimer)

    def runEditor(self):
        self.Bind(wx.EVT_END_PROCESS, self.OnProcessEnded)

        editor_path = wx.ConfigBase.Get().Read('editor_path')
        if not editor_path:
            wx.LogError("ERROR!  External editor path not selected, aborting!")
            wx.MessageBox("You have no external editor selected.  Please visit the Preferences dialog.", "No Editor")
            return
        cmd = re.split(r' +', wx.ConfigBase.Get().Read('editor_path'))
        cmd.append(f'"{self.tmpfile}"')

        # launch the editor and capture the pid
        self.process = wx.Process(self)
        self.pid = wx.Execute(' '.join(cmd), wx.EXEC_ASYNC, self.process)
        wx.LogMessage(f"Launched external editor as pid {self.pid}")

    def OnProcessEnded(self, _):
        wx.LogMessage(f"External editor pid {self.pid} exited.")

        # ...send it once the editor exits...
        self._send_file_if_needed(None)

        # ...and remove the temp file.
        self.tmpfile.unlink()

        self.watchTimer.Stop()

    def _send_file_if_needed(self, _):
        mtime = self.tmpfile.stat().st_mtime
        if not mtime:
            wx.LogError("Something went wrong with the editor:  temp file has no mtime!")
            return
        if mtime > self._last_sent:
            self.callback(self._id, self.tmpfile.read_text().splitlines())
            self._last_sent = mtime

    ###################
    # Try this:
#    def alternative_plan(self, filepath):
#        import subprocess, os, sys
#        if sys.platform.startswith('darwin'):
#            subprocess.call(('open', filepath))
#        elif os.name == 'nt':
#            os.startfile(filepath, 'edit')
#        elif os.name == 'posix':
#            subprocess.call(('xdg-open', filepath))
