import wx
import time
import re
import sys
from wxasync import StartCoroutine
import asyncio

from window.inputpane import InputPane
from window.outputpane import OutputPane
from mcp21.core import MCPCore
import prefs
from prefs import EVT_PREFS_CHANGED
from window.outputpane import EVT_ROW_COL_CHANGED
import filters.telnetiac

# the 'connection' contains both the network connection and the i/o ui
class Connection(wx.SplitterWindow):
    def __init__(self, mainwindow):
        wx.SplitterWindow.__init__(self, mainwindow.tabs, style = wx.SP_LIVE_UPDATE)
        self.world          = None
        self.debug_mcp      = None

        self.input_pane     = InputPane(self, self)
        self.output_pane    = OutputPane(self, self)

        # these two are set with dns_com_awns_serverinfo but hypothetically
        # -could- come from the saved world also
        self.home_url       = ''
        self.help_url       = ''

        self.iac = {}

        self.reader = self.writer = None

        #self.keepalive     = Keepalive(self)

        self.SplitHorizontally(self.output_pane, self.input_pane)
        self.SetMinimumPaneSize(self.input_pane.font_size()[1] * 2)

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.saveSplitterSize )
        self.Bind(wx.EVT_SIZE, self.HandleResize)
        self.output_pane.Bind(EVT_ROW_COL_CHANGED , self.on_row_col_changed )

        mainwindow.Bind(EVT_PREFS_CHANGED, self.doPrefsChanged)

    def on_row_col_changed(self, evt):
        # This is sorta icky but math is hard
        filters.telnetiac.handle_naws(self)

    def doPrefsChanged(self, evt):
        self.input_pane.restyle_thyself()
        self.output_pane.restyle_thyself()
        evt.Skip()

    def saveSplitterSize(self, evt):
        size = self.GetSize()
        prefs.set('input_height', size.GetHeight() - evt.GetSashPosition())

    def HandleResize(self, evt):
        size = self.GetSize()
        input_height = int(prefs.get('input_height')) or 25
        self.SetSashPosition(size.GetHeight() - input_height, True)
        self.output_pane.ScrollIfAppropriate()

    def ShowMessage(self, message):
        if self.IsCurrentConnection():
            self.main_window.GetStatusBar().AddStatus(message)

    def IsCurrentConnection(self):
        return self.main_window.currentConnection() == self

    def Close(self):
        if self.is_connected:
            self.output_pane.display("=== wxpymoo: Connection closed. ===\n");
        # force it again just to be sure
        #self.keepalive.Stop()
        self.connect_time = None
        if self.writer: self.writer.close()
        self.reader = self.writer = None

    # connection.connect ([host], [port])
    #
    # existing connections will remember their host and port if not supplied here,
    # for ease of reconnect etc.
    def connect(self, world):
        self.world = world
        StartCoroutine(self._connect, self)
        self.connect_time = None

    async def _connect(self):
        world    = self.world
        host     = world.get('host')
        port     = int(world.get('port'))
        conntype = world.get('conntype')

        try:
            wait = wx.BusyCursor()
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl = (conntype == "SSL")),
                timeout = 15)
        except Exception as inst:
            self.Close()
            message = "Connection error: " + str(inst)
            if inst.__class__ == asyncio.TimeoutError:
                message = "Connection to " + host + ":" + str(port) + " timed out."
            else:
                print("DEBUG: Connection Exception " + str(inst.__class__) + " " + str(inst))
            wx.MessageDialog(self, message, "Error", style = wx.OK|wx.ICON_ERROR).ShowModal()
            return
        finally:
            del wait

        self.connect_time = time.time()

        prefs.set('last_world', world.get('name'))

        self.main_window = wx.GetApp().GetTopWindow()

        self.mcp = MCPCore(self)

        if self.world.get('auto_login'):
            login_script = self.world.get('login_script')
            if login_script:
                login_script = re.sub('%u', self.world.get('username', ''), login_script)
                login_script = re.sub('%p', self.world.get('password', ''), login_script)
            self.output(login_script + "\n")

        # TODO - 'if world.connection.keepalive'
        #self.keepalive.Start()
        while True:
            line = await self.reader.readline()
            if not line: break

            line = line.decode('latin1').rstrip()
            self.output_pane.display(line)

    def output(self, stuff):
        self.writer.write(stuff.encode('latin1'))

    def reconnect(self):
        if self.writer: self.Close()
        self.connect(self.world)

    def is_connected(self):
        return True if self.writer else False


class Keepalive(wx.EvtHandler):
    ######################
    # This is a stupid brute-force keepalive that periodically tickles the
    # connection by sending a single space.  Not magical or brilliant.
    def __init__(self, connection):
        wx.EvtHandler.__init__(self)
        self.connection = connection
        self.timer = wx.Timer()

        self.timer.Bind(wx.EVT_TIMER, self.on_keepalive)

    def Start(self):
        self.timer.Start(60000, False) # 1 minute TODO make this a pref?

    def Stop(self):
        self.timer.Stop()

    def on_keepalive(self, evt):
        # TODO - this is pretty brute-force, innit?
        # This'll likely break on worlds that actually
        # are character-based instead of line-based.
        self.connection.output(" ")
