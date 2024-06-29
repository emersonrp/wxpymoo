import wx
import wx.media
import wx.lib.scrolledpanel as scrolled
import re
import os, glob, random, sys
import platform
import urllib.request
from pathlib import Path
import prefs

backend = {
    'Windows' : wx.media.MEDIABACKEND_WMP10,
    'Darwin'  : wx.media.MEDIABACKEND_QUICKTIME,
    'Linux'   : wx.media.MEDIABACKEND_GSTREAMER,
}[platform.system()]

MSP_TRIGGER = re.compile(r'!!(SOUND|MUSIC)\((.*)\)\n')

# This sooorta ought to go under filters but no
def msp_filter(output_pane, data):
    for matches in re.finditer(MSP_TRIGGER, data):
        sound_type = matches.group(1)
        payload    = re.split(r'\s+', matches.group(2))

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

        #mainwindow = wx.GetApp().GetTopWindow()
        #size = mainwindow.GetSize()
        #self.SetMaxSize((int(size.GetWidth() * 0.75), int(size.GetHeight() * 0.75)))
        self.SetMaxSize((800,400))

        self.connection = conn

        self.players  = {}
        self.base_url = ''

        self.sp = scrolled.ScrolledPanel(self, -1, size = self.GetMaxSize())

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sp.SetSizer(self.sizer)
        self.sp.SetAutoLayout(1)
        self.sp.SetupScrolling(scroll_x = False)

        self.connection.status_bar.feature_icons['MSP'].Bind(wx.EVT_LEFT_UP, self.toggle_visible)

        # make sure there's a sounds dir to spelunk in / download into
        safe_worldname = re.sub(r'[^\w\-_\. ]', '_', worldname)
        self.sound_dir = prefs.get_prefs_dir() / 'sounds' / safe_worldname
        if not self.sound_dir.exists():
            wx.LogMessage(f"no sound dir, making {self.sound_dir}")
            self.sound_dir.mkdir(parents = True)

    def make_player(self, filename, fullpath):
        player = PlayerPanel(self.sp, filename, fullpath)
        if player:
            self.sizer.Add(player, 0, wx.EXPAND)
            self.sizer.Fit(self.sp)
            self.players[filename] = player
        return player

    def toggle_visible(self, evt = None):
        self.Fit()
        self.CenterOnParent()
        self.Show(not self.IsShown())
        if evt: evt.Skip()

    def Close(self, force = False):
        self.toggle_visible()

    def play_msp_sound(self, sound_type, filename, params):
        wx.LogMessage(f"MediaInfo going to play {sound_type}, {filename}, {params}")
        fullpath = ''

        if filename == "Off":
            if not params:
                for p in self.players.values():
                    p.Stop()
            elif 'U' in params:
                base_url = params['U']
                if not base_url.endswith('/'): base_url += "/"
                wx.LogMessage(f"Setting base url for downloads to {base_url}")
                self.base_url = base_url
            # else/also got "Off" with some other param -- undefined behavior, ignore
            return

        else:
            # TODO - parse filename for wildcards and bail on invalid name
            if os.path.isabs(filename):
                wx.LogError(f"Error: absolute filename specified in MSP path  '{filename}', ignoring")
                return

            # only one '*' allowed:
            starcheck = re.search(r'(\*)', filename)
            if starcheck and len(starcheck.groups()) > 1:
                wx.LogError(f"Error: too many '*' wildcards in MSP path '{filename}', ignoring")
                return

            # [ ] are treated specially by 'glob' but not supported in the spec; escape them
            globfile = re.sub(r'(\[|\])', r'[\g<1>]', filename)

            # Now we should have a sane filename, let's go search for it

            paths_to_check = [os.path.join(self.sound_dir, globfile)]
            # params['T'] can be used to specify subdir, so try that first:
            if 'T' in params:
                paths_to_check = [os.path.join(self.sound_dir, params['T'], filename)] + paths_to_check

            for checkpath in paths_to_check:
                wx.LogMessage(f"about to check for {checkpath}")
                filelist = glob.glob(checkpath)
                if filelist:
                    # We got results;  if there's more than one, pick one at random
                    fullpath = (filelist[0] if len(filelist) == 1 else random.choice(filelist))
                    break

            if not fullpath:   # glob didn't find it
                wx.LogMessage(f"Didn't find local sound {filename}, can we download it?")
                url_path = params.get('U') or self.base_url
                if not url_path:
                    wx.LogMessage(f"No URL info to try to fetch {filename}, ignoring")
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
                        wx.LogMessage(f"Found MSP sound {filename} at {url_path + filename}, saving to {newfile}")
                        fullpath = newfile
                        break

            # ostensibly we have a file by now
            if not fullpath:
                wx.LogError(f"Somehow still don't have a file for MSP sound {filename}, skipping")
                return

            player = self.players.get(filename) or self.make_player(filename, fullpath)
            if not player: return

            # MSP param parsing
            if 'V' in params:
                wx.LogMessage(f"Setting Volume to {params['V']}")
                player.SetVolume(int(params['V']))

            if 'L' in params:
                wx.LogMessage(f"Setting Repeats to {params['L']}")
                player.SetRepeats(int(params['L']))

            if 'C' in params and sound_type == "MUSIC":
                wx.LogMessage(f"Setting Continue to {params['C']}")
                player.SetContinue(int((params['C'])))

            if 'P' in params and sound_type == "SOUND":
                wx.LogMessage(f"Setting Priority to {params['P']}")
                player.SetPriority(int(params['P']))


class PlayerPanel(wx.Panel):

    icons = {}

    def __init__(self, parent, filename, fullpath):
        wx.Panel.__init__(self, parent, -1, style = wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN)

        self.mc = wx.media.MediaCtrl(self, -1, szBackend = backend)
        self.repeats = 1
        self.cont = 1
        self.priority = 50
        self.current_volume = 100
        self.previous_volume = 100 # for when we mute and then unmute

        if not self.icons:
            if hasattr(sys, '_MEIPASS'):
                configpath = Path(sys._MEIPASS) # pyright: ignore
            else:
                configpath = Path(wx.GetApp().path)

            iconpath = configpath / 'icons' / 'media'
            if iconpath.exists():
                for icon_file in iconpath.glob('*'):
                    button = icon_file.stem
                    self.icons[button] = wx.Bitmap(str(icon_file))

        btn1 = wx.ToggleButton(self, style = wx.BU_EXACTFIT|wx.BORDER_NONE, size = (20,20))
        btn1.SetBitmap(self.icons['volume'])
        btn1.SetBitmapPressed(self.icons['mute'])
        btn1.Bind(wx.EVT_TOGGLEBUTTON, self.OnMute)
        btn1.SetToolTip("Mute")

        medialabel = wx.StaticText(self, label = Path(filename).stem, size = (150,-1),
                                  style = wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_MIDDLE,)

        volume_ctrl = wx.Slider(self, -1, 0, 0, 100)
        self.volume_ctrl = volume_ctrl
        volume_ctrl.SetMinSize((100, -1))
        volume_ctrl.Bind(wx.EVT_SLIDER, self.OnVol)
        volume_ctrl.SetToolTip("Volume")

        seekbar = wx.Slider(self, -1, 0, 0, 10)
        self.seekbar = seekbar
        seekbar.SetMinSize((150, -1))
        seekbar.Bind(wx.EVT_SLIDER, self.OnSeek)
        seekbar.SetToolTip("Seek")

        btn2 = wx.Button(self, style = wx.BU_EXACTFIT|wx.BORDER_NONE, size = (20,20))
        btn2.SetBitmap(self.icons['play'])
        btn2.Bind(wx.EVT_BUTTON, self.OnPlay)
        btn2.SetToolTip("Play")

        btn3 = wx.Button(self, style = wx.BU_EXACTFIT|wx.BORDER_NONE, size = (20,20))
        btn3.SetBitmap(self.icons['pause'])
        btn3.Bind(wx.EVT_BUTTON, self.OnPause)
        btn3.SetToolTip("Pause")

        btn4 = wx.Button(self, style = wx.BU_EXACTFIT|wx.BORDER_NONE, size = (20,20))
        btn4.SetBitmap(self.icons['stop'])
        btn4.Bind(wx.EVT_BUTTON, self.OnStop)
        btn4.SetToolTip("Stop")

        # setup the layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(btn1,        0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        sizer.Add(medialabel,  0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        sizer.Add(volume_ctrl, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        sizer.Add(seekbar,     2, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        sizer.Add(btn2,        0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        sizer.Add(btn3,        0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        sizer.Add(btn4,        0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self.Bind(wx.media.EVT_MEDIA_LOADED, self.OnLoad)
        self.Bind(wx.media.EVT_MEDIA_STOP,   self.OnStop)

        if not self.mc.Load(fullpath):
            wx.LogMessage(f"Can't find sound file {fullpath} - did you download the sound files for this world?")
            return None

    def OnLoad(self, _):
        self.SetVolume(self.current_volume)
        self.OnPlay()
        self.seekbar.SetRange(0, self.mc.Length())

    def OnPlay(self, _ = None):
        state = self.mc.GetState()
        if state == wx.media.MEDIASTATE_PLAYING:
            return
        elif state == wx.media.MEDIASTATE_STOPPED:
            self.mc.Seek(0)

        if not self.mc.Play():
            wx.MessageBox("Unable to Play media : Unsupported format?",
                          "ERROR",
                          wx.ICON_ERROR | wx.OK)
        else:
            self.timer.Start(100)
            #self.mc.SetInitialSize()
            #self.GetSizer().Layout()

    def OnMute(self, evt):
        button = evt.EventObject
        if button.GetValue(): # is pressed
            self.previous_volume = self.current_volume
            self.SetVolume(0)
        else:
            self.SetVolume(self.previous_volume)

    def OnPause(self, _):
        state = self.mc.GetState()
        if state == wx.media.MEDIASTATE_PLAYING:
            self.mc.Pause()
        elif state == wx.media.MEDIASTATE_PAUSED:
            self.mc.Play()

    def OnStop(self, evt):
        if self.repeats > 0:
            self.repeats -= 1
        if evt.GetEventType() == wx.wxEVT_BUTTON:
            # pressed the stop button, presumably we
            # explicitly want not to hear it any more
            self.repeats = 0
        elif self.repeats != 0:
            # either there are more, or we were originally sent -1,
            # which according to the spec means "repeat indefinitely"
            self.OnPlay()
            return
        self.mc.Stop()
        self.mc.Seek(0)
        self.seekbar.SetValue(0)
        self.timer.Stop()

    def OnSeek(self, _):
        offset = self.seekbar.GetValue()
        self.mc.Seek(offset)

    def OnVol(self, _):
        volume = self.volume_ctrl.GetValue()
        self.mc.SetVolume(volume / 100)

    def OnTimer(self, _):
        offset = self.mc.Tell()
        self.seekbar.SetValue(offset)

    def SetVolume(self, volume):
        self.volume_ctrl.SetValue(volume)
        self.current_volume = volume
        self.previouv_volume = volume
        self.mc.SetVolume(volume / 100)

    def SetRepeats(self, repeats):
        self.repeats = repeats

    def SetContinue(self, cont):
        self.cont = cont

    def SetPriority(self, priority):
        self.priority = priority
