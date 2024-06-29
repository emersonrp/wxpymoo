#!/usr/bin/env python3

import wx
from pathlib import Path
from wxasync import WxAsyncApp
import asyncio
from window.main import Main

import prefs
import worlds
import theme

async def run():
    app = WxAsyncApp()

    wx.Log.SetActiveTarget(wx.LogStderr())

    setattr(app, 'path', Path(__file__).parents[0])

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

    await app.MainLoop()

if __name__ == "__main__":
    asyncio.run(run())
