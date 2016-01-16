import re
from wxpymoo.mcp21.package import MCPPackageBase

msg_registry = {}
packages = {}

def register(pkg, messages):
    if not isinstance(pkg, MCPPackageBase):
        print("something that isn't an MCP package tried to register")
        return
    packages[pkg.package] = pkg
    for message in messages:
        msg_registry[message] = pkg

# next two subs taken from MCP 2.1 specification, section 2.4.3
def get_best_version(pkg, smin, smax):
    if not packages.has_key(pkg): return

    cmax = packages[pkg].max
    cmin = packages[pkg].min

    if (_version_cmp(cmax, smin) and _version_cmp(smax, cmin)):
        if _version_cmp(smax, cmax):
            return cmax
        else:
            return smax
    else:
        return undef

def _version_cmp(v1, v2):
    v1_maj, v1_min = re.split('\.', v1)
    v2_maj, v2_min = re.split('\.', v2)

    return (v1_maj > v2_maj or (v1_maj == v2_maj and v1_min >= v2_min));
