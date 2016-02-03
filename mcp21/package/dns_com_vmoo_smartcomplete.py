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

        mcp.registry.register(self, ['dns-com-vmoo-smartcomplete-result'])

    def request(self, callback, prefix, suffix = ""):
        request_id = str(wx.NewId())
        self.mcp.server_notify('dns-com-vmoo-smartcomplete-request', {
            'id'     : request_id,
            'prefix' : prefix,
            'suffix' : suffix,
            'channel' : '0',
        })
        self.callbacks[request_id] = callback

    def dispatch(self, msg):
        if msg.message == 'dns-com-vmoo-smartcomplete-result': self.do_result(msg)

    def do_result(self, msg):
        request_id = msg.data['id']
        callback = self.callbacks.pop(request_id, None)
        # TODO - maybe do more honoring of the msg.data['startpos'] etc returns
        if callback:
            options = msg.data.get('options')
            if options:
                options = list(set(options))
                options.sort()
                callback(options)
