import wx
import re, webbrowser
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package = 'dns-com-awns-serverinfo'
        self.min     = '1.0'
        self.max     = '1.0'

        mainwindow = wx.GetApp().GetTopWindow()

        self.notebook = mainwindow.tabs
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.updateMenu)

        self.menubar = mainwindow.GetMenuBar()
        self.helpmenu = self.menubar.GetMenu(self.menubar.FindMenu('Help'))

        self.mcp.register(self, ['dns-com-awns-serverinfo'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-awns-serverinfo': self.do_serverinfo(msg)

    def updateMenu(self, evt):
        if evt: cp = evt.GetSelection()
        else:   cp = self.notebook.GetSelection()

        page = self.notebook.GetPage(cp)

        # Clear the existing help menu items, if any, on any tab change...
        home_item = self.helpmenu.FindItem('World Homepage')
        if home_item != wx.NOT_FOUND: self.helpmenu.DestroyItem(self.helpmenu.FindItemById(home_item))

        help_item = self.helpmenu.FindItem('World Help Page')
        if help_item != wx.NOT_FOUND: self.helpmenu.DestroyItem(self.helpmenu.FindItemById(help_item))

        last_menu_item = self.helpmenu.FindItemByPosition(self.helpmenu.GetMenuItemCount()-1)
        if last_menu_item.IsSeparator(): self.helpmenu.DestroyItem(last_menu_item)

        # ...and if we have home/help info for the current connection...
        if not (page.home_url or page.help_url): return

        # ...make new menu entries for them
        last_menu_item = self.helpmenu.FindItemByPosition(self.helpmenu.GetMenuItemCount()-1)
        if not last_menu_item.IsSeparator():
            self.helpmenu.AppendSeparator()
        if page.home_url:
            home_item = self.helpmenu.Append(-1, "World Homepage", "Visit the homepage for the current world")
            self.menubar.Bind(wx.EVT_MENU, lambda x: webbrowser.open(page.home_url), home_item)
        if page.help_url:
            help_item = self.helpmenu.Append(-1, "World Help Page", "Visit the help page for the current world")
            self.menubar.Bind(wx.EVT_MENU, lambda x: webbrowser.open(page.home_url), help_item)

    # when we're all settled in, ask the server for the URLs
    def mcp_negotiate_end(self):
        self.mcp.server_notify('dns-com-awns-serverinfo-get')

    # When we get new URLs from the server, save them in the associated Connection
    def do_serverinfo(self, msg):
        page = self.notebook.GetPage(self.notebook.GetSelection())

        page.home_url = (msg.data.get('home_url') or '')
        page.help_url = (msg.data.get('help_url') or '')

        self.updateMenu(None)
