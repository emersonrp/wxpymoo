import wx
import re, webbrowser
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package = 'dns-com-awns-displayurl'
        self.min     = '1.0'
        self.max     = '1.0'

        self.mcp.register(self, ['dns-com-awns-displayurl'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-awns-displayurl': self.do_displayurl(msg)

    # When we get a URL from the server, shove it to the browser
    def do_displayurl(self, msg):
        webbrowser.open(msg.data['url'])
