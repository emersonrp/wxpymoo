import wx
import prefs
import ast
import re

ansi_colour_codes = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']

# TODO -- make more themes
# TODO -- put themes into the config file

# This is Solarized ANSI as per the Internet 
# https://github.com/seebi/dircolors-solarized/blob/master/dircolors.ansi-universal

all_themes = {}
_default_themes = {
    'ANSI'           : {
        'colours' : ['#000000', '#ff0000', '#00f000', '#ffff00', '#0000ff', '#ff00ff', '#00ffff', '#ffffff',],
        'foreground' : '#bbbbbb',
        'background' : '#000000',
    },
    'solarized'      : {
        'colours' : ['#073642', '#dc322f', '#859900', '#b58900', '#268bd2', '#d33682', '#2aa198', '#eee8d5',],
        'foreground' : '#93a1a1',
        'background' : '#002b36',
    },
}

class Theme(dict):

    @classmethod
    def fetch(cls, themename = ''):
        global all_themes
        return all_themes[themename or prefs.get('theme')]

    @classmethod
    def all_theme_names(cls): return list(all_themes)

    def __init__(self, init):
        for k in init:
            self[k] = init[k]

    def Colour(self, colour, intensity = ''):
        css_colour = colour
        is_hex_already = re.match(r'^#[0-9a-f]+$', colour, re.IGNORECASE)
        if not is_hex_already:
            index = ansi_colour_codes.index(colour)
            colour_list = self.get('colours')
            css_colour = colour_list[index]

        mult = 1
        if intensity == 'bright':
            # if we have a predefined bright version, use that, otherwise just mult the existing one
            if (not is_hex_already) and len(colour_list) > 8:
                css_colour = colour_list[index + 8]
            else:
                mult = 1.33
        elif intensity == 'dim':
            mult = 0.66

        r, g, b = self.hex_to_rgb(css_colour)
        hexcolour = self.rgb_to_hex(self.redist_rgb(r * mult, g * mult, b * mult))
        return hexcolour

    # this is from Adaephon http://stackoverflow.com/a/27165165
    def index256_to_hex(self, index):
        if index <= 15:
            intensity = ''
            if index > 7: # bright
                intensity = 'bright'
            colour = self.Colour(ansi_colour_codes[index], intensity)
            rgb_R, rgb_G, rgb_B = self.hex_to_rgb(colour)
        elif index > 15 and index < 232:
            index_R = ((index - 16) // 36)
            rgb_R = 55 + index_R * 40 if index_R > 0 else 0
            index_G = (((index - 16) % 36) // 6)
            rgb_G = 55 + index_G * 40 if index_G > 0 else 0
            index_B = ((index - 16) % 6)
            rgb_B = 55 + index_B * 40 if index_B > 0 else 0
        elif index >= 232:
            rgb_R = rgb_G = rgb_B = (index - 232) * 10 + 8
        else:
            print('bad 256 index: ' + str(index))

        return self.rgb_to_hex((rgb_R, rgb_G, rgb_B))

    # these two from Jeremy Cantrell http://stackoverflow.com/a/214657
    def hex_to_rgb(self, value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % rgb

    # this one from Mark Ransom http://stackoverflow.com/a/141943
    def redist_rgb(self, r, g, b):
        threshold = 255.999
        m = max(r, g, b)
        if m <= threshold:
            return int(r), int(g), int(b)
        total = r + g + b
        if total >= 3 * threshold:
            return int(threshold), int(threshold), int(threshold)
        x = (3 * threshold - total) / (3 * m - total)
        gray = threshold - x * m
        return int(gray + x * r), int(gray + x * g), int(gray + x * b)

def Initialize():
    global _config, all_themes
    _config = wx.FileConfig()

    _config.SetPath('/Themes/')

    # loop worlds...
    g_more, themename, g_index = _config.GetFirstGroup()
    if g_more:  # do we have anything at all from the config file?
        while g_more: # yes, loop and fill stuff out.
            _config.SetPath(themename)

            theme = {}
            # loop data lines inside each theme....
            e_more, keyname, e_index = _config.GetFirstEntry()
            while e_more:
                theme[keyname] = _config.Read(keyname)
                e_more, keyname, e_index = _config.GetNextEntry(e_index)

            # turn the list of colours back into a list
            theme['colours'] = ast.literal_eval(theme['colours'])
            all_themes[themename] = Theme(theme)

            # carry on, back to the top for the next world
            _config.SetPath('/Themes/')
            g_more, themename, g_index = _config.GetNextGroup(g_index)

    else:  # nothing from config file, grab the _default_themes data

        for name, theme in _default_themes.items():
            _config.SetPath(name)

            for key, val in theme.items():
                _config.Write(key, str(val))

            _config.SetPath('/Themes/')

            all_themes[name] = Theme(theme)

    _config.SetPath('/')
