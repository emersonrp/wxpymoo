#!/usr/bin/env python3

import wx
import os, sys
from wxasync import WxAsyncApp
from window.main import Main

import prefs
import worlds
import theme

def run():
    app = WxAsyncApp()

    wx.Log.SetActiveTarget(wx.LogStderr())

    app.path = os.path.dirname(sys.argv[0])

    # Let's try to unbuffer "print" for easier debug
    # This per "Perkins"' comment on https://stackoverflow.com/questions/107705/disable-output-buffering
    import builtins
    import functools
    builtins.print = functools.partial(print, flush=True)

    prefs.Initialize()
    worlds.Initialize()
    theme.Initialize()

    frame = Main(None, "wxpymoo")
    frame.Show(True)

    app.loop.run_until_complete(app.MainLoop())

if __name__ == "__main__":
    run()
