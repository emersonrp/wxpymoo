#!/usr/bin/python

import wx
from twisted.internet import wxreactor
wxreactor.install() # must be before 'import reactor'
from twisted.internet import reactor


def run():
    app = wx.App(False)

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
