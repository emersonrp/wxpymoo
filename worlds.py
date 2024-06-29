import wx
import re
import collections
import prefs
import json
import sys
from pathlib import Path

class World(dict):

    _defaults = {
        'port'         : 7777,
        'auto_login'   : False,
        'login_script' : 'connect %u %p',
    }

    def __init__(self, data):
        data = data or World._defaults
        for f in data:
            if data.get(f) is not None: self[f] = data.get(f)

    # TODO - enumerate what the various keys might be and use Write() WriteBool() etc as appropriate
    def save(self):
        worldsconfig = wx.FileConfig(localFilename = str(prefs.get_prefs_dir() / 'worlds'))
        worldname = re.sub(r'\W', '_', str(self.get('name')))

        worldsconfig.DeleteGroup(worldname)
        worldsconfig.SetPath(worldname)

        for f in self:
            if self.get(f):
                if f in ['auto_login', 'use_mcp', 'use_login_dialog', 'on_shortlist', 'use_fansi',]:
                    worldsconfig.WriteBool(f, self.get(f))
                elif f == 'port':
                    worldsconfig.WriteInt(f, self.get(f))
                else:
                    worldsconfig.Write(f, self.get(f))

        worldsconfig.SetPath('/')
        worldsconfig.Flush()

        mainwindow = wx.GetApp().GetTopWindow()
        if mainwindow:
            mainwindow.rebuildShortlist()

worlds      = collections.OrderedDict({})
def Initialize():
    global worlds
    worldsconfig = wx.FileConfig(localFilename = str(prefs.get_prefs_dir() / 'worlds'))

    # loop worlds...
    g_more, worldname, g_index = worldsconfig.GetFirstGroup()
    if g_more:  # do we have anything at all from the config file?
        while g_more: # yes, loop and fill stuff out.

            worldsconfig.SetPath(worldname)

            worlddata = {}

            # loop data lines inside each world....
            e_more, dataname, e_index = worldsconfig.GetFirstEntry()
            while e_more:
                if dataname in ['auto_login', 'use_mcp', 'use_login_dialog', 'on_shortlist', 'use_fansi',]:
                    worlddata[dataname] = worldsconfig.ReadBool(dataname)
                elif dataname == 'port':
                    worlddata[dataname] = worldsconfig.ReadInt(dataname)
                else:
                    worlddata[dataname] = worldsconfig.Read(dataname)

                e_more, dataname, e_index = worldsconfig.GetNextEntry(e_index)

            # build the World object
            worlds[worlddata['name']] = World(worlddata)

            # carry on, back to the top for the next world
            worldsconfig.SetPath('/')
            g_more, worldname, g_index = worldsconfig.GetNextGroup(g_index)

    else:  # nothing from config file, grab the initial_worlds data
        if hasattr(sys, '_MEIPASS'):
            path = Path(sys._MEIPASS) # pyright: ignore
        else:
            path = Path(wx.GetApp().path)

        initial_worlds = []
        try:
            initial_worlds = json.load(open(path / 'initial_worlds.json','r'))
        except Exception as e:
            wx.LogError(f"initial_worlds.json file could not be loaded: {e}")

        for world_data in initial_worlds:
            world = World(world_data)
            world.save()
            worlds[world.get('name')] = world

MSSP_VARS = {
    # Offical from https://tintin.sourceforge.io/protocols/mssp/
    'NAME'               : "Name of the MUD.",
    'PLAYERS'            : "Current number of logged in players.",
    'UPTIME'             : "Unix time value of the startup time of the MUD.",
    'CRAWL DELAY'        : "Preferred minimum number of hours between crawls. Send -1 to use the crawler's default.",
    'HOSTNAME'           : "Current or new hostname.",
    'PORT'               : "Current or new port number. Can be used multiple times, most important port last.",
    'CODEBASE'           : "Name of the codebase, eg Merc 2.1.",
    'CONTACT'            : "Email address for contacting the MUD.",
    'CREATED'            : "Year the MUD was created.",
    'ICON'               : "URL to a square image in bmp, png, jpg, or gif format.  The icon should be equal or larger than 32x32 pixels, with a filesize no larger than 32KB.",
    'IP'                 : "Current or new IP address.",
    'IPV6'               : "Current or new IPv6 address.",
    'LANGUAGE'           : "English name of the language used, eg German or English",
    'LOCATION'           : "English short name of the country where the server is located, using ISO 3166.",
    'MINIMUM AGE'        : "Current minimum age requirement, use 0 if not applicable.",
    'WEBSITE'            : "URL to MUD website, this should include the http:// or https:// prefix.",
    'FAMILY'             : "AberMUD, CoffeeMUD, DikuMUD, LPMud, MajorMUD, MOO, Mordor, Rapture, SocketMud, TinyMUD, Custom. Report Custom unless it's a well established family.  You can report multiple generic codebases using the array format, make sure to report the most distant codebase (the ones listed above) last.  Check the MUD family tree for naming and capitalization.",
    'GENRE'              : "Adult, Fantasy, Historical, Horror, Modern, None, Science Fiction",
    'GAMEPLAY'           : "Adventure, Educational, Hack and Slash, None, Player versus Player, Player versus Environment, Roleplaying, Simulation, Social, Strategy",
    'STATUS'             : "Alpha, Closed Beta, Open Beta, Live",
    'GAMESYSTEM'         : "D&D, d20 System, World of Darkness, Etc. Use Custom if using a custom gamesystems. Use None if not available.  ",
    'INTERMUD'           : "AberChat, I3, IMC2, MudNet, Etc.  Can be used multiple times if you support several protocols, most important protocol last. Leave empty if no Intermud protocol is supported.  ",
    'SUBGENRE'           : "LASG, Medieval Fantasy, World War II, Frankenstein, Cyberpunk, Dragonlance, Etc.  Use None if not available.",
    'AREAS'              : "Current number of areas.",
    'HELPFILES'          : "Current number of help files.",
    'MOBILES'            : "Current number of unique mobiles.",
    'OBJECTS'            : "Current number of unique objects.",
    'ROOMS'              : "Current number of unique rooms, use 0 if roomless.",
    'CLASSES'            : "Number of player classes, use 0 if classless.",
    'LEVELS'             : "Number of player levels, use 0 if level-less.",
    'RACES'              : "Number of player races, use 0 if raceless.",
    'SKILLS'             : "Number of player skills, use 0 if skill-less.",
    'ANSI'               : "Supports ANSI colors ? 1 or 0",
    'GMCP'               : "Supports GMCP ? 1 or 0",
    'MCCP'               : "Supports MCCP ? 1 or 0",
    'MCP'                : "Supports MCP ? 1 or 0",
    'MSDP'               : "Supports MSDP ? 1 or 0",
    'MSP'                : "Supports MSP ? 1 or 0",
    'MXP'                : "Supports MXP ? 1 or 0",
    'PUEBLO'             : "Supports Pueblo ?  1 or 0",
    'UTF-8'              : "Supports UTF-8 ? 1 or 0",
    'VT100'              : "Supports VT100 interface ?  1 or 0",
    'XTERM 256 COLORS'   : "Supports xterm 256 colors ?  1 or 0",
    'PAY TO PLAY'        : "Pay to play ? 1 or 0",
    'PAY FOR PERKS'      : "Pay for perks ? 1 or 0",
    'HIRING BUILDERS'    : "Game is hiring builders ? 1 or 0",
    'HIRING CODERS'      : "Game is hiring coders ? 1 or 0",
    # Extended from http://web.archive.org/web/20130322222545/http//www.mudbytes.net/index.php?a=articles&s=MSSP_Fields
    'DBSIZE'             : 'Total number of rooms, exits, objects, mobiles, and players.',
    'EXITS'              : 'Current number of exits.',
    'EXTRA DESCRIPTIONS' : 'Current number of extra descriptions.',
    'MUDPROGS'           : 'Current number of mud program lines.',
    'MUDTRIGS'           : 'Current number of mud program triggers.',
    'RESETS'             : 'Current number of resets.',
    'ADULT MATERIAL'     : '"0" or "1"',
    'MULTICLASSING'      : '"0" or "1"',
    'NEWBIE FRIENDLY'    : '"0" or "1"',
    'PLAYER CITIES'      : '"0" or "1"',
    'PLAYER CLANS'       : '"0" or "1"',
    'PLAYER CRAFTING'    : '"0" or "1"',
    'PLAYER GUILDS'      : '"0" or "1"',
    'EQUIPMENT SYSTEM'   : '"None", "Level", "Skill", "Both"',
    'MULTIPLAYING'       : '"None", "Restricted", "Full"',
    'PLAYERKILLING'      : '"None", "Restricted", "Full"',
    'QUEST SYSTEM'       : '"None", "Immortal Run", "Automated", "Integrated"',
    'ROLEPLAYING'        : '"None", "Accepted", "Encouraged", "Enforced"',
    'TRAINING SYSTEM'    : '"None", "Level", "Skill", "Both"',
    'WORLD ORIGINALITY'  : '"All Stock", "Mostly Stock", "Mostly Original", "All Original"',
    'ATCP'               : 'Supports ATCP? "1" or "0"',
    'MSDP'               : 'Supports MSDP? "1" or "0"',
    'SSL'                : 'SSL port, use "0" if not supported.',
    'ZMP'                : 'Supports ZMP? "1" or "0"',
}
