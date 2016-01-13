import wx
from WxMOO.Connection import Connection
class Main(wx.Frame):
    #use wx.Event qw( EVT_MENU EVT_SIZE )

    #use WxMOO::Prefs
    #use WxMOO::Editor

    #use WxMOO::Window::ConnectDialog
    #use WxMOO::Window::DebugMCP
    #use WxMOO::Window::InputPane
    #use WxMOO::Window::MainSplitter
    #use WxMOO::Window::OutputPane
    #use WxMOO::Window::PrefsEditor
    #use WxMOO::Window::WorldsList

    #prefs = WxMOO::Prefs.prefs

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)

        # TODO - status bar is so biig but it would be nice to have it.
        self.status_bar = self.CreateStatusBar()

        self.buildMenu()

        self.addEvents()

        self.about_info = None

        h = 600
        w = 800
#        if ( $prefs.save_window_size) {
#            $w = $prefs.window_width if $prefs.window_width
#            $h = $prefs.window_height if $prefs.window_height
#        }
        self.SetSize((w, h))
#
#        splitter = WxMOO::Window::MainSplitter($self)
#
#        $self.input_pane (WxMOO::Window::InputPane ($splitter))
#        $self.output_pane(WxMOO::Window::OutputPane($splitter))
#
#        $splitter.SplitHorizontally($self.output_pane, $self.input_pane)
#        $splitter.SetMinimumPaneSize(20); # TODO - set to "one line of input field"

        self.sizer = wx.BoxSizer( wx.VERTICAL )
        #self.sizer.Add($splitter, 1, wxALL|wxGROW)
        self.SetSizer(self.sizer)

#        # TODO - don't connect until we ask for it.
#        # TODO - probably want a tabbed interface for multiple connections
        self.connection = Connection(self)

# post .Show stuff
    def Initialize(self):
#        # TODO - don't connect until we ask for it.
#        $self.connection.connect('hayseed.net',7777)
        pass

    def buildMenu(self):
        WorldsMenu = wx.Menu()
        Worlds_worlds  = WorldsMenu.Append(-1, "&Worlds...",  "Browse list of worlds")
        Worlds_connect = WorldsMenu.Append(-1, "&Connect...", "Connect to a host and port")
        Worlds_close   = WorldsMenu.Append(wx.ID_CLOSE)
        WorldsMenu.AppendSeparator()
        Worlds_reconnect = WorldsMenu.Append(-1, "&Reconnect", "Close and re-open the current connection")
        Worlds_quit      = WorldsMenu.Append(wx.ID_EXIT)

        EditMenu = wx.Menu()
        Edit_cut   = EditMenu.Append(wx.ID_CUT)
        Edit_copy  = EditMenu.Append(wx.ID_COPY)
        Edit_paste = EditMenu.Append(wx.ID_PASTE)

        PrefsMenu = wx.Menu()
        Prefs_prefs = PrefsMenu.Append(wx.ID_PREFERENCES)

        WindowMenu = wx.Menu()
        Window_debugmcp = WindowMenu.Append(-1, "&Debug MCP", "")

        HelpMenu = wx.Menu()
        Help_help  = HelpMenu.Append(-1, "&Help Topics", "")
        Help_about = HelpMenu.Append(wx.ID_ABOUT)

        MenuBar = wx.MenuBar()
        MenuBar.Append(WorldsMenu, "&Worlds")
        MenuBar.Append(EditMenu, "&Edit")
        MenuBar.Append(PrefsMenu, "&Preferences")
        MenuBar.Append(WindowMenu, "Windows")
        MenuBar.Append(HelpMenu, "&Help")

        self.SetMenuBar(MenuBar)

        # MENUBAR EVENTS
        #EVT_MENU( $self, $Worlds_worlds,    \&showWorldsList      )
        #EVT_MENU( $self, $Worlds_connect,   \&showConnectDialog   )
        #EVT_MENU( $self, $Worlds_close,     \&closeConnection     )
        #EVT_MENU( $self, $Worlds_reconnect, \&reconnectConnection )
        #EVT_MENU( $self, $Worlds_quit,      \&quitApplication     )

        #EVT_MENU( $self, $Edit_cut,     \&handleCut   )
        #EVT_MENU( $self, $Edit_copy,    \&handleCopy  )
        #EVT_MENU( $self, $Edit_paste,   \&handlePaste )

        #EVT_MENU( $self, $Prefs_prefs, \&showPrefsEditor )

        #EVT_MENU( $self, $Window_debugmcp, \&showDebugMCP )

        #EVT_MENU( $self, $Help_help,  sub {1} )
        #EVT_MENU( $self, $Help_about, \&showAboutBox )
        pass

    def addEvents(self):
        #EVT_SIZE( $self, \&onSize )
        pass

    def closeConnection(self):
        #$self.connection.Close
        pass

    def reconnectConnection(self):
        #$self.connection.reconnect
        pass

    def onSize(self, evt):
        #if ($prefs.save_window_size) {
        #    my ($w, $h) = $self.GetSizeWH
        #    $prefs.window_width($w)
        #    $prefs.window_height($h)
        #}
        #$evt.Skip
        pass

    def handleCopy(self):
        #if    ($self.output_pane.HasSelection) { $self.output_pane.Copy }
        #elsif ($self.input_pane .HasSelection) { $self.input_pane .Copy }
        pass

    def handleCut(self):
        self.input_pane.Cut

    def handlePaste(self):
        self.input_pane.Paste

### DIALOGS AND SUBWINDOWS

    def showWorldsList(self):
        #$self.{'worlds_list'} ||= WxMOO::Window::WorldsList($self)
        #$self.{'worlds_list'}.Show
        pass

    def showConnectDialog(self):
        #$self.{'connect_dialog'} ||= WxMOO::Window::ConnectDialog($self)
        #$self.{'connect_dialog'}.Show
        pass

    def showPrefsEditor(self):
        #$self.{'prefs_editor'} ||= WxMOO::Window::PrefsEditor($self)
        #$self.{'prefs_editor'}.Show
        pass

    def showDebugMCP(self):
        #$self.{'debug_mcp'} ||= WxMOO::Window::DebugMCP($self)
        #$self.{'debug_mcp'}.toggle_visible
        pass

# TODO - WxMOO::Window::About
    def showAboutBox(self):
        if self.about_info is None:
             info = wx.AboutDialogInfo
             info.AddDeveloper('R Pickett (emerson@hayseed.net)')
             info.SetCopyright('(c) 2013, 2014, 2015')
             info.SetWebSite('http://github.com/emersonrp/WxMOO')
             info.SetName('WxMOO')
             info.SetVersion('0.0.1')
             self.about_info = info
        wx.AboutBox(self.about_info)

    def quitApplication(self):
        self.closeConnection
        self.Close(True)
