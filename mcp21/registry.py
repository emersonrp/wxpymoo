import re
from mcp21.package import MCPPackageBase

class MCPRegistry:
    def __init__(self):

        self.msg_registry = {}
        self.packages = {}

    def register(self, pkg, messages):
        if not isinstance(pkg, MCPPackageBase):
            print("something that isn't an MCP package tried to register")
            return
        self.packages[pkg.package] = pkg
        for message in messages:
            self.msg_registry[message] = pkg

    # next two subs taken from MCP 2.1 specification, section 2.4.3
    def get_best_version(self, pkg, smin, smax):
        if not self.packages.has_key(pkg): return

        cmax = self.packages[pkg].max
        cmin = self.packages[pkg].min

        if (_version_cmp(cmax, smin) and _version_cmp(smax, cmin)):
            if _version_cmp(smax, cmax):
                return cmax
            else:
                return smax
        else:
            return undef

    def _version_cmp(self, v1, v2):
        v1_maj, v1_min = re.split('\.', v1)
        v2_maj, v2_min = re.split('\.', v2)

        return (v1_maj > v2_maj or (v1_maj == v2_maj and v1_min >= v2_min));
