# wxpymoo

wxpymoo (pronounced "wispy-moo") is a wxPython MOO/MUD client, very work-in-progress.  It's intended to run on Windows, MacOS, and Linux/etc.

This is a response to Andrew Wilson's fantastic [tkMOO-light](http://www.awns.com/tkMOO-light) MOO client being long abandoned, tk-based, which is ugly, and coded in TCL which ouch.  So I thought I'd see if I could reproduce the 75% of it that I use, using Perl which I understand, and Wx which looks at least somewhat modern.

[Which I did](https://github.com/emersonrp/WxMOO).  And then I started discovering how difficult it is to package and release wxPerl applications.

So I punted, and reimplemented the entire thing in wxPython.  And here we are.

## Done
* Connects to arbitrary host/port combinations
* Contains a "worlds list" full of ~50 currently-active MOOs/MUDS/etc to choose from.
* ANSI 16, 256, and 24-bit support, as well as [FANSI](http://fansi.org/); multiple color themes for core ANSI colors
* Partial [MCP/2.1](http://www.moo.mud.org/mcp/mcp2.html) implementation -- mcp-negotiate is implemented;  mcp-cord only partially.
* MCP packages:
    * dns-com-awns-displayurl
    * dns-com-awns-rehash (partial)
    * dns-com-awns-serverinfo
    * dns-com-awns-status (partial)
    * dns-com-vmoo-client
    * dns-com-vmoo-smartcomplete
    * dns-org-mud-moo-simpleedit
* A growing number of MUD protocols supported:
    * [MSSP](https://tintin.sourceforge.io/protocols/mssp/) (partial),
    * [MTTS](https://tintin.sourceforge.io/protocols/mtts/)
    * [MCCP](http://www.gammon.com.au/mccp/protocol.html)
* Multiple connections supported via tabbed interface
* SSL support per-world
* Works at least reasonably well on Linux, MacOS, Windows.
* Basic but functional command history.
* Tab-complete, currently fed from dns-com-vmoo-smartcomplete

## Immediate Concerns
* fix output pane scroll-to-bottom behavior to dwym.
* More keyboard accelerators;  page-up/down etc
* Finish toast-style popups for dns-com-awns-status et al

## To do
* Add proper prefs and world/connection handling (85% done)
* Pondering schemes to scrape online MOO lists to offer suggestions. (70% done)
* Start rolling binary packages for all platforms once it's remotely useful to anyone but me.
* Per-world settings?  Colors, fonts?
* Finish implementation of MCP 2.1 and the various supported packages.
* More MCP packages as I find them.
* MOO object browser, like MacMOOSE but hopefully nicer.
* Implement "SSH Forwarding" connection type.
* color theme editor
* Support more MUD protocols
* More complete VT100 support
* Character-mode improvements for non-MOO worlds

## Blue-sky
* HTML help, using jtext?
* MIME-based external apps, ie mplayer for audio/flac etc?  MCP package to accept MIME+data?  dns-com-vmoo-mmedia?
* inline MOO syntax highlighting?  Like, detect the output of "@list $player:tell" and auto-highlight it?

## Guiding thoughts
* Monospaced fonts and line-based terminal output are not mutually incompatible with intuitive, pleasant UIs.
* There are many wheels out there that have been invented well already.  My MOO client doesn't need its own built-in text editor.  Lather, rinse, repeat.
* Nobody's living on a shell account on a VMS machine.  The MOO doesn't need to be a black-and-white culdesac.  There are dozens of interesting things a MOO client could do, connected to the 21st-century Internet, that I haven't thought of yet.  Detect chat in a different language and offer to translate?  Tweet you when your friends log on?  Display Google Maps for a MOO that knows how to host that?

## Contributors
* [lisdude](https://github.com/lisdude)

## Credits
wxpymoo contains:
* [wxasync](https://github.com/sirk390/wxasync) (c) 2018 Christian Bodt
* [EnhancedStatusBar](https://infinity77.net/main/EnhancedStatusBar.html) (c) 2005 Andrea Gavana and Nitro
* [Feather Icons](https://feathericons.com/) (c) 2013-2017 Cole Bemis
* The color themes were lovingly lifted from [Terminal Sexy](http://terminal.sexy) by George Czabania

wxpymoo owes a great debt to [tkMOO-light](http://www.awns.com/tkMOO-light/) by Andrew Wilson.

## Dependencies
* [Python](http://www.python.org) 3.11
* [wxPython](http://www.wxpython.org) 4.2.1+

### Windows / Mac users:
* Clone this repo
* Go to the Python link above, get the latest version of Python
* Install it
* Open a terminal, type <code>pip3 install wxPython</code>
* Double-click "wxpymoo.py" inside the wxpymoo directory

### Linux / etc users:
* Clone this repo
* install the latest version of python3 and of wxpython from your distribution
* Either run ./wxpymoo.py from a terminal or double-click it in your file manager
