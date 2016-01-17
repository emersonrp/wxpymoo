import wx
import prefs

class MainSplitter(wx.SplitterWindow):

    def __init__(self, parent, connection):
        wx.SplitterWindow.__init__(self, parent, style = wx.SP_LIVE_UPDATE)

        self.connection = connection
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.saveSplitterSize )
        self.Bind(wx.EVT_SIZE, self.HandleResize)

    def saveSplitterSize(self, evt):
        size = self.GetSize()
        prefs.set('input_height', size.GetHeight() - evt.GetSashPosition())

    def HandleResize(self, evt):
        size = self.GetSize()
        input_height = int(prefs.get('input_height')) or 25
        self.SetSashPosition(size.GetHeight() - input_height, True)
        self.connection.output_pane.ScrollIfAppropriate()
