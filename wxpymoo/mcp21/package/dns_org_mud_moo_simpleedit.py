import re
import wxpymoo.mcp21.core as mcp21
import wxpymoo.mcp21.registry as registry
# import wxpymoo.editor as editor
from wxpymoo.mcp21.package import MCPPackageBase

class DNSOrgMudMooSimpleEdit(MCPPackageBase):
    def __init__(self):
        MCPPackageBase.__init__(self)

        self.package   = 'dns-org-mud-moo-simpleedit'
        self.min       = '1.0'
        self.max       = '1.0'

        self.in_progress = {}

        registry.register(self, ['dns-org-mud-moo-simpleedit-content'])

    def dispatch(self, msg):
        if msg['message'] == 'dns-org-mud-moo-simpleedit-content':
                self.dns_org_mud_moo_simpleedit_content(msg)

    def dns_org_mud_moo_simpleedit_content(self, msg):

#        id = editor.launch_editor({
#            'type'     : msg['data']['type'],
#            'content'  : msg['data']['content'],
#            'callback' : self._send_file_if_needed,
#        });
#        self.in_progress[id] = msg
        pass

    def _send_file_if_needed(send, id, content):
        msg = self.in_progress[id]
        mcp21.server_notify(
            'dns-org-mud-moo-simpleedit-set', {
                'reference' : msg['data']['reference'],
                'type'      : msg['data']['type'],
                'content'   : content,
            }
        )

