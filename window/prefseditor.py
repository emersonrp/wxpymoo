import wx
import prefs
from theme import Theme

from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED

class PrefsEditor(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, size=(500,500), title="WxPyMOO Preferences")

        self.parent = parent

        self.book = wx.Notebook(self)

        self.general_page = self.createGeneralPanel()
        self.fonts_page   = self.createFontPanel   ()
        self.paths_page   = self.createPathsPanel  ()

        self.book.AddPage(self.general_page, "General")
        self.book.AddPage(self.fonts_page, "Fonts and Colors")
        self.book.AddPage(self.paths_page, "Paths and Dirs")

        sizer        = wx.BoxSizer(wx.VERTICAL)
        button_sizer = self.CreateButtonSizer( wx.OK | wx.CANCEL )

        sizer.Add(self.book,    1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 5)

        self.SetSizer(sizer)
        self.Centre(wx.BOTH)

        self.update_sample_text(None)


        self.Bind(wx.EVT_BUTTON, self.update_prefs, id = wx.ID_OK)

    def update_prefs(self, evt):
        prefs.update(self)
        evt.Skip()

    def createGeneralPanel(self):
        _config = wx.ConfigBase.Get()
        gp = wx.Panel(self.book)
        self.save_size_checkbox = wx.CheckBox(gp, -1, 'Save Window Size')
        self.save_size_checkbox.SetValue( _config.ReadBool('save_window_size') )

        self.autoconnect_checkbox = wx.CheckBox(gp, -1, 'Autoconnect to last world at startup')
        self.autoconnect_checkbox.SetValue( _config.ReadBool('autoconnect_last_world') )

        self.xmouse_checkbox = wx.CheckBox(gp, -1, 'Use X-style mouse copy/paste behavior')
        self.xmouse_checkbox.SetValue( _config.ReadBool('use_x_copy_paste') )

        self.local_echo_checkbox = wx.CheckBox(gp, -1, 'Echo Typed Commands')
        self.local_echo_checkbox.SetValue( _config.ReadBool('local_echo') )

        self.scroll_on_output_checkbox = wx.CheckBox(gp, -1, 'Scroll to bottom when new text arrives')
        self.scroll_on_output_checkbox.SetValue( _config.ReadBool('scroll_on_output') )

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(self.save_size_checkbox, flag = wx.ALL, border = 10)
        panel_sizer.Add(self.autoconnect_checkbox, flag = wx.ALL, border = 10)
        panel_sizer.Add(self.xmouse_checkbox, flag = wx.ALL, border = 10)
        panel_sizer.Add(self.local_echo_checkbox, flag = wx.ALL, border = 10)
        panel_sizer.Add(self.scroll_on_output_checkbox, flag = wx.ALL, border = 10)

        gp.SetSizer(panel_sizer)
        return gp

    def createFontPanel(self):
        _config = wx.ConfigBase.Get()
        fcp = wx.Panel(self.book)

        font = wx.Font(_config.Read('font'))

        fgcolour = _config.Read('fgcolour')
        bgcolour = _config.Read('bgcolour')

        # output sample/controls
        self.sample    =    ExpandoTextCtrl(fcp, style = wx.TE_READONLY | wx.TE_RICH | wx.TE_MULTILINE , size = wx.Size(400,-1))
        self.font_ctrl = wx.FontPickerCtrl (fcp, style = wx.FNTP_FONTDESC_AS_LABEL | wx.FNTP_USEFONT_FOR_LABEL, font = font)

        self.theme_picker = wx.Choice(fcp, choices = Theme.all_theme_names())

        self.ansi_checkbox       = wx.CheckBox(fcp, -1, 'Use ANSI colors')
        self.ansi_blink_checkbox = wx.CheckBox(fcp, -1, 'Honor ANSI blink')
        # TODO - get and set these two at display time not create time
        self.theme = _config.Read('theme')
        self.theme_picker.SetSelection(self.theme_picker.FindString(self.theme))

        if _config.ReadBool('use_ansi'):
            self.ansi_checkbox.SetValue(True)
            self.theme_picker.Enable()
        else:
            self.ansi_checkbox.SetValue(False)
            self.theme_picker.Disable()

        ansi_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ansi_sizer.Add(self.ansi_checkbox,       0, wx.ALL|wx.EXPAND)
        ansi_sizer.Add(self.ansi_blink_checkbox, 0, wx.ALL|wx.EXPAND)
        ansi_sizer.Add(self.theme_picker,        0, wx.ALL|wx.EXPAND)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(self.sample,  0, wx.RIGHT|wx.LEFT|wx.EXPAND|wx.TOP, 10)
        panel_sizer.AddSpacer(10)
        panel_sizer.Add(self.font_ctrl    , 0, wx.EXPAND, 0)
        panel_sizer.AddSpacer(10)
        panel_sizer.Add(ansi_sizer,  0, wx.RIGHT|wx.LEFT|wx.EXPAND,        10)

        self.Bind(wx.EVT_FONTPICKER_CHANGED  , self.update_sample_text, self.font_ctrl)
        self.Bind(wx.EVT_CHOICE              , self.update_sample_text, self.theme_picker)
        self.Bind(wx.EVT_CHECKBOX            , self.update_sample_text, self.ansi_checkbox)

        self.Bind(EVT_ETC_LAYOUT_NEEDED      , self.resize_everything, self.sample)

        fcp.SetSizer(panel_sizer)

        fcp.Layout()

        return fcp

    def createPathsPanel(self):
        pp = wx.Panel(self.book)

        editor_label       = wx.StaticText(pp, -1, "External Editor")
        self.external_editor = wx.TextCtrl(pp, -1, "")
        self.external_editor.SetValue( wx.ConfigBase.Get().Read('external_editor') )

        editor_sizer = wx.FlexGridSizer(1,2,5,10)
        editor_sizer.Add(editor_label,       0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        editor_sizer.Add(self.external_editor, 1, wx.EXPAND, 0)
        editor_sizer.AddGrowableCol(1)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(editor_sizer, 0, wx.EXPAND | wx.ALL, 10)

        pp.SetSizer(panel_sizer)

        return pp

    def resize_everything(self, evt):
        self.Fit()
        if evt: evt.Skip()

    def update_sample_text(self, evt):
        theme = Theme.fetch(self.theme_picker.GetStringSelection())

        fgcolour = theme.get('foreground')
        bgcolour = theme.get('background')
        font     = self.font_ctrl.GetSelectedFont()

        textattr = wx.TextAttr(fgcolour, bgcolour, font)

        self.sample.SetBackgroundColour(bgcolour)
        self.sample.SetValue(
            'Emerson says, "This is what your window will look like."\n'
            'Emerson waves around a brightly-colored banner.\n'
            '\n'
            'It\'s super effective!\n'
            '\n'
            '01234567 89ABCDEF\n'
        )
        self.sample.SetStyle(0, self.sample.GetLastPosition(), textattr)

        # Mock up ANSI if ANSI pref is on
        # TODO - maybe actually just shove ANSI-code-ful stuff through the actual output_panel ANSIfier?
        if self.ansi_checkbox.GetValue():
            textattr.SetTextColour(theme.Colour('blue'))
            self.sample.SetStyle(1,    8, textattr)

            self.sample.SetStyle(58,   66,textattr)
            textattr.SetTextColour(theme.Colour('red'))
            self.sample.SetStyle(81,   89, textattr)
            textattr.SetTextColour(theme.Colour('yellow'))
            self.sample.SetStyle(90,   97, textattr)
            textattr.SetTextColour(theme.Colour('green'))
            self.sample.SetStyle(98,  104, textattr)
            self.theme_picker.Enable()

            textattr.SetTextColour(theme.Colour('white'))
            textattr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            self.sample.SetStyle(107, 128, textattr)
            textattr.SetTextColour(theme.Colour('red', 'bright'))
            self.sample.SetStyle(112, 117, textattr)

            textattr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
            textattr.SetTextColour(theme.Colour('black'))
            self.sample.SetStyle(130, 131, textattr)
            textattr.SetTextColour(theme.Colour('red'))
            self.sample.SetStyle(131, 132, textattr)
            textattr.SetTextColour(theme.Colour('green'))
            self.sample.SetStyle(132, 133, textattr)
            textattr.SetTextColour(theme.Colour('yellow'))
            self.sample.SetStyle(133, 134, textattr)
            textattr.SetTextColour(theme.Colour('blue'))
            self.sample.SetStyle(134, 135, textattr)
            textattr.SetTextColour(theme.Colour('magenta'))
            self.sample.SetStyle(135, 136, textattr)
            textattr.SetTextColour(theme.Colour('cyan'))
            self.sample.SetStyle(136, 137, textattr)
            textattr.SetTextColour(theme.Colour('white'))
            self.sample.SetStyle(137, 138, textattr)

            textattr.SetTextColour(fgcolour)
            textattr.SetBackgroundColour(theme.Colour('black'))
            self.sample.SetStyle(139, 140, textattr)
            textattr.SetBackgroundColour(theme.Colour('red'))
            self.sample.SetStyle(140, 141, textattr)
            textattr.SetBackgroundColour(theme.Colour('green'))
            self.sample.SetStyle(141, 142, textattr)
            textattr.SetBackgroundColour(theme.Colour('yellow'))
            self.sample.SetStyle(142, 143, textattr)
            textattr.SetBackgroundColour(theme.Colour('blue'))
            self.sample.SetStyle(143, 144, textattr)
            textattr.SetBackgroundColour(theme.Colour('magenta'))
            self.sample.SetStyle(144, 145, textattr)
            textattr.SetBackgroundColour(theme.Colour('cyan'))
            self.sample.SetStyle(145, 146, textattr)
            textattr.SetBackgroundColour(theme.Colour('white'))
            self.sample.SetStyle(146, 147, textattr)
        else:
            self.theme_picker.Disable()

        if evt: evt.Skip()
