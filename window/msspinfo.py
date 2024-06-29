import wx

class MSSPInfo(wx.Dialog):
    def __init__(self, conn):
        worldname = conn.world.get('name')
        wx.Dialog.__init__(self, conn, title = "MSSP Info: " + worldname,
            style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE
        )

        self.connection = conn
        self.output_list = wx.ListCtrl(self, style = wx.LC_REPORT)

        # TODO - the MSSP messages should live somewhere else, like in telnetiac.mssp or something
        self.mssp_msgs = {}

        sizer = wx.BoxSizer( wx.VERTICAL )
        sizer.Add(self.output_list, 1, wx.ALL|wx.GROW, 10)
        self.SetSizer(sizer)

        self.connection.status_bar.feature_icons['MSSP'].Bind(wx.EVT_LEFT_UP, self.toggle_visible)

        self.update()

    def toggle_visible(self, evt = None):
        if self.IsShown():
            self.Hide()
        else:
            self.update()
            self.Layout()
            self.CenterOnParent()
            self.Show()
        if evt: evt.Skip()

    def add_message(self, msg):
        for k,v in msg.items():
            self.mssp_msgs[k] = v

    def update(self):
        self.output_list.ClearAll()
        self.output_list.AppendColumn("Variable")
        self.output_list.AppendColumn("Value")
        for k in sorted(self.mssp_msgs.keys()):
            self.output_list.Append([k, self.mssp_msgs[k]])
        self.output_list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.output_list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
