import wx
import wx.media
import os, glob, random
import urllib.request
from appdirs import user_config_dir
from utility import platform

backend = {
    'windows' : wx.media.MEDIABACKEND_WMP10,
    'mac'     : wx.media.MEDIABACKEND_QUICKTIME,
    'linux'   : wx.media.MEDIABACKEND_GSTREAMER,
}[platform]

import re

MSP_TRIGGER = re.compile('!!(SOUND|MUSIC)\((.*)\)\n')

# This sooorta ought to go under filters but no
def msp_filter(output_pane, data):
    for matches in re.finditer(MSP_TRIGGER, data):
        sound_type = matches.group(1)
        payload    = re.split('\s+', matches.group(2))

        filename = payload.pop()
        params = {}
        for param in payload:
            k, v = re.split('=', param)
            params[k] = v
        output_pane.connection.media_info.play_msp_sound(sound_type, filename, params)

    return re.sub(MSP_TRIGGER, '', data)

#####################
class MediaInfo(wx.Dialog):
    def __init__(self, conn):
        worldname = conn.world.get('name')
        wx.Dialog.__init__(self, conn, title = "Media Status: " + worldname,
            style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE
        )

        self.connection = conn

        self.players  = {}
        self.base_url = ''

        self.sizer = wx.BoxSizer( wx.VERTICAL )
        self.SetSizer(self.sizer)

        self.connection.status_bar.feature_icons['MSP'].Bind(wx.EVT_LEFT_UP, self.toggle_visible)

        # make sure there's a sounds dir to spelunk in / download into
        self.sound_dir = os.path.join(user_config_dir('wxpymoo'),'sounds',worldname)
        if not os.path.exists(self.sound_dir):
            print(f"no sound dir, making {self.sound_dir}")
            os.makedirs(self.sound_dir)

    def toggle_visible(self, evt = None):
        self.Fit()
        self.CenterOnParent()
        self.Show(not self.IsShown())
        if evt: evt.Skip()

    def Close(self):
        self.toggle_visible()

    def play_msp_sound(self, sound_type, filename, params):
        print(f"MediaInfo going to play {sound_type}, {filename}, {params}")
        fullpath = ''

        if filename == "Off":
            if not params:
                for p in self.players.values():
                    p.Stop()
            elif 'U' in params:
                base_url = params['U']
                if not base_url.endswith('/'): base_url += "/"
                print(f"Setting base url for downloads to {base_url}")
                self.base_url = base_url
            # else/also got "Off" with some other param -- undefined behavior, ignore
            return

        else:
            # TODO - parse filename for wildcards and bail on invalid name
            if os.path.isabs(filename):
                print(f"Error: absolute filename specified in MSP path  '{filename}', ignoring")
                return

            # only one '*' allowed:
            starcheck = re.search('(\*)', filename)
            if starcheck and len(starcheck.groups()) > 1:
                print(f"Error: too many '*' wildcards in MSP path '{filename}', ignoring")
                return

            # [ ] are treated specially by 'glob' but not supported in the spec; escape them
            globfile = re.sub(r'(\[|\])', '[\g<1>]', filename)

            # Now we should have a sane filename, let's go search for it

            paths_to_check = [os.path.join(self.sound_dir, globfile)]
            # params['T'] can be used to specify subdir, so try that first:
            if 'T' in params:
                paths_to_check = [os.path.join(self.sound_dir, params['T'], filename)] + paths_to_check

            for checkpath in paths_to_check:
                print(f"about to check for {checkpath}")
                filelist = glob.glob(checkpath)
                if filelist:
                    # We got results;  if there's more than one, pick one at random
                    fullpath = (filelist[0] if len(filelist) == 1 else random.choice(filelist))
                    break

            if not fullpath:   # glob didn't find it
                print(f"Didn't find local sound {filename}, can we download it?")
                url_path = params.get('U') or self.base_url
                if not url_path:
                    print(f"No URL info to try to fetch {filename}, ignoring")
                    return
                if not url_path.endswith('/'): url_path += "/"

                extra_path = ''

                urls_to_check = [filename]
                # params['T'] can be used to specify subdir, so try that first:
                if 'T' in params:
                    extra_path = params['T']
                    urls_to_check = [extra_path + "/" + filename] + urls_to_check

                for url in urls_to_check:
                    newfile, headers = urllib.request.urlretrieve(url_path + filename,
                            os.path.join(self.sound_dir, extra_path, filename))
                    # TODO - how do we check for errors?
                    if os.path.exists(newfile):
                        print(f"Found MSP sound {filename} at {url_path + filename}, saving to {newfile}")
                        fullpath = newfile
                        break

            # ostensibly we have a file by now
            if not fullpath:
                print(f"Somehow still don't have a file for MSP sound {filename}, skipping")
                return

            player = self.players.get(filename) or self.make_player(filename, fullpath)
            if not player: return

            # TODO - parse params and set MediaCtrl appropriately
            player.OnPlay()

    def make_player(self, label, fullpath):
        player = PlayerPanel(self, label, fullpath)
        if player:
            self.sizer.Add(player, 0, wx.EXPAND)
            self.Layout()
            self.sizer.Fit(self)
            self.players[label] = player
        return player


class PlayerPanel(wx.Panel):
    def __init__(self, parent, label, fullpath):
        wx.Panel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN)

        self.mc = wx.media.MediaCtrl(self, -1, szBackend = backend)
        self.play_queued = False

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
        sizer.Add(wx.StaticText(self, label = label, style = wx.ALIGN_RIGHT), 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(slider, 0)
        sizer.Add(btn2, 0)
        sizer.Add(btn3, 0)
        sizer.Add(btn4, 0)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(100)

        self.Bind(wx.media.EVT_MEDIA_LOADED, self.OnLoad)

        if not self.mc.Load(fullpath):
            print(f"Can't find sound file {fullpath} - did you download the sound files for this world?")
            return None

    def OnLoad(self, evt):
        if self.play_queued:
            self.play_queue = False
            self.OnPlay()

    def OnPlay(self, evt = None):
        if self.mc.GetState() == wx.media.MEDIASTATE_PLAYING: return

        # We're calling "Play" up above whether or not we've just made the mediactrl,
        # so if we're not fully loaded yet, set a flag for OnLoad() to catch and play.
        if self.mc.Length() == 0:
            self.play_queued = True
            return

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

