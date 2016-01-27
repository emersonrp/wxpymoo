wxpymoo
=======

wxpymoo (pronounced "wispy-moo") is a wxPython MOO client, very work-in-progress.  It's intended to run on Windows, MacOS, and Linux/etc.

This is a response to Andrew Wilson's fantastic [tkMOO-light](http://www.awns.com/tkMOO-light) MOO client being basically abandoned, and tk-based, which is uugly, and coded in TCL which I find eye-stabbingly difficult to work with.  So I thought I'd see if I could reproduce the 75% of it that I use, in Perl which I understand, and Wx which looks like something even remotely from the 21st century, and so forth.

Which I did.

And then started discovering how difficult it is to package and release wxPerl applications.

So I punted, and reimplemented the entire thing in wxPython.  And here we are.

Done:
* It connects to a MOO.  Initially, it defaults to my MOO at hayseed.net:7777, specifically, but the Worlds->Connect dialog now works to connect wherever you like, and it'll remember your last-connected MOO and reconnect there automatically, if you set the preference to.
* It takes input, and shows output.  Almost pleasantly, even.
* The input field has a super-basic but functional command history.
* ANSI color/style codes are supported.
* Partial [MCP/2.1](http://www.moo.mud.org/mcp/mcp2.html) implementation -- mcp-negotiate is implemented;  mcp-cord is only partially.
* Starting in on MCP packages:
    * dns-org-mud-moo-simpleedit (external editor configurable)
    * dns-com-awns-serverinfo
    * dns-com-vmoo-client
* Saving prefs works, for the small set of prefs it honors.  Lots of work intended here, still.

0.1 Milestone:
* fix output pane scroll-to-bottom behavior to dwym
* More keyboard accelerators;  page-up/down etc
    * TODO - probably make several profiles (vi-like, emacs-like, windows-like) or maybe just actually expose ways to bind your own choices to everything.


To do:
* Add proper prefs and world/connection handling (85% done!)
* Actually support multiple simultaneous connections (80% done)
* Pondering schemes to scrape online MOO lists to offer suggestions. (70% done!)
* Start making sure it works on Windows and MacOS.  (Has been demonstrated to work at all on Windows, woot.)
* Start rolling binary packages for all platforms once it's remotely useful to anyone but me.
* Customizable colors / themes (currently you can have any colors you want as long as they're solarized-dark.)
* Per-world settings?  Colors, fonts?
* Complete the MCP 2.1 implementation.  It does the version dance with the server (both the MCP version, and mcp-negotiate package-version), but ignores whatever it sees.  Also mcp-cord isn't tested/usable at all.
* object browser, like MacMOOSE but hopefully nicer.
* Connections will hopefully have a 'connection type' -- currently thinking in terms of plain'ol TCP port, SSL, and SSH port forwarding (automagic at connection time).

Blue-sky:
* HTML help, using jtext?
* MIME-based external apps, ie mplayer for audio/flac etc?  MCP package to accept MIME+data?
* inline MOO syntax highlighting?  Like, detect the output of "@list $player:tell" and auto-highlight it?

Things that aren't currently on the rader:
* tkMOO-light has a whole plugin architecture, and all sorts of third-party additions (I even wrote one, years ago).  I'm not delusional enough to think that there'll be a flourishing ecosystem of developers around **this** MOO client, so I'm not actually desigining with that in mind.  (Update:  MCP packages are now plugin-able.)
* I MOO socially, occasionally.  I don't do RPG MUDs or things like that, so I have no need for triggers and macros and so forth.  I don't even have a clear idea of what people do with them.  Convince me.

Guiding thoughts:
* Monospaced fonts and line-based terminal output are not mutually incompatible with intuitive, pleasant UIs.
* There are many wheels out there that have been invented well already.  My MOO client doesn't need its own built-in text editor.  Lather, rinse, repeat.
* Nobody's living on a shell account on a VMS machine.  The MOO doesn't need to be a black-and-white culdesac.  There are dozens of interesting things a MOO client could do, connected to the 21st-century Internet, that I haven't thought of yet.  Detect chat in a different language and offer to translate?  Tweet you when your friends log on?  Display Google Maps for a MOO that knows how to host that?  Who knows.

Dependencies
------------

* [Python](http://www.python.org) 2.7
* [wxPython](http://www.wxpython.org) 3.0+
* [twisted](https://twistedmatrix.com/trac/)

Fedora users:
    sudo dnf install python wxPython python-twisted


Acknowledgements
----------------

* wxpymoo is inspired by (and occasionally directly borrows from) [Andrew Wilson](http://www.awns.com)'s [tkMOO-light](http://www.awns.com/tkMOO-light), which is still probably the most-capable and -advanced MOO client around.
* [PADRE](http://padre.perlide.org) is not something I use, being a [vim](http://www.vim.org) junkie, but their generously-licensed code for a production wxperl application was an invaluable reference while getting the original perl version working..
* [Daring Fireball](http://www.daringfireball.net)'s blog graciously supplied to the public domain the [URL-detecting regex](http://daringfireball.net/2010/07/improved_regex_for_matching_urls) that I adapted.

