import wx
from worlds import World

class ConnectDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, name = 'Connect to World', style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.parent = parent
        self.host = ''
        self.port = ''

        host_label = wx.StaticText(self, label = "Host:")
        port_label = wx.StaticText(self, label = "Port:")
        self.host = wx.TextCtrl(self)
        self.port = wx.SpinCtrl(self)
        self.port.SetRange(1, 65535)
        self.port.SetValue(7777)

        self.host.SetBackgroundColour(wx.YELLOW)

        input_sizer = wx.FlexGridSizer(2, 2, 0, 0)
        input_sizer.AddGrowableCol( True )
        input_sizer.Add(host_label, 0, wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        input_sizer.Add(self.host,  0, wx.EXPAND | wx.ALL, 5)
        input_sizer.Add(port_label, 0, wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        input_sizer.Add(self.port,  0, wx.EXPAND | wx.ALL, 5)

        button_sizer = self.CreateButtonSizer( wx.OK | wx.CANCEL )

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(input_sizer,  True,  wx.ALL | wx.EXPAND, 10)
        sizer.Add(button_sizer, False, wx.ALL, 10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Centre(wx.BOTH)

        self.FindWindowById(wx.ID_OK).Enable(False)

        self.Bind(wx.EVT_BUTTON, self.connect_please, id = wx.ID_OK)
        self.host.Bind(wx.EVT_KEY_UP, self.check_fields)

    def check_fields(self, evt):
        test_host = self.host.GetValue()
        enable_button = False

        # host needs to have something at all in it.
        # TODO -- check for "looks like hostname or ip"?  Maybe not.
        if test_host:
            self.host.SetBackgroundColour(wx.WHITE)
            enable_button = True
        else:
            self.host.SetBackgroundColour(wx.YELLOW)

        # deactivate the button if we're not aok with the values
        self.FindWindowById(wx.ID_OK).Enable(enable_button)


    def connect_please(self, evt):
        host = self.host.GetValue()
        port = self.port.GetValue()

        if host and port:
            new_world = World({
                'host' : host,
                'port' : port,
                'name' : 'New Connection',
            })
            self.parent.openWorld(new_world)

        self.Close()
