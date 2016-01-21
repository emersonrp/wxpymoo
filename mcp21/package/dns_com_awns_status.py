import re
import mcp21.core as mcp21
import mcp21.registry as registry
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self, conn):
        MCPPackageBase.__init__(self, conn)

        self.package = 'dns-com-awns-status'
        self.min     = '1.0'
        self.max     = '1.0'

        registry.register(self, ['dns-com-awns-status'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-awns-status': self.do_status(msg)

    def do_status(self, msg):
        mcp21.debug("DEBUG: dns-com-awns-status got: " + str(msg))
