import wx
import os
import prefs
import datetime, time
import EnhancedStatusBar as ESB
from utility import platform

iconpath = os.path.join(wx.GetApp().path, "icons")
class StatusBar(ESB.EnhancedStatusBar):

    def __init__(self, parent, connection):
        ESB.EnhancedStatusBar.__init__(self, parent)
        self.parent = parent
        self.connection = connection

        # status field
        self.status_field = wx.Panel(self)

        # "feature icons" container
        self.feature_tray = wx.Window(self)
        self.feature_sizer = wx.BoxSizer()
        self.feature_tray.SetSizer(self.feature_sizer)
        self.feature_icons = {}

        # connected-time widget
        self.conn_time = wx.StaticText(self, label = "--:--:--:--", style = wx.ALIGN_CENTER_HORIZONTAL)

        # "connection status" light
        self.conn_status = wx.Window(self)
        self.conn_status.SetBackgroundColour(wx.RED)

        self.SetFieldsCount(4)
        #self.SetStatusStyles([wx.SB_RAISED, wx.SB_NORMAL, wx.SB_NORMAL, wx.SB_NORMAL])

        self.AddWidget(self.status_field, horizontalalignment = ESB.ESB_EXACT_FIT),
        self.AddWidget(self.feature_tray, horizontalalignment = ESB.ESB_ALIGN_RIGHT, verticalalignment = ESB.ESB_EXACT_FIT)
        self.AddWidget(self.conn_time,    horizontalalignment = ESB.ESB_EXACT_FIT)
        self.AddWidget(self.conn_status,  horizontalalignment = ESB.ESB_EXACT_FIT)

        self.update_timer = wx.CallLater(1000, self.UpdateConnectionStatus)
        self.status_timer = None
        self.LayoutWidgets()

    def UpdateConnectionStatus(self, evt = None):
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
        for feature in self.connection.features:
            if not self.feature_icons.get(feature):
                filename = os.path.join(iconpath, feature+".png")
                if os.path.isfile(filename):
                    print(f"Adding icon for {feature}")
                    icon = wx.StaticBitmap(self.feature_tray, -1,
                        wx.Image(filename).ConvertToBitmap())
                    #icon.SetToolTip(feature + " enabled")
                    self.feature_icons[feature] = icon
                    self.feature_sizer.Add(icon, 0, wx.EXPAND|wx.SHAPED)
                    print(self.feature_sizer)
                    print(self.feature_sizer.GetSize())
                else:
                    print(f"No icon file for connection feature '{feature}'")

        self.SetStatusWidths(
            [-1,
                self.feature_tray.GetSize().width,
                conn_time_size.Width + 3,
                self.GetSize().height + 2
            ])

    def AddStatus(self, status):
        self.SetStatusText(status, 2)
        if self.status_timer:
            if self.status_timer.IsRunning():
                self.status_timer.Restart(10000)
        self.status_timer = wx.CallLater(10000, self.ClearStatus)

    def ClearStatus(self):
        self.SetStatusText('', 2)
