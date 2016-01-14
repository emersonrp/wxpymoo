#!/usr/bin/python

import wx
from twisted.internet import wxreactor
wxreactor.install() # must be before 'import reactor'
from twisted.internet import reactor

import wxpymoo.prefs
from wxpymoo.window.main import Main

def run():
    app = wx.App(False)

    reactor.registerWxApp(app)

    wxpymoo.prefs.Initialize()
    frame = Main(None, "wxpymoo")
    frame.Show(True)
    reactor.run()
    app.MainLoop()

if __name__ == "__main__":
    run()
