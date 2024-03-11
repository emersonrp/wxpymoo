import wx
import prefs
from theme import Theme

from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED

class PrefsEditor(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, size=(500,500), title="WxPyMOO Preferences")

        self.parent = parent

        panel = wx.Panel(self)
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
        gp = wx.Panel(self.book)
        gp.save_size_checkbox = wx.CheckBox(gp, -1, 'Save Window Size')
        gp.save_size_checkbox.SetValue( prefs.get('save_window_size') )

        gp.autoconnect_checkbox = wx.CheckBox(gp, -1, 'Autoconnect to last world at startup')
        gp.autoconnect_checkbox.SetValue( prefs.get('autoconnect_last_world') )

        gp.xmouse_checkbox = wx.CheckBox(gp, -1, 'Use X-style mouse copy/paste behavior')
        gp.xmouse_checkbox.SetValue( prefs.get('use_x_copy_paste') )

        gp.local_echo_checkbox = wx.CheckBox(gp, -1, 'Echo Typed Commands')
        gp.local_echo_checkbox.SetValue( prefs.get('local_echo') )

        gp.scroll_on_output_checkbox = wx.CheckBox(gp, -1, 'Scroll to bottom when new text arrives')
        gp.scroll_on_output_checkbox.SetValue( prefs.get('scroll_on_output') )

        gp.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        gp.panel_sizer.Add(gp.save_size_checkbox, flag = wx.ALL, border = 10)
        gp.panel_sizer.Add(gp.autoconnect_checkbox, flag = wx.ALL, border = 10)
        gp.panel_sizer.Add(gp.xmouse_checkbox, flag = wx.ALL, border = 10)
        gp.panel_sizer.Add(gp.local_echo_checkbox, flag = wx.ALL, border = 10)
        gp.panel_sizer.Add(gp.scroll_on_output_checkbox, flag = wx.ALL, border = 10)

        gp.SetSizer(gp.panel_sizer)
        return gp

    def createFontPanel(self):
        fcp = wx.Panel(self.book)

        font = wx.Font(prefs.get('font'))

        fgcolour = prefs.get('fgcolour')
        bgcolour = prefs.get('bgcolour')

        # output sample/controls
        fcp.sample    =    ExpandoTextCtrl(fcp, style = wx.TE_READONLY | wx.TE_RICH | wx.TE_MULTILINE , size = wx.Size(400,-1))
        fcp.font_ctrl = wx.FontPickerCtrl (fcp, style = wx.FNTP_FONTDESC_AS_LABEL | wx.FNTP_USEFONT_FOR_LABEL, font = font)

        fcp.theme_picker = wx.Choice(fcp, choices = Theme.all_theme_names())

        fcp.ansi_checkbox       = wx.CheckBox(fcp, -1, 'Use ANSI colors')
        fcp.ansi_blink_checkbox = wx.CheckBox(fcp, -1, 'Honor ANSI blink')
        # TODO - get and set these two at display time not create time
        fcp.theme = prefs.get('theme')
        fcp.theme_picker.SetSelection(fcp.theme_picker.FindString(fcp.theme))

        if prefs.get('use_ansi'):
            fcp.ansi_checkbox.SetValue(True)
            fcp.theme_picker.Enable()
        else:
            fcp.ansi_checkbox.SetValue(False)
            fcp.theme_picker.Disable()

        ansi_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ansi_sizer.Add(fcp.ansi_checkbox,       0, wx.ALL|wx.EXPAND)
        ansi_sizer.Add(fcp.ansi_blink_checkbox, 0, wx.ALL|wx.EXPAND)
        ansi_sizer.Add(fcp.theme_picker,        0, wx.ALL|wx.EXPAND)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(fcp.sample,  0, wx.RIGHT|wx.LEFT|wx.EXPAND|wx.TOP, 10)
        panel_sizer.AddSpacer(10)
        panel_sizer.Add(fcp.font_ctrl    , 0, wx.EXPAND, 0)
        panel_sizer.AddSpacer(10)
        panel_sizer.Add(ansi_sizer,  0, wx.RIGHT|wx.LEFT|wx.EXPAND,        10)

        self.Bind(wx.EVT_FONTPICKER_CHANGED  , self.update_sample_text, fcp.font_ctrl)
        self.Bind(wx.EVT_CHOICE              , self.update_sample_text, fcp.theme_picker)
        self.Bind(wx.EVT_CHECKBOX            , self.update_sample_text, fcp.ansi_checkbox)

        self.Bind(EVT_ETC_LAYOUT_NEEDED      , self.resize_everything, fcp.sample)

        fcp.SetSizer(panel_sizer)

        fcp.Layout()

        return fcp

    def createPathsPanel(self):
        pp = wx.Panel(self.book)

        editor_label       = wx.StaticText(pp, -1, "External Editor")
        pp.external_editor = wx.TextCtrl(pp, -1, "")
        pp.external_editor.SetValue( prefs.get('external_editor') )

        editor_sizer = wx.FlexGridSizer(1,2,5,10)
        editor_sizer.Add(editor_label,       0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        editor_sizer.Add(pp.external_editor, 1, wx.EXPAND, 0)
        editor_sizer.AddGrowableCol(1)

        pp.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        pp.panel_sizer.Add(editor_sizer, 0, wx.EXPAND | wx.ALL, 10)

        pp.SetSizer(pp.panel_sizer)

        return pp

    def resize_everything(self, evt):
        self.Fit()

    def update_sample_text(self, evt):
        fp = self.fonts_page

        theme = Theme.fetch(fp.theme_picker.GetStringSelection())

        fgcolour = theme.get('foreground')
        bgcolour = theme.get('background')
        font     = fp.font_ctrl.GetSelectedFont()

        textattr = wx.TextAttr(fgcolour, bgcolour, font)

        fp.sample.SetBackgroundColour(bgcolour)
        fp.sample.SetValue("""
Emerson says, "This is what your window will look like."
Emerson waves around a brightly-colored banner.

It's super effective!

01234567 89ABCDEF
""")
        fp.sample.SetStyle(0, fp.sample.GetLastPosition(), textattr)

        # Mock up ANSI if ANSI pref is on
        # TODO - maybe actually just shove ANSI-code-ful stuff through the actual output_panel ANSIfier?
        if fp.ansi_checkbox.GetValue():
            textattr.SetTextColour(theme.Colour('blue'))
            fp.sample.SetStyle(1,    8, textattr)

            fp.sample.SetStyle(58,   66,textattr)
            textattr.SetTextColour(theme.Colour('red'))
            fp.sample.SetStyle(81,   89, textattr)
            textattr.SetTextColour(theme.Colour('yellow'))
            fp.sample.SetStyle(90,   97, textattr)
            textattr.SetTextColour(theme.Colour('green'))
            fp.sample.SetStyle(98,  104, textattr)
            fp.theme_picker.Enable()

            textattr.SetTextColour(theme.Colour('white'))
            textattr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            fp.sample.SetStyle(107, 128, textattr)
            textattr.SetTextColour(theme.Colour('red', 'bright'))
            fp.sample.SetStyle(112, 117, textattr)

            textattr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
            textattr.SetTextColour(theme.Colour('black'))
            fp.sample.SetStyle(130, 131, textattr)
            textattr.SetTextColour(theme.Colour('red'))
            fp.sample.SetStyle(131, 132, textattr)
            textattr.SetTextColour(theme.Colour('green'))
            fp.sample.SetStyle(132, 133, textattr)
            textattr.SetTextColour(theme.Colour('yellow'))
            fp.sample.SetStyle(133, 134, textattr)
            textattr.SetTextColour(theme.Colour('blue'))
            fp.sample.SetStyle(134, 135, textattr)
            textattr.SetTextColour(theme.Colour('magenta'))
            fp.sample.SetStyle(135, 136, textattr)
            textattr.SetTextColour(theme.Colour('cyan'))
            fp.sample.SetStyle(136, 137, textattr)
            textattr.SetTextColour(theme.Colour('white'))
            fp.sample.SetStyle(137, 138, textattr)

            textattr.SetTextColour(fgcolour)
            textattr.SetBackgroundColour(theme.Colour('black'))
            fp.sample.SetStyle(139, 140, textattr)
            textattr.SetBackgroundColour(theme.Colour('red'))
            fp.sample.SetStyle(140, 141, textattr)
            textattr.SetBackgroundColour(theme.Colour('green'))
            fp.sample.SetStyle(141, 142, textattr)
            textattr.SetBackgroundColour(theme.Colour('yellow'))
            fp.sample.SetStyle(142, 143, textattr)
            textattr.SetBackgroundColour(theme.Colour('blue'))
            fp.sample.SetStyle(143, 144, textattr)
            textattr.SetBackgroundColour(theme.Colour('magenta'))
            fp.sample.SetStyle(144, 145, textattr)
            textattr.SetBackgroundColour(theme.Colour('cyan'))
            fp.sample.SetStyle(145, 146, textattr)
            textattr.SetBackgroundColour(theme.Colour('white'))
            fp.sample.SetStyle(146, 147, textattr)
        else:
            fp.theme_picker.Disable()

        if evt: evt.Skip()
