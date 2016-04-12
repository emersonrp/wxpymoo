import wx
import wx.richtext as rtc
import wx.lib.newevent

import prefs
import utility
from theme import Theme
from window.basepane import BasePane

#import webbrowser, re, math, emoji
import webbrowser, re, math

RowColChangeEvent, EVT_ROW_COL_CHANGED = wx.lib.newevent.NewEvent()

class OutputPane(BasePane):
    def __init__(self, parent, connection):
        BasePane.__init__(self, parent, connection,
            style = wx.TE_AUTO_URL | wx.TE_READONLY | wx.TE_NOHIDESEL | wx.TE_MULTILINE
        )

        # state toggles for ANSI processing
        self.intensity = ''
        self.inverse = False

        self.theme = Theme()

        # TODO - this probably should be a preference, but for now, this is the
        # least-bad default behavior.
        self.Bind(wx.EVT_SIZE                        , self.on_size)
        self.Bind(wx.EVT_SET_FOCUS                   , self.focus_input)
        self.Bind(wx.EVT_TEXT_URL                    , self.process_url_click)
        self.Bind(wx.EVT_MIDDLE_UP                   , self.connection.input_pane.paste_from_selection )
        self.Bind(rtc.EVT_RICHTEXT_SELECTION_CHANGED , self.copy_from_selection )
        self.Bind(EVT_ROW_COL_CHANGED                , self.on_row_col_changed )

    # EVENT HANDLERS #######################
    def on_row_col_changed(self, evt):
        pass
        # TODO - "if preferences dictate, send @linelength to self.connection"

    # This updates the widget's internal notion of "how big" it is in characters
    # it throws an event if the size *in chars* changes, nothing if the change in size was < 1 char
    def on_size(self, evt):

        font_width, font_height = self.font_size()
        self_width, self_height = self.GetSizeTuple()

        new_cols = math.floor(self_width  / font_width) - 2  # "-2" to allow for margins
        new_rows = math.floor(self_height / font_height)

        if (new_cols != self.cols) or (new_rows != self.rows):
            self.cols = new_cols
            self.rows = new_rows
            rc_evt = RowColChangeEvent()
            wx.PostEvent(self, rc_evt)

        self.ScrollIfAppropriate()
        evt.Skip()

    def copy_from_selection(self, evt):
        uxcp = prefs.get('use_x_copy_paste') == 'True'
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(True)
        self.Copy()
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(False)

    def process_url_click(self, evt):
        url = evt.GetString()
        wx.BeginBusyCursor()
        webbrowser.open(url)
        wx.EndBusyCursor()

    def focus_input(self, evt):
        self.connection.input_pane.SetFocus()

    ######################################
    def WriteText(self, rest):
        super(OutputPane, self).WriteText(rest)
        self.ScrollIfAppropriate()

    def is_at_bottom(self):
        return True

    def ScrollIfAppropriate(self):
        if (self.is_at_bottom() or prefs.get('scroll_on_output') == 'True'):
            self.ShowPosition(self.GetLastPosition())
        self.Refresh()

    def Thaw(self):
        super(OutputPane, self).Thaw()
        self.ScrollIfAppropriate()

    def display(self, text):
        self.SetInsertionPointEnd()
        text = text.decode('latin-1') # TODO - is this the right thing and/or place for this?
        # self.Freeze() # causing delay on last line - TODO: investigate
        for line in text.split('\n'):
            line = line + "\n"
            if prefs.get('use_mcp') == 'True':
                line = self.connection.mcp.output_filter(line)
                if not line: continue  # output_filter returns falsie if it handled it.

            #if (True or prefs.get('render_emoji') == 'True'):
                # TODO - preference?  "if (we detect an emoji)?"
                #line = emoji.emojize(line, use_aliases = True)

            if prefs.get('use_ansi') == 'True':
                # Dear lord this is sorta ugly

                # snip and ring bells
                # TODO -- "if beep is enabled in the prefs"
                line, count = re.subn("\007", '', line)
                for b in range(0, count):
                    print("DEBUG: found an ANSI beep")
                    wx.Bell();

                # chop the line into text, ansi, text, ansi....
                bits = re.split('\033\[(\d+(?:;\d+)*)m', line)

                for idx, bit in enumerate(bits):
                    if bit == '': continue

                    # if it's ansi...
                    if (idx % 2):
                        # pick apart the ANSI stuff.
                        codes = [int(c) for c in bit.split(';')]
                        while codes:
                            command, payload = ansi_codes[codes.pop(0)]
                            if command == 'control':
                                if payload == 'normal':
                                    self.EndAllStyles()
                                    self.intensity = ''
                                    self.inverse = False
                                    self.fg_colour = prefs.get('fgcolour')
                                    self.bg_colour = prefs.get('bgcolour')
                                    self.set_current_colours()
                                elif payload == 'bright':
                                    self.intensity = 'bright'
                                    self.set_current_colours()
                                elif payload == 'dim':
                                    self.intensity = 'dim'
                                    self.set_current_colours()
                                elif payload == 'italic':    self.BeginItalic()
                                elif payload == 'underline': self.BeginUnderline()
                                elif payload == 'blink':
                                    print('Got an ANSI "blink"')
                                    # TODO - create timer
                                    # apply style name
                                    # periodically switch foreground color to background
                                elif payload == 'inverse':
                                    self.inverse = True
                                    self.set_current_colours()
                                elif payload == 'conceal':
                                    print('Got an ANSI "conceal"')
                                elif payload == 'strike':
                                    font = self.GetFont()
                                    font.SetStrikethrough(True)
                                    self.BeginFont(font)
                                elif payload == 'normal_weight':
                                    self.intensity = ''
                                    self.set_current_colours()
                                elif payload == "no_italic":    self.EndItalic()
                                elif payload == 'no_underline': self.EndUnderline()
                                elif payload == 'no_blink':
                                    print('Got an ANSI "no_blink"')
                                    # TODO - remove blink-code-handles style
                                elif payload == "no_conceal":
                                    print('Got an ANSI "no_conceal"')
                                elif payload == 'no_strike':
                                    font = self.GetFont()
                                    font.SetStrikethrough(False)
                                    self.BeginFont(font)

                                elif payload == 'framed':
                                    print('Got an ANSI "framed"')
                                elif payload == 'encircled':
                                    print('Got an ANSI "encircled"')
                                elif payload == 'overline':
                                    print('Got an ANSI "overline"')

                                elif payload == 'no_framed_encircled':
                                    print('Got an ANSI "no_framed_encircled"')
                                elif payload == 'no_overline':
                                    print('Got an ANSI "no_overline"')

                            elif command == 'foreground' or command == "background":
                                if payload == "extended":
                                    subtype = codes.pop(0)
                                    # 24-bit color
                                    if subtype == 2:
                                        colour = self.theme.rgb_to_hex((codes.pop(0), codes.pop(0), codes.pop(0)))
                                    # 256-color
                                    elif subtype == 5:
                                        colour = self.theme.index256_to_hex(codes.pop(0))
                                    else:
                                        print("Got an unknown fg/bg ANSI subtype: " + str(subtype))
                                else:
                                    colour = payload

                                if command == "foreground":
                                    self.fg_colour = colour
                                else:
                                    self.bg_colour = colour
                                self.set_current_colours()
                            else:
                                print("unknown ANSI command:", command)
                    else:
                        # is a text-only chunk, check for URLs
                        if prefs.get('highlight_urls') == 'True':
                            matches = re.split(utility.URL_REGEX, bit)
                            for chunk in matches:
                                if chunk is None: continue
                                if re.match(utility.URL_REGEX, chunk):
                                    self.BeginURL(chunk)
                                    self.BeginUnderline()

                                    current_intensity = self.intensity
                                    self.intensity = 'normal'
                                    self.BeginTextColour( self.lookup_colour('blue') )
                                    self.intensity = current_intensity

                                    self.WriteText(chunk)

                                    self.EndTextColour()
                                    self.EndUnderline()
                                    self.EndURL()
                                else:
                                    self.WriteText(chunk)
                        else:
                            self.WriteText(bit)
        # self.Thaw() # causing delay on last line - TODO investigate.

    def foreground_colour(self):
        return self.theme.Colour(self.fg_colour, self.intensity)

    def background_colour(self):
        return self.theme.Colour(self.bg_colour)

    def lookup_colour(self, color):
        return self.theme.Colour(color, self.intensity)

    def set_current_colours(self):
        current = rtc.RichTextAttr()
        if self.inverse:
            current.SetTextColour      (self.background_colour())
            current.SetBackgroundColour(self.foreground_colour())
        else:
            current.SetTextColour      (self.foreground_colour())
            current.SetBackgroundColour(self.background_colour())

        self.BeginStyle(current)

    def ansi_test(self):
        self.Freeze()
        self.display("")
        self.display("--- ANSI TEST BEGIN ---")
        self.display("System Colors:")

        fg_cube = bg_cube = ''

        for c in range(0,7):
            fg_cube += "\033[3" + str(c) + "m*\033[0m"
            bg_cube += "\033[4" + str(c) + "m \033[0m"
        self.display(fg_cube + "    " + bg_cube)
        fg_cube = bg_cube = ''

        self.display("")
        self.display("Color cube, 6x6x6")
        for g in range(0,6):
            for b in range(0,6):
                for r in range(0,6):
                    c = ((r * 36) + (g * 6) + b) + 16
                    fg_cube += "\033[38;5;" + str(c) + "m*\033[0m"
                    bg_cube += "\033[48;5;" + str(c) + "m \033[0m"
            self.display(fg_cube + "    " + bg_cube)
            fg_cube = bg_cube = ''

        self.display("")
        self.display("Greyscale ramp:")
        for c in range(232,255):
            fg_cube += "\033[38;5;" + str(c) + "m*\033[0m"
            bg_cube += "\033[48;5;" + str(c) + "m \033[0m"
        self.display(fg_cube + "    " + bg_cube)
        fg_cube = bg_cube = ''

        self.display("")
        self.display("Some random 24-bit color samples:")
        from random import randint
        line = ""
        for i in range(0,6):
            for j in range(0,6):
                r = randint(0,255)
                g = randint(0,255)
                b = randint(0,255)
                fg_bg = 48 if (j % 2) else 38

                line += "\033[" + ("%d;2;%d;%d;%dm (%3d,%3d,%3d) " % (fg_bg, r, g, b, r, g, b)) + "\033[0m"
            self.display(line)
            line = ""
        self.display("")
        self.display("--- ANSI TEST END ---")
        self.display("")
        self.Thaw()


ansi_codes = {
    0     : [ 'control' , 'normal'    ],
    1     : [ 'control' , 'bright'    ],
    2     : [ 'control' , 'dim'       ],
    3     : [ 'control' , 'italic'    ],
    4     : [ 'control' , 'underline' ],
    5     : [ 'control' , 'blink'     ],
    7     : [ 'control' , 'inverse'   ],
    8     : [ 'control' , 'conceal'   ],
    9     : [ 'control' , 'strike'    ],
    # 10 - primary font
    # 11 - 19 - alternate fonts
    # 20 - fraktur
    22    : [ 'control' , 'normal_weight' ],
    23    : [ 'control' , 'no_italic'     ],
    24    : [ 'control' , 'no_underline'  ],
    25    : [ 'control' , 'no_blink'      ],
    28    : [ 'control' , 'no_conceal'    ],
    29    : [ 'control' , 'no_strike'     ],

    30    : [ 'foreground' , 'black'    ],
    31    : [ 'foreground' , 'red'      ],
    32    : [ 'foreground' , 'green'    ],
    33    : [ 'foreground' , 'yellow'   ],
    34    : [ 'foreground' , 'blue'     ],
    35    : [ 'foreground' , 'magenta'  ],
    36    : [ 'foreground' , 'cyan'     ],
    37    : [ 'foreground' , 'white'    ],
    38    : [ 'foreground' , 'extended' ],
    # 39 - default foreground color

    40    : [ 'background' , 'black'    ],
    41    : [ 'background' , 'red'      ],
    42    : [ 'background' , 'green'    ],
    43    : [ 'background' , 'yellow'   ],
    44    : [ 'background' , 'blue'     ],
    45    : [ 'background' , 'magenta'  ],
    46    : [ 'background' , 'cyan'     ],
    47    : [ 'background' , 'white'    ],
    48    : [ 'background' , 'extended' ],
    # 49 - default background color
    # 50 - reserved
    51    : [ 'control' , 'framed' ],
    52    : [ 'control' , 'encircled' ],
    53    : [ 'control' , 'overline' ],
    54    : [ 'control' , 'no_framed_encircled' ],
    55    : [ 'control' , 'no_overline' ],
}

