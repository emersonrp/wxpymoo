import wx
import ast
import re
import prefs

all_themes = {}

class Theme(dict):

    @classmethod
    def fetch(cls, themename = ''):
        config = wx.ConfigBase.Get()
        global all_themes
        return all_themes[themename or config.Read('theme')]

    @classmethod
    def all_theme_names(cls): return list(all_themes)

    def __init__(self, init):
        for k in init:
            self[k] = init[k]

    def Colour(self, colour, intensity = ''):
        css_colour = colour
        colour_list = []
        index = 0
        is_hex_already = re.match(r'^#[0-9a-f]+$', colour, re.IGNORECASE)
        if not is_hex_already:
            index = ansi_colour_codes.index(colour)
            colour_list = self.get('colours', [])
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
        rgb_R = 0
        rgb_G = 0
        rgb_B = 0
        if index <= 15:
            intensity = ''
            if index > 7: # bright
                intensity = 'bright'
                index = index - 8
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
            wx.LogMessage('bad 256 index: ' + str(index))

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
    themesconfig = wx.FileConfig(localFilename = str(prefs.get_prefs_dir() / 'themes'))

    # loop themes...
    g_more, themename, g_index = themesconfig.GetFirstGroup()
    if g_more:  # do we have anything at all from the themesconfig file?
        while g_more: # yes, loop and fill stuff out.
            themesconfig.SetPath(themename)

            theme = {}
            # loop data lines inside each theme....
            e_more, keyname, e_index = themesconfig.GetFirstEntry()
            while e_more:
                theme[keyname] = themesconfig.Read(keyname)
                e_more, keyname, e_index = themesconfig.GetNextEntry(e_index)

            # turn the list of colours back into a list
            theme['colours'] = ast.literal_eval(theme['colours'])
            all_themes[themename] = Theme(theme)

            # carry on, back to the top for the next world
            themesconfig.SetPath('/')
            g_more, themename, g_index = themesconfig.GetNextGroup(g_index)

    else:  # nothing from themesconfig file, grab the _default_themes data

        for name, theme in _default_themes.items():
            themesconfig.SetPath(name)

            for key, val in theme.items():
                themesconfig.Write(key, str(val))

            themesconfig.SetPath('/')

            all_themes[name] = Theme(theme)


#### DATA
ansi_colour_codes = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
_default_themes = {
        'ANSI'           : {
            'colours' : ['#000000', '#ff0000', '#00f000', '#ffff00', '#0000ff', '#ff00ff', '#00ffff', '#ffffff',],
            'foreground' : '#bbbbbb',
            'background' : '#000000',
            },
        'solarized'      : {
            'author' : 'Ethan Schoonover',
            'colours' : ['#073642', '#dc322f', '#859900', '#b58900', '#268bd2', '#d33682', '#2aa198', '#eee8d5',],
            'foreground' : '#93a1a1',
            'background' : '#002b36',
            },
        'Dawn': {
            'author': 'Escapist',
            'colours': [ '#353535', '#744B40', '#6D6137', '#765636', '#61564B', '#6B4A49', '#435861', '#B3B3B3',
                         '#5F5F5F', '#785850', '#6F6749', '#776049', '#696057', '#6F5A59', '#525F66', '#CDCDCD' ],
            'foreground': '#9B9081',
            'background': '#181B20'
            },
        'Gotham': {
            'author': 'whatyouhide',
            'colours': [ '#0a0f14', '#c33027', '#26a98b', '#edb54b', '#195465', '#4e5165', '#33859d', '#98d1ce',
                         '#10151b', '#d26939', '#081f2d', '#245361', '#093748', '#888ba5', '#599caa', '#d3ebe9' ],
            'foreground': '#98d1ce',
            'background': '#0a0f14'
            },
        'hund' : {
            'author': 'hund',
            'colours': [ '#222222', '#E84F4F', '#B7CE42', '#FEA63C', '#66AABB', '#B7416E', '#6D878D', '#DDDDDD',
                         '#666666', '#D23D3D', '#BDE077', '#FFE863', '#AACCBB', '#E16A98', '#42717B', '#CCCCCC' ],
            'foreground': '#FFFFFF',
            'background': '#161616'
            },
        'Hybrid' : {
            'author': 'w0ng',
            'colours': [ '#282A2E', '#A54242', '#8C9440', '#DE935F', '#5F819D', '#85678F', '#5E8D87', '#707880',
                         '#373B41', '#CC6666', '#B5BD68', '#F0C674', '#81A2BE', '#B294BB', '#8ABEB7', '#C5C8C6' ],
            'foreground': '#C5C8C6',
            'background': '#1D1F21'
            },
        'Invisibone': {
            'author': 'Baskerville',
            'colours': [ '#303030', '#D370A3', '#6D9E3F', '#B58858', '#6095C5', '#AC7BDE', '#3BA275', '#CFCFCF',
                         '#686868', '#FFA7DA', '#A3D572', '#EFBD8B', '#98CBFE', '#E5B0FF', '#75DAA9', '#FFFFFF' ],
            'foreground': '#A0A0A0',
            'background': '#232323'
            },
        'jmbi' : {
                'author': 'jmbi',
                'colours': [ '#5A7260', '#8F423C', '#BBBB88', '#F9D25B', '#E0BA69', '#709289', '#D13516', '#EFE2E0',
                             '#8DA691', '#EEAA88', '#CCC68D', '#EEDD99', '#C9B957', '#FFCBAB', '#C25431', '#F9F1ED' ],
                'foreground': '#ffffff',
                'background': '#1e1e1e'
                },
        'Kasugano' : {
                'author': 'Kori Ayakashi',
                'colours': [ '#3D3D3D', '#6673BF', '#3EA290', '#B0EAD9', '#31658C', '#596196', '#8292B2', '#C8CACC',
                             '#4D4D4D', '#899AFF', '#52AD91', '#98C9BB', '#477AB3', '#7882BF', '#95A7CC', '#EDEFF2' ],
                'foreground': '#ffffff',
                'background': '#1b1b1b'
                },

        'Monokai': {
                'author': 'Cacodaimon',
                'colours': [ '#48483e', '#dc2566', '#8fc029', '#d4c96e', '#55bcce', '#9358fe', '#56b7a5', '#acada1',
                             '#76715e', '#fa2772', '#a7e22e', '#e7db75', '#66d9ee', '#ae82ff', '#66efd5', '#cfd0c2' ],
                'foreground': '#f1ebeb',
                'background': '#272822'
                },
        'Mostly Bright': {
                'author': 'm83',
                'colours': [ '#D3D3D3', '#EF6B7B', '#A1D569', '#F59335', '#4EC2E8', '#FEC7CD', '#95C1C0', '#707070',
                             '#B3B3B3', '#ED5466', '#AFDB80', '#F59335', '#5DC7EA', '#D2A4B4', '#75A1A0', '#909090' ],
                'foreground': '#707070',
                'background': '#F3F3F3'
                },
        'Navy and Ivory': {
                'author': 'hal',
                'colours': [ '#032c36', '#c2454e', '#7cbf9e', '#8a7a63', '#2e3340', '#ff5879', '#44b5b1', '#f2f1b9',
                             '#065f73', '#ef5847', '#a2d9b1', '#beb090', '#61778d', '#ff99a1', '#9ed9d8', '#f6f6c9' ],
                'foreground': '#e8dfd6',
                'background': '#021b21'
                },
        'Pretty and Pastel' : {
                'author': 'IWAFU',
                'colours': [ '#292929', '#CF6A4C', '#19CB00', '#FAD07A', '#8197BF', '#8787AF', '#668799', '#888888',
                             '#525252', '#FF9D80', '#23FD00', '#FFEFBF', '#ACCAFF', '#C4C4FF', '#80BFAF', '#E8E8D3' ],
                'foreground': '#888888',
                'background': '#151515'
                },
        's3r0 modified' : {
                'author': 'earsplit',
                'colours': [ '#4A3637', '#D17B49', '#7B8748', '#AF865A', '#535C5C', '#775759', '#6D715E', '#C0B18B',
                             '#4A3637', '#D17B49', '#7B8748', '#AF865A', '#535C5C', '#775759', '#6D715E', '#C0B18B' ],
                'foreground': '#C0B18B',
                'background': '#1F1F1F'
                },
        'Sweet Love' : {
                'author': 'Boroshlawa',
                'colours': [ '#4A3637', '#D17B49', '#7B8748', '#AF865A', '#535C5C', '#775759', '#6D715E', '#C0B18B',
                             '#402E2E', '#AC5D2F', '#647035', '#8F6840', '#444B4B', '#614445', '#585C49', '#978965' ],
                'foreground': '#C0B18B',
                'background': '#1F1F1F'
                },
        'Trim Yer Beard' : {
                'author': 'franksn',
                'colours': [ '#0F0E0D', '#845336', '#57553C', '#A17E3E', '#43454F', '#604848', '#5C6652', '#A18B62',
                             '#383332', '#8C4F4A', '#898471', '#C8B491', '#65788F', '#755E4A', '#718062', '#BC9D66' ],
                'foreground': '#DABA8B',
                'background': '#191716'
                },
        'Vacuous 2' : {
                'author': 'hal',
                'colours': [ '#202020', '#b91e2e', '#81957c', '#f9bb80', '#356579', '#2d2031', '#0b3452', '#909090',
                             '#606060', '#d14548', '#a7b79a', '#fae3a0', '#7491a1', '#87314e', '#0f829d', '#fff0f0' ],
                'foreground': '#d2c5bc',
                'background': '#101010'
                },
        'Visibone Alt. 2' : {
                'author': 'Gutterslob',
                'colours': [ '#666666', '#CC6699', '#99CC66', '#CC9966', '#6699CC', '#9966CC', '#66CC99', '#CCCCCC',
                             '#999999', '#FF99CC', '#CCFF99', '#FFCC99', '#99CCFF', '#CC99FF', '#99FFCC', '#FFFFFF' ],
                'foreground': '#CCCCCC',
                'background': '#333333'
                },
        'X::DotShare' : {
                'author': 'crshd',
                'colours': [ '#101010', '#E84F4F', '#B8D68C', '#E1AA5D', '#7DC1CF', '#9B64FB', '#6D878D', '#DDDDDD',
                             '#404040', '#D23D3D', '#A0CF5D', '#F39D21', '#4E9FB1', '#8542FF', '#42717B', '#DDDDDD' ],
                'foreground': '#D7D0C7',
                'background': '#151515'
                },
        'X::Erosion' : {
                'author': 'earsplit',
                'colours': [ '#332D29', '#8C644C', '#746C48', '#908A66', '#646A6D', '#605655', '#4B5C5E', '#504339',
                             '#817267', '#9F7155', '#857B52', '#9C956E', '#71777A', '#656565', '#556D70', '#9A875F' ],
                'foreground': '#BEA492',
                'background': '#181512'
                },
        'Yousai' : {
                'author': 'Kori',
                'colours': [ '#666661', '#992E2E', '#4C3226', '#A67C53', '#4C7399', '#BF9986', '#D97742', '#34302D',
                             '#7F7F7A', '#B23636', '#664233', '#BF8F60', '#5986B2', '#D9AE98', '#F2854A', '#4C4742' ],
                'foreground': '#34302D',
                'background': '#F5E7DE'
                },

        }
