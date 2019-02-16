import wx
import wx.lib.newevent
import utility

PrefsChangedEvent, EVT_PREFS_CHANGED = wx.lib.newevent.NewEvent()

_config      = None
_defaults   = {
    'font'     :  wx.Font( 12, wx.TELETYPE, wx.NORMAL, wx.NORMAL ).GetNativeFontInfoDesc(),

    'save_window_size' : True,
    'window_width'     : 800,
    'window_height'    : 600,
    'input_height'     : 25,

    'use_ansi'               : True,
    'use_ansi_blink'         : True,
    'highlight_urls'         : True,
    'save_mcp_window_size'   : True,
    'autoconnect_last_world' : True,
    'local_echo'             : False,

    'mcp_window_width'  : 600,
    'mcp_window_height' : 400,

    'external_editor'  : 'gvim -f',
    'use_x_copy_paste' : utility.platform == 'linux',

    'theme' : 'ANSI',
}

def Initialize():
    global _config

    _config = wx.FileConfig()

    for default in _defaults.items():
        (key, def_val) = default
        # if nothing exists for that key, set it to the default.
        if not get(key):
            set(key, str(def_val))

def get(key):
    val =  _config.Read(key)
    # ugly string -> Boolean handling.  Hope we never have a value actually named "True" or "False"
    if val == "True":  val = True
    if val == "False": val = False
    return val

def set(param, val):
    _config.Write(param, str(val))
    _config.Flush()

def update(pw):
    # pw == prefs_window
    # This is doing some nasty GetAsString and GetNativeFontInfoDesc foo here,
    # instead of encapsulated in prefs, which I think I'm OK with.

    set('save_window_size',       pw.general_page.save_size_checkbox.GetValue() )
    set('autoconnect_last_world', pw.general_page.autoconnect_checkbox.GetValue() )
    set('use_x_copy_paste',       pw.general_page.xmouse_checkbox.GetValue() )
    set('local_echo',             pw.general_page.local_echo_checkbox.GetValue() )

    set('font',           pw.fonts_page.font_ctrl.GetSelectedFont().GetNativeFontInfoDesc())
    set('use_ansi',       pw.fonts_page.ansi_checkbox.GetValue() )
    set('use_ansi_blink', pw.fonts_page.ansi_blink_checkbox.GetValue() )

    set('theme',    pw.fonts_page.theme_picker.GetStringSelection() )

    set('external_editor', pw.paths_page.external_editor.GetValue() )

    wx.PostEvent(pw.parent, PrefsChangedEvent())

