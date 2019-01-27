#wxpymoo

wxpymoo (pronounced "wispy-moo") is a wxPython MOO client, very work-in-progress.  It's intended to run on Windows, MacOS, and Linux/etc.

This is a response to Andrew Wilson's fantastic [tkMOO-light](http://www.awns.com/tkMOO-light) MOO client being basically abandoned, tk-based, which is ugly, and coded in TCL which I find eye-stabbingly difficult to work with.  So I thought I'd see if I could reproduce the 75% of it that I use, using Perl which I understand, and Wx which looks like something even remotely from the 21st century.

[Which I did](https://github.com/emersonrp/WxMOO).

And then I started discovering how difficult it is to package and release wxPerl applications.

So I punted, and reimplemented the entire thing in wxPython.  And here we are.

##Done
* Connects to arbitrary host/port combinations
* Contains a "worlds list" full of ~50 currently-active MOOs to choose from.
* Basic but functional command history.
* Tab-complete, currently fed from dns-com-vmoo-smartcomplete
* ANSI color/style codes are well-supported.
* Partial [MCP/2.1](http://www.moo.mud.org/mcp/mcp2.html) implementation -- mcp-negotiate is implemented;  mcp-cord only partially.
* MCP packages:
    * dns-com-awns-displayurl
    * dns-com-awns-rehash (partial)
    * dns-com-awns-serverinfo
    * dns-com-awns-status (partial)
    * dns-com-vmoo-client
    * dns-com-vmoo-smartcomplete (partial)
    * dns-org-mud-moo-simpleedit
* Colors and fonts, ANSI support, external editor, chosen via prefs
* Multiple connections supported via tabbed interface
* SSL support per-world
* Works at least reasonably on Linux, MacOS, Windows.

##Immediate Concerns
* fix output pane scroll-to-bottom behavior to dwym.
* More keyboard accelerators;  page-up/down etc
* Finish toast-style popups for dns-com-awns-status et al

##To do
* Add proper prefs and world/connection handling (85% done)
* Pondering schemes to scrape online MOO lists to offer suggestions. (70% done)
* Start rolling binary packages for all platforms once it's remotely useful to anyone but me.
* Customizable colors / themes (currently you can have any colors you want as long as they're solarized-dark.)
* Per-world settings?  Colors, fonts?
* Finish MCP 2.1 implementation.
* Object browser, like MacMOOSE but hopefully nicer.
* Implement "SSH Forwarding" connection type.

##Blue-sky
* HTML help, using jtext?
* MIME-based external apps, ie mplayer for audio/flac etc?  MCP package to accept MIME+data?  dns-com-vmoo-mmedia?
* inline MOO syntax highlighting?  Like, detect the output of "@list $player:tell" and auto-highlight it?

##Things not currently on the radar
* tkMOO-light has a plugin architecture, and all sorts of third-party additions (I even wrote one, years ago).  I have no expectation that there'll be an ecosystem of developers around **this** MOO client, so I'm not actually desigining with that in mind.
* I MOO socially, occasionally.  I don't do RPG MUDs or things like that, so I have no need for triggers and macros and so forth.  I don't even have a clear idea of what people do with them.  Convince me.

##Guiding thoughts
* Monospaced fonts and line-based terminal output are not mutually incompatible with intuitive, pleasant UIs.
* There are many wheels out there that have been invented well already.  My MOO client doesn't need its own built-in text editor.  Lather, rinse, repeat.
* Nobody's living on a shell account on a VMS machine.  The MOO doesn't need to be a black-and-white culdesac.  There are dozens of interesting things a MOO client could do, connected to the 21st-century Internet, that I haven't thought of yet.  Detect chat in a different language and offer to translate?  Tweet you when your friends log on?  Display Google Maps for a MOO that knows how to host that?  Who knows?

##Credits
wxpymoo contains wxasync (https://github.com/sirk390/wxasync), which is (c) 2018 Christian Bodt
and generously provided under the MIT License.

##Dependencies
* [Python](http://www.python.org) 3.7
* [wxPython](http://www.wxpython.org) 4.0+

Windows / Mac users:
    * Clone this repo
    * Go to the Python link above, get the latest version of Python
    * Install it
    * Open a terminal, type "pip install wxPython"
    * Double-click "wxpymoo.py" inside the wxpymoo directory

Fedora users:
    * Clone this repo
    * sudo dnf install python wxPython
    * cd wxpymoo; python3 wxpymoo.py
