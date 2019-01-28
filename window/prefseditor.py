import wx
import prefs
from theme import Theme

from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED

class PrefsEditor(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent)

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

        sizer.Add(self.book,    1, wx.EXPAND | wx.ALL)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 5)

        self.SetSizer(sizer)

        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_BUTTON, self.update_prefs, id = wx.ID_OK)

        self.update_sample_text(None)

        self.Layout()

    def update_prefs(self, evt):
        prefs.update(self)
        evt.Skip()

    def createGeneralPanel(self):
        gp = wx.Panel(self.book)
        gp.save_size_checkbox = wx.CheckBox(gp, -1, 'Save Window Size')
        gp.save_size_checkbox.SetValue( True if prefs.get('save_window_size') == 'True' else False )

        gp.autoconnect_checkbox = wx.CheckBox(gp, -1, 'Autoconnect to last world at startup')
        gp.autoconnect_checkbox.SetValue( True if prefs.get('autoconnect_last_world') == 'True' else False )

        gp.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        gp.panel_sizer.Add(gp.save_size_checkbox, flag = wx.ALL, border = 10)
        gp.panel_sizer.Add(gp.autoconnect_checkbox, flag = wx.ALL, border = 10)

        gp.SetSizer(gp.panel_sizer)
        return gp

    def createFontPanel(self):
        fcp = wx.Panel(self.book)

        font = wx.Font(prefs.get('font'))

        fgcolour = prefs.get('fgcolour')
        bgcolour = prefs.get('bgcolour')

        # output sample/controls
        fcp.sample    =    ExpandoTextCtrl(fcp, style = wx.TE_READONLY | wx.TE_RICH | wx.TE_MULTILINE )
        fcp.font_ctrl = wx.FontPickerCtrl (fcp, style = wx.FNTP_FONTDESC_AS_LABEL | wx.FNTP_USEFONT_FOR_LABEL, font = font)

        fcp.theme_picker = wx.Choice(fcp, choices = Theme.all_theme_names())

        # TODO - get and set these two at display time not create time
        fcp.theme = prefs.get('theme')
        fcp.theme_picker.SetSelection(fcp.theme_picker.FindString(fcp.theme))

        fcp.ansi_checkbox = wx.CheckBox(fcp, -1, 'Use ANSI colors')
        fcp.ansi_checkbox.SetValue( True if prefs.get('use_ansi') == "True" else False )

        fc_sizer = wx.FlexGridSizer(1, 3, 5, 10)
        fc_sizer.Add(fcp.font_ctrl    , 0, wx.EXPAND, 0)
        fc_sizer.AddGrowableCol(0)
        fc_sizer.Fit(fcp)

        theme_sizer = wx.BoxSizer(wx.VERTICAL)
        theme_sizer.Add(fcp.theme_picker)
        theme_sizer.Fit(fcp)

        ansi_sizer = wx.BoxSizer(wx.VERTICAL)
        ansi_sizer.Add(fcp.ansi_checkbox)
        ansi_sizer.Fit(fcp)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(fcp.sample,  0, wx.RIGHT|wx.LEFT|wx.EXPAND|wx.TOP, 10)
        panel_sizer.Add(fc_sizer,    0, wx.RIGHT|wx.LEFT|wx.EXPAND,        10)
        panel_sizer.Add(theme_sizer, 0, wx.RIGHT|wx.LEFT|wx.EXPAND,        10)
        panel_sizer.AddSpacer(10)
        panel_sizer.Add(ansi_sizer,  0, wx.RIGHT|wx.LEFT|wx.EXPAND,        10)

        self.Bind(wx.EVT_FONTPICKER_CHANGED  , self.update_sample_text, fcp.font_ctrl)
        self.Bind(wx.EVT_CHOICE              , self.update_sample_text, fcp.theme_picker)
        self.Bind(wx.EVT_CHECKBOX            , self.update_sample_text, fcp.ansi_checkbox)

        fcp.SetSizer(panel_sizer)

        fcp.Layout()
        fcp.Fit()

        return fcp

    def createPathsPanel(self):
        pp = wx.Panel(self.book)

        editor_label       = wx.StaticText(pp, -1, "External Editor")
        pp.external_editor = wx.TextCtrl(pp, -1, "")
        pp.external_editor.SetValue( prefs.get('external_editor') )
        #pp.external_editor.Fit()

        editor_sizer = wx.FlexGridSizer(1,2,5,10)
        editor_sizer.Add(editor_label,       0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        editor_sizer.Add(pp.external_editor, 1, wx.EXPAND, 0)
        editor_sizer.AddGrowableCol(1)

        pp.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        pp.panel_sizer.Add(editor_sizer, 0, wx.EXPAND | wx.ALL, 10)

        pp.SetSizer(pp.panel_sizer)

        return pp

    def update_sample_text(self, evt):
        fp = self.fonts_page

        theme = Theme.fetch(fp.theme_picker.GetStringSelection())

        fgcolour = theme.get('foreground')
        bgcolour = theme.get('background')
        font     = fp.font_ctrl.GetSelectedFont()

        textattr = wx.TextAttr(fgcolour, bgcolour, font)

        fp.sample.SetBackgroundColour(bgcolour)
        fp.sample.SetValue('Emerson says, "This is what your window will look like."')
        fp.sample.SetStyle(0, fp.sample.GetLastPosition(), textattr)

        # Mock up ANSI 'Emerson' if ANSI pref is on
        if fp.ansi_checkbox.GetValue() == True:
            textattr.SetTextColour(theme.get('blue'))
            fp.sample.SetStyle(0, 7, textattr)

        if evt: evt.Skip()
