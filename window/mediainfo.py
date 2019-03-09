import wx
import wx.media
import re
import os, glob, random
import urllib.request
from appdirs import user_config_dir
from utility import platform

backend = {
    'windows' : wx.media.MEDIABACKEND_WMP10,
    'mac'     : wx.media.MEDIABACKEND_QUICKTIME,
    'linux'   : wx.media.MEDIABACKEND_GSTREAMER,
}[platform]

# get the images once at compile time
icons = {}
iconpath = os.path.join(wx.GetApp().path, "icons", "media")
if os.path.exists(iconpath):
    for icon_file in os.listdir(iconpath):
        button, _ = icon_file.split('.')
        icons[button] = wx.Image(os.path.join(iconpath, icon_file)).ConvertToBitmap()

MSP_TRIGGER = re.compile('!!(SOUND|MUSIC)\((.*)\)\n')

# This sooorta ought to go under filters but no
def msp_filter(output_pane, data):
    for matches in re.finditer(MSP_TRIGGER, data):
        sound_type = matches.group(1)
        payload    = re.split('\s+', matches.group(2))

        filename = payload.pop(0)
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
        safe_worldname = re.sub('[^\w\-_\. ]', '_', worldname)
        self.sound_dir = os.path.join(user_config_dir('wxpymoo'),'sounds', safe_worldname)
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

            # MSP param parsing
            if 'V' in params:
                print(f"Setting Volume to {params['V']}")
                player.SetVolume(int(params['V']))

            if 'L' in params:
                print(f"Setting Repeats to {params['L']}")
                player.SetRepeats(int(params['L']))

            if 'C' in params and sound_type == "MUSIC":
                print(f"Setting Continue to {params['C']}")
                player.SetContinue(int((params['C'])))

            if 'P' in params and sound_type == "SOUND":
                print(f"Setting Priority to {params['P']}")
                player.SetPriority(int(params['P']))

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
        wx.Panel.__init__(self, parent, -1, style = wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN)

        self.mc = wx.media.MediaCtrl(self, -1, szBackend = backend)
        self.play_queued = False
        self.repeats = 1
        self.cont = 1
        self.priority = 50
        self.current_volume = 100

        btn1 = wx.ToggleButton(self, style = wx.BU_EXACTFIT)
        if 'volume' in icons:
            btn1.SetBitmap(icons['volume'])
            btn1.SetBitmapPressed(icons['mute'])
        else:                 btn1.SetLabel('Mute')
        self.Bind(wx.EVT_BUTTON, self.OnMute, btn1)
        btn1.SetToolTip("Mute")

        volume_ctrl = wx.Slider(self, -1, 0, 0, 100)
        self.volume_ctrl = volume_ctrl
        volume_ctrl.SetMinSize((100, -1))
        self.Bind(wx.EVT_SLIDER, self.OnVol, volume_ctrl)
        volume_ctrl.SetToolTip("Volume")

        seekbar = wx.Slider(self, -1, 0, 0, 10)
        self.seekbar = seekbar
        seekbar.SetMinSize((150, -1))
        self.Bind(wx.EVT_SLIDER, self.OnSeek, seekbar)
        seekbar.SetToolTip("Seek")

        btn2 = wx.Button(self, style = wx.BU_EXACTFIT|wx.BORDER_NONE)
        if 'play' in icons: btn2.SetBitmap(icons['play'])
        else:               btn2.SetLabel('Play')
        self.Bind(wx.EVT_BUTTON, self.OnPlay, btn2)
        btn2.SetToolTip("Play")

        btn3 = wx.Button(self, style = wx.BU_EXACTFIT|wx.BORDER_NONE)
        if 'pause' in icons: btn3.SetBitmap(icons['pause'])
        else:                btn3.SetLabel('Pause')
        self.Bind(wx.EVT_BUTTON, self.OnPause, btn3)
        btn3.SetToolTip("Pause")

        btn4 = wx.Button(self, style = wx.BU_EXACTFIT|wx.BORDER_NONE)
        if 'stop' in icons: btn4.SetBitmap(icons['stop'])
        else:               btn4.SetLabel('Stop')
        self.Bind(wx.EVT_BUTTON, self.OnStop, btn4)
        btn4.SetToolTip("Stop")

        namelabel = wx.StaticText(self, label = label, style = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

        # setup the layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(btn1, 0, wx.ALIGN_CENTER)
        sizer.Add(namelabel, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(volume_ctrl, 0, wx.ALIGN_CENTER)
        sizer.Add(seekbar, 0, wx.ALIGN_CENTER)
        sizer.Add(btn2, 0, wx.ALIGN_CENTER|wx.ALL, 3)
        sizer.Add(btn3, 0, wx.ALIGN_CENTER|wx.ALL, 3)
        sizer.Add(btn4, 0, wx.ALIGN_CENTER|wx.ALL, 3)
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
        self.SetVolume(self.current_volume)
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
            self.seekbar.SetRange(0, self.mc.Length())

    def OnMute(self, evt):
        pass

    def OnPause(self, evt):
        self.mc.Pause()

    def OnStop(self, evt):
        self.mc.Stop()

    def OnSeek(self, evt):
        offset = self.seekbar.GetValue()
        self.mc.Seek(offset)

    def OnVol(self, evt):
        volume = self.volume_ctrl.GetValue()
        self.mc.SetVolume(volume / 100)

    def OnTimer(self, evt):
        offset = self.mc.Tell()
        self.seekbar.SetValue(offset)

    def SetVolume(self, volume):
        self.volume_ctrl.SetValue(volume)
        self.current_volume = volume
        self.mc.SetVolume(volume / 100)

    def SetRepeats(self, repeats):
        self.repeats = repeats

    def SetContinue(self, cont):
        self.cont = cont

    def SetPriority(self, priority):
        self.priority = priority
