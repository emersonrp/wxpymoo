import wx

#use WxMOO::Prefs;

class MainSplitter(wx.SplitterWindow):

    def __init__(self, parent):
        wx.SplitterWindow.__init__(self, parent, style = wx.SP_LIVE_UPDATE)

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.saveSplitterSize )
        self.Bind(wx.EVT_SIZE, self.HandleResize)

    def saveSplitterSize(self, evt):
        size = self.GetSize()
        #WxMOO::Prefs->prefs->input_height( $h - $evt->GetSashPosition );

    def HandleResize(self, evt):
        size = self.GetSize()
        #my $InputHeight = WxMOO::Prefs->prefs->input_height || 25;
        InputHeight = 30
        self.SetSashPosition(size.GetHeight() - InputHeight, True)
        self.GetWindow1().ScrollIfAppropriate()
