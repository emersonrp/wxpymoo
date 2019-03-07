import wx
import wx.media
import os
from appdirs import user_config_dir

import re

MSP_TRIGGER = re.compile('!!(SOUND|MUSIC)\((.*)\)')

# This sooorta ought to go under filters but no
def msp_filter(output_pane, data):
    return_val = ''

    for line in re.split('(\n)', data):
        matches = MSP_TRIGGER.match(line)
        if matches:
            sound_type = matches.group(1)
            payload    = re.split('\s+', matches.group(2))

            filename = payload.pop()
            params = {}
            for param in payload:
                k, v = re.split('=', param)
                params[k] = v
            output_pane.connection.msp_info.play_sound(sound_type, filename, params)
        else:
            return_val += line
    return return_val

class MSPInfo(wx.Dialog):
    def __init__(self, conn):
        worldname = conn.world.get('name')
        wx.Dialog.__init__(self, conn, title = "MSP Status: " + worldname,
            style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE
        )

        self.connection = conn

        self.players = {}

        self.sizer = wx.BoxSizer( wx.VERTICAL )
        self.SetSizer(self.sizer)

        self.connection.status_bar.feature_icons['MSP'].Bind(wx.EVT_LEFT_UP, self.toggle_visible)

        # make sure there's a sounds dir to spelunk in.
        self.sound_dir = user_config_dir('wxpymoo/sounds/' + worldname)
        if not os.path.exists(self.sound_dir):
            os.makedirs(self.sound_dir)

    def toggle_visible(self, evt = None):
        self.Fit()
        self.CenterOnParent()
        self.Show(not self.IsShown())
        if evt: evt.Skip()

    def Close(self):
        self.toggle_visible()

    def play_sound(self, sound_type, filename, params):
        print(f"MSPInfo going to play {sound_type}, {filename}, {params}")
        player = self.players.get(filename)
        if not player:
            player = PlayerPanel(self, filename)
            self.sizer.Add(player, 0)
            self.Layout()
            self.sizer.Fit(self)
            self.players[filename] = player

        player.mc.Play()

class PlayerPanel(wx.Panel):
    def __init__(self, parent, filename):
        wx.Panel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN)

        fullpath = os.path.join(parent.sound_dir, filename)
        self.mc = wx.media.MediaCtrl(self, -1, fullpath)

        btn2 = wx.Button(self, -1, "Play")
        self.Bind(wx.EVT_BUTTON, self.OnPlay, btn2)
        self.playBtn = btn2

        btn3 = wx.Button(self, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.OnPause, btn3)

        btn4 = wx.Button(self, -1, "Stop")
        self.Bind(wx.EVT_BUTTON, self.OnStop, btn4)

        slider = wx.Slider(self, -1, 0, 0, 10)
        self.slider = slider
        slider.SetMinSize((150, -1))
        self.Bind(wx.EVT_SLIDER, self.OnSeek, slider)

        # setup the layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        #sizer.Add(self.mc, 1, wx.EXPAND)
        sizer.Add(wx.StaticText(self, label = filename), 0, wx.EXPAND)
        sizer.Add(slider, 0)
        sizer.Add(btn2, 0)
        sizer.Add(btn3, 0)
        sizer.Add(btn4, 0)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(100)

    def OnPlay(self, evt):
        if not self.mc.Play():
            wx.MessageBox("Unable to Play media : Unsupported format?",
                          "ERROR",
                          wx.ICON_ERROR | wx.OK)
        else:
            self.mc.SetInitialSize()
            self.GetSizer().Layout()
            self.slider.SetRange(0, self.mc.Length())

    def OnPause(self, evt):
        self.mc.Pause()

    def OnStop(self, evt):
        self.mc.Stop()

    def OnSeek(self, evt):
        offset = self.slider.GetValue()
        self.mc.Seek(offset)

    def OnTimer(self, evt):
        offset = self.mc.Tell()
        self.slider.SetValue(offset)

