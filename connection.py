import wx
import time
import sys
import zlib

from wxasync import StartCoroutine
import asyncio

from window.inputpane  import InputPane
from window.outputpane import OutputPane, EVT_ROW_COL_CHANGED
from window.statusbar  import StatusBar
from window.debugmcp   import DebugMCP
from window.msspinfo   import MSSPInfo

from mcp21.core import MCPCore
import prefs
from prefs import EVT_PREFS_CHANGED
import filters.telnetiac

# the 'connection' contains both the network connection and the i/o ui
class Connection(wx.SplitterWindow):
    def __init__(self, mainwindow):
        wx.SplitterWindow.__init__(self, mainwindow.tabs, style = wx.SP_LIVE_UPDATE)
        self.world          = None

        # these two are set with dns_com_awns_serverinfo but hypothetically
        # -could- come from the saved world also
        # EDIT: and/or from MSSP, which should also be mashed into the world
        self.home_url       = ''
        self.help_url       = ''

        self.decompressor = zlib.decompressobj()

        # bin for Telnet IAC commands to stash any status info (on/off, etc)
        self.features = set()
        self.feature_init_callback = {
            'MCP' : self.mcp_init_callback,
            'MSSP' : self.mssp_init_callback,
        }

        # re-queue stuff for re-processing (ie if we turn on compression)
        self.filter_queue = b''

        self.reader = None
        self.writer = None

        self.input_pane  = InputPane(self, self)
        self.output_pane = OutputPane(self, self)
        self.status_bar  = StatusBar(mainwindow, self)
        self.mainwindow  = mainwindow
        self.debug_mcp   = None

        self.SplitHorizontally(self.output_pane, self.input_pane)
        self.SetMinimumPaneSize(self.input_pane.font_size()[1] * 2)

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.saveSplitterSize )
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.output_pane.Bind(EVT_ROW_COL_CHANGED , self.on_row_col_changed )

        mainwindow.Bind(EVT_PREFS_CHANGED, self.doPrefsChanged)

    def doPrefsChanged(self, evt):
        self.input_pane.restyle_thyself()
        self.output_pane.restyle_thyself()
        evt.Skip()

    def saveSplitterSize(self, evt):
        size = self.GetSize()
        prefs.set('input_height', size.GetHeight() - evt.GetSashPosition())
        evt.Skip()

    def OnSize(self, evt):
        size = self.GetSize()
        input_height = int(prefs.get('input_height')) or 25
        self.SetSashPosition(size.GetHeight() - input_height, True)
        self.output_pane.ScrollIfAppropriate()
        evt.Skip()

    def on_row_col_changed(self, evt):
        # This is sorta icky but math is hard
        filters.telnetiac.handle_naws(self)

    def ActivateFeature(self, feature, on = True):
        if on:
            self.features.add(feature)
            if self.feature_init_callback.get(feature):
                self.feature_init_callback[feature]()
        else:
            self.features.discard(feature)
        self.UpdateStatus()

    def SetTitle(self, text):
        tabindex = self.mainwindow.tabs.GetPageIndex(self)
        self.mainwindow.tabs.SetPageText(tabindex, text)

    def UpdateStatus(self):
        self.status_bar.LayoutWidgets()

    def UpdateIcon(self, icon, message):
        icon = self.status_bar.feature_icons.get(icon)
        if icon: icon.SetToolTip(message)

    def ShowMessage(self, message):
        self.status_bar.AddStatus(message)

    def IsCurrentConnection(self):
        return self.mainwindow.currentConnection() == self

    def Close(self):
        if self.is_connected():
            self.output_pane.display("=== wxpymoo: Connection closed. ===\n");

        if self.writer: self.writer.close()
        self.filter_queue = b''
        self.features.clear()
        self.connect_time = self.reader = self.writer = None

    # TODO - we need to cram charset into worlds more deterministically
    def charset(self):
        return self.world.get('charset', 'latin1') if self.world else 'latin1'

    # connection.connect ([host], [port])
    #
    # existing connections will remember their host and port if not supplied here,
    # for ease of reconnect etc.
    def connect(self, world):
        self.world = world
        self.connect_time = None

        StartCoroutine(self._connect, self)

    async def _connect(self):
        world    = self.world
        host     = world.get('host')
        port     = int(world.get('port'))
        conntype = world.get('conntype')

        try:
            wx.BeginBusyCursor()
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
            wx.EndBusyCursor()

        if conntype == "SSL":
            self.ActivateFeature('SSL')

        self.connect_time = time.time()

        prefs.set('last_world', world.get('name'))

        self.mcp = MCPCore(self)

        if self.world.get('auto_login'):
            login_script = self.world.get('login_script')
            if login_script:
                login_script = re.sub('%u', self.world.get('username', ''), login_script)
                login_script = re.sub('%p', self.world.get('password', ''), login_script)
            self.output(login_script + "\n")

        while True:
            data = await self.reader.read(65535)
            if not data: break

            if self.filter_queue:
                data = self.filter_queue + data
                self.filter_queue = b''

            # Do the initial telnet filtering here, while we're still in 'bytes' mode
            data = filters.telnetiac.process_line(self, data)
            if not data: continue

            data = data.decode(self.charset())

            self.output_pane.display(data)

    def output(self, stuff):
        if isinstance(stuff, str):
            stuff = bytes(stuff, self.charset())
        if self.writer:
            self.writer.write(stuff)
        else:
            print(f"Tried to write stuff to closed writer: {stuff}")

    def reconnect(self):
        if self.writer: self.Close()
        self.connect(self.world)

    def is_connected(self):
        return True if self.writer else False

    ### feature init callbacks
    def mcp_init_callback(self):
        self.debug_mcp = DebugMCP(self.mainwindow, self)

    def mssp_init_callback(self):
        self.mssp_info = MSSPInfo(self)
