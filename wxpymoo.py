#!/usr/bin/python

import wx
import os, sys
from twisted.internet import wxreactor
wxreactor.install() # must be before 'import reactor'
from twisted.internet import reactor


def run():
    app = wx.App(False)

    app.path = os.path.dirname(sys.argv[0])

    from window.main import Main
    import prefs

    prefs.Initialize()
    frame = Main(None, "wxpymoo")
    frame.Show(True)

    reactor.registerWxApp(app)
    reactor.run()

    app.MainLoop()


if __name__ == "__main__":
    run()
