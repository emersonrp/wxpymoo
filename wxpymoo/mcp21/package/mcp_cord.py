import re
import wxpymoo.mcp21 as mcp21
import wxpymoo.mcp21.registry as registry
from wxpymoo.mcp21.package import MCPPackageBase

class MCPCord(MCPPackageBase):
    def __init__(self):
        MCPPackageBase.__init__(self)

        self.package = 'mcp-cord'
        self.min     = '1.0'
        self.max     = '1.0'

        registry.register(self, ['mcp-cord','mcp-cord-open','mcp-cord-closed'])

    def dispatch(self, msg):
        if re.match('mcp-cord',        msg.message): self.do_mcp_cord(msg)
        if re.match('mcp-cord-open',   msg.message): self.do_mcp_cord_open(msg)
        if re.match('mcp-cord-closed', msg.message): self.do_mcp_cord_closed(msg)

    def do_mcp_cord(self, msg):        mcp21.debug("do_mcp_cord called with "        + str(msg))
    def do_mcp_cord_open(self, msg):   mcp21.debug("do_mcp_cord_open called with "   + str(msg))
    def do_mcp_cord_closed(self, msg): mcp21.debug("do_mcp_cord_closed called with " + str(msg))
