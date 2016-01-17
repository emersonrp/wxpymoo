import mcp21.core as mcp21
import mcp21.registry as registry
from mcp21.package import MCPPackageBase

from editor import Editor
class MCPPackage(MCPPackageBase):
    def __init__(self):
        MCPPackageBase.__init__(self)

        self.package = 'dns-org-mud-moo-simpleedit'
        self.min     = '1.0'
        self.max     = '1.0'

        self.in_progress = {}

        registry.register(self, ['dns-org-mud-moo-simpleedit-content'])

    def dispatch(self, msg):
        if msg.message == 'dns-org-mud-moo-simpleedit-content':
                self.dns_org_mud_moo_simpleedit_content(msg)

    def dns_org_mud_moo_simpleedit_content(self, msg):
        editor = Editor({
            'filetype' : msg.data['type'],
            'content'  : msg.data['content'],
            'callback' : self._send_file
        })
        self.in_progress[editor._id] = msg

    def _send_file(self, id, content):
        msg = self.in_progress[id]
        mcp21.server_notify(
            'dns-org-mud-moo-simpleedit-set', {
                'reference' : msg.data['reference'],
                'type'      : msg.data['type'],
                'content'   : content,
            }
        )