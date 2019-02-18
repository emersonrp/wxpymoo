import wx
import wx.richtext as rtc
import wx.lib.newevent
import re

import prefs
import utility
from editor import Editor
from window.basepane import BasePane
from filters.ansi import fansi_replace, ansi_test_contents

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
        self.intensity        = ''
        self.conceal          = self.inverse          = False
        self.blink            = self.fast_blink       = False
        self.blink_timer      = self.fast_blink_timer = False
        self.blink_chars      = []
        self.fast_blink_chars = []

        self.initial_style = rtc.RichTextAttr()
        self.initial_style.SetLeftIndent(10, 50) # TODO make this a pref?
        self.current_style = rtc.RichTextAttr(self.initial_style)

        self.is_scrolled_back = False

        # output filters can register themselves
        self.filters = [self.lm_localedit_filter]
        self.localedit_contents = None

        # "holding bin" for line-based filters to enqueue partial lines
        self.global_queue = ''

        # TODO - this probably should be a preference, but for now, this is the
        # least-bad default behavior.
        self.Bind(wx.EVT_SIZE         , self.on_size)
        self.Bind(wx.EVT_SET_FOCUS    , self.on_set_focus)
        self.Bind(wx.EVT_TEXT_URL     , self.on_url_click)
        self.Bind(wx.EVT_SCROLLWIN    , self.on_scroll )

        self.Bind(EVT_ROW_COL_CHANGED , self.on_row_col_changed)

    def register_filter(self, name, filter_callback):
        self.filters.append(filter_callback)

    # EVENT HANDLERS #######################
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

    def on_set_focus(self, evt):
        self.connection.input_pane.SetFocus()

    def on_url_click(self, evt):
        url = evt.GetString()
        wx.BeginBusyCursor()
        if not re.match(r'^https?://', url):
            url = "http://" + url
        webbrowser.open(url)
        wx.EndBusyCursor()

    def on_scroll(self, evt):
        evt.Skip()
        if (evt.GetOrientation() == wx.VERTICAL):
            pos = self.GetScrollPos(wx.VSCROLL)
            thm = self.GetScrollThumb(wx.VSCROLL)
            rge = self.GetScrollRange(wx.VSCROLL)
            self.is_scrolled_back = ((pos + thm) < rge)
            print(f"{pos} {thm} {rge}")
            print(f"I'm scrolled back: { self.is_scrolled_back }")
        if not self.is_scrolled_back:
            self.connection.status_bar.StopBlinker()
            self.connection.SetTitle(self.connection.world.get('name'))

    def on_row_col_changed(self, evt):
        pass
        # TODO - "if preferences dictate, send @linelength to self.connection"

    ######################################
    def WriteText(self, rest):
        super(OutputPane, self).WriteText(rest)
        self.ScrollIfAppropriate()
        if self.is_scrolled_back:
            self.connection.status_bar.StartBinker()
        if not self.connection.IsCurrentConnection():
            self.connection.SetTitle(self.connection.world.get('name') + " (*)")

    def ScrollIfAppropriate(self):
        if ((not self.is_scrolled_back) or prefs.get('scroll_on_output')):
            self.ShowPosition(self.GetLastPosition())
            self.Refresh()

    def Thaw(self):
        super(OutputPane, self).Thaw()
        self.ScrollIfAppropriate()

    def display(self, text):
        self.SetInsertionPointEnd()
        self.Freeze()

        if self.global_queue:
            text = self.global_queue + text
            self.global_queue = ''

        # it is not clear whether this is the correct (a) thing to do, or
        # (b) place to do it, but some wackass MUDs seem to be sending \r\n
        # with an ANSI blob in between(!!!).  Going Unixy and just using \n
        text = re.sub('\r', '', text)

        # line-based filters should do their thing, returning None if they ate
        # everything they should enqueue any partial lines they're "in the
        # middle of" handling and be ready for the rest of the line;  then they
        # should examine the remainder for further handling or enqueueing.
        for fil in self.filters:
            text = fil(self, text)
            if text == None: return  # output_filter must return None if it handled it

        #if (True or prefs.get('render_emoji'):
            # TODO - preference?  "if (we detect an emoji)?"
            #text = emoji.emojize(text, use_aliases = True)

        if prefs.get('use_ansi'):
            # Dear lord this is sorta ugly

            # TODO -- let's make this whole thing an external filter that
            # returns text chunks and TextAttrs to blat at the screen.  For
            # now, we can still do it line-by-line, but eventually we might
            # want to be properly character-based/VT supporting.

            # For now, we'll stick the FANSI character poop into an
            # external filter.
            if self.connection.world.get("use_fansi"):
                text = fansi_replace(text)

            # snip and ring bells
            # TODO -- "if beep is enabled in the prefs"
            text, count = re.subn("\007", '', text)
            for b in range(0, count):
                print("DEBUG: found an ANSI beep")
                wx.Bell();

            # chop the text into text, ansi, text, ansi....
            bits = re.split('\033\[(\d+(?:;\d+)*)m', text)

            for idx, bit in enumerate(bits):
                # if we're on the last bit, check whether it might be a partial ANSI blob
                if idx == len(bits)-1:
                    if re.search('\033', bit):
                        print(f"I think I have a spare ANSI bit ({bit}), requeueing it")
                        self.global_queue += bit
                        break

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
                            self.style_thyself()

                        elif command == 'control':
                            switcher = {
                                'normal'              : self.doansi_normal,
                                'bright'              : self.doansi_bright,
                                'dim'                 : self.doansi_dim,
                                'italic'              : self.doansi_italic,
                                'underline'           : self.doansi_underline,
                                'blink'               : self.doansi_blink,
                                'fast_blink'          : self.doansi_fast_blink,
                                'inverse'             : self.doansi_inverse,
                                'conceal'             : self.doansi_conceal,
                                'strike'              : self.doansi_strike,
                                'double_underline'    : self.doansi_double_underline,
                                'normal_weight'       : self.doansi_normal_weight,
                                'no_italic'           : self.doansi_no_italic,
                                'no_underline'        : self.doansi_no_underline,
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
                            ansifunc = switcher.get(payload, lambda: print("Unknown ANSI control sequence"))
                            ansifunc()
                            self.style_thyself()

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
            self.WriteText(text)

        self.Thaw()

    ### ANSI HANDLERS
    def doansi_normal(self):
        self.current_style = rtc.RichTextAttr(self.initial_style)
        self.intensity = ''
        self.conceal = self.inverse = False
        self.fg_colour = self.theme.get('foreground')
        self.bg_colour = self.theme.get('background')
        self.doansi_no_blink()
    def doansi_bright(self):     self.intensity = 'bright'
    def doansi_dim(self):        self.intensity = 'dim'
    def doansi_italic(self):     self.current_style.SetFontStyle(wx.FONTSTYLE_ITALIC)
    def doansi_underline(self):  self.current_style.SetFontUnderlined(True)
    def doansi_blink(self):
        if prefs.get('use_ansi_blink'):
            self.blink = True
            self.blink_start = self.GetInsertionPoint()
    def doansi_fast_blink(self):
        if prefs.get('use_ansi_blink'):
            self.fast_blink = True
            self.fast_blink_start = self.GetInsertionPoint()
    def doansi_inverse(self):    self.inverse = True
    def doansi_strike(self):
        font = self.GetFont()
        font.SetStrikethrough(True)
        self.current_style.SetFont(font)
    def doansi_normal_weight(self): self.intensity = ''
    def doansi_no_italic(self):     self.current_style.SetFontStyle(wx.FONTSTYLE_NORMAL)
    def doansi_no_underline(self):  self.current_style.SetFontUnderlined(False)
    def doansi_no_blink(self):
        if not prefs.get('use_ansi_blink'): return
        end = self.GetInsertionPoint()
        if self.blink:
            if self.blink_start:
                for c in range(self.blink_start, end):
                    s = wx.TextAttr()
                    self.GetStyle(c,s)
                    self.blink_chars.append((c, s.GetTextColour(), s.GetBackgroundColour()))
            self.blink_start = self.blink = False
        if self.fast_blink:
            if self.fast_blink_start:
                for c in range(self.fast_blink_start, end):
                    s = wx.TextAttr()
                    self.GetStyle(c,s)
                    self.fast_blink_chars.append((c, s.GetTextColour(), s.GetBackgroundColour()))
            self.fast_blink_start = self.fast_blink = False
    def doansi_no_strike(self):
        font = self.GetFont()
        font.SetStrikethrough(False)
        self.current_style.SetFont(font)
    def doansi_default_fg(self): self.fg_colour = self.theme.get('foreground')
    def doansi_default_bg(self): self.bg_colour = self.theme.get('background')
    def doansi_double_underline(self)    : print('Got an ANSI "double_underline"')
    def doansi_conceal(self):    self.conceal = True
    def doansi_no_conceal(self): self.conceal = False
    def doansi_framed(self)              : print('Got an ANSI "framed"')
        # TODO - this seems to be correct all the way up to textboxattr having the border set
        # and getting it into current_style, but nothing changes on-screen
        #border = rtc.TextAttrBorders()
        #border.SetColour(wx.WHITE)
        #border.SetStyle(2)
        #border.SetWidth(4)
        #textboxattr = rtc.TextBoxAttr()
        #textboxattr.m_border = border
        #self.current_style.SetTextBoxAttr(textboxattr)

    def doansi_encircled(self)           : print('Got an ANSI "encircled"')
    def doansi_overline(self)            : print('Got an ANSI "overline"')
    def doansi_no_framed_encircled(self) : print('Got an ANSI "no_framed_encircled"')
    def doansi_no_overline(self)         : print('Got an ANSI "no_overline"')

    def foreground_colour(self)    : return self.theme.Colour(self.bg_colour if self.conceal else self.fg_colour, self.intensity)
    def background_colour(self)    : return self.theme.Colour(self.bg_colour)
    def lookup_colour(self, color) : return self.theme.Colour(color, self.intensity)

    def style_thyself(self):
        self.EndAllStyles()
        if self.inverse:
            self.current_style.SetTextColour      (self.background_colour())
            self.current_style.SetBackgroundColour(self.foreground_colour())
        else:
            self.current_style.SetTextColour      (self.foreground_colour())
            self.current_style.SetBackgroundColour(self.background_colour())
        self.BeginStyle(self.current_style)

        if self.blink_chars:
            if not self.blink_timer:      self.blink_timer      = wx.CallLater(1000, self.do_blink)
        if self.fast_blink_chars:
            if not self.fast_blink_timer: self.fast_blink_timer = wx.CallLater(400,  self.do_fast_blink)

    def do_blink(self):
        self._do_blink(self.blink_chars)
        self.blink_timer = wx.CallLater(800, self.do_blink)

    def do_fast_blink(self):
        self._do_blink(self.fast_blink_chars)
        self.fast_blink_timer = wx.CallLater(400, self.do_fast_blink)

    def _do_blink(self, chars):
        self.Freeze()
        s = wx.TextAttr()
        for c,fg,bg in chars:
            self.GetStyle(c,s)
            s.SetTextColour(fg if (s.GetTextColour() == bg) else bg)
            self.SetStyle(c,c+1,s)
        self.Thaw()

    def ansi_test(self):
        self.Freeze()
        self.display(ansi_test_contents())
        self.Thaw()

    ########### LM LOCALEDIT
    def lm_localedit_filter(self, _, data):
        return_val = ''
        # Are we in the middle of an ongoing localedit blast?
        line, p, rest = data.partition('\n')
        while p:
            if self.localedit_contents:
                line = line.rstrip()
                self.localedit_contents.append(line)
                if re.match('\.$', line):
                    self.send_localedit_to_editor()
                    self.localedit_contents = None
            else:
                # Check for precisely "#$# edit name: xxxxxx upload: xxxxx"
                if LOCALEDIT_LINE.match(line):
                    line = line.rstrip()
                    self.localedit_contents = [line]
                else:
                    # Nope?  OK, pass back the line for the next lucky winner to play with
                    return_val += line + "\n"

            line, p, rest = rest.partition('\n')

        return return_val + line

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
            'reference': name,
            'filetype' : type,
            'content'  : self.localedit_contents,
            'callback' : self._send_file
        })

    def _send_file(self, id, content):
        for l in content:
            self.connection.output(l + "\n")


ansi_codes = {
    0     : [ 'control' , 'normal'     ],
    1     : [ 'control' , 'bright'     ],
    2     : [ 'control' , 'dim'        ],
    3     : [ 'control' , 'italic'     ],
    4     : [ 'control' , 'underline'  ],
    5     : [ 'control' , 'blink'      ],
    6     : [ 'control' , 'fast_blink' ],
    7     : [ 'control' , 'inverse'    ],
    8     : [ 'control' , 'conceal'    ],
    9     : [ 'control' , 'strike'     ],
    # 10 - primary font
    # 11 - 19 - alternate fonts
    # 20 - fraktur
    21    : [ 'control' , 'double_underline' ],
    22    : [ 'control' , 'normal_weight'    ],
    23    : [ 'control' , 'no_italic'        ],
    24    : [ 'control' , 'no_underline'     ],
    25    : [ 'control' , 'no_blink'         ],
    28    : [ 'control' , 'no_conceal'       ],
    29    : [ 'control' , 'no_strike'        ],

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

