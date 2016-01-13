import wx
import wx.richtext

#use Wx qw( :color :misc :textctrl :sizer )
#use Wx.RichText
#use Wx.Event qw( EVT_SET_FOCUS EVT_TEXT_URL EVT_SIZE )
#
#use WxMOO.Prefs
#use WxMOO.Theme
#use WxMOO.Utility qw( URL_REGEX )

# TODO we need a better output_filter scheme, probably?
#use WxMOO.MCP21

class OutputPane(wx.richtext.RichTextCtrl):

    def __init__(self, parent):
        wx.richtext.RichTextCtrl.__init__(self, parent,
            style = wx.TE_AUTO_URL | wx.TE_READONLY | wx.TE_NOHIDESEL
        )
        self.input_pane = parent.input_pane()

        self.restyle_thyself()

        self.Bind(wx.EVT_SET_FOCUS, self.focus_input)
        self.Bind(wx.EVT_TEXT_URL,  self.process_url_click)
        # TODO - this probably should be a preference, but for now, this is the
        # least-bad default behavior.
        self.Bind(wx.EVT_SIZE,        self.scroll_to_bottom)

    def scroll_to_bottom(self, evt):
        self.ShowPosition(self.GetLastPosition())

    def process_url_click(self, evt):
        url = evt.GetString
        # TODO - make this whole notion into a platform-agnostic launchy bit
        #system('xdg-open', url)

    def WriteText(self, rest):
        super(OutputPane, self).WriteText(rest)
        self.ScrollIfAppropriate

    def is_at_bottom(): True

    def ScrollIfAppropriate(self):
        #if (True || self.is_at_bottom() || WxMOO.Prefs.prefs.scroll_on_output()):
            self.scroll_to_bottom(False)

    def restyle_thyself(self):
        #basic_style = wx.RichTextAttr()
        #basic_style.SetTextColour      (WxMOO.Prefs.prefs.output_fgcolour)
        #basic_style.SetBackgroundColour(WxMOO.Prefs.prefs.output_bgcolour)
        #self.SetBackgroundColour(WxMOO.Prefs.prefs.output_bgcolour)
        #self.SetBasicStyle(basic_style)
        #self.SetFont(WxMOO.Prefs.prefs.output_font)
        pass

    def display(self, text):

        #range = self.GetSelectionRange()

        self.WriteText(text)
        self.WriteText("\n")

        self.SetInsertionPointEnd()
        return

# TODO - ANSI parsing woo
        for line in text.split():
        #    if (WxMOO.Prefs.prefs.use_mcp) {
        #        next unless (line = WxMOO.MCP21.output_filter(line))
        #    }
            #if (True || WxMOO.Prefs.prefs.use_ansi):
                stuff = self.ansi_parse(line)
                line = ''
                for bit in stuff:
                    if (bit):
                        self.apply_ansi(bit)
                    else:
                        #if (WxMOO.Prefs.prefs.highlight_urls and bit =~ URL_REGEX):
                        #        self.WriteText({^PREMATCH})

                        #        self.BeginURL({^MATCH})
                        #        self.BeginUnderline
                        #        self.BeginTextColour( self.lookup_color('blue', 1) )

                        #        self.WriteText({^MATCH})

                        #        self.EndTextColour
                        #        self.EndUnderline
                        #        self.EndURL

                        #        self.WriteText({^POSTMATCH})
                        #else:
                            self.WriteText(bit)
                #else:
                #self.WriteText(line)

#        if (from != to) {
#            self.SetSelection(from, to)
#        }

    def focus_input(self,evt): self.input_pane.SetFocus()

    #theme = wxpymoo.theme.Theme()

    def lookup_color(self, color):
        #return theme.Colour(color, True if self.bright else False)
        pass

    def apply_ansi(self, bit):
        (type, payload) = bit
#        if (type == 'control'):
#            given (payload) {
#                when ('normal')       {
#                    my plain_style = Wx.TextAttr.new
#                    if (self.{'inverse'}) {
#                        say STDERR "I'm inverse!"
#                        self.invert_colors
#                    }
#                    self.SetDefaultStyle(plain_style)
#                }
#                when ('bold')         { self.BeginBold;     }
#                when ('dim')          { self.EndBold;       } # TODO - dim further than normal?
#                when ('underline')    { self.BeginUnderline }
#                when ('blink')     {
#                    # TODO - create timer
#                    # apply style name
#                    # periodically switch foreground color to background
#                }
#                when ('inverse')      { self.invert_colors; }
#                when ('hidden')       { 1; }
#                when ('strikethru')   { 1; }
#                when ('no_bold')      { self.EndBold; }
#                when ('no_underline') { self.EndUnderline }
#                when ('no_blink')  {
#                    # TODO - remove blink-code-handles style
#                }
#                when ('no_strikethru') { 1; }
#            }
#        } elsif (type eq 'foreground') {
#            self.BeginTextColour(self.lookup_color(payload))
#        } elsif (type eq "background") {
#            my bg_attr = Wx.TextAttr.new
#            bg_attr.SetBackgroundColour(self.lookup_color(payload))
#            self.SetDefaultStyle(bg_attr)
#            # self.BeginBackgroundColour(self.lookup_color(payload))
#        } else {
#            say STDERR "unknown ANSI type type"
#        }

    def invert_colors(self):
        current = self.GetStyle(self.GetInsertionPoint())
        fg = current.GetTextColour()
        bg = current.GetBackgroundColour()
        # TODO - hrmn current bg color seems to be coming out wrong.

        current.SetTextColour(bg)
        current.SetBackgroundColour(fg)

        self.inverse = False if self.inverse else True
        # self.SetDefaultStyle(current);  # commenting this out until bg color confusion is resolved

    ansi_codes = ()
#    ansi_codes = (
#        0     => [ control => 'normal'        ],
#        1     => [ control => 'bold'          ],
#        2     => [ control => 'dim'           ],
#        4     => [ control => 'underline'     ],
#        5     => [ control => 'blink'         ],
#        7     => [ control => 'inverse'       ],
#        8     => [ control => 'hidden'        ],
#        9     => [ control => 'strikethru'    ],
#        22    => [ control => 'no_bold'       ], # normal font weight also cancels 'dim'
#        24    => [ control => 'no_underline'  ],
#        25    => [ control => 'no_blink'      ],
#        29    => [ control => 'no_strikethru' ],
#        30    => [ foreground => 'black'  ],
#        31    => [ foreground => 'red'    ],
#        32    => [ foreground => 'green'  ],
#        33    => [ foreground => 'yellow' ],
#        34    => [ foreground => 'blue'   ],
#        35    => [ foreground => 'magenta'],
#        36    => [ foreground => 'cyan'   ],
#        37    => [ foreground => 'white'  ],
#
#        40    => [ background => 'black'  ],
#        41    => [ background => 'red'    ],
#        42    => [ background => 'green'  ],
#        43    => [ background => 'yellow' ],
#        44    => [ background => 'blue'   ],
#        45    => [ background => 'magenta'],
#        46    => [ background => 'cyan'   ],
#        47    => [ background => 'white'  ],
#    )


    def ansi_parse(self, line):
        return line
        #if (my beepcount = line =~ s/\007//g) {
        #    for (1..beepcount) {
        #        say STDERR "found a beep"
        #        Wx.Bell();  # TODO -- "if beep is enabled in the prefs"
        #    }
        #}

        #my @bits = split /\e\[(\d+(?:;\d+)*)m/, line

        #my @styled_text
        #while (my (i, val) = each @bits) {
        #    if (i % 2) {
        #        for my c (split /;/, val) {
        #            if (my style = ansi_codes{val}) {
        #                push @styled_text, style
        #            }
        #        }
        #    } else {
        #        push @styled_text, val if val
        #    }
        #}
        #return [@styled_text]

