#!/usr/bin/env python3

import wx
import wx.richtext as rtc
import random

class OutputPane(rtc.RichTextCtrl):
    def __init__(self, parent):
        rtc.RichTextCtrl.__init__(self, parent, wx.TE_MULTILINE)

        for i in range(50):
            self.WriteText(''.join('*' for _ in range(random.choice(range(40)))) + "\n")

        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll)

    def on_scroll(self, evt):
        evt.Skip()
        if (evt.GetOrientation() == wx.VERTICAL):
            lastpos = self.GetLastPosition()
            print(f"lastpos is {lastpos}; At the bottom: {self.IsPositionVisible(lastpos)}")

app = wx.App(False)

frame = wx.Frame(None, -1, "Scrolling Test")
frame.Show()

frame.output_pane = OutputPane(frame)
frame.Layout()

app.MainLoop()

