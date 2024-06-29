import re
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package   = 'mcp-negotiate'
        self.min       = '2.0'
        self.max       = '2.0'
        self.activated = '2.0'

        mcp.register(self, ['mcp-negotiate-can','mcp-negotiate-end'])

    def Initialize(self):
        for p in self.mcp.packages.values():

            if p.package == 'mcp': continue
            self.mcp.server_notify("mcp-negotiate-can", {
                'package'     : p.package,
                'min-version' : p.min,
                'max-version' : p.max,
            })
        self.mcp.server_notify('mcp-negotiation-end')

    def dispatch(self, msg):
        if re.match('mcp-negotiate-can', msg.message): self.do_mcp_negotiate_can(msg)
        if re.match('mcp-negotiate-end', msg.message): self.do_mcp_negotiate_end()

    def do_mcp_negotiate_can(self, msg):
        min = msg.data['min-version']
        max = msg.data['max-version']
        pkg = msg.data['package']
        ver = self.mcp.get_best_version(pkg, min, max)
        if ver:
            self.mcp.debug("activating " + pkg)
            self.mcp.packages[pkg].activated = ver
            package_list = '\n* '.join(self.mcp.packages.keys())
            self.mcp.connection.UpdateIcon('MCP', 'MCP enabled\nActive packages:\n* ' + package_list)

    def do_mcp_negotiate_end(self):
        deactivate_packages = []
        for pkg_name in self.mcp.packages:
            pkg = self.mcp.packages[pkg_name]
            if pkg.activated:
                pkg.mcp_negotiate_end()
            else:
                deactivate_packages.append(pkg_name)

        for pkg_name in deactivate_packages:
            self.mcp.packages.pop(pkg_name, None)
