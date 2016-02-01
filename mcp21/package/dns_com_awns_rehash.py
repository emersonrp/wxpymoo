import re
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package = 'dns-com-awns-rehash'
        self.min     = '1.0'
        self.max     = '1.1'

        mcp.registry.register(self, ['dns-com-awns-rehash-commands'])
        mcp.registry.register(self, ['dns-com-awns-rehash-add'])
        mcp.registry.register(self, ['dns-com-awns-rehash-remove'])

    def dispatch(self, msg):
        if msg.message == 'dns-com-awns-rehash-commands': self.do_commands(msg)
        if msg.message == 'dns-com-awns-rehash-add':      self.do_add(msg)
        if msg.message == 'dns-com-awns-rehash-remove':   self.do_remove(msg)

    def do_commands(self, msg):
        self.mcp.connection.input_pane.tab_completion.set_verbs(msg.data['list'].split(' '))
        self.mcp.connection.input_pane.tab_completion.set_names([])

    def do_add(self, msg):
        self.mcp.connection.input_pane.tab_completion.add_verbs(msg.data['list'].split(' '))
        self.mcp.connection.input_pane.tab_completion.add_names([])

    def do_remove(self, msg):
        self.mcp.connection.input_pane.tab_completion.remove_verbs(msg.data['list'].split(' '))
        self.mcp.connection.input_pane.tab_completion.remove_names([])
