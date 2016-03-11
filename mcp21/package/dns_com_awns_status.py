import re
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package = 'dns-com-awns-status'
        self.min     = '1.0'
        self.max     = '1.0'

        mcp.register(self, ['dns-com-awns-status'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-awns-status': self.do_status(msg)

    def do_status(self, msg):
        self.mcp.connection.ShowMessage(msg.data['text'])
