#!/usr/bin/env python3

import os, sys
from wxasync import WxAsyncApp
from window.main import Main

import prefs
import worlds
import theme

def run():
    app = WxAsyncApp()

    app.path = os.path.dirname(sys.argv[0])

    prefs.Initialize()
    worlds.Initialize()
    theme.Initialize()

    frame = Main(None, "wxpymoo")
    frame.Show(True)

    app.loop.run_until_complete(app.MainLoop())

if __name__ == "__main__":
    run()
