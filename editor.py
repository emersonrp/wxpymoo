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
        self.reference  = opts['reference'] or 'wxpymoo'
        self.watchTimer = wx.Timer(self, -1)

        # if it's a known type, give it an extension to give the editor a hint
        if self.filetype == "moo-code": extension = '.moo'
        else:                           extension = '.txt'

        # Create the tmpfile...
        tempfd, self.tmpfilename = tempfile.mkstemp(
                prefix = self.reference+"_", suffix = extension)
        tmpfile = open(self.tmpfilename, 'w')

        # ...write to it...
        for line in self.content: tmpfile.write(line + "\n")
        tmpfile.flush()

        # ... then let's get the os' hands off it so the editor can write to it.
        tmpfile.close()
        os.close(tempfd)

        # set the "last sent" time so we don't send it instantly
        self._last_sent = os.stat(self.tmpfilename).st_mtime

        # hands are off now, start the editor
        thread = threading.Thread(target = self.runEditor)
        thread.start()

        # We run a timer to check the file a few times a second so that a
        # "save" will send, even without a "quit" attached.
        self.watchTimer.Start(250, 0)
        self.Bind(wx.EVT_TIMER, self._send_file_if_needed, self.watchTimer)

    def runEditor(self):
        _config = wx.ConfigBase.Get()
        cmd = re.split(r' +', _config.Read('external_editor'))
        cmd.append(self.tmpfilename)

        # block the thread while the editor runs...
        subprocess.Popen(cmd).wait()

        # ...then send it once the editor exits...
        self._send_file_if_needed(None)

        # ...and remove the temp file.
        os.remove(self.tmpfilename)

        self.watchTimer.Stop()

    def _send_file_if_needed(self, evt):
        mtime = os.stat(self.tmpfilename).st_mtime
        if not mtime: print("wtf is wrong with file?!?")
        if mtime > self._last_sent:
            tmpfile = open(self.tmpfilename, 'r')
            tmpfile.seek(0)
            self.callback(self._id, tmpfile.readlines())
            self._last_sent = mtime

    ###################
    # Try this:
    def alternative_plan(self, filepath):
        import subprocess, os, sys
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            os.startfile(filepath, 'edit')
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))
