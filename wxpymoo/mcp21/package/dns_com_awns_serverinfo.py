import wx
import re, webbrowser
import wxpymoo.mcp21.core as mcp21
import wxpymoo.mcp21.registry as registry
from wxpymoo.mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self):
        MCPPackageBase.__init__(self)

        self.package = 'dns-com-awns-serverinfo'
        self.min     = '1.0'
        self.max     = '1.0'

        self.home_url = ''
        self.help_url = ''

        registry.register(self, ['dns-com-awns-serverinfo'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-awns-serverinfo': self.do_serverinfo(msg)

    # when we're all settled in, ask the server for the URLs
    def mcp_negotiate_end(self):
        mcp21.server_notify('dns-com-awns-serverinfo-get')

    # When we get new URLs from the server, install/activate the "Help" menu entries
    def do_serverinfo(self, msg):
        self.home_url = msg.data['home_url']
        self.help_url = msg.data['help_url']
        if not (self.home_url or self.help_url): return

        menubar = mcp21.connection.mainwindow.GetMenuBar()
        if not menubar: return

        help_menu = menubar.GetMenu(menubar.FindMenu('Help'))
        if not help_menu: return

        # TODO - we'll stash all these away so we can remove them on disconnect.... later someday
        self.menuitem_separator = help_menu.AppendSeparator()
        if self.home_url:
            self.menuitem_home = help_menu.Append(-1, "World Homepage", "Visit the homepage for the current world")
            menubar.Bind(wx.EVT_MENU, self.visit_home, self.menuitem_home)
        if self.help_url:
            self.menuitem_help = help_menu.Append(-1, "World Help Page", "Visit the help page for the current world")
            menubar.Bind(wx.EVT_MENU, self.visit_help, self.menuitem_help)

    def visit_home(self, evt): webbrowser.open(self.home_url)
    def visit_help(self, evt): webbrowser.open(self.help_url)
