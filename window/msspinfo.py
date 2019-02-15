import wx

serverMsgAttr = wx.TextAttr(wx.Colour(128, 0, 0))
clientMsgAttr = wx.TextAttr(wx.Colour(0,   0, 128))
plainMsgAttr  = wx.TextAttr(wx.Colour(0,   0, 0))

class MSSPInfo(wx.Dialog):
    def __init__(self, conn):
        worldname = conn.world.get('name')
        wx.Dialog.__init__(self, conn, title = "Debug MCP: " + worldname,
            style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE
        )

        self.connection = conn
        self.output_pane = wx.StaticText(self)

        # TODO - the MSSP messages should live somewhere else, like in telnetiac.mssp or something
        self.mssp_msgs = {}

        sizer = wx.BoxSizer( wx.VERTICAL )
        sizer.Add(self.output_pane, 1, wx.ALL|wx.GROW, 10)
        self.SetSizer(sizer)

        self.connection.status_bar.feature_icons['MSSP'].Bind(wx.EVT_LEFT_UP, self.toggle_visible)

        self.update()

    def toggle_visible(self, evt = None):
        self.update()
        self.Fit()
        self.Show(not self.IsShown())
        if evt: evt.Skip()

    def Close(self):
        self.toggle_visible()

    def add_message(self, msg):
        for k,v in msg.items():
            self.mssp_msgs[k] = v
        self.update()

    def update(self):
        output = ''
        for k in sorted(self.mssp_msgs.keys()):
            output += f"{k}: {self.mssp_msgs[k]}\n"

        self.output_pane.SetLabel(output)
