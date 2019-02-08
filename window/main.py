import wx
import wx.adv
from connection import Connection
from window.connectdialog import ConnectDialog
from window.debugmcp import DebugMCP
from window.prefseditor import PrefsEditor
from window.statusbar import StatusBar
from window.worldslist import WorldsList
from functools import partial

from pathlib import Path

from worlds import worlds

import prefs
class Main(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)

        self.status_bar = StatusBar(self)
        self.SetStatusBar(self.status_bar)

        self.about_info     = None
        self.connect_dialog = None
        self.prefs_editor   = None
        self.worlds_list    = None
        self.shortlist      = []

        self.buildMenu()

        h = 600
        w = 800
        if prefs.get('save_window_size'):
            if prefs.get('window_width'):  w = int(prefs.get('window_width'))
            if prefs.get('window_height'): h = int(prefs.get('window_height'))
        self.SetSize((w, h))

        self.tabs = MOONotebook(self)

        self.addEvents()

        if prefs.get('autoconnect_last_world'):
            world = worlds.get(prefs.get('last_world'))
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

    def connect_to_shortlist(self, worldname, evt):
        world = worlds.get(worldname, None)
        if not world: return
        self.openWorld(world)

    def buildMenu(self):
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
        Window_ansi_test = WindowMenu.Append(-1, "&ANSI Color Test", "")

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

    def addEvents(self):
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.tabs.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.status_bar.UpdateConnectionStatus)
        self.tabs.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED, self.tabs.showOrHideTabs)

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

    def closeConnection(self, evt):
        if self.currentConnection():
            self.currentConnection().Close()

    def reconnectConnection(self, evt):
        self.currentConnection().reconnect()

    def currentConnection(self):
        if (self.tabs.GetSelection() != wx.NOT_FOUND):
            return self.tabs.GetPage(self.tabs.GetSelection())

    def onSize(self, evt):
        if prefs.get('save_window_size'):
            size = self.GetSize()
            prefs.set('window_width',  str(size.GetWidth()))
            prefs.set('window_height', str(size.GetHeight()))
        self.Layout()
        evt.Skip()

    def handleCopy(self, evt):
        c = self.currentConnection()
        if   (c.output_pane.HasSelection()): c.output_pane.Copy()
        elif (c.input_pane .HasSelection()): c.input_pane .Copy()

    def handleCut(self, evt):
        self.currentConnection().input_pane.Cut()

    def handlePaste(self, evt):
        self.currentConnection().input_pane.Paste()

    def ansi_test(self, evt):
        self.currentConnection().output_pane.ansi_test()

    ### DIALOGS AND SUBWINDOWS

    def showWorldsList(self, evt = None):
        if self.worlds_list is None: self.worlds_list = WorldsList(self)
        self.worlds_list.Show()

    def showConnectDialog(self, evt):
        if self.connect_dialog is None: self.connect_dialog = ConnectDialog(self)
        self.connect_dialog.Show()

    def showPrefsEditor(self, evt):
        if self.prefs_editor is None: self.prefs_editor = PrefsEditor(self)
        self.prefs_editor.Show()
        pass

    def toggleDebugMCP(self, evt):
        conn = self.currentConnection()
        if conn.debug_mcp is None: conn.debug_mcp = DebugMCP(self, conn)
        conn.debug_mcp.toggle_visible()

    def showHelp(self, evt):
        pass

    def showAboutBox(self, evt):
        if self.about_info is None:
            info = wx.adv.AboutDialogInfo()
            info.AddDeveloper('R Pickett (emerson@hayseed.net)')
            info.AddDeveloper('C Bodt (https://github.com/sirk390)')
            info.SetCopyright('(c) 2013-2019')
            info.SetWebSite('https://emersonrp.github.io/wxpymoo/')
            info.SetName('wxpymoo')
            info.SetLicense(Path('LICENSE').read_text())
            info.SetVersion('0.2')
            self.about_info = info
        wx.adv.AboutBox(self.about_info)

    def quitApplication(self, evt):
        self.closeConnection
        self.Close(True)

from wx.aui import AuiNotebook
class MOONotebook(AuiNotebook):
    def __init__(self, parent):
        AuiNotebook.__init__(self, parent, style =
                wx.aui.AUI_NB_TAB_FIXED_WIDTH|wx.aui.AUI_NB_CLOSE_ON_ALL_TABS|wx.aui.AUI_NB_DEFAULT_STYLE)

    def showOrHideTabs(self, evt = None):
        self.SetTabCtrlHeight(-1 if self.GetPageCount() > 1 else 0)

