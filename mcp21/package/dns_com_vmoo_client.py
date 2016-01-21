import re
import mcp21.core as mcp21
import mcp21.registry as registry
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self):
        MCPPackageBase.__init__(self)

        self.package = 'dns-com-vmoo-client'
        self.min     = '1.0'
        self.max     = '1.0'

        registry.register(self, ['dns-com-vmoo-client-disconnect'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-vmoo-client-disconnect': self.do_disconnect(msg)

    def do_disconnect(self, msg):
        mcp21.debug("Got a disconnect from dns-com-vmoo-client")

    def mcp_negotiate_end(self):
        self.send_info()
        self.send_screensize()

    def send_info(self):
        mcp21.server_notify(
            'dns-com-vmoo-client-info', {
                'name' : 'wxpymoo',
                'version' : 'pre-alpha',
            }
        )

    def send_screensize(self):
        mcp21.server_notify(
            'dns-com-vmoo-client-screensize', {
                'cols' : '100',
                'rows' : '60',
            }
        )
