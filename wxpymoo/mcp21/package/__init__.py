import wx

class MCPPackageBase(wx.EvtHandler):
    def __init__(self):
        wx.EvtHandler.__init__(self)

        self.activated = None
        self.callback = None
        self.max = 0.0
        self.min = 0.0
        self.message = ''
        self.package = ''

    def Initialize(self):
        pass
