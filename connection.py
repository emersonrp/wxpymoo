import wx
import time
import re
import zlib

from wxasync import StartCoroutine
import asyncio

from window.inputpane  import InputPane
from window.outputpane import OutputPane, EVT_ROW_COL_CHANGED
from window.statusbar  import StatusBar
from window.debugmcp   import DebugMCP
from window.msspinfo   import MSSPInfo
from window.mediainfo  import MediaInfo

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

        self.do_echo = False

        self.decompressor = zlib.decompressobj()

        # bin for Telnet IAC commands to stash any status info (on/off, etc)
        self.features = set()
        self.feature_init_callback = {
            'MCP'  : self.mcp_init_callback,
            'MSSP' : self.mssp_init_callback,
            'MSP'  : self.msp_init_callback,
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
        config = wx.ConfigBase.Get()
        size = self.GetSize()
        config.WriteInt('input_height', size.GetHeight() - evt.GetSashPosition())
        config.Flush()
        evt.Skip()

    def OnSize(self, evt):
        config = wx.ConfigBase.Get()
        size = self.GetSize()
        input_height = config.ReadInt('input_height') or 25
        self.SetSashPosition(size.GetHeight() - input_height, True)
        self.output_pane.ScrollIfAppropriate()
        evt.Skip()

    def on_row_col_changed(self, _):
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

    def GetTitle(self):
        tabindex = self.mainwindow.tabs.GetPageIndex(self)
        return self.mainwindow.tabs.GetPageText(tabindex)

    def UpdateStatus(self):
        self.status_bar.LayoutWidgets()

    def UpdateIcon(self, icon, message):
        iconpanel = self.status_bar.feature_icons.get(icon)
        if iconpanel: iconpanel.icon.SetToolTip(message)

    def ShowMessage(self, message):
        self.status_bar.AddStatus(message)

    def IsCurrentConnection(self):
        return self.mainwindow.currentConnection() == self

    def Close(self, force = False):
        if self.is_connected():
            self.output_pane.display("=== wxpymoo: Connection closed. ===\n");

        if self.writer: self.writer.close()
        self.filter_queue = b''
        self.features.clear()
        self.connect_time = self.reader = self.writer = None
        super().Close(force)

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
        if not world:
            wx.LogError("No world is set in connection._connect")
            return
        host     = world.get('host')
        port     = int(world.get('port'))
        conntype = world.get('conntype')

        message = ''
        try:
            wx.BeginBusyCursor()
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl = (conntype == "SSL")),
                timeout = 15)
            message = ""
        except asyncio.CancelledError:
            raise
        except ConnectionRefusedError:
            message = f"Connection to {host}:{port} failed - connection refused"
        except asyncio.TimeoutError:
            message = f"Connection to {host}:{port} timed out."
        except OSError as inst:
            message = f"Connection to {host}:{port} failed - {inst}"
        except Exception as inst:
            message = f"Connection error: {inst}"
            wx.LogError(f"DEBUG: Connection Exception {inst.__class__} {inst}")
        finally:
            if message:
                self.Close()
                wx.MessageDialog(self, message, "Error", style = wx.OK|wx.ICON_ERROR).ShowModal()
                return
            wx.EndBusyCursor()

        if conntype == "SSL":
            self.ActivateFeature('SSL')









        from window.mediainfo import msp_filter
        self.ActivateFeature('MSP')
        self.output_pane.register_filter('msp', msp_filter)


















        self.connect_time = time.time()

        config = wx.ConfigBase.Get()
        config.Write('last_world', world.get('name'))
        config.Flush()

        self.mcp = MCPCore(self)

        if world.get('auto_login'):
            login_script = world.get('login_script')
            if login_script:
                login_script = re.sub(r'%u', world.get('username', ''), login_script)
                login_script = re.sub(r'%p', world.get('password', ''), login_script)
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
            wx.LogError(f"Tried to write stuff to closed writer: {stuff}")

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

    def msp_init_callback(self):
        self.media_info = MediaInfo(self)
