#!/usr/bin/env python3

import wx
import os, sys
from wxasync import WxAsyncApp
import asyncio
from asyncio.events import get_event_loop

def run():
    app = WxAsyncApp()

    app.path = os.path.dirname(sys.argv[0])

    from window.main import Main
    import prefs
    import worlds

    prefs.Initialize()
    worlds.Initialize()

    frame = Main(None, "wxpymoo")
    frame.Show(True)

    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())

if __name__ == "__main__":
    run()
