import re
import mcp21.core as mcp21
import mcp21.registry as registry
from mcp21.package import MCPPackageBase

class MCPPackage(MCPPackageBase):
    def __init__(self):
        MCPPackageBase.__init__(self)

        self.package   = 'mcp-negotiate'
        self.min       = '2.0'
        self.max       = '2.0'
        self.activated = '2.0'

        registry.register(self, ['mcp-negotiate-can','mcp-negotiate-end'])

    def Initialize(self):
        for p in registry.packages.values():

            if p.package == 'mcp': continue
            mcp21.server_notify("mcp-negotiate-can", {
                'package'     : p.package,
                'min-version' : p.min,
                'max-version' : p.max,
            })
        mcp21.server_notify('mcp-negotiation-end')

    def dispatch(self, msg):
        if re.match('mcp-negotiate-can', msg.message): self.do_mcp_negotiate_can(msg)
        if re.match('mcp-negotiate-end', msg.message): self.do_mcp_negotiate_end()

    def do_mcp_negotiate_can(self, msg):
        min = msg.data['min-version']
        max = msg.data['max-version']
        pkg = msg.data['package']
        ver = registry.get_best_version(pkg, min, max)
        if ver:
            mcp21.debug("activating " + pkg)
            registry.packages[pkg].activated = ver

    def do_mcp_negotiate_end(self):
        for pkg_name in registry.packages:
            pkg = registry.packages[pkg_name]
            if pkg.activated:
                pkg.mcp_negotiate_end()
            else:
                registry.packages.pop(pkg_name, None)