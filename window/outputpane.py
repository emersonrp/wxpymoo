import wx
import wx.richtext as rtc
import wx.lib.newevent
import re

import filters.telnetiac

import prefs
import utility
from editor import Editor
from window.basepane import BasePane
from filters.ansi import fansi_replace

#import webbrowser, re, math, emoji
import webbrowser, re, math

LOCALEDIT_LINE = re.compile(utility.OOB_PREFIX.pattern + ' edit name: (.+?) upload: (.+)')

RowColChangeEvent, EVT_ROW_COL_CHANGED = wx.lib.newevent.NewEvent()

class OutputPane(BasePane):
    def __init__(self, parent, connection):
        BasePane.__init__(self, parent, connection,
            style = wx.TE_AUTO_URL | wx.TE_READONLY | wx.TE_NOHIDESEL | wx.TE_MULTILINE
        )

        # state toggles for ANSI processing
        self.intensity = ''
        self.inverse = False

        # output filters can register themselves
        self.filters = [filters.telnetiac.process_line, self.lm_localedit_filter]
        self.localedit_contents = None

        # TODO - this probably should be a preference, but for now, this is the
        # least-bad default behavior.
        self.Bind(wx.EVT_SIZE                        , self.on_size)
        self.Bind(wx.EVT_SET_FOCUS                   , self.focus_input)
        self.Bind(wx.EVT_TEXT_URL                    , self.process_url_click)
        self.Bind(EVT_ROW_COL_CHANGED                , self.on_row_col_changed )

    def register_filter(self, filter_callback):
        self.filters.append(filter_callback)

    # EVENT HANDLERS #######################
    def on_row_col_changed(self, evt):
        pass
        # TODO - "if preferences dictate, send @linelength to self.connection"

    # This updates the widget's internal notion of "how big" it is in characters
    # it throws an event if the size *in chars* changes, nothing if the change in size was < 1 char
    def on_size(self, evt):

        font_width, font_height = self.font_size()
        self_size               = self.GetSize()

        new_cols = math.floor(self_size.width  / font_width) - 3  # "- 3" to allow for margins
        new_rows = math.floor(self_size.height / font_height)

        if (new_cols != self.cols) or (new_rows != self.rows):
            self.cols = new_cols
            self.rows = new_rows
            rc_evt = RowColChangeEvent()
            wx.PostEvent(self, rc_evt)

        wx.CallAfter( self.ScrollIfAppropriate )
        evt.Skip()

    def process_url_click(self, evt):
        url = evt.GetString()
        wx.BeginBusyCursor()
        if not re.match(r'^https?://', url):
            url = "http://" + url
        webbrowser.open(url)
        wx.EndBusyCursor()

    def focus_input(self, evt):
        self.connection.input_pane.SetFocus()

    ######################################
    def WriteText(self, rest):
        super(OutputPane, self).WriteText(rest)
        self.ScrollIfAppropriate()

    def is_at_bottom(self):
        # TODO - "is the bottom line currently visible / not scrolled-off"
        return True

    def ScrollIfAppropriate(self):
        if (self.is_at_bottom() or prefs.get('scroll_on_output')):
            self.ShowPosition(self.GetLastPosition())
            self.Refresh()

    def Thaw(self):
        super(OutputPane, self).Thaw()
        self.ScrollIfAppropriate()

    def display(self, text):
        self.SetInsertionPointEnd()
        self.Freeze()
        for line in text.split('\n+'):

            for fil in self.filters:
                line = fil(self, line)
                if line == None: break  # output_filter must return None / void, if it handled it
            if not line: continue

            #if (True or prefs.get('render_emoji'):
                # TODO - preference?  "if (we detect an emoji)?"
                #line = emoji.emojize(line, use_aliases = True)

            if prefs.get('use_ansi'):
                # Dear lord this is sorta ugly

                # TODO -- let's make this whole thing an external filter that
                # returns text chunks and TextAttrs to blat at the screen.  For
                # now, we can still do it line-by-line, but eventually we might
                # want to be properly character-based/VT supporting.

                # For now, we'll stick the FANSI character poop into an
                # external filter.
                if self.connection.world.get("use_fansi"):
                    line = fansi_replace(line)

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

                            if command == 'foreground' or command == "background":
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

                                if command == "foreground" : self.fg_colour = colour
                                else                       : self.bg_colour = colour
                                self.set_current_colours()

                            elif command == 'control':
                                switcher = {
                                    'normal'              : self.doansi_normal,
                                    'bright'              : self.doansi_bright,
                                    'dim'                 : self.doansi_dim,
                                    'italic'              : self.BeginItalic,
                                    'underline'           : self.BeginUnderline,
                                    'blink'               : self.doansi_blink,
                                    'inverse'             : self.doansi_inverse,
                                    'conceal'             : self.doansi_conceal,
                                    'strike'              : self.doansi_strike,
                                    'normal_weight'       : self.doansi_normal_weight,
                                    'no_italic'           : self.EndItalic,
                                    'no_underline'        : self.EndUnderline,
                                    'no_blink'            : self.doansi_no_blink,
                                    'no_conceal'          : self.doansi_no_conceal,
                                    'no_strike'           : self.doansi_no_strike,
                                    'framed'              : self.doansi_framed,
                                    'encircled'           : self.doansi_encircled,
                                    'overline'            : self.doansi_overline,
                                    'no_framed_encircled' : self.doansi_no_framed_encircled,
                                    'no_overline'         : self.doansi_no_overline,
                                    'default_fg'          : self.doansi_default_fg,
                                    'default_bg'          : self.doansi_default_bg,
                                }
                                ansifunc = switcher.get(payload, lambda: "Unknown ANSI sequence")
                                ansifunc()

                            else:
                                print("unknown ANSI command:", command)
                    else:
                        # is a text-only chunk, check for URLs
                        if prefs.get('highlight_urls'):
                            matches = utility.URL_REGEX.split(bit)
                            for chunk in matches:
                                if not chunk: continue
                                if utility.URL_REGEX.match(chunk):
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
            else:
                self.WriteText(line)
        self.Thaw()
        if not line == None: self.WriteText("\n")

    ### ANSI HANDLERS
    def doansi_normal(self):
        self.EndAllStyles()
        self.intensity = ''
        self.inverse = False
        self.fg_colour = self.theme.get('foreground')
        self.bg_colour = self.theme.get('background')
        self.set_current_colours()
    def doansi_bright(self):
        self.intensity = 'bright'
        self.set_current_colours()
    def doansi_dim(self):
        self.intensity = 'dim'
        self.set_current_colours()
    def doansi_blink(self):
        print('Got an ANSI "blink"')
        # TODO - create timer
        # apply style name
        # periodically switch foreground color to background
    def doansi_inverse(self):
        self.inverse = True
        self.set_current_colours()
    def doansi_strike(self):
        font = self.GetFont()
        font.SetStrikethrough(True)
        self.BeginFont(font)
    def doansi_normal_weight(self):
        self.intensity = ''
        self.set_current_colours()
    def doansi_no_blink(self):
        print('Got an ANSI "no_blink"')
        # TODO - remove blink-code-handles style
    def doansi_no_strike(self):
        font = self.GetFont()
        font.SetStrikethrough(False)
        self.BeginFont(font)
    def doansi_default_fg(self):
        self.fg_colour = self.theme.get('foreground')
        self.set_current_colours()
    def doansi_default_bg(self):
        self.bg_colour = self.theme.get('background')
        self.set_current_colours()
    def doansi_conceal(self)             : print('Got an ANSI "conceal"')
    def doansi_no_conceal(self)          : print('Got an ANSI "no_conceal"')
    def doansi_framed(self)              : print('Got an ANSI "framed"')
    def doansi_encircled(self)           : print('Got an ANSI "encircled"')
    def doansi_overline(self)            : print('Got an ANSI "overline"')
    def doansi_no_framed_encircled(self) : print('Got an ANSI "no_framed_encircled"')
    def doansi_no_overline(self)         : print('Got an ANSI "no_overline"')


    def foreground_colour(self)    : return self.theme.Colour(self.fg_colour, self.intensity)
    def background_colour(self)    : return self.theme.Colour(self.bg_colour)
    def lookup_colour(self, color) : return self.theme.Colour(color, self.intensity)

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

    ########### LM LOCALEDIT
    def lm_localedit_filter(self, _, line):
        # Are we in the middle of an ongoing localedit blast?
        if self.localedit_contents:
            self.localedit_contents.append(line.rstrip())
            if re.match('^\.$', line):
                self.send_localedit_to_editor()
                self.localedit_contents = None
            return None
        # Check for precisely "#$# edit name: xxxxxx upload: xxxxx"
        else:
            if LOCALEDIT_LINE.match(line):
                self.localedit_contents = [line.rstrip()]
                return None

        # Nope?  OK, pass back the line for the next lucky winner to play with
        return line

    def send_localedit_to_editor(self):
        invocation = self.localedit_contents[0]
        matches = LOCALEDIT_LINE.match(invocation)
        name    = matches.group(1)
        upload  = matches.group(2)
        self.localedit_contents[0] = upload

        if re.match('@program', upload):
            type = "moo-code"
        else:
            type = "text"

        editor = Editor({
            'filetype' : type,
            'content'  : self.localedit_contents,
            'callback' : self._send_file
        })

    def _send_file(self, id, content):
        for l in content:
            self.connection.output(l + "\n")


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

    30    : [ 'foreground' , 'black'       ],
    31    : [ 'foreground' , 'red'         ],
    32    : [ 'foreground' , 'green'       ],
    33    : [ 'foreground' , 'yellow'      ],
    34    : [ 'foreground' , 'blue'        ],
    35    : [ 'foreground' , 'magenta'     ],
    36    : [ 'foreground' , 'cyan'        ],
    37    : [ 'foreground' , 'white'       ],
    38    : [ 'foreground' , 'extended'    ],
    39    : [ 'control'    , 'default_fg ' ],

    40    : [ 'background' , 'black'       ],
    41    : [ 'background' , 'red'         ],
    42    : [ 'background' , 'green'       ],
    43    : [ 'background' , 'yellow'      ],
    44    : [ 'background' , 'blue'        ],
    45    : [ 'background' , 'magenta'     ],
    46    : [ 'background' , 'cyan'        ],
    47    : [ 'background' , 'white'       ],
    48    : [ 'background' , 'extended'    ],
    49    : [ 'control'    , 'default_bg ' ],

    # 50 - reserved
    51    : [ 'control' , 'framed' ],
    52    : [ 'control' , 'encircled' ],
    53    : [ 'control' , 'overline' ],
    54    : [ 'control' , 'no_framed_encircled' ],
    55    : [ 'control' , 'no_overline' ],
}

