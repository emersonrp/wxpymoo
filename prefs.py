import wx
import wx.lib.newevent
import utility

PrefsChangedEvent, EVT_PREFS_CHANGED = wx.lib.newevent.NewEvent()

_get         = None
_config      = None
_defaultFont = None
_defaults   = {
    'fgcolour' : '#839496',
    'bgcolour' : '#002b36',

    'save_window_size' : True,
    'window_width'     : 800,
    'window_height'    : 600,
    'input_height'     : 25,

    # 'theme'        : 'solarized',

    'use_ansi'             : True,
    'use_mcp'              : True,
    'highlight_urls'       : True,
    'save_mcp_window_size' : True,
    # TODO -- make this default to False, but currently having no connection
    # at start-time breaks mainwindow
    'autoconnect_last_world'  : True,

    'mcp_window_width'  : 600,
    'mcp_window_height' : 400,

    'external_editor'  : 'gvim -f',
    'use_x_copy_paste' : utility.platform == 'linux',
}

def Initialize():
    global _config, _defaultFont, get

    _config                  = wx.FileConfig()
    _get                     = _config.Read
    _defaultFont             = wx.Font( 12, wx.TELETYPE, wx.NORMAL, wx.NORMAL )
    _defaults['input_font']  = _defaultFont.GetNativeFontInfoDesc()
    _defaults['output_font'] = _defaultFont.GetNativeFontInfoDesc()
    for default in _defaults.items():
        (key, def_val) = default
        # if nothing exists for that key, set it to the default.
        if not get(key):
            set(key, str(def_val))

def get(val): return _config.Read(val)
def set(param, val):
    global _config

    _config.Write(param, str(val))
    _config.Flush()

def update(prefs_window):
    # This is doing some nasty GetAsString and GetNativeFontInfoDesc foo here,
    # instead of encapsulated in prefs, which I think I'm OK with.

    set('save_window_size',       prefs_window.general_page.save_size_checkbox.GetValue() )
    set('autoconnect_last_world', prefs_window.general_page.autoconnect_checkbox.GetValue() )

    set('font',prefs_window.fonts_page.font_ctrl.GetSelectedFont().GetNativeFontInfoDesc())

    set('fgcolour',prefs_window.fonts_page.fgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
    set('bgcolour',prefs_window.fonts_page.bgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))

    set('use_ansi', prefs_window.fonts_page.ansi_checkbox.GetValue() )

    set('external_editor', prefs_window.paths_page.external_editor.GetValue() )

    prefs_evt = PrefsChangedEvent()
    wx.PostEvent(prefs_window.parent, prefs_evt)

