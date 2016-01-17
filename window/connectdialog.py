import wx

class ConnectDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, name = 'Connect to World', style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.parent = parent
        self.host = ''
        self.port = ''

        host_label = wx.StaticText(self, label = "Host:")
        port_label = wx.StaticText(self, label = "Port:")
        self.host = wx.TextCtrl(self)
        self.port = wx.TextCtrl(self)

        input_sizer = wx.FlexGridSizer(2, 2, 0, 0)
        input_sizer.AddGrowableCol( True )
        input_sizer.Add(host_label, 0, wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        input_sizer.Add(self.host,  0, wx.EXPAND | wx.ALL, 5)
        input_sizer.Add(port_label, 0, wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        input_sizer.Add(self.port, 0 , wx.EXPAND | wx.ALL, 5)


        button_sizer = self.CreateButtonSizer( wx.OK | wx.CANCEL )

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(input_sizer,  True,  wx.ALL | wx.EXPAND, 10)
        sizer.Add(button_sizer, False, wx.ALL, 10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_BUTTON, self.connect_please, id=wx.ID_OK)

    def connect_please(self, evt):
        host = self.host.GetValue()
        port = self.port.GetValue()

        if host and port:
            self.host.Clear()
            self.port.Clear()
            self.parent.connection.connect(host, int(port))

        self.Close()
