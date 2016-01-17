import wx
import prefs
import threading, tempfile, subprocess, os, re

class Editor(wx.EvtHandler):
    def __init__(self, opts):
        wx.EvtHandler.__init__(self)

        self._id        = wx.NewId()
        self.filetype   = opts['filetype']
        self.content    = opts['content']
        self.callback   = opts['callback']
        self.watchTimer = wx.Timer(self, -1)

        # if it's a known type, give it an extension to give the editor a hint
        if self.filetype == "moo-code": extension = '.moo'
        else:                           extension = '.txt'

        self.tempfile = tempfile.NamedTemporaryFile(prefix="wxpymoo_", suffix=extension)

        for line in self.content: self.tempfile.write(line + "\n")
        self.tempfile.flush()
        self._last_sent = os.stat(self.tempfile.name).st_mtime

        thread = threading.Thread(target = self.runEditor)
        thread.start()

        self.watchTimer.Start(250, 0)
        self.Bind(wx.EVT_TIMER, self._send_file_if_needed, self.watchTimer)

    def runEditor(self):
        cmd = re.split(' +', prefs.get('external_editor'))
        cmd.append(self.tempfile.name)
        proc = subprocess.call(cmd)
        # blocks the thread while the editor runs, then:
        self._send_file_if_needed(None)
        self.watchTimer.Stop()

    def _send_file_if_needed(self, evt):
        mtime = os.stat(self.tempfile.name).st_mtime
        if not mtime: print "wtf is wrong with file?!?"
        if mtime > self._last_sent:
            self.tempfile.seek(0)
            self.callback(self._id, self.tempfile.readlines())
            self._last_sent = mtime

    ###################
    # Try this:
    def alternative_plan(filepath):
        import subprocess, os
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))
