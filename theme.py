import wx

# This is Solarized ANSI as per the Internet 
# https://github.com/seebi/dircolors-solarized/blob/master/dircolors.ansi-universal
# except with the 'bright' colors tweaked to be actually brighter versions of 
# the dark colors, instead of various of the 'base' colors.
solarized = {
    'b_black'   : '#586e75',
    'd_black'   : '#073642',
    'b_red'     : '#cb4b16',
    'd_red'     : '#dc322f',
    'b_green'   : '#85bb00',
    'd_green'   : '#859900',
    'b_yellow'  : '#c79b00',
    'd_yellow'  : '#b58900',
    'b_blue'    : '#26aef5',
    'd_blue'    : '#268bd2',
    'b_magenta' : '#f636a5',
    'd_magenta' : '#d33682',
    'b_cyan'    : '#2ac4cb',
    'd_cyan'    : '#2aa198',
    'b_white'   : '#fdf6e3',
    'd_white'   : '#eee8d5',
}

class Theme(dict):
    def __init__(self, *init):
        global solarized
        for k in solarized:
            self[k] = solarized[k]
        for k in init:
            self[k] = init[k]

    def Colour(self, colour, bright):
        prefix = 'b' if bright else 'd'
        return self[prefix + "_" + colour]
