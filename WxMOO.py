#!/usr/bin/python

import wx
from WxMOO.Window.Main import Main

def run():
    app = wx.App(False)
    frame = Main(None, "WxMOO")
    frame.Show(True)
    app.MainLoop()

if __name__ == "__main__":
    run()
