import wx
from worlds import World

class ConnectDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title = 'Connect to World', style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.parent = parent

        self.host = wx.TextCtrl(self)
        self.port = wx.TextCtrl(self)
        self.port.SetValue("7777")

        input_sizer = wx.FlexGridSizer(2, 2, 0, 0)
        input_sizer.AddGrowableCol( True )
        input_sizer.Add(wx.StaticText(self, label = "Host:"), 0, wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        input_sizer.Add(self.host,  0, wx.EXPAND | wx.ALL, 5)
        input_sizer.Add(wx.StaticText(self, label = "Port:"), 0, wx.LEFT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
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

        self.host.Bind(wx.EVT_SET_FOCUS, self.SelectAllText)
        self.port.Bind(wx.EVT_SET_FOCUS, self.SelectAllText)

        self.Bind(wx.EVT_BUTTON, self.connect_please, id = wx.ID_OK)
        self.host.Bind(wx.EVT_KEY_UP, self.check_fields)
        self.port.Bind(wx.EVT_KEY_UP, self.check_fields)

        self.check_fields(None);

    def Show(self, show = True):
        if show:
            self.Centre(wx.BOTH)
            self.host.SetFocus()
        super(wx.Dialog, self).Show(show)

    def SelectAllText(self, evt):
        evt.GetEventObject().SelectAll()
        evt.Skip()

    def check_fields(self, _):
        enable_button = False

        # both need to have something at all in it.
        for i in [self.host, self.port]:
            if i.GetValue() == "":
                yellow = wx.Colour(255,255,0)
                if yellow:
                    i.SetBackgroundColour(yellow)
            else:
                i.SetBackgroundColour(wx.WHITE)
                enable_button = True
        # deactivate the button if we're not aok with the values
        self.FindWindowById(wx.ID_OK).Enable(enable_button)

    def connect_please(self, _):
        host = self.host.GetValue()
        port = self.port.GetValue()

        if host and port:
            # TODO - make a notion of 'save the current world to worlds file'
            new_world = World({
                'name' : host + ":" + port,
                'host' : host,
                'port' : port,
            })
            self.parent.openWorld(new_world)

        self.Close()
