import wx
import wx.aui
import wx.adv
from connection import Connection
from window.connectdialog import ConnectDialog
from window.prefseditor import PrefsEditor
from window.worldslist import WorldsList
from functools import partial

from pathlib import Path

from worlds import worlds

class Main(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)

        self.about_info     = None
        self.connect_dialog = None
        self.prefs_editor   = None
        self.worlds_list    = None
        self.shortlist      = []

        WorldsMenu = wx.Menu()
        Worlds_worlds  = WorldsMenu.Append(-1, "&Worlds...",  "Browse list of worlds")
        Worlds_connect = WorldsMenu.Append(-1, "&Connect...", "Connect to a host and port")
        Worlds_close   = WorldsMenu.Append(-1, "C&lose", "Close the connection to the current world")
        WorldsMenu.AppendSeparator()
        Worlds_reconnect = WorldsMenu.Append(-1, "&Reconnect", "Close and re-open the connection to the current world")
        Worlds_quit      = WorldsMenu.Append(wx.ID_EXIT)

        EditMenu = wx.Menu()
        Edit_cut   = EditMenu.Append(wx.ID_CUT)
        Edit_copy  = EditMenu.Append(wx.ID_COPY)
        Edit_paste = EditMenu.Append(wx.ID_PASTE)

        PrefsMenu = wx.Menu()
        Prefs_prefs = PrefsMenu.Append(wx.ID_PREFERENCES)

        WindowMenu = wx.Menu()
        Window_debugmcp = WindowMenu.Append(-1, "&Debug MCP", "")
        Window_ansi_test = WindowMenu.Append(-1, "&ANSI Code Test", "")

        HelpMenu = wx.Menu()
        Help_help  = HelpMenu.Append(wx.ID_HELP)
        Help_about = HelpMenu.Append(wx.ID_ABOUT)

        MenuBar = wx.MenuBar()
        MenuBar.Append(WorldsMenu, "&Worlds")
        MenuBar.Append(EditMenu, "&Edit")
        MenuBar.Append(PrefsMenu, "&Preferences")
        MenuBar.Append(WindowMenu, "Windows")
        MenuBar.Append(HelpMenu, "&Help")

        self.SetMenuBar(MenuBar)

        self.rebuildShortlist()

        # MENUBAR EVENTS
        self.Bind(wx.EVT_MENU, self.showWorldsList,      Worlds_worlds    )
        self.Bind(wx.EVT_MENU, self.showConnectDialog,   Worlds_connect   )
        self.Bind(wx.EVT_MENU, self.closeConnection,     Worlds_close     )
        self.Bind(wx.EVT_MENU, self.reconnectConnection, Worlds_reconnect )
        self.Bind(wx.EVT_MENU, self.quitApplication,     Worlds_quit      )

        self.Bind(wx.EVT_MENU, self.handleCut,   Edit_cut   )
        self.Bind(wx.EVT_MENU, self.handleCopy,  Edit_copy  )
        self.Bind(wx.EVT_MENU, self.handlePaste, Edit_paste )

        self.Bind(wx.EVT_MENU, self.showPrefsEditor, Prefs_prefs )

        self.Bind(wx.EVT_MENU, self.toggleDebugMCP, Window_debugmcp )
        self.Bind(wx.EVT_MENU, self.ansi_test,      Window_ansi_test )

        self.Bind(wx.EVT_MENU, self.showHelp,     Help_help  )
        self.Bind(wx.EVT_MENU, self.showAboutBox, Help_about )

        _config = wx.ConfigBase.Get()

        h = 600
        w = 800
        if _config.ReadBool('save_window_size'):
            if _config.ReadInt('window_width'):  w = _config.ReadInt('window_width')
            if _config.ReadInt('window_height'): h = _config.ReadInt('window_height')
        self.SetSize((w, h))

        self.tabs = MOONotebook(self)

        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onTabChanged)

        if _config.ReadBool('autoconnect_last_world'):
            world = worlds.get(_config.Read('last_world'))
            if world:
                self.openWorld(world)
            else:
                wx.CallAfter(self.showWorldsList)
        else:
            wx.CallAfter(self.showWorldsList)

    def openWorld(self, world):
        conn = Connection(self)
        conn.connect(world)
        self.tabs.AddPage(conn, world.get('name'), select = True)
        self.tabs.showOrHideTabs()
        conn.input_pane.SetFocus()

    def connect_to_shortlist(self, worldname, _):
        world = worlds.get(worldname, None)
        if not world: return
        self.openWorld(world)

    def rebuildShortlist(self):
        shortlist = []
        for worldname, world in worlds.items():
            if world.get('on_shortlist'):
                shortlist.append(worldname)

        # remove any existing shortlist
        for menuitem in self.shortlist:
            menuitem.GetMenu().Delete(menuitem)
        self.shortlist = []

        if shortlist:
            mb = self.GetMenuBar()
            WorldsMenu = mb.GetMenu(mb.FindMenu("Worlds"))
            self.shortlist.append(WorldsMenu.AppendSeparator())
            for world in sorted(shortlist):
                menuitem = WorldsMenu.Append(-1, world)
                self.shortlist.append(menuitem)
                self.Bind(wx.EVT_MENU, partial(self.connect_to_shortlist, world), menuitem)

    def closeConnection(self, _):
        if self.currentConnection():
            self.currentConnection().Close()

    def reconnectConnection(self, _):
        self.currentConnection().reconnect()

    def currentConnection(self):
        return self.tabs.GetCurrentPage()

    def onSize(self, evt):
        _config = wx.ConfigBase.Get()
        if _config.ReadBool('save_window_size'):
            size = self.GetSize()
            _config.WriteInt('window_width',  size.GetWidth())
            _config.WriteInt('window_height', size.GetHeight())
        self.Layout()
        evt.Skip()

    def onTabChanged(self, _):
        current_status = self.GetStatusBar()
        if current_status:
            current_status.Hide()
            self.SetStatusBar(None)
        new_status = self.currentConnection().status_bar
        self.SetStatusBar(new_status)
        new_status.Show()
        new_status.UpdateConnectionStatus()
        self.SetTitle("wxpymoo - " + self.currentConnection().GetTitle())

    def handleCopy(self, _):
        c = self.currentConnection()
        if not c: return
        if   (c.output_pane and c.output_pane.HasSelection()): c.output_pane.Copy()
        elif (c.input_pane  and c.input_pane .HasSelection()): c.input_pane .Copy()

    def handleCut(self, _):
        if self.currentConnection():
            self.currentConnection().input_pane.Cut()

    def handlePaste(self, _):
        if self.currentConnection():
            self.currentConnection().input_pane.Paste()

    def ansi_test(self, _):
        if self.currentConnection():
            self.currentConnection().output_pane.ansi_test()

    ### DIALOGS AND SUBWINDOWS

    def showWorldsList(self, _ = None):
        if self.worlds_list is None: self.worlds_list = WorldsList(self)
        self.worlds_list.Show()

    def showConnectDialog(self, _):
        if self.connect_dialog is None: self.connect_dialog = ConnectDialog(self)
        self.connect_dialog.Show()

    def showPrefsEditor(self, _):
        if self.prefs_editor is None: self.prefs_editor = PrefsEditor(self)
        self.prefs_editor.Show()

    def toggleDebugMCP(self, _):
        conn = self.currentConnection()
        if conn.debug_mcp: conn.debug_mcp.toggle_visible()

    def showHelp(self, _):
        ...

    def showAboutBox(self, _):
        if self.about_info is None:
            info = wx.adv.AboutDialogInfo()
            info.AddDeveloper('R Pickett (emerson@hayseed.net)')
            info.AddDeveloper('lisdude (https://github.com/lisdude)')
            info.AddDeveloper('C Bodt (https://github.com/sirk390)')
            info.AddDeveloper('Andrea Gavana')
            info.SetCopyright('(c) 2013-2024')
            info.SetWebSite('https://emersonrp.github.io/wxpymoo/')
            info.SetName('wxpymoo')
            info.SetLicense(Path('LICENSE').read_text())
            info.SetVersion('0.1.8')
            self.about_info = info
        wx.adv.AboutBox(self.about_info)

    def quitApplication(self, evt):
        self.closeConnection(evt)
        self.Close(True)

from wx.aui import AuiNotebook
class MOONotebook(AuiNotebook):
    def __init__(self, parent):
        AuiNotebook.__init__(self, parent, style =
                wx.aui.AUI_NB_TAB_FIXED_WIDTH|wx.aui.AUI_NB_CLOSE_ON_ALL_TABS|wx.aui.AUI_NB_DEFAULT_STYLE)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE,   self.onPageClose)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED,  self.showOrHideTabs)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onPageChanged)

    def onPageClose(self, _ = None):
        status_bar = self.GetCurrentPage().status_bar
        status_bar.update_timer.Stop()
        status_bar.Destroy()

    def showOrHideTabs(self, _ = None):
        self.SetTabCtrlHeight(-1 if self.GetPageCount() > 1 else 0)

    def onPageChanged(self, evt):
        # Remove the "(*)" from the tab title
        conn = self.GetCurrentPage()
        conn.SetTitle(conn.world.get('name'))
        evt.Skip()
