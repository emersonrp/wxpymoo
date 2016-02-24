#wxpymoo

wxpymoo (pronounced "wispy-moo") is a wxPython MOO client, very work-in-progress.  It's intended to run on Windows, MacOS, and Linux/etc.

This is a response to Andrew Wilson's fantastic [tkMOO-light](http://www.awns.com/tkMOO-light) MOO client being basically abandoned, tk-based, which is ugly, and coded in TCL which I find eye-stabbingly difficult to work with.  So I thought I'd see if I could reproduce the 75% of it that I use, using Perl which I understand, and Wx which looks like something even remotely from the 21st century.

[Which I did](https://github.com/emersonrp/WxMOO).

And then I started discovering how difficult it is to package and release wxPerl applications.

So I punted, and reimplemented the entire thing in wxPython.  And here we are.

##Done
* Connects to a MOO.  Initially, it defaults to my MOO at hayseed.net:7777, but the Worlds->Connect dialog now works to connect wherever you like.
* Takes input, and shows output.  Almost pleasantly, even.
* Input field has a super-basic but functional command history.
* ANSI color/style codes are well-supported.
* Partial [MCP/2.1](http://www.moo.mud.org/mcp/mcp2.html) implementation -- mcp-negotiate is implemented;  mcp-cord is only partially.
* Starting in on MCP packages:
    * dns-com-awns-rehash (partial)
    * dns-com-awns-serverinfo
    * dns-com-awns-status (partial)
    * dns-com-vmoo-client
    * dns-com-vmoo-smartcomplete (partial)
    * dns-org-mud-moo-simpleedit (external editor configurable)
* Saving prefs works, for the small set of prefs it honors.  Lots of work intended here, still.
* Rudimentary tab-complete

##0.1 Milestone
* fix output pane scroll-to-bottom behavior to dwym.
* More keyboard accelerators;  page-up/down etc
* make sure it works on MacOS and Windows
* Clean up tab-complete ui
* Finish dns-com-awns-status Toast-style popups

##To do
* Add proper prefs and world/connection handling (85% done)
* Actually support multiple simultaneous connections (90% done)
* Pondering schemes to scrape online MOO lists to offer suggestions. (70% done)
* Start rolling binary packages for all platforms once it's remotely useful to anyone but me.
* Customizable colors / themes (currently you can have any colors you want as long as they're solarized-dark.)
* Per-world settings?  Colors, fonts?
* Finish MCP 2.1 implementation.
* Object browser, like MacMOOSE but hopefully nicer.
* Connections to have a 'connection type' -- currently thinking TCP port, SSL, and SSH port forwarding (automagic at connection time).

##Blue-sky
* HTML help, using jtext?
* MIME-based external apps, ie mplayer for audio/flac etc?  MCP package to accept MIME+data?  dns-com-vmoo-mmedia?
* inline MOO syntax highlighting?  Like, detect the output of "@list $player:tell" and auto-highlight it?

##Things that aren't currently on the rader
* tkMOO-light has a plugin architecture, and all sorts of third-party additions (I even wrote one, years ago).  Ihave no expectation that there'll be an ecosystem of developers around **this** MOO client, so I'm not actually desigining with that in mind.
* I MOO socially, occasionally.  I don't do RPG MUDs or things like that, so I have no need for triggers and macros and so forth.  I don't even have a clear idea of what people do with them.  Convince me.

##Guiding thoughts
* Monospaced fonts and line-based terminal output are not mutually incompatible with intuitive, pleasant UIs.
* There are many wheels out there that have been invented well already.  My MOO client doesn't need its own built-in text editor.  Lather, rinse, repeat.
* Nobody's living on a shell account on a VMS machine.  The MOO doesn't need to be a black-and-white culdesac.  There are dozens of interesting things a MOO client could do, connected to the 21st-century Internet, that I haven't thought of yet.  Detect chat in a different language and offer to translate?  Tweet you when your friends log on?  Display Google Maps for a MOO that knows how to host that?  Who knows.

##Dependencies
* [Python](http://www.python.org) 2.7
* [wxPython](http://www.wxpython.org) 3.0+
* [twisted](https://twistedmatrix.com/trac/)

Fedora users:
    sudo dnf install python wxPython python-twisted


##Acknowledgements
* wxpymoo is inspired by (and occasionally directly borrows from) [Andrew Wilson](http://www.awns.com)'s [tkMOO-light](http://www.awns.com/tkMOO-light), which is still probably the most-capable and -advanced MOO client around.
* [PADRE](http://padre.perlide.org) is not something I use, being a [vim](http://www.vim.org) junkie, but their generously-licensed code for a production wxperl application was an invaluable reference while getting the original perl version working..
* [Daring Fireball](http://www.daringfireball.net)'s blog graciously supplied to the public domain the [URL-detecting regex](http://daringfireball.net/2010/07/improved_regex_for_matching_urls) that I adapted.
* [Stack Overflow](http://www.stackoverflow.com) has helped me in countless large and small ways.  Specifically, answers by Adaephon, Jeremy Cantrell, and Mark Ransom assisted in getting my head around working with color in Python.
