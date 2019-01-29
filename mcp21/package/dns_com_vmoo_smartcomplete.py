import wx
import re
from mcp21.package import MCPPackageBase


class MCPPackage(MCPPackageBase):
    def __init__(self, mcp):
        MCPPackageBase.__init__(self, mcp)

        self.package   = 'dns-com-vmoo-smartcomplete'
        self.min       = '1.0'
        self.max       = '1.0'
        self.callbacks = {}

        mcp.register(self, ['dns-com-vmoo-smartcomplete-result'])

    def mcp_negotiate_end(self):
        # TODO - is there a less intrusive way to do this?
        self.mcp.connection.input_pane.tab_completion.completers = self

    def request(self, callback, prefix, suffix = ""):
        request_id = str(wx.NewId())
        self.mcp.server_notify('dns-com-vmoo-smartcomplete-request', {
            'id'     : request_id,
            'prefix' : prefix,
            'suffix' : suffix,
            'channel' : '0',
        })
        self.callbacks[request_id] = (prefix, callback)

    def dispatch(self, msg):
        if msg.message == 'dns-com-vmoo-smartcomplete-result': self.do_result(msg)

    def do_result(self, msg):
        request_id = msg.data['id']
        to_complete, callback = self.callbacks.pop(request_id, None)
        if callback:
            completions = msg.data.get('options')
            if completions:
                completions = list(set(completions))
                completions.sort()
                callback(msg.data.get('startpos'), to_complete, completions)
