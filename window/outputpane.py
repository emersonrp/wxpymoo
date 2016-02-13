import wx
import wx.richtext as rtc
import wx.lib.newevent

import prefs
import utility
from theme import Theme
from window.basepane import BasePane

import webbrowser, re, math, emoji

RowColChangeEvent, EVT_ROW_COL_CHANGED = wx.lib.newevent.NewEvent()

class OutputPane(BasePane):
    def __init__(self, parent, connection):
        BasePane.__init__(self, parent, connection,
            style = wx.TE_AUTO_URL | wx.TE_READONLY | wx.TE_NOHIDESEL | wx.TE_MULTILINE
        )

        # state toggles for ANSI processing
        self.weight  = None
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

    def on_size(self, evt):
        self.scroll_to_bottom()
        self.update_size()
        evt.Skip()

    def copy_from_selection(self, evt = None):
        uxcp = prefs.get('use_x_copy_paste') == 'True'
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(True)
        self.Copy()
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(False)

    def process_url_click(self, evt):
        url = evt.GetString()
        wx.BeginBusyCursor()
        webbrowser.open(url)
        wx.EndBusyCursor()

    def focus_input(self,evt): self.connection.input_pane.SetFocus()

    ######################################
    def WriteText(self, rest):
        super(OutputPane, self).WriteText(rest)
        self.ScrollIfAppropriate()

    def scroll_to_bottom(self):
        self.ShowPosition(self.GetLastPosition())

    def is_at_bottom(self): return True

    def ScrollIfAppropriate(self):
        if (self.is_at_bottom() or prefs.get('scroll_on_output') == 'True'):
            self.scroll_to_bottom()


    # This updates the widget's internal notion of "how big" it is in characters
    # it throws an event if the size *in chars* changes, nothing if the change in size was < 1 char
    def update_size(self, evt = None):
        font_width, font_height = self.font_size()
        self_width, self_height = self.GetSizeTuple()

        new_cols = math.floor(self_width  / font_width) - 2  # "-2" to allow for margins
        new_rows = math.floor(self_height / font_height)

        if (new_cols != self.cols) or (new_rows != self.rows):
            self.cols = new_cols
            self.rows = new_rows
            rc_evt = RowColChangeEvent()
            wx.PostEvent(self, rc_evt)

    def display(self, text):
        self.SetInsertionPointEnd()
        for line in text.split('\n'):
            line = line + "\n"
            if prefs.get('use_mcp') == 'True':
                line = self.connection.mcp.output_filter(line)
                if not line: continue  # output_filter returns falsie if it handled it.

            if (True or prefs.get('render_emoji') == 'True'):
                # TODO - preference?  "if (we detect an emoji)?"
                line = emoji.emojize(line, use_aliases = True)

            if prefs.get('use_ansi') == 'True':
                stuff = self.ansi_parse(line)
                for bit in stuff:
                    if type(bit) is list:
                        self.apply_ansi(bit)
                    else:
                        # TODO - this might should be separate from use_ansi.
                        # TODO - snip URLs first then ansi-parse pre and post?
                        if prefs.get('highlight_urls') == 'True':
                            matches = re.split(utility.URL_REGEX, bit)
                            for chunk in matches:
                                if chunk is None: continue
                                if re.match(utility.URL_REGEX, chunk):
                                    self.BeginURL(chunk)
                                    self.BeginUnderline()
                                    tmp_weight = self.weight
                                    self.weight = 'bright'
                                    self.BeginTextColour( self.lookup_colour('blue', True) )
                                    self.weight = tmp_weight

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

    def lookup_colour(self, color, *bright):
        return self.theme.Colour(color,
                True if (bright or self.bright) else False)

    def apply_ansi(self, bit):
        type, payload = bit
        if type == 'control':
            if payload == 'normal':
                self.SetDefaultStyle(self.basic_style)
                self.bright = False
                self.inverse = False
            elif payload == 'bold':
                self.BeginBold()
                self.end_dim()
                self.bright = True
            elif payload == 'dim':
                self.EndBold()
                self.start_dim()
                self.bright = False
            elif payload == 'italic':    self.BeginItalic()
            elif payload == 'underline': self.BeginUnderline()
            elif payload == 'blink':
                print('Got an ANSI "blink"')
                # TODO - create timer
                # apply style name
                # periodically switch foreground color to background
            elif payload == 'inverse':      self.invert_colors()
            elif payload == 'conceal':
                print('Got an ANSI "conceal"')
            elif payload == 'strike':
                font = self.GetFont()
                font.SetStrikethrough(True)
                self.BeginFont(font)
            elif payload == 'normal_weight':
                self.EndBold()
                self.end_dim()
                self.bright = False
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

        elif type == 'foreground':
            self.BeginTextColour(self.lookup_colour(payload))
        elif type == "background":
            bg_attr = rtc.RichTextAttr()
            self.GetStyle(self.GetInsertionPoint(), bg_attr)
            bg_attr.SetBackgroundColour(self.lookup_colour(payload))
            bg_attr.SetFlags( wx.TEXT_ATTR_BACKGROUND_COLOUR )
            self.BeginStyle(bg_attr)
        else:
            print("unknown ANSI type:", type)

    def start_dim(self):
        pass

    def end_dim(self):
        pass

    def invert_colors(self):
        if self.inverse: return

        current = rtc.RichTextAttr()
        self.GetStyle(self.GetInsertionPoint(), current)
        fg = wx.Colour(*current.GetTextColour())
        bg = wx.Colour(*current.GetBackgroundColour())

        current.SetTextColour      (bg)
        current.SetBackgroundColour(fg)

        self.inverse = True

        self.BeginStyle(current);

    def ansi_parse(self, line):
        global ansi_codes
        beep_cleaned, count = re.subn("\007", '', line)

        if count:
            line = beep_cleaned
            for b in range(0, count):
                print("DEBUG: found an ANSI beep")
                wx.Bell();  # TODO -- "if beep is enabled in the prefs"

        styled_text = []

        bits = re.split('\x1b\[(\d+(?:;\d+)*)m', line)

        if len(bits) > 1:
            # We'll have a list that alternates text, ansicode, text, ansicode....
            for idx, bit in enumerate(bits):
                if bit == '': continue
                # if it's ansi...
                if (idx % 2):
                    # ...split it up and add the style(s) to the styled_text list
                    for code in bit.split(';'):
                        styled_text.append(ansi_codes[int(code)])
                # otherwise it's text, just mash it on there
                else: styled_text.append(bit)
        else:
            styled_text.append(bits[0])

        return styled_text

ansi_codes = {
    0     : [ 'control' , 'normal'        ],
    1     : [ 'control' , 'bright'        ],
    2     : [ 'control' , 'dim'           ],
    3     : [ 'control' , 'italic'        ],
    4     : [ 'control' , 'underline'     ],
    5     : [ 'control' , 'blink'         ],
    7     : [ 'control' , 'inverse'       ],
    8     : [ 'control' , 'conceal'       ],
    9     : [ 'control' , 'strike'        ],
    # 10 - primary font
    # 11 - 19 - alternate fonts
    # 20 - fraktur
    # 21 - bright_off or underline_double
    22    : [ 'control' , 'normal_weight' ],
    23    : [ 'control' , 'no_italic'     ],
    24    : [ 'control' , 'no_underline'  ],
    25    : [ 'control' , 'no_blink'      ],
    28    : [ 'control' , 'no_conceal'    ],
    29    : [ 'control' , 'no_strike'     ],

    30    : [ 'foreground' , 'black'  ],
    31    : [ 'foreground' , 'red'    ],
    32    : [ 'foreground' , 'green'  ],
    33    : [ 'foreground' , 'yellow' ],
    34    : [ 'foreground' , 'blue'   ],
    35    : [ 'foreground' , 'magenta'],
    36    : [ 'foreground' , 'cyan'   ],
    37    : [ 'foreground' , 'white'  ],
    # 38 - extended foreground colors
    # 39 - default foreground color

    40    : [ 'background' , 'black'  ],
    41    : [ 'background' , 'red'    ],
    42    : [ 'background' , 'green'  ],
    43    : [ 'background' , 'yellow' ],
    44    : [ 'background' , 'blue'   ],
    45    : [ 'background' , 'magenta'],
    46    : [ 'background' , 'cyan'   ],
    47    : [ 'background' , 'white'  ],
    # 48 - extended background colors
    # 49 - default background color
    # 50 - reserved
    # 51 - framed
    # 52 - encircled
    # 53 - overlined
    # 54 - no_framed + no_encircled
    # 55 - no_overined
}

