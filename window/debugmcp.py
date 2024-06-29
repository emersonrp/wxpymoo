import wx
import re

import prefs


serverMsgAttr = wx.TextAttr(wx.Colour(128, 0, 0))
clientMsgAttr = wx.TextAttr(wx.Colour(0,   0, 128))
plainMsgAttr  = wx.TextAttr(wx.Colour(0,   0, 0))

class DebugMCP(wx.Dialog):
    def __init__(self, parent, conn):
        worldname = conn.world.get('name')
        wx.Dialog.__init__(self, parent, title = "Debug MCP: " + worldname,
            style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE
        )

        self.connection = conn
        self.output_pane = wx.TextCtrl(self,
                style = wx.TE_READONLY | wx.TE_NOHIDESEL | wx.TE_MULTILINE | wx.TE_RICH)

        self.addEvents()

        config = wx.ConfigBase.Get()
        if (config.ReadBool('save_mcp_window_size')):
            w = config.ReadInt('mcp_window_width')  or 600
            h = config.ReadInt('mcp_window_height') or 400
            self.SetSize([int(w), int(h)])

        sizer = wx.BoxSizer( wx.VERTICAL )
        sizer.Add(self.output_pane, 1, wx.ALL|wx.GROW, 5)
        self.SetSizer(sizer)

        self.connection.status_bar.feature_icons['MCP'].Bind(wx.EVT_LEFT_UP, self.toggle_visible)

    def addEvents(self):
        self.Bind(wx.EVT_SIZE, self.onSize)

    def toggle_visible(self, evt = None):
        self.Show(not self.IsShown())
        if evt: evt.Skip()

    def Close(self, force = False):
        self.toggle_visible()

    def display(self, data):
        op = self.output_pane

        for line in re.split('\n', data):
            if line == '': continue

            if   re.match('S->C', line): op.SetDefaultStyle(serverMsgAttr)
            elif re.match('C->S', line): op.SetDefaultStyle(clientMsgAttr)
            else:                        op.SetDefaultStyle(plainMsgAttr)

            op.WriteText(line + "\n")

        op.ShowPosition(op.GetInsertionPoint())

    def onSize(self, evt):
        config = wx.ConfigBase.Get()
        if (config.ReadBool('save_mcp_window_size')):
            size = self.GetSize()
            config.WriteInt('mcp_window_width',  size.GetWidth())
            config.WriteInt('mcp_window_height', size.GetHeight())
        evt.Skip()
