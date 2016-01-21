import wx
import re

import prefs
import mcp21.core as mcp21

class DebugMCP(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title = "Debug MCP",
            style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE
        )

        self.active = False
        self.output_pane = None

        self.addEvents()

        if (True or prefs.get('save_mcp_window_size')):
            w = prefs.get('mcp_window_width')  or 600
            h = prefs.get('mcp_window_height') or 400
            self.SetSize([int(w), int(h)])

        self.output_pane = DebugMCPPane(self)
        sizer = wx.BoxSizer( wx.VERTICAL )
        sizer.Add(self.output_pane, 1, wx.ALL|wx.GROW, 5)
        self.SetSizer(sizer)

        # pre-stage monkey-patching
        mcp21.orig_debug = mcp21.debug

    def addEvents(self):
        self.Bind(wx.EVT_SIZE, self.onSize)

    def toggle_visible(self):
        if self.IsShown():
            self.Hide()
            self.active = False
            # de-monkey-patch mcp21
            mcp21.debug = mcp21.orig_debug
        else:
            self.Show()
            self.active = True
            # monkey-patch mcp21 so debug goes here
            mcp21.debug = self.display


    def Close(self):
        self.toggle_visible()

    def display(self, data):
        if not self.active: return

        op = self.output_pane

        serverMsgColour = wx.Colour(128, 0, 0)
        clientMsgColour = wx.Colour(0,   0, 128)
        plainMsgColour  = wx.Colour(0,   0, 0)

        for line in re.split('\n', data):
            if line == '': continue

            if   re.match('S->C', line): op.BeginTextColour(serverMsgColour)
            elif re.match('C->S', line): op.BeginTextColour(clientMsgColour)
            else:                        op.BeginTextColour(plainMsgColour)

            op.WriteText(line + "\n")
            op.EndTextColour()

        op.ShowPosition(op.GetCaretPosition())

    def onSize(self, evt):
        if (True or prefs.get('save_mcp_window_size')):
            size = self.GetSize()
            prefs.set('mcp_window_width',  size.GetWidth())
            prefs.set('mcp_window_height', size.GetHeight())
        evt.Skip()

class DebugMCPPane(wx.richtext.RichTextCtrl):

    def __init__(self, parent):
        wx.richtext.RichTextCtrl.__init__(self, parent, style = wx.TE_READONLY | wx.TE_NOHIDESEL)
