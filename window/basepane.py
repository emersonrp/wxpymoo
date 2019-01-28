import wx
import wx.richtext as rtc
import prefs
import re
from utility import platform
from theme import Theme

class BasePane(rtc.RichTextCtrl):

    def __init__(self, parent, connection, style):
        rtc.RichTextCtrl.__init__(self, parent, style)

        self.connection = connection
        self.cols = 0
        self.rows = 0
        self.basic_style = None

        self.theme = Theme.fetch()

        self.fg_colour = self.theme.get('foreground')
        self.bg_colour = self.theme.get('background')

        self.Clear()
        self.restyle_thyself()

    def restyle_thyself(self):
        basic_style = rtc.RichTextAttr()
        self.theme = Theme.fetch()
        basic_style.SetTextColour      (self.fg_colour)
        basic_style.SetBackgroundColour(self.bg_colour)

        self.SetBackgroundColour(self.bg_colour)
        self.SetBasicStyle(basic_style)
        self.basic_style = basic_style

        font = wx.Font(prefs.get('font'))
        self.SetFont(font)

        # set one-half character's worth of left / top margin
        font_width, font_height = self.font_size()
        # Apparently Centos' Wx doesn't have this, so commenting it out.
        #self.SetMargins((font_width / 2, -1))

        self.update_size()

    def font_size(self):
        font = self.GetFont()

        # suss out how big one character is
        dc = wx.ScreenDC()
        dc.SetFont(font)
        return dc.GetTextExtent('M')

    #### override in subclasses
    def check_for_interesting_keystrokes(self, evt):
        pass

    def update_size(self, evt = None):
        pass
