import wx
import prefs
import datetime, time
import EnhancedStatusBar as ESB
from utility import platform

class StatusBar(ESB.EnhancedStatusBar):

    def __init__(self, parent):
        ESB.EnhancedStatusBar.__init__(self, parent)
        self.parent = parent

        self.SetFieldsCount(4)
        self.SetStatusStyles([wx.SB_RAISED, wx.SB_RAISED, wx.SB_NORMAL, wx.SB_NORMAL])
        # TODO, second field just long enough for xx:xx connection time
        self.SetStatusWidths([-1, 85, 15, 30])

        # connected-time widget
        self.connected_time = wx.StaticText(self, style = wx.ALIGN_CENTER_HORIZONTAL)
        self.AddWidget(self.connected_time, horizontalalignment = ESB.ESB_EXACT_FIT, pos = 1)

        # "connection status" light
        self.connection_status = wx.Panel(self)
        self.connection_status.SetBackgroundColour(wx.RED)
        self.AddWidget(self.connection_status, horizontalalignment = ESB.ESB_EXACT_FIT, pos = 2)

        self.update_timer = wx.CallLater(1000, self.UpdateConnectionStatus)
        self.status_timer = None


    def UpdateConnectionStatus(self, evt = None):
        self.update_timer.Restart(1000)
        conn = self.parent.currentConnection()
        if not conn:
            return

        if conn.is_connected():
            self.connection_status.SetBackgroundColour(wx.GREEN)
            self.connection_status.Refresh()
        else:
            self.connection_status.SetBackgroundColour(wx.RED)
            self.connection_status.Refresh()
            self.connected_time.SetLabel('')
            self.connected_time.SetToolTip(None)
            return


        if conn.connect_time:
            if not self.connected_time.GetToolTip():
                conn_time = time.localtime(conn.connect_time)
                self.connected_time.SetToolTip(time.strftime('Connected since: %c', conn_time))

            ctime = time.time() - conn.connect_time
            dd, rest = divmod(ctime, 3600 * 24)
            hh, rest = divmod(rest, 3600)
            mm, ss   = divmod(rest, 60)
            conn_time_str = '%02d:%02d:%02d:%02d' % (dd, hh, mm, ss)
        else:
            conn_time_str = '--:--:--:--'

        self.connected_time.SetLabel(conn_time_str)

    def AddStatus(self, status):
        self.SetStatusText(status, 2)
        if self.status_timer:
            if self.status_timer.IsRunning():
                self.status_timer.Restart(10000)
        self.status_timer = wx.CallLater(10000, self.ClearStatus)

    def ClearStatus(self):
        self.SetStatusText('', 2)

