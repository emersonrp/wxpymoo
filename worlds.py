import wx
import re
import os
import collections
import prefs

class World(dict):

    _defaults = {
        'port'         : '7777',
        'auto_login'   : False,
        'login_script' : 'connect %u %p',
    }

    def __init__(self, data):
        data = data or World._defaults
        for f in data:
            if data.get(f) is not None: self[f] = data.get(f)

    # TODO - enumerate what the various keys might be and use Write() WriteBool() etc as appropriate
    def save(self):
        _config = wx.FileConfig(localFilename = str(prefs.prefs_dir() / 'worlds'))
        worldname = re.sub(r'\W', '_', str(self.get('name')))

        _config.DeleteGroup(worldname)
        _config.SetPath(worldname)

        for f in self:
            if self.get(f): _config.Write(f, str(self.get(f)))

        _config.SetPath('/')
        _config.Flush()

        mainwindow = wx.GetApp().GetTopWindow()
        if mainwindow:
            mainwindow.rebuildShortlist()

worlds      = collections.OrderedDict({})
_defaults   = {}
def Initialize():
    global worlds, _defaults
    _config = wx.FileConfig(localFilename = str(prefs.prefs_dir() / 'worlds'))

    # loop worlds...
    g_more, worldname, g_index = _config.GetFirstGroup()
    if g_more:  # do we have anything at all from the config file?
        while g_more: # yes, loop and fill stuff out.

            # TODO - enumerate what the various keys might be and use Read() ReadBool() etc as appropriate
            _config.SetPath(worldname)

            worlddata = {}

            # loop data lines inside each world....
            e_more, dataname, e_index = _config.GetFirstEntry()
            while e_more:
                worlddata[dataname] = _config.Read(dataname)
                # ew boolean handling.  Maybe go thru prefs to do this in one place
                if worlddata[dataname] == "True" : worlddata[dataname] = True
                if worlddata[dataname] == "False": worlddata[dataname] = False
                e_more, dataname, e_index = _config.GetNextEntry(e_index)

            # build the World object
            worlds[worlddata['name']] = World(worlddata)

            # carry on, back to the top for the next world
            _config.SetPath('/')
            g_more, worldname, g_index = _config.GetNextGroup(g_index)

    else:  # nothing from config file, grab the initial_worlds data
        import json
        path = wx.GetApp().path
        initial_worlds = json.load(open(os.path.join(path, 'initial_worlds.json'),'r'))

        for world_data in initial_worlds:
            world = World(world_data)
            world.save()
            worlds[world.get('name')] = world

