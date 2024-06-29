import wx
import wx.lib.newevent
import platform
from pathlib import Path

PrefsChangedEvent, EVT_PREFS_CHANGED = wx.lib.newevent.NewEvent()

# set us up XDG please
if platform.system() == "Linux":
    wx.StandardPaths.Get().SetFileLayout(wx.StandardPaths.Get().FileLayout.FileLayout_XDG)

def get_prefs_dir():
    return Path(wx.StandardPaths.Get().GetUserConfigDir()) / 'wxpymoo'

def Initialize():
    _defaults   = {
        'font'     :  wx.Font( 12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ).GetNativeFontInfoDesc(),

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
        'scroll_on_output'       : True,

        'mcp_window_width'  : 600,
        'mcp_window_height' : 400,

        'use_x_copy_paste' : platform.system() == 'Linux',

        'theme' : 'ANSI',
    }
    if platform.system() == "Windows":
        _defaults['external_editor'] = "notepad"
    elif platform.system() == "Linux":
        _defaults['external_editor'] = "gvim -f"
    #elif platform.system() == "Darwin":
    # TODO what goes here?

    prefs_dir = get_prefs_dir()
    if not prefs_dir.exists():
        prefs_dir.mkdir(parents = True)
    config_file = prefs_dir / 'config'
    wx.ConfigBase.Set(wx.FileConfig(localFilename = str(config_file)))

    for key, def_val in _defaults.items():
        # if nothing exists for that key, set it to the default.
        if get(key) == None:
            set(key, str(def_val))

def get(key): return wx.ConfigBase.Get().Read(key)

def set(param, val):
    _config = wx.ConfigBase.Get()
    if param in ['save_window_size', 'use_ansi', 'use_ansi_blink', 'highlight_urls', 'save_mcp_window_size', 'autoconnect_last_world', 'local_echo', 'scroll_on_output', 'use_x_copy_paste',]:
        _config.WriteBool(param, val)
    elif param == 'theme':
        _config.Write(param, val)
    else:
        _config.WriteInt(param, val)
    _config.Flush()

def update(pw):
    _config = wx.ConfigBase.Get()
    # pw == prefs_window
    # This is doing some nasty GetAsString and GetNativeFontInfoDesc foo here,
    # instead of encapsulated in prefs, which I think I'm OK with.

    _config.WriteBool('save_window_size',       pw.save_size_checkbox.GetValue() )
    _config.WriteBool('autoconnect_last_world', pw.autoconnect_checkbox.GetValue() )
    _config.WriteBool('use_x_copy_paste',       pw.xmouse_checkbox.GetValue() )
    _config.WriteBool('local_echo',             pw.local_echo_checkbox.GetValue() )
    _config.WriteBool('scroll_on_output',       pw.scroll_on_output_checkbox.GetValue() )

    _config.Write('font',               pw.font_ctrl.GetSelectedFont().GetNativeFontInfoDesc())
    _config.WriteBool('use_ansi',       pw.ansi_checkbox.GetValue() )
    _config.WriteBool('use_ansi_blink', pw.ansi_blink_checkbox.GetValue() )

    _config.Write('theme',    pw.theme_picker.GetStringSelection() )

    _config.Write('external_editor', pw.external_editor.GetValue() )

    wx.PostEvent(pw.parent, PrefsChangedEvent())

