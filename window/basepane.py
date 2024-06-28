import wx
import wx.richtext as rtc
import prefs
import platform
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

        self.is_dragging = False

        self.Clear()
        self.restyle_thyself()

        self.Bind(wx.EVT_MIDDLE_DOWN                 , self.paste_with_middle_mouse )
        self.Bind(wx.EVT_LEFT_UP                     , self.left_mouse_up)
        self.Bind(wx.EVT_LEFT_DOWN                   , self.left_mouse_down)
        self.Bind(wx.EVT_MOTION                      , self.mouse_moved)

    # reinventing xmouse, one event at a time.
    def mouse_moved(self, evt):
        self.is_dragging = evt.Dragging()
        evt.Skip(True)

    def left_mouse_up(self, evt):
        if self.is_dragging:
            self.is_dragging = False
            if wx.ConfigBase.Get().ReadBool('use_x_copy_paste'):
                if platform.system() == 'Linux': wx.TheClipboard.UsePrimarySelection(True)
                if self.CanCopy(): self.Copy()
                if platform.system() == 'Linux': wx.TheClipboard.UsePrimarySelection(False)
        evt.Skip(True)

    # treat selectin in input/output as mutually exclusive
    def left_mouse_down(self, evt):
        for pane in (self.connection.output_pane, self.connection.input_pane):
            if not self == pane:
                pane.SelectNone()
        evt.Skip(True)

    def paste_with_middle_mouse(self,evt):
        if wx.ConfigBase.Get().ReadBool('use_x_copy_paste'): self.connection.input_pane.paste_from_selection()

    def restyle_thyself(self):
        basic_style = rtc.RichTextAttr()
        self.theme = Theme.fetch()
        basic_style.SetTextColour      (self.fg_colour)
        basic_style.SetBackgroundColour(self.bg_colour)

        self.SetBackgroundColour(self.bg_colour)
        self.SetBasicStyle(basic_style)
        self.basic_style = basic_style

        font = wx.Font(wx.ConfigBase.Get().Read('font'))
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
