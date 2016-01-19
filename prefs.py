import wx

_get         = None
_config      = None
_defaultFont = None
_defaults   = {
    'output_fgcolour' : '#839496',
    'output_bgcolour' : '#002b36',
    'input_fgcolour'  : '#839496',
    'input_bgcolour'  : '#002b36',

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
    #'use_x_copy_paste' : WxMOO::Utility::is_unix,
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

