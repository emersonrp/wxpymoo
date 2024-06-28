import wx
import os
import time
import EnhancedStatusBar as ESB

# get the images once at compile time
icons = {}

class StatusBar(ESB.EnhancedStatusBar):

    def __init__(self, parent, connection):
        ESB.EnhancedStatusBar.__init__(self, parent)
        self.parent = parent
        self.connection = connection

        iconpath = os.path.join(wx.GetApp().path, "icons", "features")
        if os.path.exists(iconpath):
            for icon_file in os.listdir(iconpath):
                feature, _ = icon_file.split('.')
                icons[feature] = wx.Image(os.path.join(iconpath, icon_file)).ConvertToBitmap()

        # status field
        self.status_field = wx.Panel(self)

        # "feature icons" container
        self.feature_tray = wx.Window(self)
        self.feature_sizer = wx.BoxSizer()
        self.feature_icons = {}
        for i,w in icons.items():
            icon = FeatureIcon(self.feature_tray, i, w)
            self.feature_sizer.Add(icon, 0, wx.EXPAND|wx.SHAPED)
            icon.Hide()
            self.feature_icons[i] = icon
        self.feature_tray.SetSizerAndFit(self.feature_sizer)

        # connected-time widget
        self.conn_time = wx.StaticText(self, label = "--:--:--:--", style = wx.ALIGN_CENTER_HORIZONTAL)

        # "connection status" light
        self.conn_status = wx.Window(self)
        self.conn_status.SetBackgroundColour(wx.RED)

        # Activity blinker for when we're scrolled back
        self.activity_blinker = wx.Window(self)
        self.blinker_timer = None

        # placeholder to keep stuff from being on top of the resizer thumb
        self.spacer = wx.Window(self)

        self.SetFieldsCount(6)
        #self.SetStatusStyles([wx.SB_RAISED, wx.SB_NORMAL, wx.SB_NORMAL, wx.SB_NORMAL])

        self.AddWidget(self.status_field  , horizontalalignment = ESB.ESB_EXACT_FIT)
        self.AddWidget(self.feature_tray  , horizontalalignment = ESB.ESB_ALIGN_RIGHT , verticalalignment = ESB.ESB_EXACT_FIT)
        self.AddWidget(self.conn_time     , horizontalalignment = ESB.ESB_EXACT_FIT)
        self.AddWidget(self.conn_status   , horizontalalignment = ESB.ESB_EXACT_FIT)
        self.AddWidget(self.activity_blinker, horizontalalignment = ESB.ESB_EXACT_FIT)
        self.AddWidget(self.spacer        , horizontalalignment = ESB.ESB_EXACT_FIT)

        self.update_timer = wx.CallLater(1000, self.UpdateConnectionStatus)
        self.status_timer = None
        self.LayoutWidgets()

    def Destroy(self):
        if self.update_timer and self.update_timer.IsRunning():  self.update_timer.Stop()
        if self.status_timer and self.status_timer.IsRunning():  self.status_timer.Stop()

    def UpdateConnectionStatus(self, _ = None):
        self.update_timer.Restart(1000)
        conn = self.connection

        if conn.is_connected():
            self.conn_status.SetBackgroundColour(wx.GREEN)
            self.conn_status.Refresh()
        else:
            self.conn_status.SetBackgroundColour(wx.RED)
            self.conn_status.Refresh()
            self.conn_time.SetLabel('')
            self.conn_time.SetToolTip(None)
            self.LayoutWidgets()
            return

        if conn.connect_time:
            if not self.conn_time.GetToolTip():
                conn_time = time.localtime(conn.connect_time)
                self.conn_time.SetToolTip(time.strftime('Connected since: %c', conn_time))

            ctime = time.time() - conn.connect_time
            dd, rest = divmod(ctime, 3600 * 24)
            hh, rest = divmod(rest, 3600)
            mm, ss   = divmod(rest, 60)
            conn_time_str = '%02d:%02d:%02d:%02d' % (dd, hh, mm, ss)
        else:
            conn_time_str = '--:--:--:--'

        self.conn_time.SetLabel(conn_time_str)

    def LayoutWidgets(self):
        # calculate a reasonable size for "connected time"
        self.conn_time.SetLabel('00:00:00:00')
        conn_time_size = self.conn_time.GetClientSize()
        self.conn_time.SetLabel('')

        # Iterate the features, add icons
        for f, i in self.feature_icons.items():
            i.Show(True if f in self.connection.features else False)
        self.feature_tray.Fit()

        self.SetStatusWidths(
            [-1,                                   # status pane
                self.feature_tray.GetSize().width, # feature icons
                conn_time_size.Width + 3,          # conn timer
                self.GetSize().height + 2,         # status light
                12,                                # activity blinker
                self.GetSize().height + 2,         # placeholder
            ])

        self.OnSize(None)

    def AddStatus(self, status):
        self.SetStatusText(status, 2)
        if self.status_timer:
            if self.status_timer.IsRunning():
                self.status_timer.Restart(10000)
        self.status_timer = wx.CallLater(10000, self.ClearStatus)

    def ClearStatus(self):
        self.SetStatusText('', 2)

    def StartBlinker(self):
        if self.blinker_timer and self.blinker_timer.IsRunning(): return
        new_bg = (wx.RED if self.activity_blinker.GetBackgroundColour() != wx.RED else None)
        self.activity_blinker.SetBackgroundColour(new_bg)
        self.activity_blinker.Refresh()
        self.activity_blinker.SetToolTip("New text has arrived")
        self.blinker_timer = wx.CallLater(1000, self.StartBlinker)

    def StopBlinker(self):
        if self.blinker_timer and self.blinker_timer.IsRunning():
            self.blinker_timer.Stop()
            self.activity_blinker.SetBackgroundColour(None)
            self.activity_blinker.SetToolTip(None)

class FeatureIcon(wx.Panel):
    def __init__(self, parent, i, w):
        wx.Panel.__init__(self, parent)
        wx.StaticBitmap(self, -1, w)
        self.SetToolTip(i + " enabled")

    # Bind mouse events to the bitmaps inside the panel, add "hand" cursor
    def Bind(self, event, handler, source = None, id = wx.ID_ANY, id2 = wx.ID_ANY):
        if event == wx.EVT_LEFT_UP:
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            for c in self.GetChildren():
                c.Bind(event, handler)
        super(FeatureIcon, self).Bind(event, handler, source, id, id2)
