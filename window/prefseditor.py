import wx
import prefs
# use Wx qw( :dialog :sizer :id :misc :notebook :font :colour :textctrl
#             wxFNTP_USEFONT_FOR_LABEL wxFNTP_FONTDESC_AS_LABEL
#             wxCLRP_USE_TEXTCTRL wxCLRP_SHOW_LABEL
# )
# use wx.Event qw( EVT_BUTTON EVT_FONTPICKER_CHANGED EVT_COLOURPICKER_CHANGED )

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

        self.Layout()

    def update_prefs(self, evt):
        # This is doing some nasty GetAsString and GetNativeFontInfoDesc foo here,
        # instead of encapsulated in prefs, which I think I'm OK with.

        prefs.set('save_window_size', self.general_page.save_size_checkbox.GetValue() )
        prefs.set('autoconnect_last_world', self.general_page.autoconnect_checkbox.GetValue() )

        prefs.set('output_font',self.fonts_page.ofont_ctrl.GetSelectedFont().GetNativeFontInfoDesc())
        prefs.set('input_font', self.fonts_page.ifont_ctrl.GetSelectedFont().GetNativeFontInfoDesc())

        prefs.set('output_fgcolour',self.fonts_page.o_fgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
        prefs.set('output_bgcolour',self.fonts_page.o_bgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
        prefs.set('input_fgcolour', self.fonts_page.i_fgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
        prefs.set('input_bgcolour', self.fonts_page.i_bgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))

        prefs.set('use_ansi', self.fonts_page.ansi_checkbox.GetValue() )

        prefs.set('external_editor', self.paths_page.external_editor.GetValue() )

        self.parent.connection.output_pane.restyle_thyself()
        self.parent.connection.input_pane.restyle_thyself()
        evt.Skip()

    def createGeneralPanel(self):
        gp = wx.Panel(self.book)
        gp.save_size_checkbox = wx.CheckBox(gp, -1, 'Save Window Size')
        gp.save_size_checkbox.SetValue( True if prefs.get('save_window_size') == 'True' else False )
        #gp.save_size_checkbox.Fit()

        gp.autoconnect_checkbox = wx.CheckBox(gp, -1, 'Autoconnect to last world at startup')
        gp.autoconnect_checkbox.SetValue( True if prefs.get('autoconnect_last_world') == 'True' else False )

        gp.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        gp.panel_sizer.Add(gp.save_size_checkbox, flag = wx.ALL, border = 10)
        gp.panel_sizer.Add(gp.autoconnect_checkbox, flag = wx.ALL, border = 10)

        gp.SetSizer(gp.panel_sizer)
        return gp

    def createFontPanel(self):
        fcp = wx.Panel(self.book)

        ofont = wx.NullFont
        ifont = wx.NullFont
        ofont.SetNativeFontInfoFromString(prefs.get('output_font'))
        ifont.SetNativeFontInfoFromString(prefs.get('input_font'))


        o_fgcolour = prefs.get('output_fgcolour')
        o_bgcolour = prefs.get('output_bgcolour')
        i_fgcolour = prefs.get('input_fgcolour')
        i_bgcolour = prefs.get('input_bgcolour')

        # output sample/controls
        fcp.o_sample    = wx.TextCtrl      (fcp, style = wx.TE_READONLY)
        fcp.ofont_ctrl  = wx.FontPickerCtrl(fcp, style = wx.FNTP_FONTDESC_AS_LABEL | wx.FNTP_USEFONT_FOR_LABEL)

        bsize = fcp.ofont_ctrl.GetSize().GetHeight()
        button_size = [bsize, bsize]

        fcp.o_fgcolour_ctrl = wx.ColourPickerCtrl(fcp, col = o_fgcolour, size = button_size)
        fcp.o_bgcolour_ctrl = wx.ColourPickerCtrl(fcp, col = o_bgcolour, size = button_size)

        fcp.o_sample.SetFont(ofont)
        fcp.o_sample.SetBackgroundColour(o_bgcolour)
        fcp.o_sample.SetForegroundColour(o_fgcolour)
        fcp.o_sample.SetValue('Haakon says, "This is the output window."')

        # input sample/controls
        fcp.i_sample    = wx.TextCtrl      (fcp, style = wx.TE_READONLY)
        fcp.ifont_ctrl  = wx.FontPickerCtrl(fcp, style = wx.FNTP_FONTDESC_AS_LABEL | wx.FNTP_USEFONT_FOR_LABEL)
        fcp.i_fgcolour_ctrl = wx.ColourPickerCtrl(fcp, col = i_fgcolour, size = button_size)
        fcp.i_bgcolour_ctrl = wx.ColourPickerCtrl(fcp, col = o_bgcolour, size = button_size)

        fcp.i_sample.SetFont(ifont)
        fcp.i_sample.SetBackgroundColour(i_bgcolour)
        fcp.i_sample.SetForegroundColour(i_fgcolour)
        fcp.i_sample.SetValue('`Haakon Hello from the input window.')

        fcp.ansi_checkbox = wx.CheckBox(fcp, -1, 'Use ANSI colors')
        fcp.ansi_checkbox.SetValue( True if prefs.get('use_ansi') == "True" else False )

        output_sizer = wx.FlexGridSizer(1, 3, 5, 10)
        output_sizer.Add(fcp.ofont_ctrl     , 0, wx.EXPAND, 0)
        output_sizer.Add(fcp.o_fgcolour_ctrl, 0)
        output_sizer.Add(fcp.o_bgcolour_ctrl, 0)
        output_sizer.AddGrowableCol(0)
        #output_sizer.Fit(fcp)

        input_sizer = wx.FlexGridSizer(1, 3, 5, 10)
        input_sizer.Add(fcp.ifont_ctrl      , 0, wx.EXPAND, 0)
        input_sizer.Add(fcp.i_fgcolour_ctrl , 0)
        input_sizer.Add(fcp.i_bgcolour_ctrl , 0)
        input_sizer.AddGrowableCol(0)
        #input_sizer.Fit(fcp)

        ansi_sizer = wx.BoxSizer(wx.VERTICAL)
        ansi_sizer.Add(fcp.ansi_checkbox)
        #ansi_sizer.Fit(fcp)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(fcp.o_sample, 0, wx.RIGHT|wx.LEFT|wx.EXPAND|wx.TOP, 10)
        panel_sizer.Add(output_sizer, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 10)
        panel_sizer.AddSpacer(bsize)
        panel_sizer.Add(fcp.i_sample, 0, wx.RIGHT|wx.LEFT|wx.EXPAND|wx.TOP, 10)
        panel_sizer.Add(input_sizer,  0, wx.RIGHT|wx.LEFT|wx.EXPAND, 10)
        panel_sizer.AddSpacer(bsize)
        panel_sizer.Add(ansi_sizer)

        self.Bind(wx.EVT_FONTPICKER_CHANGED  , self.update_sample_text, fcp.ofont_ctrl)
        self.Bind(wx.EVT_FONTPICKER_CHANGED  , self.update_sample_text, fcp.ifont_ctrl)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.update_sample_text, fcp.i_fgcolour_ctrl)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.update_sample_text, fcp.i_bgcolour_ctrl)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.update_sample_text, fcp.o_fgcolour_ctrl)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.update_sample_text, fcp.o_bgcolour_ctrl)

        fcp.SetSizer(panel_sizer)

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
        fcp = self.fonts_page
        fcp.i_sample.SetFont            (fcp.ifont_ctrl.GetSelectedFont())
        fcp.i_sample.SetForegroundColour(fcp.i_fgcolour_ctrl.GetColour())
        fcp.i_sample.SetBackgroundColour(fcp.i_bgcolour_ctrl.GetColour())
        fcp.o_sample.SetFont            (fcp.ofont_ctrl.GetSelectedFont())
        fcp.o_sample.SetForegroundColour(fcp.o_fgcolour_ctrl.GetColour())
        fcp.o_sample.SetBackgroundColour(fcp.o_bgcolour_ctrl.GetColour())
        evt.Skip()

