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

        self.media_ctrls = {}

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
        fullpath = os.path.join(self.sound_dir, filename)
        if not os.path.exists(fullpath):
            print(f"MSP told to play missing file {fullpath} -- Did you download the sounds for this world?")
        else:
            mc = wx.media.MediaCtrl(self, -1, fullpath)
            self.sizer.Add(mc, 1, wx.EXPAND)
            self.Fit()
            self.Layout()
            self.media_ctrls[filename] = mc

            mc.Play()
