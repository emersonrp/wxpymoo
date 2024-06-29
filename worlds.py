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
_defaults   = {}
def Initialize():
    global worlds, _defaults
    worldsconfig = wx.FileConfig(localFilename = str(prefs.get_prefs_dir() / 'worlds'))

    # loop worlds...
    g_more, worldname, g_index = worldsconfig.GetFirstGroup()
    if g_more:  # do we have anything at all from the config file?
        while g_more: # yes, loop and fill stuff out.

            # TODO - enumerate what the various keys might be and use Read() ReadBool() etc as appropriate
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
                # ew boolean handling.  Maybe go thru prefs to do this in one place
                if worlddata[dataname] == "True" : worlddata[dataname] = True
                if worlddata[dataname] == "False": worlddata[dataname] = False
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

