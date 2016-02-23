import wx

# This is Solarized ANSI as per the Internet 
# https://github.com/seebi/dircolors-solarized/blob/master/dircolors.ansi-universal
color_codes = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
solarized = {
    'black'   : '#073642',
    'red'     : '#dc322f',
    'green'   : '#859900',
    'yellow'  : '#b58900',
    'blue'    : '#268bd2',
    'magenta' : '#d33682',
    'cyan'    : '#2aa198',
    'white'   : '#eee8d5',
}

class Theme(dict):
    def __init__(self, *init):
        global solarized
        for k in solarized:
            self[k] = solarized[k]
        for k in init:
            self[k] = init[k]

    def Colour(self, colour, intensity):
        hexcolour = self.get(colour) or colour
        if intensity:
            r, g, b = self.hex_to_rgb(hexcolour)
            mult = 1.33 if (intensity == "bright") else 0.66

            hexcolour = self.rgb_to_hex(self.redist_rgb(r * mult, g * mult, b * mult))

        return hexcolour

    # this is from Adaephon http://stackoverflow.com/a/27165165
    def index256_to_hex(self, index):
        index = int(index)
        if index <= 15:
            intensity = ''
            if index > 7: # bright
                intensity = 'bright'
            color = self.Colour(color_codes[index], intensity)
        elif index > 15 and index < 232:
            print("256-color index: " + str(index))
            index_R = ((index - 16) // 36)
            rgb_R = 55 + index_R * 40 if index_R > 0 else 0
            index_G = (((index - 16) % 36) // 6)
            rgb_G = 55 + index_G * 40 if index_G > 0 else 0
            index_B = ((index - 16) % 6)
            rgb_B = 55 + index_B * 40 if index_B > 0 else 0
        elif index >= 232:
            print("grayscale index: " + str(index))
            rgb_R = rgb_G = rgb_B = (index - 232) * 10 + 8
        else:
            print("bad 256 index: " + str(index))

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

