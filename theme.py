import wx

# This is Solarized ANSI as per the Internet 
# https://github.com/seebi/dircolors-solarized/blob/master/dircolors.ansi-universal
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
            r, g, b = hex_to_rgb(hexcolour)
            mult = 1.33 if (intensity == "bright") else 0.66

            hexcolour = rgb_to_hex(redist_rgb(r * mult, g * mult, b * mult))

        return hexcolour

# these two from Jeremy Cantrell http://stackoverflow.com/a/214657
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

# this one from Mark Ransom http://stackoverflow.com/a/141943
def redist_rgb(r, g, b):
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

