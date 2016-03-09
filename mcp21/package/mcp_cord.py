import re
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package = 'mcp-cord'
        self.min     = '1.0'
        self.max     = '1.0'

        mcp.register(self, ['mcp-cord','mcp-cord-open','mcp-cord-closed'])

    def dispatch(self, msg):
        if re.match('mcp-cord',        msg.message): self.do_mcp_cord(msg)
        if re.match('mcp-cord-open',   msg.message): self.do_mcp_cord_open(msg)
        if re.match('mcp-cord-closed', msg.message): self.do_mcp_cord_closed(msg)

    def do_mcp_cord(self, msg):        self.mcp.debug("do_mcp_cord called with "        + str(msg))
    def do_mcp_cord_open(self, msg):   self.mcp.debug("do_mcp_cord_open called with "   + str(msg))
    def do_mcp_cord_closed(self, msg): self.mcp.debug("do_mcp_cord_closed called with " + str(msg))
