import re
from mcp21.package import MCPPackageBase

# This has been pulled from the tab-completion scheme in favor of
# dns-com-vmoo-smartcompletion.  Now this package maintains its own
# list of rehashed thingies, with which it does nothing.
class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package = 'dns-com-awns-rehash'
        self.min     = '1.0'
        self.max     = '1.1'

        self.hashes = []

        mcp.register(self, ['dns-com-awns-rehash-commands'])
        mcp.register(self, ['dns-com-awns-rehash-add'])
        mcp.register(self, ['dns-com-awns-rehash-remove'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-awns-rehash-commands': self.do_commands(msg)
        if msg.message == 'dns-com-awns-rehash-add':      self.do_add(msg)
        if msg.message == 'dns-com-awns-rehash-remove':   self.do_remove(msg)

    def do_commands(self, msg):
        self.hashes = msg.data['list'].split(' ')

    def do_add(self, msg):
        self.hashes.append(msg.data['list'].split(' '))

    def do_remove(self, msg):
        self.hashes[:] = [x for x in self.hashes if x not in msg.data['list'].split()]
